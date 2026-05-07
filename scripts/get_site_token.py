"""Obtain a fresh Bearer JWT from back.dreamisland.ru and optionally update .env.

Usage:
    python scripts/get_site_token.py              # print token to stdout
    python scripts/get_site_token.py --update-env # write token to .env file
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import requests
from dotenv import load_dotenv

load_dotenv(ROOT_DIR / ".env", override=False)

import os

LOGIN_URL = "https://back.dreamisland.ru/api/security/login"
ENV_KEY = "DREAMCRM_MOBILE_SITE_AUTHORIZATION"


def get_token(username: str, password: str) -> str:
    resp = requests.post(
        LOGIN_URL,
        json={"username": username, "password": password},
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=15,
    )
    if resp.status_code != 200:
        sys.exit(f"Login failed: HTTP {resp.status_code}\n{resp.text[:400]}")
    data = resp.json()
    token = data.get("access_token") or data.get("token")
    if not token:
        sys.exit(f"No access_token in response: {list(data.keys())}")
    token_type = data.get("token_type", "Bearer")
    return f"{token_type} {token}"


def update_env_file(env_path: Path, key: str, value: str) -> None:
    text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    new_line = f"{key}={value}"
    if pattern.search(text):
        text = pattern.sub(new_line, text)
    else:
        text = text.rstrip("\n") + f"\n{new_line}\n"
    env_path.write_text(text, encoding="utf-8")
    print(f"Updated {key} in {env_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh mobile-site Bearer token")
    parser.add_argument("--update-env", action="store_true", help="Write token to .env")
    args = parser.parse_args()

    username = os.getenv("DREAMCRM_MOBILE_USERNAME") or os.getenv("DREAMCRM_MOBILE_EMAIL", "")
    password = os.getenv("DREAMCRM_MOBILE_PASSWORD", "")

    if not username or not password:
        sys.exit(
            "Set DREAMCRM_MOBILE_USERNAME (or DREAMCRM_MOBILE_EMAIL) and "
            "DREAMCRM_MOBILE_PASSWORD in .env"
        )

    token = get_token(username, password)
    print(f"\n{ENV_KEY}={token}\n")

    if args.update_env:
        update_env_file(ROOT_DIR / ".env", ENV_KEY, token)
        print("Run 'python scripts/availability_monitor.py' to use the new token.")


if __name__ == "__main__":
    main()
