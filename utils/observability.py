from __future__ import annotations

import contextvars
import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

from configs.settings import ARTIFACTS_DIR, REPORTS_DIR
from utils.openapi import match_openapi_path


_CURRENT_TEST_CONTEXT: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "current_test_context",
    default={},
)


def set_test_context(**context: Any) -> contextvars.Token:
    return _CURRENT_TEST_CONTEXT.set(context)


def reset_test_context(token: contextvars.Token) -> None:
    _CURRENT_TEST_CONTEXT.reset(token)


def get_test_context() -> dict[str, Any]:
    return dict(_CURRENT_TEST_CONTEXT.get())


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): ensure_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [ensure_jsonable(item) for item in value]
    return str(value)


def redact_headers(headers: dict[str, Any]) -> dict[str, Any]:
    sensitive = {"x-api-key", "authorization", "proxy-authorization"}
    result: dict[str, Any] = {}
    for key, value in headers.items():
        if key.lower() in sensitive and value:
            result[key] = "***REDACTED***"
        else:
            result[key] = ensure_jsonable(value)
    return result


def safe_json_from_response(response) -> Any:
    content_type = response.headers.get("Content-Type", "")
    if "application/json" not in content_type:
        return None
    try:
        return response.json()
    except Exception:
        return None


def classify_observation(observation: dict[str, Any]) -> str:
    status = observation["response"]["status_code"]
    markers = set(observation.get("test", {}).get("markers", []))
    if status == 0:
        return "infra"
    if status == 401:
        return "auth"
    if status in {400, 404, 409, 422, 429}:
        return "validation" if "negative" in markers else "business"
    if status >= 500:
        return "infra"
    if "contract" in markers:
        return "contract"
    return "business"


@dataclass
class RequestObservation:
    timestamp: str
    service: str
    test: dict[str, Any]
    request: dict[str, Any]
    response: dict[str, Any]
    classification: str


