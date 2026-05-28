"""Persistence tests: row-shape assertion and the DB-unavailable error path.

The row-shape test checks each column from PRD Section 5.2 by reading the
row back from the sqlite-in-memory session. The DB-unavailable test
injects a session_factory whose commit raises so the endpoint hits the
SQLAlchemyError branch and surfaces HTTP 500.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from src.api.config import Settings
from src.api.db.models import InferenceLog
from src.api.db.session import SessionFactory
from src.api.main import create_app


class FakeModel:
    def predict(self, x: Any) -> np.ndarray:
        return np.array([1] * len(x))

    def predict_proba(self, x: Any) -> np.ndarray:
        return np.array([[0.13, 0.87]] * len(x))


@pytest.fixture
def cfg() -> Settings:
    return Settings()


def test_successful_prediction_writes_inference_log_row(
    cfg: Settings, sqlite_engine: Engine, session_factory: SessionFactory
) -> None:
    app = create_app(
        cfg=cfg,
        model_loader=lambda _c: (FakeModel(), "v7"),
        session_factory=session_factory,
    )
    payload = {"feature_1": 0.25, "feature_2": -1.5, "category": 3}

    with TestClient(app) as client:
        response = client.post("/api/predict", json=payload)
    assert response.status_code == 200

    with Session(sqlite_engine) as session:
        rows = session.execute(select(InferenceLog)).scalars().all()

    assert len(rows) == 1
    row = rows[0]
    assert row.id is not None
    assert row.timestamp is not None
    assert row.model_version == "v7"
    assert row.input_payload == payload
    assert row.prediction == 1
    assert row.probability == pytest.approx(0.87)
    assert row.latency_ms >= 0
    assert row.is_drift_detected is False


def test_db_unavailable_returns_500(cfg: Settings) -> None:
    class BrokenSession:
        def add(self, _: object) -> None:
            return None

        def commit(self) -> None:
            raise OperationalError("INSERT", {}, Exception("database is unreachable"))

        def rollback(self) -> None:
            return None

        def close(self) -> None:
            return None

    def broken_factory() -> BrokenSession:
        return BrokenSession()

    app = create_app(
        cfg=cfg,
        model_loader=lambda _c: (FakeModel(), "v7"),
        session_factory=broken_factory,  # type: ignore[arg-type]
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/predict",
            json={"feature_1": 0.1, "feature_2": 0.2, "category": 1},
        )
    assert response.status_code == 500
    assert response.json() == {"detail": "Persistence Error"}
