"""
financial_models.py —— 财务分析核心模型（纯 Python，无第三方依赖，可离线验证）

本模块提供 Agent 的"财务工具集"：从财务报表/指标，到估值与信用风险模型。
每一步都是可解释的标准公式，便于逐行讲清与单测。

支持的模型：
  比率类    gross_margin / net_margin / turnover / current_ratio / quick_ratio /
            debt_to_equity / roe / roa / inventory_turnover
  估值类    firm_value_dcf（FCFF + WACC + 终值）/ wacc / irr（牛顿迭代）
  信用类    expected_loss（ECL ≈ PD × LGD × EAD）/ lgd_recovery
"""
from __future__ import annotations
import math
from typing import Optional, Sequence

# ---------- 比率类 ----------
def gross_margin(revenue: float, cogs: float) -> float:
    """毛利率 = (收入 - 营业成本) / 收入。"""
    if revenue == 0: return 0.0
    return (revenue - cogs) / revenue

def net_margin(net_income: float, revenue: float) -> float:
    """净利率 = 净利润 / 收入。"""
    if revenue == 0: return 0.0
    return net_income / revenue

def asset_turnover(revenue: float, total_assets: float) -> float:
    """总资产周转率 = 收入 / 资产。衡量资产使用效率。"""
    if total_assets == 0: return 0.0
    return revenue / total_assets

def inventory_turnover(cogs: float, inventory: float) -> float:
    """存货周转率 = 营业成本 / 存货。"""
    if inventory == 0: return 0.0
    return cogs / inventory

def receivable_turnover(revenue: float, receivables: float) -> float:
    """应收周转率 = 收入 / 应收。"""
    if receivables == 0: return 0.0
    return revenue / receivables

def current_ratio(current_assets: float, current_liabilities: float) -> float:
    """流动比率 = 流动资产 / 流动负债。短期偿债能力。"""
    if current_liabilities == 0: return 0.0
    return current_assets / current_liabilities

def quick_ratio(current_assets: float, inventory: float, current_liabilities: float) -> float:
    """速动比率 = (流动资产 - 存货) / 流动负债。剔除存货后的短期偿债能力。"""
    if current_liabilities == 0: return 0.0
    return (current_assets - inventory) / current_liabilities

def debt_to_equity(total_liabilities: float, equity: float) -> float:
    """资产负债率（负债/权益）。杠杆水平。"""
    if equity == 0: return 0.0
    return total_liabilities / equity

def roe(net_income: float, equity: float) -> float:
    """净资产收益率 ROE = 净利润 / 权益。"""
    if equity == 0: return 0.0
    return net_income / equity

def roa(net_income: float, total_assets: float) -> float:
    """总资产收益率 ROA = 净利润 / 资产。"""
    if total_assets == 0: return 0.0
    return net_income / total_assets

# ---------- 估值类 ----------
def wacc(equity: float, debt: float, cost_equity: float, cost_debt: float, tax_rate: float) -> float:
    """
    加权平均资本成本 WACC = E/(E+D)·Re + D/(E+D)·Rd·(1-T)
    E/(E+D)、D/(E+D) 为权重；Rd 税前，×(1-T) 复税盾。
    """
    total = equity + debt
    if total == 0: return 0.0
    we, wd = equity / total, debt / total
    return we * cost_equity + wd * cost_debt * (1 - tax_rate)

def firm_value_dcf(fcf: Sequence[float], discount_rate: float,
                   terminal_growth: float = 0.02, horizon: Optional[int] = None) -> float:
    """
    收益法（DCF）企业整体价值 = Σ FCF_t/(1+r)^t + 终值/(1+r)^N
    终值（Gordon）= FCF_N·(1+g)/(r-g)。
    fcf 为预测期自由现金流列表；horizon 默认取 fcf 长度。
    """
    fcfs = list(fcf)
    if not fcfs: return 0.0
    n = len(fcfs)
    pv = sum(cf / (1 + discount_rate) ** (t + 1) for t, cf in enumerate(fcfs))
    # 终值：用最后一期现金流按永续增长折现
    r = discount_rate
    terminal = fcfs[-1] * (1 + terminal_growth) / (r - terminal_growth) if r > terminal_growth else 0.0
    return pv + terminal / (1 + r) ** n

def _npv(rate: float, cashflows: Sequence[float]) -> float:
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows))

def irr(cashflows: Sequence[float], guess: float = 0.1, tol: float = 1e-9, max_iter: int = 100) -> Optional[float]:
    """
    内部收益率 IRR：使 NPV=0 的贴现率。用牛顿迭代法求根。
    cashflows[0] 为初始投入（负数），其余为各期现金流入。
    """
    def derivative(r: float) -> float:
        return sum(-t * cf / (1 + r) ** (t + 1) for t, cf in enumerate(cashflows))
    r = guess
    for _ in range(max_iter):
        v = _npv(r, cashflows)
        dv = derivative(r)
        if abs(dv) < 1e-12: break
        nxt = r - v / dv
        if abs(nxt - r) < tol: return nxt
        r = nxt
    return None

# ---------- 信用类 ----------
def expected_loss(pd: float, lgd: float, ead: float) -> float:
    """预期信用损失 ECL ≈ PD × LGD × EAD。IFRS9 减值常用。"""
    return pd * lgd * ead

def lgd_recovery(exposure: float, recovered: float, costs: float = 0.0) -> float:
    """违约损失率 LGD = 1 - (回收 - 处置成本) / 敞口。"""
    if exposure == 0: return 0.0
    return 1 - (recovered - costs) / exposure


if __name__ == "__main__":
    # 自检示例
    print("毛利率", round(gross_margin(100, 60), 4))
    print("WACC", round(wacc(equity=60, debt=40, cost_equity=0.12, cost_debt=0.05, tax_rate=0.25), 4))
    print("DCF", round(firm_value_dcf([100, 110, 120], 0.10, 0.03), 2))
    print("IRR", round(irr([-1000, 300, 350, 400, 350]) or 0, 4))
    print("ECL", round(expected_loss(0.02, 0.4, 1_000_000), 2))
