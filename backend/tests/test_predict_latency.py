"""P95 inference-latency check against a fixture model.

The 150 ms budget (PRD Section 4.2) is at the API's inference call site,
not the TestClient roundtrip — so we read `latency_ms` from the response
body, which is measured strictly around `model.predict` /
`model.predict_proba`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.config import Settings
from src.api.main import create_app
from src.models.train import train_and_register

N_REQUESTS = 100
P95_BUDGET_MS = 150


@pytest.fixture(scope="module")
def client(tmp_path_factory: pytest.TempPathFactory) -> TestClient:
    tmp = tmp_path_factory.mktemp("mlruns_latency")
    tracking_uri = f"file://{Path(tmp)}/mlruns"
    cfg = Settings(mlflow_tracking_uri=tracking_uri)

    from src.api import config as config_module

    original = config_module.settings
    config_module.settings = cfg
    try:
        train_and_register(seed=11, n_estimators=20)
    finally:
        config_module.settings = original

    app = create_app(cfg=cfg)
    return TestClient(app)


def test_p95_inference_latency_under_budget(client: TestClient) -> None:
    payload = {"feature_1": 0.1, "feature_2": -0.4, "category": 2}
    latencies: list[int] = []
    for _ in range(N_REQUESTS):
        response = client.post("/api/predict", json=payload)
        assert response.status_code == 200
        latencies.append(response.json()["latency_ms"])

    latencies.sort()
    p95 = latencies[int(0.95 * N_REQUESTS) - 1]
    assert p95 < P95_BUDGET_MS, f"P95 inference latency {p95}ms exceeds {P95_BUDGET_MS}ms"
