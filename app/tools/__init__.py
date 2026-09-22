"""
tools —— Agent 财务工具集
每项定义（JSON Schema, OpenAI function-calling 格式）与执行器。
"""
from . import financial_models as fm
from . import db
from .rag import RAG
from .code_exec import run as run_code

def _handle_calc(model_name: str, params: dict) -> dict:
    """按名称调用财务模型，返回结构化结果。"""
    m = model_name.lower()
    fns = {
        "gross_margin": lambda: {"gross_margin": fm.gross_margin(params["revenue"], params["cogs"])},
        "net_margin": lambda: {"net_margin": fm.net_margin(params["net_income"], params["revenue"])},
        "current_ratio": lambda: {"current_ratio": fm.current_ratio(params["current_assets"], params["current_liabilities"])},
        "quick_ratio": lambda: {"quick_ratio": fm.quick_ratio(params["current_assets"], params["inventory"], params["current_liabilities"])},
        "debt_to_equity": lambda: {"debt_to_equity": fm.debt_to_equity(params["total_liabilities"], params["equity"])},
        "roe": lambda: {"roe": fm.roe(params["net_income"], params["equity"])},
        "roa": lambda: {"roa": fm.roa(params["net_income"], params["total_assets"])},
        "asset_turnover": lambda: {"asset_turnover": fm.asset_turnover(params["revenue"], params["total_assets"])},
        "inventory_turnover": lambda: {"inventory_turnover": fm.inventory_turnover(params["cogs"], params["inventory"])},
        "receivable_turnover": lambda: {"receivable_turnover": fm.receivable_turnover(params["revenue"], params["receivables"])},
        "wacc": lambda: {"wacc": fm.wacc(params["equity"], params["debt"], params["cost_equity"], params["cost_debt"], params["tax_rate"])},
        "dcf": lambda: {"firm_value": fm.firm_value_dcf(params["fcf"], params["discount_rate"], params.get("terminal_growth", 0.02))},
        "irr": lambda: {"irr": fm.irr(params["cashflows"])},
        "expected_loss": lambda: {"ecl": fm.expected_loss(params["pd"], params["lgd"], params["ead"])},
    }
    if m not in fns: raise ValueError(f"未知模型: {model_name}（可选: {sorted(fns)}）")
    return fns[m]()

# ---- 工具定义（OpenAI function-calling schema）----
TOOLS = [
  {
    "type": "function",
    "function": {
      "name": "query_db",
      "description": "对财务数据库执行只读 SQL 查询（SELECT/WITH）。用于取公司财务数据、跨年对比、筛主体等。",
      "parameters": {"type": "object", "properties": {"sql": {"type": "string", "description": "标准 SQL，仅 SELECT/WITH"}}, "required": ["sql"]},
    },
  },
  {
    "type": "function",
    "function": {
      "name": "calc_financial_model",
      "description": "计算财务模型/指标，如毛利率、净利率、流动/速动比率、资产负债率、ROE/ROA、周转率、WACC、DCF(dcf)、IRR(irr)、预期信用损失。",
      "parameters": {"type": "object", "properties": {
        "model_name": {"type": "string", "description": "模型名，如 gross_margin/net_margin/current_ratio/quick_ratio/debt_to_equity/roe/roa/asset_turnover/inventory_turnover/wacc/dcf/irr/expected_loss"},
        "params": {"type": "object", "description": "模型参数，key 见具体模型（如 revenue/cogs/net_income/equity/debt 等）"}
      }, "required": ["model_name", "params"]},
    },
  },
  {
    "type": "function",
    "function": {
      "name": "rag_search",
      "description": "在会计准则/审计/估值/金融知识库做语义检索，用于回答涉及准则、模型定义、专业术语的问题（RAG）。",
      "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "要检索的问题或关键词"}}, "required": ["query"]},
    },
  },
  {
    "type": "function",
    "function": {
      "name": "run_python",
      "description": "执行一小段 Python 财务运算脚本（如复现某个计算、格式化输出），返回 stdout。",
      "parameters": {"type": "object", "properties": {"code": {"type": "string", "description": "合法的 Python 代码，print 输出"}}, "required": ["code"]},
    },
  },
]

def dispatch(name: str, args: dict) -> dict:
    if name == "query_db":
        return {"rows": db.query(args["sql"])}
    if name == "calc_financial_model":
        return _handle_calc(args["model_name"], args.get("params", {}))
    if name == "rag_search":
        return {"results": RAG.search(args["query"])}
    if name == "run_python":
        return run_code(args["code"])
    return {"error": f"未知工具: {name}"}
