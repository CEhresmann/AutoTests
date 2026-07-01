"""Build reports/availability.html from artifacts/availability_history.jsonl.

Can be run standalone to regenerate the dashboard without running probes:
    python scripts/build_availability_report.py
"""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from html import escape
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from configs.settings import ARTIFACTS_DIR, REPORTS_DIR

HISTORY_PATH = ARTIFACTS_DIR / "availability_history.jsonl"
REPORT_PATH = REPORTS_DIR / "availability.html"

SLOW_MS = 500   # amber threshold
DOWN_MS = 2000  # treated as degraded even if technically up


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _load_records() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    records = []
    with HISTORY_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return sorted(records, key=lambda r: r["timestamp"])


def _ts(record: dict) -> datetime:
    return datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))


def _uptime_pct(records: list[dict], service: str, hours: int) -> float | None:
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    relevant = [r for r in records if _ts(r) >= cutoff and service in r.get("summary", {})]
    if not relevant:
        return None
    up = sum(1 for r in relevant if r["summary"][service]["up"])
    return round(up / len(relevant) * 100, 1)


def _find_incidents(records: list[dict], service: str) -> list[dict]:
    incidents: list[dict] = []
    current: dict | None = None
    for r in records:
        if service not in r.get("summary", {}):
            continue
        is_up = r["summary"][service]["up"]
        if not is_up:
            if current is None:
                current = {"start": r["timestamp"], "end": r["timestamp"], "checks": 1}
            else:
                current["end"] = r["timestamp"]
                current["checks"] += 1
        else:
            if current is not None:
                incidents.append(current)
                current = None
    if current is not None:
        incidents.append(current)
    return list(reversed(incidents))[:10]


def _extract_services(records: list[dict]) -> list[str]:
    seen: set[str] = set()
    for r in records:
        seen.update(r.get("summary", {}).keys())
    return sorted(seen)


# ---------------------------------------------------------------------------
# HTML building blocks
# ---------------------------------------------------------------------------

_SERVICE_COLORS = {
    "crm":        ("#0f766e", "#ccfbf1"),
    "accounting": ("#7c3aed", "#ede9fe"),
}


def _color(service: str) -> tuple[str, str]:
    return _SERVICE_COLORS.get(service, ("#374151", "#f3f4f6"))


def _pct_color(pct: float | None) -> str:
    if pct is None:
        return "#9ca3af"
    if pct >= 99:
        return "#16a34a"
    if pct >= 95:
        return "#d97706"
    return "#dc2626"


def _render_ribbon(records: list[dict], service: str, n: int = 60) -> str:
    tail = [r for r in records if service in r.get("summary", {})][-n:]
    if not tail:
        return '<p class="muted">Нет данных</p>'

    blocks: list[str] = []
    for r in tail:
        s = r["summary"][service]
        ts_label = escape(r["timestamp"])
        ms_label = f"{s['avg_ms']} ms"
        if not s["up"]:
            css = "blk down"
            title = f"DOWN — {ts_label}"
        elif s["avg_ms"] > SLOW_MS:
            css = "blk slow"
            title = f"SLOW {ms_label} — {ts_label}"
        else:
            css = "blk up"
            title = f"UP {ms_label} — {ts_label}"
        blocks.append(f'<span class="{css}" title="{title}"></span>')
    return (
        '<div class="ribbon">'
        + "".join(blocks)
        + f'<span class="muted ribbon-label">← {len(tail)} проверок (старые слева)</span>'
        + "</div>"
    )


def _render_service_card(records: list[dict], service: str) -> str:
    last_record = next(
        (r for r in reversed(records) if service in r.get("summary", {})), None
    )
    ink, bg = _color(service)

    if last_record is None:
        status_html = '<span class="status-badge unknown">Нет данных</span>'
        ms_html = "—"
    else:
        s = last_record["summary"][service]
        if s["up"]:
            status_html = '<span class="status-badge up">ONLINE</span>'
        else:
            status_html = '<span class="status-badge down">OFFLINE</span>'
        ms_html = f'{s["avg_ms"]} ms'

    up24 = _uptime_pct(records, service, 24)
    up7d = _uptime_pct(records, service, 168)

    def _pct_str(v: float | None) -> str:
        return f"{v}%" if v is not None else "—"

    last_ts = last_record["timestamp"] if last_record else "—"

    return f"""
    <div class="card" style="border-top: 4px solid {ink}; background: {bg}20;">
      <div class="card-head">
        <span class="card-title" style="color:{ink}">{escape(service.upper())}</span>
        {status_html}
      </div>
      <div class="card-stats">
        <div class="cstat">
          <strong style="color:{_pct_color(up24)}">{_pct_str(up24)}</strong>
          <span>Uptime 24 ч</span>
        </div>
        <div class="cstat">
          <strong style="color:{_pct_color(up7d)}">{_pct_str(up7d)}</strong>
          <span>Uptime 7 дней</span>
        </div>
        <div class="cstat">
          <strong>{ms_html}</strong>
          <span>Ответ (последний)</span>
        </div>
      </div>
      <div class="ribbon-wrap">
        {_render_ribbon(records, service)}
      </div>
      <p class="muted last-check">Последняя проверка: {escape(last_ts)}</p>
    </div>
    """


