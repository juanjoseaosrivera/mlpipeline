"""End-to-end smoke test: train, register, load from `models:/...`, predict.

Uses a tmp_path-backed local MLflow tracking store so the test runs without
any external services. Mirrors the artifact URI shape (`models:/<name>/latest`)
that the API will use in production.
"""

from __future__ import annotations

from pathlib import Path

import mlflow
import mlflow.sklearn
import pytest


@pytest.fixture
def local_mlflow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    tracking_uri = f"file://{tmp_path}/mlruns"
    monkeypatch.setenv("MLFLOW_TRACKING_URI", tracking_uri)

    from src.api import config as config_module

    config_module.settings = config_module.Settings()
    return tracking_uri


def test_train_register_load_predict(local_mlflow: str) -> None:
    from src.models.data import generate_dataset
    from src.models.train import train_and_register

    version = train_and_register(seed=7, n_estimators=20)
    assert int(version) >= 1

    mlflow.set_tracking_uri(local_mlflow)
    model = mlflow.sklearn.load_model("models:/ProductionModel/latest")

    x, _ = generate_dataset(seed=7)
    preds = model.predict(x[:4])
    assert preds.shape == (4,)
