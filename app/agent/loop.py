"""
loop.py —— 财务分析 Agent 主循环

流程：
  用户问题 → 组装 system 提示词 + 工具定义 → 调 DeepSeek(chat, tools) →
  若返回 tool_calls：逐一执行（dispatch）→ 把结果作为 tool 消息回填 → 继续 →
  直到模型不再调用工具 → 输出最终分析与结论。

记录完整 tool_trace，便于可观测（Trace/日志）与面试逐行讲清。
"""
from __future__ import annotations
import json, os, time
import requests

from app.tools import TOOLS, dispatch

BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
MAX_ITERS = int(os.environ.get("AGENT_MAX_ITERS", "10"))

SYSTEM_PROMPT = """你是一位资深的智能财务分析 Agent。你的任务是：利用财务数据、财务模型与会计准则知识，为客户/公司做深度财务分析与洞察。

工作方式：
1. 需要数据时，先用 query_db 查询财务库（先用 SELECT * FROM companies 了解主体，再 SELECT ... FROM financials）；
2. 需要算指标时，用 calc_financial_model（如毛利率、净利率、流动/速动、资产负债率、ROE/ROA、周转、WACC、DCF、IRR、预期信用损失）；
3. 涉及准则/术语/模型定义时，用 rag_search 检索知识库（保证回答有依据）；
4. 需要复现计算或格式化时，用 run_python。

输出要求：在【结论】给出中文要点与关键数字；在【指标】用 markdown 表格列出关键财务指标（同比变化）；在【依据】引用数据来源（查了哪张表/哪个模型/哪条知识）；在【建议】给出 2-3 条可执行建议。所有数字必须来自工具真实结果，不得编造。
"""

def _chat(messages):
    r = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
        json={"model": MODEL, "messages": messages, "tools": TOOLS, "tool_choice": "auto", "temperature": 0.2},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]

def analyze(question: str) -> dict:
    if not API_KEY:
        raise RuntimeError("未配置 DEEPSEEK_API_KEY（见 .env.example）")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]
    trace = []
    start = time.time()
    for _ in range(MAX_ITERS):
        msg = _chat(messages)
        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            return {"answer": msg.get("content", ""), "trace": trace, "iterations": len(trace), "elapsed_ms": int((time.time()-start)*1000)}
        messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": tool_calls})
        for tc in tool_calls:
            fn = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"] or "{}")
            t0 = time.time()
            try:
                result = dispatch(fn, args)
            except Exception as e:
                result = {"error": str(e)}
            trace.append({"tool": fn, "args": args, "result": result, "ms": int((time.time()-t0)*1000)})
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(result, ensure_ascii=False)})
    return {"answer": "已达到最大迭代次数，未能收敛。", "trace": trace, "iterations": len(trace), "elapsed_ms": int((time.time()-start)*1000)}