def _render_incidents(records: list[dict], services: list[str]) -> str:
    all_incidents: list[dict] = []
    for svc in services:
        for inc in _find_incidents(records, svc):
            all_incidents.append({"service": svc, **inc})
    all_incidents.sort(key=lambda i: i["start"], reverse=True)
    if not all_incidents:
        return '<p class="muted">Зафиксированных инцидентов нет.</p>'
    rows = []
    for inc in all_incidents[:20]:
        ink, _ = _color(inc["service"])
        rows.append(
            f'<tr>'
            f'<td><span style="color:{ink};font-weight:700">{escape(inc["service"].upper())}</span></td>'
            f'<td>{escape(inc["start"])}</td>'
            f'<td>{escape(inc["end"])}</td>'
            f'<td>{inc["checks"]}</td>'
            f'</tr>'
        )
    return (
        "<table><thead><tr>"
        "<th>Сервис</th><th>Начало</th><th>Конец</th><th>Проверок упавших</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _render_run_log(records: list[dict], services: list[str]) -> str:
    if not records:
        return '<p class="muted">Нет данных.</p>'
    tail = list(reversed(records[-40:]))
    rows = []
    for r in tail:
        cells = [f'<td class="muted">{escape(r["timestamp"])}</td>']
        for svc in services:
            s = r.get("summary", {}).get(svc)
            if s is None:
                cells.append("<td>—</td>")
            elif s["up"]:
                ms = s["avg_ms"]
                color = "#16a34a" if ms < SLOW_MS else "#d97706"
                cells.append(f'<td style="color:{color}">✓ {ms} ms</td>')
            else:
                cells.append('<td style="color:#dc2626">✗ DOWN</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")

    service_headers = "".join(f"<th>{escape(s.upper())}</th>" for s in services)
    return (
        "<table><thead><tr><th>Timestamp</th>"
        + service_headers
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _chart_data(records: list[dict], services: list[str]) -> str:
    tail = records[-48:]
    labels = json.dumps([r["timestamp"] for r in tail], ensure_ascii=False)
    palette = [ink for ink, _ in (_color(s) for s in services)]
    datasets = []
    for i, svc in enumerate(services):
        data = [
            r["summary"][svc]["avg_ms"] if svc in r.get("summary", {}) else None
            for r in tail
        ]
        color = palette[i % len(palette)]
        datasets.append(
            f'{{"label":{json.dumps(svc.upper()+" avg ms")},'
            f'"data":{json.dumps(data)},'
            f'"borderColor":"{color}",'
            f'"backgroundColor":"{color}22",'
            f'"tension":0.3,"fill":false,"spanGaps":true}}'
        )
    return f'{{"labels":{labels},"datasets":[{",".join(datasets)}]}}'


# ---------------------------------------------------------------------------
# Full report
# ---------------------------------------------------------------------------

def build_report() -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    records = _load_records()
    services = _extract_services(records) or ["crm", "accounting"]

    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    total_checks = len(records)

    service_cards = "\n".join(_render_service_card(records, svc) for svc in services)
    incidents_html = _render_incidents(records, services)
    run_log_html = _render_run_log(records, services)
    chart_json = _chart_data(records, services)

    overall_up = (
        records[-1]["overall_up"] if records else True
    )
    overall_badge = (
        '<span class="status-badge up">ВСЕ СЕРВИСЫ В НОРМЕ</span>'
        if overall_up
        else '<span class="status-badge down">ЕСТЬ ПРОБЛЕМЫ</span>'
    )

    html = f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="300">
  <title>DREAMCRM — Availability Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      --bg: #f5f1e8;
      --panel: #fffdf8;
      --ink: #1f2937;
      --muted: #6b7280;
      --line: #ded4c2;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; font-family: Georgia, serif;
      color: var(--ink);
      background: radial-gradient(circle at top left, #efe4cf 0, transparent 30%),
                  linear-gradient(180deg, #f8f4ec 0%, var(--bg) 100%);
    }}
    .wrap {{ width: min(1300px, calc(100% - 48px)); margin: 32px auto 56px; }}
    .hero, .panel {{
      background: var(--panel); border: 1px solid var(--line);
      border-radius: 18px; box-shadow: 0 10px 30px rgba(55,65,81,.08);
      padding: 24px; margin-bottom: 20px;
    }}
    h1, h2 {{ margin-top: 0; }}
    .hero-top {{ display: flex; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 8px; }}
    .status-badge {{
      display: inline-block; border-radius: 999px;
      padding: 4px 14px; font-size: 13px; font-weight: 700;
      font-family: Consolas, monospace; letter-spacing: .03em;
    }}
    .status-badge.up      {{ background: #dcfce7; color: #15803d; }}
    .status-badge.down    {{ background: #fee2e2; color: #991b1b; }}
    .status-badge.unknown {{ background: #f3f4f6; color: #6b7280; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }}
    .card {{
      border-radius: 16px; border: 1px solid var(--line);
      padding: 18px 20px;
    }}
    .card-head {{ display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }}
    .card-title {{ font-size: 18px; font-weight: 700; }}
    .card-stats {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }}
    .cstat {{
      flex: 1; min-width: 90px;
      border: 1px solid var(--line); border-radius: 12px;
      padding: 10px 12px; background: #fff;
    }}
    .cstat strong {{ display: block; font-size: 22px; }}
    .cstat span {{ font-size: 12px; color: var(--muted); }}
    .ribbon {{ display: flex; flex-wrap: wrap; gap: 3px; align-items: center; }}
    .ribbon-wrap {{ margin-bottom: 10px; }}
    .ribbon-label {{ font-size: 11px; color: var(--muted); margin-left: 6px; }}
    .blk {{
      display: inline-block; width: 12px; height: 30px;
      border-radius: 4px; cursor: default; transition: opacity .15s;
    }}
    .blk:hover {{ opacity: .75; }}
    .blk.up   {{ background: #22c55e; }}
    .blk.slow {{ background: #f59e0b; }}
    .blk.down {{ background: #ef4444; }}
    .last-check {{ font-size: 11px; color: var(--muted); margin: 0; }}
    .chart-box {{ position: relative; height: 280px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 9px 8px; text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 700; }}
    .muted {{ color: var(--muted); font-size: 12px; }}
    .meta {{ margin-top: 12px; font-size: 12px; color: var(--muted); }}
    .tabs-nav {{
      display: flex; gap: 4px;
      background: var(--panel); border: 1px solid var(--line);
      border-radius: 14px; padding: 5px;
      margin-bottom: 20px; box-shadow: 0 4px 12px rgba(55,65,81,.06);
      width: fit-content;
    }}
    .tab-link {{
      display: block; padding: 8px 22px;
      border-radius: 10px; text-decoration: none;
      color: var(--muted); font-size: 14px;
      font-family: Georgia, serif; transition: background .15s, color .15s;
    }}
    .tab-link:hover {{ background: var(--bg); color: var(--ink); }}
    .tab-link.active {{ background: var(--ink); color: #fff; }}
  </style>
</head>
<body>
<div class="wrap">

  <nav class="tabs-nav">
    <a href="availability.html" class="tab-link active">Доступность</a>
    <a href="index.html" class="tab-link">Покрытие API</a>
  </nav>

  <section class="hero">
    <div class="hero-top">
      <h1 style="margin:0">DREAMCRM — Availability Dashboard</h1>
      {overall_badge}
    </div>
    <p class="muted">Автоматически обновляется каждые 5 минут (meta refresh). Крон запускает зонды каждые 4 часа.</p>
    <p class="meta">Всего проверок: <strong>{total_checks}</strong> &nbsp;|&nbsp; Сгенерирован: {escape(generated_at)}</p>
  </section>

  <section class="panel">
    <h2>Статус сервисов</h2>
    <div class="cards">
      {service_cards}
    </div>
  </section>

  <section class="panel">
    <h2>Время ответа — тренд (последние 48 проверок)</h2>
    <div class="chart-box">
      <canvas id="rtChart"></canvas>
    </div>
  </section>

  <section class="panel">
    <h2>Инциденты</h2>
    {incidents_html}
  </section>

  <section class="panel">
    <h2>Журнал проверок (последние 40)</h2>
    {run_log_html}
  </section>

</div>

<script>
(function () {{
  const data = {chart_json};
  // Trim ISO timestamps to HH:MM for readability
  data.labels = data.labels.map(function(l) {{
    try {{ return l.substring(0, 16).replace('T', ' '); }} catch(e) {{ return l; }}
  }});
  new Chart(document.getElementById('rtChart').getContext('2d'), {{
    type: 'line',
    data: data,
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ position: 'bottom' }},
        tooltip: {{ mode: 'index', intersect: false }}
      }},
      scales: {{
        x: {{ ticks: {{ maxRotation: 45, maxTicksLimit: 16 }} }},
        y: {{
          beginAtZero: true,
          title: {{ display: true, text: 'Response time (ms)' }}
        }}
      }}
    }}
  }});
}})();
</script>
</body>
</html>
"""
    REPORT_PATH.write_text(html, encoding="utf-8")
    return REPORT_PATH


def main() -> None:
    path = build_report()
    records = _load_records()
    print(f"Report built ({len(records)} records): {path}")


if __name__ == "__main__":
    main()