@dataclass
class ObservationRecorder:
    artifacts_dir: Path = field(default_factory=lambda: ARTIFACTS_DIR)
    reports_dir: Path = field(default_factory=lambda: REPORTS_DIR)
    clear_artifacts_on_init: bool = True
    observations: list[RequestObservation] = field(default_factory=list)
    test_reports: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.observations_path = self.artifacts_dir / "observed_responses.jsonl"
        self.coverage_json_path = self.artifacts_dir / "coverage_matrix.json"
        self.coverage_csv_path = self.artifacts_dir / "coverage_matrix.csv"
        self.failures_json_path = self.artifacts_dir / "failed_tests.json"
        self.index_html_path = self.reports_dir / "index.html"
        if self.clear_artifacts_on_init:
            if self.observations_path.exists():
                self.observations_path.unlink()
            if self.failures_json_path.exists():
                self.failures_json_path.unlink()

    def record(
        self,
        *,
        service: str,
        method: str,
        base_url: str,
        path: str,
        request_headers: dict[str, Any],
        params: dict[str, Any] | None,
        json_body: Any,
        response,
        elapsed_ms: float,
    ) -> None:
        test_context = get_test_context()
        observation_dict = {
            "timestamp": utc_now_iso(),
            "service": service,
            "test": {
                "nodeid": test_context.get("nodeid"),
                "name": test_context.get("name"),
                "markers": test_context.get("markers", []),
                "outcome": test_context.get("outcome"),
            },
            "request": {
                "base_url": base_url,
                "method": method.upper(),
                "path": path,
                "url": f"{base_url}{path}",
                "headers": redact_headers(request_headers),
                "params": ensure_jsonable(params),
                "json": ensure_jsonable(json_body),
            },
            "response": {
                "status_code": response.status_code,
                "headers": ensure_jsonable(dict(response.headers)),
                "json": ensure_jsonable(safe_json_from_response(response)),
                "text_preview": response.text[:2000],
                "elapsed_ms": round(elapsed_ms, 2),
            },
        }
        observation_dict["classification"] = classify_observation(observation_dict)
        observation = RequestObservation(**observation_dict)
        self.observations.append(observation)
        with self.observations_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(observation), ensure_ascii=False) + "\n")

    def record_exception(
        self,
        *,
        service: str,
        method: str,
        base_url: str,
        path: str,
        request_headers: dict[str, Any],
        params: dict[str, Any] | None,
        json_body: Any,
        error: Exception,
        elapsed_ms: float,
    ) -> None:
        test_context = get_test_context()
        observation_dict = {
            "timestamp": utc_now_iso(),
            "service": service,
            "test": {
                "nodeid": test_context.get("nodeid"),
                "name": test_context.get("name"),
                "markers": test_context.get("markers", []),
                "outcome": test_context.get("outcome"),
            },
            "request": {
                "base_url": base_url,
                "method": method.upper(),
                "path": path,
                "url": f"{base_url}{path}",
                "headers": redact_headers(request_headers),
                "params": ensure_jsonable(params),
                "json": ensure_jsonable(json_body),
            },
            "response": {
                "status_code": 0,
                "headers": {},
                "json": None,
                "text_preview": str(error),
                "elapsed_ms": round(elapsed_ms, 2),
                "error_type": error.__class__.__name__,
            },
        }
        observation_dict["classification"] = classify_observation(observation_dict)
        observation = RequestObservation(**observation_dict)
        self.observations.append(observation)
        with self.observations_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(observation), ensure_ascii=False) + "\n")

    def _normalize_observation_path(
        self,
        openapi_documents: dict[str, dict[str, Any]],
        observation: RequestObservation,
    ) -> str:
        document = openapi_documents.get(observation.service)
        if document is None:
            return observation.request["path"]
        return match_openapi_path(document, observation.request["path"]) or observation.request["path"]

    def _observation_key(
        self,
        openapi_documents: dict[str, dict[str, Any]],
        observation: RequestObservation,
    ) -> tuple[str, str, str]:
        return (
            observation.service,
            observation.request["method"],
            self._normalize_observation_path(openapi_documents, observation),
        )

    def build_coverage_matrix(self, openapi_documents: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        observed_statuses: dict[tuple[str, str, str], set[int]] = defaultdict(set)
        example_by_endpoint: dict[tuple[str, str, str], RequestObservation] = {}
        counts_by_endpoint: dict[tuple[str, str, str], int] = defaultdict(int)

        for observation in self.observations:
            key = self._observation_key(openapi_documents, observation)
            observed_statuses[key].add(observation.response["status_code"])
            example_by_endpoint.setdefault(key, observation)
            counts_by_endpoint[key] += 1

        rows: list[dict[str, Any]] = []
        for service, document in openapi_documents.items():
            for path, operations in document["paths"].items():
                for method, operation in operations.items():
                    key = (service, method.upper(), path)
                    declared = sorted(int(code) for code in operation.get("responses", {}))
                    observed = sorted(observed_statuses.get(key, set()))
                    missing = sorted(code for code in declared if code not in observed)
                    unexpected = sorted(code for code in observed if code not in declared)
                    example = example_by_endpoint.get(key)
                    rows.append(
                        {
                            "service": service,
                            "method": method.upper(),
                            "path": path,
                            "declared_statuses": declared,
                            "observed_statuses": observed,
                            "missing_statuses": missing,
                            "unexpected_statuses": unexpected,
                            "observation_count": counts_by_endpoint.get(key, 0),
                            "example_test": example.test["nodeid"] if example else None,
                            "example_classification": example.classification if example else None,
                            "tag_count": len(operation.get("tags", [])),
                            "summary": operation.get("summary"),
                        }
                    )
        return sorted(rows, key=lambda item: (item["service"], item["path"], item["method"]))

    def write_coverage_artifacts(self, rows: list[dict[str, Any]]) -> None:
        self.coverage_json_path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        with self.coverage_csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "service",
                    "method",
                    "path",
                    "declared_statuses",
                    "observed_statuses",
                    "missing_statuses",
                    "unexpected_statuses",
                    "observation_count",
                    "example_test",
                    "example_classification",
                ]
            )
            for row in rows:
                writer.writerow(
                    [
                        row["service"],
                        row["method"],
                        row["path"],
                        "|".join(map(str, row["declared_statuses"])),
                        "|".join(map(str, row["observed_statuses"])),
                        "|".join(map(str, row["missing_statuses"])),
                        "|".join(map(str, row["unexpected_statuses"])),
                        row["observation_count"],
                        row["example_test"] or "",
                        row["example_classification"] or "",
                    ]
                )

    def build_endpoint_passports(
        self,
        rows: list[dict[str, Any]],
        openapi_documents: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        observations_by_endpoint: dict[tuple[str, str, str], list[RequestObservation]] = defaultdict(list)
        for observation in self.observations:
            observations_by_endpoint[self._observation_key(openapi_documents, observation)].append(observation)

        reports_by_nodeid = {report["nodeid"]: report for report in self.test_reports}
        passports: list[dict[str, Any]] = []
        for row in rows:
            key = (row["service"], row["method"], row["path"])
            examples_by_status: dict[int, RequestObservation] = {}
            related_tests: list[dict[str, str]] = []
            for observation in observations_by_endpoint.get(key, []):
                examples_by_status.setdefault(observation.response["status_code"], observation)
                nodeid = observation.test.get("nodeid")
                if nodeid and nodeid in reports_by_nodeid:
                    related_tests.append(reports_by_nodeid[nodeid])
            passports.append(
                {
                    "service": row["service"],
                    "method": row["method"],
                    "path": row["path"],
                    "summary": row.get("summary") or "",
                    "declared_statuses": row["declared_statuses"],
                    "observed_statuses": row["observed_statuses"],
                    "missing_statuses": row["missing_statuses"],
                    "unexpected_statuses": row["unexpected_statuses"],
                    "examples_by_status": {
                        status: asdict(observation) for status, observation in sorted(examples_by_status.items())
                    },
                    "related_failures": related_tests[:5],
                }
            )
        return passports

    def write_html_report(self, rows: list[dict[str, Any]], openapi_documents: dict[str, dict[str, Any]]) -> None:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[row["service"]].append(row)

        mismatches = self.build_contract_mismatches()
        passports = self.build_endpoint_passports(rows, openapi_documents)

        observations_html = []
        for observation in self.observations[-50:]:
            payload = escape(
                json.dumps(asdict(observation), ensure_ascii=False, indent=2, default=str)
            )
            observations_html.append(
                f"""
                <details class="obs-card">
                  <summary>
                    <span>{escape(observation.request["method"])} {escape(observation.request["path"])}</span>
                    <span class="badge status">{observation.response["status_code"]}</span>
                    <span class="badge cls">{escape(observation.classification)}</span>
                    <span class="muted">{escape(observation.test.get("nodeid") or "unknown test")}</span>
                  </summary>
                  <pre>{payload}</pre>
                </details>
                """
            )

        failures_html = []
        for report in self.test_reports:
            body = escape(report.get("longrepr", "")[:5000])
            failures_html.append(
                f"""
                <details class="obs-card">
                  <summary>
                    <span>{escape(report["outcome"].upper())}</span>
                    <span class="badge status">{escape(report["nodeid"])}</span>
                  </summary>
                  <pre>{body}</pre>
                </details>
                """
            )

        mismatch_html = []
        for mismatch in mismatches:
            mismatch_html.append(
                f"""
                <details class="obs-card mismatch-card">
                  <summary>
                    <span>{escape(mismatch["title"])}</span>
                    <span class="badge mismatch">{escape(mismatch["kind"])}</span>
                    <span class="muted">{escape(mismatch["nodeid"])}</span>
                  </summary>
                  <pre>{escape(mismatch["details"])}</pre>
                </details>
                """
            )

        passport_html = []
        for passport in passports:
            if not passport["observed_statuses"] and not passport["related_failures"]:
                continue
            status_blocks = []
            for status, example in passport["examples_by_status"].items():
                status_blocks.append(
                    f"""
                    <details class="obs-card">
                      <summary>
                        <span>Status {status}</span>
                        <span class="badge cls">{escape(example["classification"])}</span>
                        <span class="muted">{escape(example["test"].get("nodeid") or "unknown test")}</span>
                      </summary>
                      <pre>{escape(json.dumps(example, ensure_ascii=False, indent=2))}</pre>
                    </details>
                    """
                )
            failure_blocks = []
            for failure in passport["related_failures"]:
                failure_blocks.append(
                    f"""
                    <details class="obs-card mismatch-card">
                      <summary>
                        <span>{escape(failure["outcome"].upper())}</span>
                        <span class="muted">{escape(failure["nodeid"])}</span>
                      </summary>
                      <pre>{escape(failure.get("longrepr", "")[:2500])}</pre>
                    </details>
                    """
                )
            passport_html.append(
                f"""
                <details class="obs-card passport-card">
                  <summary>
                    <span>{escape(passport["method"])} {escape(passport["path"])}</span>
                    <span class="badge status">declared: {', '.join(map(str, passport["declared_statuses"])) or '-'}</span>
                    <span class="badge cls">observed: {', '.join(map(str, passport["observed_statuses"])) or '-'}</span>
                  </summary>
                  <p class="muted">{escape(passport["summary"])}</p>
                  <p><strong>Missing:</strong> {', '.join(map(str, passport["missing_statuses"])) or 'none'} | <strong>Unexpected:</strong> {', '.join(map(str, passport["unexpected_statuses"])) or 'none'}</p>
                  {''.join(status_blocks) or '<p class="muted">Observed examples are not available yet.</p>'}
                  {''.join(failure_blocks)}
                </details>
                """
            )

        sections = []
        for service, service_rows in grouped.items():
            table_rows = []
            for row in service_rows:
                drift_class = "drift" if row["unexpected_statuses"] else ""
                table_rows.append(
                    f"""
                    <tr class="{drift_class}">
                      <td>{escape(row["method"])}</td>
                      <td>{escape(row["path"])}</td>
                      <td>{", ".join(map(str, row["declared_statuses"])) or "&mdash;"}</td>
                      <td>{", ".join(map(str, row["observed_statuses"])) or "&mdash;"}</td>
                      <td>{", ".join(map(str, row["missing_statuses"])) or "&mdash;"}</td>
                      <td>{", ".join(map(str, row["unexpected_statuses"])) or "&mdash;"}</td>
                      <td>{row["observation_count"]}</td>
                      <td>{escape(row["example_classification"] or "")}</td>
                    </tr>
                    """
                )
            sections.append(
                f"""
                <section class="panel">
                  <h2>{escape(service.upper())}</h2>
                  <table>
                    <thead>
                      <tr>
                        <th>Method</th>
                        <th>Path</th>
                        <th>Declared</th>
                        <th>Observed</th>
                        <th>Missing</th>
                        <th>Unexpected</th>
                        <th>Obs.</th>
                        <th>Class</th>
                      </tr>
                    </thead>
                    <tbody>
                      {''.join(table_rows)}
                    </tbody>
                  </table>
                </section>
                """
            )

        total_requests = len(self.observations)
        endpoints_with_drift = sum(1 for row in rows if row["unexpected_statuses"])
        html = f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>DREAMCRM API Observations</title>
  <style>
    :root {{
      --bg: #f5f1e8;
      --panel: #fffdf8;
      --ink: #1f2937;
      --muted: #6b7280;
      --line: #ded4c2;
      --accent: #0f766e;
      --warn: #b45309;
      --danger: #b91c1c;
    }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #efe4cf 0, transparent 30%),
        linear-gradient(180deg, #f8f4ec 0%, var(--bg) 100%);
    }}
    .wrap {{
      width: min(1400px, calc(100% - 48px));
      margin: 32px auto 48px;
    }}
    .hero, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: 0 10px 30px rgba(55, 65, 81, 0.08);
      padding: 24px;
      margin-bottom: 20px;
    }}
    h1, h2 {{
      margin-top: 0;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-top: 16px;
    }}
    .stat {{
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
      background: #fffaf1;
    }}
    .stat strong {{
      display: block;
      font-size: 28px;
      color: var(--accent);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
      vertical-align: top;
      text-align: left;
    }}
    th {{
      color: var(--muted);
      font-weight: 700;
    }}
    tr.drift {{
      background: #fff7ed;
    }}
    .obs-card {{
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px 14px;
      background: #fffefb;
      margin-bottom: 12px;
    }}
    .obs-card summary {{
      cursor: pointer;
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }}
    .badge {{
      display: inline-block;
      border-radius: 999px;
      padding: 3px 10px;
      font-size: 12px;
      font-family: Consolas, monospace;
    }}
    .status {{
      background: #e0f2fe;
      color: #075985;
    }}
    .cls {{
      background: #ecfccb;
      color: #3f6212;
    }}
    .mismatch {{
      background: #fee2e2;
      color: #991b1b;
    }}
    .muted {{
      color: var(--muted);
      font-size: 12px;
    }}
    .mismatch-card {{
      background: #fff8f7;
    }}
    .passport-card {{
      background: #f9fcfb;
    }}
    pre {{
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      margin: 12px 0 0;
      padding: 12px;
      background: #faf7f1;
      border-radius: 12px;
      border: 1px solid var(--line);
      font-family: Consolas, monospace;
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>DREAMCRM API Observation Report</h1>
      <p>Отчёт строится по фактическим request/response из тестов и помогает одновременно видеть OpenAPI-контракт, покрытие кодов ответа и реальные отклонения стенда.</p>
      <div class="stats">
        <div class="stat"><strong>{total_requests}</strong>Наблюдений запросов</div>
        <div class="stat"><strong>{len(rows)}</strong>Методов в OpenAPI</div>
        <div class="stat"><strong>{endpoints_with_drift}</strong>Методов с unexpected status</div>
        <div class="stat"><strong>{sum(1 for row in rows if row["observed_statuses"])}</strong>Методов с runtime-данными</div>
      </div>
      <p class="muted">Сырые данные: {escape(str(self.observations_path))} | Матрица: {escape(str(self.coverage_json_path))}</p>
    </section>
    {''.join(sections)}
    <section class="panel">
      <h2>Endpoint Passports</h2>
      <p>Observed-only view for writing functional requirements: declared codes, runtime examples by status, and linked failing scenarios.</p>
      {''.join(passport_html) or '<p class="muted">Endpoint passports will appear after runtime requests are collected.</p>'}
    </section>
    <section class="panel">
      <h2>Contract Mismatches</h2>
      {''.join(mismatch_html) or '<p class="muted">Явные contract mismatches по тексту падений пока не обнаружены.</p>'}
    </section>
    <section class="panel">
      <h2>Проблемные тесты</h2>
      {''.join(failures_html) or '<p class="muted">Failing/Skipped кейсы в этой сессии не зафиксированы.</p>'}
    </section>
    <section class="panel">
      <h2>Последние наблюдения</h2>
      {''.join(observations_html) or '<p class="muted">Пока нет наблюдений.</p>'}
    </section>
  </div>
</body>
</html>
"""
        self.index_html_path.write_text(html, encoding="utf-8")

    def finalize(self, openapi_documents: dict[str, dict[str, Any]]) -> None:
        rows = self.build_coverage_matrix(openapi_documents)
        self.write_coverage_artifacts(rows)
        self.failures_json_path.write_text(
            json.dumps(self.test_reports, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.write_html_report(rows, openapi_documents)

    def record_test_report(self, *, nodeid: str, outcome: str, longrepr: str = "") -> None:
        self.test_reports.append(
            {
                "nodeid": nodeid,
                "outcome": outcome,
                "longrepr": longrepr,
            }
        )

    def build_contract_mismatches(self) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        for report in self.test_reports:
            longrepr = report.get("longrepr", "")
            if "ValidationError" in longrepr and "is not valid under any of the given schemas" in longrepr:
                title = "Response does not match OpenAPI schema"
                kind = "schema-drift"
            elif "AssertionError" in longrepr and "CONTACT_POINT_NOT_FOUND" in longrepr:
                title = "Business prerequisite missing on stand"
                kind = "business-drift"
            elif "AssertionError" in longrepr and "assert response.status_code == 200" in longrepr:
                title = "Unexpected status for business-valid scenario"
                kind = "unexpected-status"
            elif "AssertionError" in longrepr and "assert 200 in {400, 422}" in longrepr:
                title = "Undocumented filter is accepted instead of being rejected"
                kind = "validation-drift"
            elif "AssertionError" in longrepr and "assert data[\"total\"] <= 1" in longrepr:
                title = "Semantic drift in pagination or filtering"
                kind = "semantic-drift"
            elif "ReadTimeout" in longrepr:
                title = "Endpoint timed out on valid or near-valid request"
                kind = "timeout-drift"
            else:
                continue
            results.append(
                {
                    "nodeid": report["nodeid"],
                    "title": title,
                    "kind": kind,
                    "details": longrepr[:5000],
                }
            )
        return results
