"""
load_demo.py —— 载入 data/demo_financials.json 到财务库（清空重建）

用法：
  python load_demo.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from app.tools import db

DEMO = os.path.join(os.path.dirname(__file__), "data", "demo_financials.json")

def main():
    with open(DEMO, encoding="utf-8") as f:
        data = json.load(f)
    conn = db.get_conn()
    c = conn.cursor()
    c.executescript("""
    DROP TABLE IF EXISTS companies;
    DROP TABLE IF EXISTS financials;
    CREATE TABLE companies(
      code TEXT PRIMARY KEY, name TEXT, industry TEXT, risk_level TEXT, credit_rating TEXT
    );
    CREATE TABLE financials(
      code TEXT, fiscal_year INTEGER, revenue REAL, cogs REAL, net_income REAL,
      total_assets REAL, total_liabilities REAL, current_assets REAL, current_liabilities REAL,
      inventory REAL, receivables REAL, equity REAL, ebitda REAL, fcf REAL,
      PRIMARY KEY(code, fiscal_year)
    );
    """)
    c.executemany("INSERT INTO companies VALUES(?,?,?,?,?)",
                  [(x["code"], x["name"], x["industry"], x["risk_level"], x["credit_rating"]) for x in data["companies"]])
    cols = ["code", "fiscal_year", "revenue", "cogs", "net_income", "total_assets", "total_liabilities",
            "current_assets", "current_liabilities", "inventory", "receivables", "equity", "ebitda", "fcf"]
    c.executemany("INSERT INTO financials VALUES(" + ",".join(["?"] * len(cols)) + ")",
                  [tuple(r[k] for k in cols) for r in data["financials"]])
    conn.commit(); conn.close()
    print("已载入 demo 数据：", len(data["companies"]), "家公司，", len(data["financials"]), "条财务记录")
    print("估值/信用参数见 data/demo_financials.json 的 valuation 段")

if __name__ == "__main__":
    main()
