import math
from app.tools.financial_models import (gross_margin, net_margin, wacc, firm_value_dcf,
                                        irr, expected_loss, current_ratio, debt_to_equity)

def test_gross_margin():
    assert abs(gross_margin(100, 60) - 0.4) < 1e-9
    assert gross_margin(0, 0) == 0.0

def test_net_margin():
    assert abs(net_margin(50, 200) - 0.25) < 1e-9

def test_wacc():
    # E=60 Re=0.12, D=40 Rd=0.05 T=0.25 → 0.6*0.12+0.4*0.05*0.75=0.087
    assert abs(wacc(60, 40, 0.12, 0.05, 0.25) - 0.087) < 1e-9

def test_dcf():
    # [100,110,120] r=0.10 g=0.03 → PV≈ 90.91+90.91+90.16 + 终值折现
    v = firm_value_dcf([100, 110, 120], 0.10, 0.03)
    assert v > 0 and v < 2000

def test_irr():
    r = irr([-1000, 300, 350, 400, 350])
    assert r is not None and abs(r - 0.1448) < 0.01

def test_expected_loss():
    assert abs(expected_loss(0.02, 0.4, 1_000_000) - 8000) < 1e-6

def test_current_ratio():
    assert abs(current_ratio(1400, 700) - 2.0) < 1e-9

def test_debt_to_equity():
    assert abs(debt_to_equity(900, 1100) - 900/1100) < 1e-9
