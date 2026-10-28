import os
import sys
from datetime import datetime


# =====================
# Debug 开关
# =====================

DEBUG = os.getenv("DEBUG", "True").lower() == "true"


def log(title, content):
    """输出调试日志到 stderr，避免污染 MCP stdio 协议。"""

    if not DEBUG:
        return

    print("\n========== DEBUG ==========", file=sys.stderr)

    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] {title}",
        file=sys.stderr,
    )

    print(content, file=sys.stderr)

    print("==========================", file=sys.stderr)