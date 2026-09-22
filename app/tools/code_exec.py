"""
code_exec.py —— 让 Agent 运行一段 Python 财务脚本（子进程隔离 + 真实超时）

安全说明：子进程 `sys.executable -c code` 执行，配合 20s 超时与输出截断，
避免无限占用与过长输出；这不是安全沙箱（不用于恶意代码场景），仅作本地可信分析执行。
"""
from __future__ import annotations
import subprocess, sys, textwrap

TIMEOUT = float(__import__("os").environ.get("CODE_TIMEOUT", "20"))
MAX_OUT = 4000

def run(code: str) -> dict:
    safe = textwrap.dedent(code).strip()
    try:
        p = subprocess.run([sys.executable, "-c", safe], capture_output=True, text=True, timeout=TIMEOUT)
        return {
            "ok": p.returncode == 0,
            "exit_code": p.returncode,
            "stdout": (p.stdout or "")[-MAX_OUT:],
            "stderr": (p.stderr or "")[-MAX_OUT:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "exit_code": None, "stdout": "", "stderr": f"执行超时（>{TIMEOUT}s）", "timed_out": True}
