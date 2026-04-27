from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.observability import ObservationRecorder, RequestObservation
from utils.openapi import load_schema_registry


def main() -> None:
    recorder = ObservationRecorder(clear_artifacts_on_init=False)
    recorder.observations.clear()

    if recorder.observations_path.exists():
        with recorder.observations_path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                recorder.observations.append(RequestObservation(**json.loads(line)))

    if recorder.failures_json_path.exists():
        recorder.test_reports = json.loads(recorder.failures_json_path.read_text(encoding="utf-8"))

    recorder.finalize(load_schema_registry())


if __name__ == "__main__":
    main()
