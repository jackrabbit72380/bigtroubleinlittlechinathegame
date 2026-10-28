"""Regenerate every generated asset and validate the result.

Run:  python3 tools/build_all.py
"""

from __future__ import annotations

import os
import subprocess
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))


def run(script):
    print(f"$ python3 tools/{script}")
    result = subprocess.run([sys.executable, os.path.join(TOOLS, script)])
    return result.returncode


def main():
    for script in ("build_stages.py", "build_chars.py", "validate.py"):
        code = run(script)
        if code != 0:
            print(f"\n{script} failed (exit {code})")
            return code
    print("\nAll assets rebuilt and validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
