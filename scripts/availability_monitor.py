"""Run health probes and append one availability record to availability_history.jsonl.

Called by cron every few hours. Exits 0 if all services are up, 1 otherwise.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import requests
from configs.settings import ACCOUNTING_SETTINGS, ARTIFACTS_DIR, CRM_SETTINGS

HISTORY_PATH = ARTIFACTS_DIR / "availability_history.jsonl"
PROBE_TIMEOUT = 10

PROBES = [
    {"service": "crm",        "settings": CRM_SETTINGS,        "path": "/health"},
    {"service": "crm",        "settings": CRM_SETTINGS,        "path": "/api/v1/customers/ping"},
    {"service": "accounting", "settings": ACCOUNTING_SETTINGS, "path": "/health"},
    {"service": "accounting", "settings": ACCOUNTING_SETTINGS, "path": "/api/v1/accounting/ping"},
]


def _probe(service: str, base_url: str, headers: dict, path: str) -> dict:
    url = f"{base_url}{path}"
    t0 = time.perf_counter()
    try:
        r = requests.get(url, headers=headers, timeout=PROBE_TIMEOUT)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "service": service,
            "path": path,
            "status_code": r.status_code,
            "elapsed_ms": elapsed_ms,
            "up": 200 <= r.status_code < 300,
            "error": None,
        }
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "service": service,
            "path": path,
            "status_code": 0,
            "elapsed_ms": elapsed_ms,
            "up": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def run_probes() -> dict:
    ts = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    t0 = time.perf_counter()

    probes = [
        _probe(p["service"], p["settings"].base_url, p["settings"].default_headers, p["path"])
        for p in PROBES
    ]
    duration_ms = round((time.perf_counter() - t0) * 1000, 2)

    by_service: dict[str, list[dict]] = {}
    for probe in probes:
        by_service.setdefault(probe["service"], []).append(probe)

    summary = {
        svc: {
            "up": all(p["up"] for p in ps),
            "avg_ms": round(sum(p["elapsed_ms"] for p in ps) / len(ps), 2),
        }
        for svc, ps in by_service.items()
    }

    return {
        "timestamp": ts,
        "duration_ms": duration_ms,
        "probes": probes,
        "summary": summary,
        "overall_up": all(s["up"] for s in summary.values()),
    }


def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    record = run_probes()

    with HISTORY_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    status_label = "UP  " if record["overall_up"] else "DOWN"
    print(f"[{record['timestamp']}] {status_label}  ({record['duration_ms']} ms total)")
    for p in record["probes"]:
        icon = "+" if p["up"] else "!"
        err = f"  — {p['error']}" if p["error"] else ""
        print(f"  [{icon}] {p['service']:<12} {p['path']:<36} HTTP {p['status_code']}  {p['elapsed_ms']} ms{err}")

    try:
        from scripts.build_availability_report import build_report
        report_path = build_report()
        print(f"Dashboard updated: {report_path}")
    except Exception as exc:
        print(f"Warning: dashboard not updated — {exc}", file=sys.stderr)

    sys.exit(0 if record["overall_up"] else 1)


if __name__ == "__main__":
    main()
