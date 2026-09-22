"""main.py —— FastAPI 入口：暴露 Agent 分析、工具清单、RAG 检索、健康检查。"""
from __future__ import annotations
import os
from dotenv import load_dotenv
load_dotenv()  # 在导入 loop/工具前读取 .env，供 DEEPSEEK_API_KEY 等使用

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.tools import TOOLS, db
from app.tools.rag import RAG
from app.agent.loop import analyze as agent_analyze

app = FastAPI(title="财务分析 Agent", version="0.1.0")

class AnalyzeRequest(BaseModel):
    query: str

WEB_INDEX = os.path.join(os.path.dirname(__file__), "..", "web", "index.html")

@app.get("/")
def index():
    """浏览器打开 http://localhost:8000/ 时的网页界面。"""
    return FileResponse(WEB_INDEX)

@app.get("/health")
def health():
    return {"status": "ok", "tools": len(TOOLS)}

@app.get("/tools")
def tools():
    return {"tools": [{"name": t["function"]["name"], "description": t["function"]["description"]} for t in TOOLS]}

@app.get("/api/rag/search")
def rag_search(q: str, k: int = 3):
    return {"results": RAG.search(q, k)}

@app.get("/api/db/seed")
def reseed(force: bool = True):
    path = db.seed(force=force)
    return {"seeded": path}

@app.post("/api/agent/analyze")
def analyze(req: AnalyzeRequest):
    try:
        return agent_analyze(req.query)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {e}")
