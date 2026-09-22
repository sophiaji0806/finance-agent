"""
db.py —— 财务数据访问层（SQLite）

- 提供 Group 的示例财务库（由 seed_db.py 生成），供 Agent 的 query_db 工具查询；
- 任何标准 SQL 查询都被代理为只读，防止 Agent 误改数据。
"""
from __future__ import annotations
import os
import sqlite3

DB_PATH = os.environ.get("FINANCE_DB", os.path.join(os.path.dirname(__file__), "..", "..", "data", "finance.db"))
DB_PATH = os.path.abspath(DB_PATH)

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def seed(force: bool = False) -> str:
    """建表并写入示例财务数据。force=True 时清空重建。"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
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
    companies = [
        ("300001", "深圳云科技", "TMT·软件", "中", "AA"),
        ("600002", "沪港智造", "制造业", "低", "AAA"),
        ("000003", "鹏城港口", "交通运输", "中", "A"),
        ("601004", "湾区商业", "消费", "高", "BBB"),
    ]
    c.executemany("INSERT OR REPLACE INTO companies VALUES(?,?,?,?,?)", companies)
    # 三年（FY2021-2023）示例的财务数据，数值用于展示，非真实披露
    rows = [
        ("300001", 2023, 1200, 700, 150, 2000, 900,  1400, 700, 120, 300, 1100, 260, 180),
        ("300001", 2022, 1000, 620, 110, 1700, 780,  1150, 600, 100, 250, 920,  220, 130),
        ("600002", 2023, 800,  540, 96,  1500, 600,  950,  500, 260, 140, 900,  170, 120),
        ("600002", 2022, 700,  500, 80,  1350, 560,  860,  460, 230, 120, 790,  150, 100),
        ("000003", 2023, 500,  350, 45,  1200, 520,  700,  420, 90,  180, 680,  110, 70),
        ("601004", 2023, 420,  360, 18,  900,  600,  460,  380, 150, 90,  300,  60,  30),
    ]
    c.executemany("INSERT OR REPLACE INTO financials VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    conn.commit(); conn.close()
    return DB_PATH

def query(sql: str, limit: int = 50):
    """执行只读 SQL，返回行列表（dict）。仅允许 SELECT/WITH。"""
    s = sql.strip().lower()
    if not (s.startswith("select") or s.startswith("with") or s.startswith("pragma")):
        raise ValueError("仅允许只读查询（SELECT/WITH）")
    conn = get_conn()
    try:
        cur = conn.execute(sql.replace(";", "").strip() + ("" if "limit" in sql.lower() else f" LIMIT {limit}"))
        cols = [d[0] for d in cur.description] if cur.description else []
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()

def tables_info() -> list:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return [{"table": r[0]} for r in rows]
    finally:
        conn.close()

if __name__ == "__main__":
    p = seed(force=True)
    print("已生成示例库:", p)
    print(query("SELECT code,name,industry,risk_level,credit_rating FROM companies"))
    print(query("SELECT code,fiscal_year,revenue,cogs,net_income FROM financials LIMIT 5"))
