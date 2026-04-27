from __future__ import annotations

import subprocess
import sys
import webbrowser
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
REPORT_PATH = ROOT_DIR / "reports" / "index.html"


def main() -> int:
    pytest_args = sys.argv[1:] or ["-q"]
    result = subprocess.run([sys.executable, "-m", "pytest", *pytest_args], cwd=ROOT_DIR)
    subprocess.run([sys.executable, "scripts/build_observation_report.py"], cwd=ROOT_DIR, check=False)
    if REPORT_PATH.exists():
        webbrowser.open(REPORT_PATH.resolve().as_uri())
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
