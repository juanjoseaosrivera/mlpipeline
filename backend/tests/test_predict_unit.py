"""Unit tests for POST /api/predict with a fake model and sqlite session.

The fake model exposes the sklearn contract (`predict`, `predict_proba`) so
the endpoint code is exercised end-to-end without MLflow. The session
factory comes from `conftest.py` (sqlite in-memory).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import numpy as np
import pytest
from fastapi.testclient import TestClient

from src.api.config import Settings
from src.api.db.session import SessionFactory
from src.api.main import create_app


class FakeModel:
    def __init__(self, prediction: int = 1, probability: float = 0.87) -> None:
        self._prediction = prediction
        self._probability = probability

    def predict(self, x: Any) -> np.ndarray:
        return np.array([self._prediction] * len(x))

    def predict_proba(self, x: Any) -> np.ndarray:
        other = 1.0 - self._probability
        return np.array([[other, self._probability]] * len(x))


class ExplodingModel:
    def predict(self, x: Any) -> np.ndarray:
        raise RuntimeError("boom")

    def predict_proba(self, x: Any) -> np.ndarray:
        raise RuntimeError("boom")


@pytest.fixture
def cfg() -> Settings:
    return Settings(allowed_origins=("http://localhost:4200",), enable_docs=False)


@pytest.fixture
def client(cfg: Settings, session_factory: SessionFactory) -> Iterator[TestClient]:
    app = create_app(
        cfg=cfg,
        model_loader=lambda _c: (FakeModel(), "fixture-v1"),
        session_factory=session_factory,
    )
    with TestClient(app) as test_client:
        yield test_client


def test_predict_returns_typed_response(client: TestClient) -> None:
    response = client.post(
        "/api/predict",
        json={"feature_1": 0.1, "feature_2": -0.4, "category": 2},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["prediction"] == 1
    assert body["probability"] == pytest.approx(0.87)
    assert body["model_version"] == "fixture-v1"
    assert body["latency_ms"] >= 0


def test_predict_rejects_extra_fields(client: TestClient) -> None:
    response = client.post(
        "/api/predict",
        json={"feature_1": 0.1, "feature_2": -0.4, "category": 2, "rogue": 9},
    )
    assert response.status_code == 422


def test_predict_rejects_missing_fields(client: TestClient) -> None:
    response = client.post("/api/predict", json={"feature_1": 0.1})
    assert response.status_code == 422


def test_predict_rejects_negative_category(client: TestClient) -> None:
    response = client.post(
        "/api/predict",
        json={"feature_1": 0.1, "feature_2": -0.4, "category": -1},
    )
    assert response.status_code == 422


def test_predict_returns_500_on_inference_failure(
    cfg: Settings, session_factory: SessionFactory
) -> None:
    app = create_app(
        cfg=cfg,
        model_loader=lambda _c: (ExplodingModel(), "fixture-v1"),
        session_factory=session_factory,
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/predict",
            json={"feature_1": 0.1, "feature_2": -0.4, "category": 2},
        )
    assert response.status_code == 500
    assert response.json() == {"detail": "Inference Error"}


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_swagger_disabled_by_default(client: TestClient) -> None:
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_cors_allows_configured_origin(client: TestClient) -> None:
    response = client.options(
        "/api/predict",
        headers={
            "Origin": "http://localhost:4200",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:4200"


def test_cors_does_not_echo_unknown_origin(client: TestClient) -> None:
    response = client.options(
        "/api/predict",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.headers.get("access-control-allow-origin") != "http://evil.example.com"
