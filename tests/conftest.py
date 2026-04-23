from __future__ import annotations

import pytest

from configs.settings import ACCOUNTING_SETTINGS, CRM_SETTINGS, TEST_DATA
from utils.api_client import APIClient
from utils.observability import ObservationRecorder, reset_test_context, set_test_context
from utils.openapi import (
    ACCOUNTING_SCHEMA_FILE,
    CRM_SCHEMA_FILE,
    load_openapi_schema,
)

@pytest.fixture(scope="session")
def crm_client(observation_recorder: ObservationRecorder) -> APIClient:
    return APIClient(CRM_SETTINGS, recorder=observation_recorder)


@pytest.fixture(scope="session")
def accounting_client(observation_recorder: ObservationRecorder) -> APIClient:
    return APIClient(ACCOUNTING_SETTINGS, recorder=observation_recorder)


@pytest.fixture(scope="session")
def crm_openapi() -> dict:
    return load_openapi_schema(CRM_SCHEMA_FILE)


@pytest.fixture(scope="session")
def accounting_openapi() -> dict:
    return load_openapi_schema(ACCOUNTING_SCHEMA_FILE)


@pytest.fixture(scope="session")
def test_data():
    return TEST_DATA


@pytest.fixture(autouse=True)
def _bind_test_context(request):
    token = set_test_context(
        nodeid=request.node.nodeid,
        name=request.node.name,
        markers=sorted(marker.name for marker in request.node.iter_markers()),
        outcome=None,
    )
    yield
    reset_test_context(token)

def pytest_sessionfinish(session, exitstatus):
    recorder = session.config._observation_recorder if hasattr(session.config, "_observation_recorder") else None
    if recorder is None:
        return
    recorder.finalize(
        {
            "crm": load_openapi_schema(CRM_SCHEMA_FILE),
            "accounting": load_openapi_schema(ACCOUNTING_SCHEMA_FILE),
        }
    )


def pytest_configure(config):
    config._observation_recorder = ObservationRecorder()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    pytestconfig = item.config
    recorder = getattr(pytestconfig, "_observation_recorder", None)
    if recorder is None:
        return
    if report.failed or report.skipped:
        recorder.record_test_report(
            nodeid=item.nodeid,
            outcome=report.outcome,
            longrepr=str(report.longrepr),
        )


@pytest.fixture(scope="session", autouse=True)
def _share_session_recorder(pytestconfig) -> ObservationRecorder:
    return pytestconfig._observation_recorder


@pytest.fixture(scope="session")
def observation_recorder(pytestconfig) -> ObservationRecorder:
    return pytestconfig._observation_recorder
