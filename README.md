# 智能财务分析 Agent（Finance Agent）

一个用 **LLM（DeepSeek）+ 工具调用（Function Calling）** 搭建的**智能财务分析 Agent**：输入一个财务问题，Agent 自动决定「查库 → 算财务模型 → 检索会计准则(RAG) → 运行计算脚本」的步骤组合，最后输出带**依据**的结构化分析报告。

> 定位：给 A 用的是**真实、可逐行讲清**的项目，用于求职（财务信息化 + AI Agent + AI Coding 方向）。

## 架构

```
用户问题
   │
   ▼
┌─────────────────────────────── App.agent.loop（主循环） ───────────────────────────────┐
│  system 提示词 + 工具集(TOOLS)  →  调 DeepSeek chat(tools)                               │
│      ▲        │ 返回 tool_calls                                                          │
│      │        ▼                                                                          │
│      └─── 执行工具(dispatch) → 结果回填为 tool 消息 → 继续迭代                            │
└──────────────────────────────────────────────────────────────────────────────────────── ┘
   │
   工具集（app.tools）
   ├─ query_db(sql)                  → 只读 SQL 查财务库（SQLite）
   ├─ calc_financial_model(model,..) → 毛利率/净利率/流动速动/资产负债率/ROE・ROA/周转/WACC/DCF/IRR/预期信用损失
   ├─ rag_search(q)                  → 会计准则・审计・估值・ML/NLP 知识检索（TF-IDF 轻量 RAG）
   └─ run_python(code)               → 子进程运行财务计算脚本（带超时）
```

- `app/tools/financial_models.py`  财务模型（纯 Python，公式标准，可单测）
- `app/tools/db.py`                SQLite 财务数据库 + 只读查询代理（禁止写）
- `app/tools/rag.py` + `app/knowledge/corpus.json`  轻量 TF-IDF 检索（无向量库依赖）
- `app/agent/loop.py`              Agent 主循环（function calling + tool trace）
- `app/main.py`                    FastAPI：`GET /`（网页界面）、`POST /api/agent/analyze`、`GET /api/rag/search`、`GET /tools`、`GET /health`
- `web/index.html`                 浏览器界面：输入问题 → 显示分析报告 + tool_trace 调用过程（面试可现场演示）
- 配套：`Dockerfile`、`.github/workflows/ci.yml`（CI）、`tests/`（pytest）

## 快速开始

```bash
cd finance-agent
pip install -r requirements-dev.txt
cp .env.example .env          # 填入 DeepSeek API Key
python -c "from app.tools import db; db.seed(force=True)"   # 生成示例财务库
uvicorn app.main:app --reload
```

接口示例：

```bash
# 健康检查
curl http://localhost:8000/health

# 工具清单
curl http://localhost:8000/tools

# RAG 检索
curl "http://localhost:8000/api/rag/search?q=新收入准则+时段+确认"

# 财务分析（跑 Agent）
curl -X POST http://localhost:8000/api/agent/analyze -H "Content-Type: application/json" \
  -d '{"query":"对比深圳云科技与湾区商业近三年毛利率、偿债能力与运营效率，并给出投资角度的建议"}'
```

## 安全与工程规范
- db 查询强制只读：仅允许 `SELECT / WITH / PRAGMA`。
- 代码执行：子进程隔离 + 超时 + 输出截断（非恶意场景的本地可信分析）。
- 结构化日志 `tool_trace`：每次工具调用（名称、参数、结果、耗时）都留痕，便于可观测与排查。
- 容器化：`docker build -t finance-agent . && docker run -p 8000:8000 --env-file .env finance-agent`。
- CI：push/pull_request 自动跑 pytest。

## 对应对口 JD（智能财务 + AI Agent + AI Coding）
- **AI Agent 架构 / Function Calling / RAG / 提示词工程** → loop.py + TOOLS + rag.py
- **Python 后端 + Web 框架 + 数据库** → FastAPI + SQLite + 财务模型
- **机器学习/NLP 原理** → corpus 中 ML/NLP 基础；财务模型含回归/比率等
- **容器化 / CI-CD / 系统监控与工程规范** → Dockerfile + GitHub Actions + tool_trace 日志
