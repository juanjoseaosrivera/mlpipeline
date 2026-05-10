"""Integration test: train + register against a file:// MLflow store, then
serve `/api/predict` using the default loader.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.config import Settings
from src.api.main import create_app
from src.models.train import train_and_register


@pytest.fixture(scope="module")
def registered_model(tmp_path_factory: pytest.TempPathFactory) -> Settings:
    tmp = tmp_path_factory.mktemp("mlruns")
    tracking_uri = f"file://{Path(tmp)}/mlruns"
    cfg = Settings(mlflow_tracking_uri=tracking_uri)

    from src.api import config as config_module

    original = config_module.settings
    config_module.settings = cfg
    try:
        train_and_register(seed=7, n_estimators=20)
    finally:
        config_module.settings = original

    return cfg


@pytest.fixture(scope="module")
def client(registered_model: Settings) -> TestClient:
    app = create_app(cfg=registered_model)
    return TestClient(app)


def test_predict_against_registered_model(client: TestClient) -> None:
    response = client.post(
        "/api/predict",
        json={"feature_1": 0.1, "feature_2": -0.4, "category": 2},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["prediction"] in {0, 1}
    assert 0.0 <= body["probability"] <= 1.0
    assert body["latency_ms"] >= 0
    assert int(body["model_version"]) >= 1
