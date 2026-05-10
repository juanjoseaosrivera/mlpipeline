"""Drift-detector tests.

Seeds the `inference_logs` table with two distributions (shifted vs.
in-distribution) and asserts the detector flags the recent window and
updates `is_drift_detected` only when the recent rows are drawn from a
different distribution.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

import numpy as np
import pytest
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from src.api.db.models import InferenceLog
from src.api.db.session import SessionFactory
from src.drift.detector import detect_drift


def _seed(
    session: Session, payloads: Iterable[dict], base_time: datetime, model_version: str = "v1"
) -> None:
    ts = base_time
    for payload in payloads:
        session.add(
            InferenceLog(
                timestamp=ts,
                model_version=model_version,
                input_payload=payload,
                prediction=1,
                probability=0.5,
                latency_ms=10,
            )
        )
        ts += timedelta(seconds=1)
    session.commit()


def _gen(rng: np.random.Generator, n: int, mean: float, sd: float) -> list[dict]:
    f1 = rng.normal(mean, sd, n)
    f2 = rng.normal(mean, sd, n)
    cat = rng.integers(0, 5, n)
    return [
        {"feature_1": float(a), "feature_2": float(b), "category": int(c)}
        for a, b, c in zip(f1, f2, cat)
    ]


def test_detect_no_drift_when_recent_matches_reference(
    sqlite_engine: Engine, session_factory: SessionFactory
) -> None:
    rng = np.random.default_rng(42)
    base = datetime(2026, 5, 10, tzinfo=timezone.utc) - timedelta(seconds=400)
    # Reference window (older), then recent window (newer) — same distribution.
    _seed(session_factory(), _gen(rng, 200, 0.0, 1.0), base)
    _seed(session_factory(), _gen(rng, 200, 0.0, 1.0), base + timedelta(seconds=200))

    with session_factory() as session:
        report = detect_drift(session, recent=200, reference=200)

    assert report.sufficient_data is True
    assert report.drifted_features == []
    assert report.flagged_rows == 0
    with Session(sqlite_engine) as session:
        flagged = session.execute(
            select(InferenceLog).where(InferenceLog.is_drift_detected.is_(True))
        ).scalars().all()
    assert flagged == []


def test_detect_drift_flags_recent_window_when_distribution_shifts(
    sqlite_engine: Engine, session_factory: SessionFactory
) -> None:
    rng = np.random.default_rng(7)
    base = datetime(2026, 5, 10, tzinfo=timezone.utc) - timedelta(seconds=400)
    # Reference window: mean 0. Recent window: mean shifted by 3 sd.
    _seed(session_factory(), _gen(rng, 200, 0.0, 1.0), base)
    _seed(session_factory(), _gen(rng, 200, 3.0, 1.0), base + timedelta(seconds=200))

    with session_factory() as session:
        report = detect_drift(session, recent=200, reference=200)

    assert report.sufficient_data is True
    assert "feature_1" in report.drifted_features
    assert report.flagged_rows == 200
    with Session(sqlite_engine) as session:
        flagged = session.execute(
            select(InferenceLog).where(InferenceLog.is_drift_detected.is_(True))
        ).scalars().all()
    assert len(flagged) == 200


def test_detect_drift_returns_insufficient_data_when_rows_below_threshold(
    session_factory: SessionFactory,
) -> None:
    rng = np.random.default_rng(0)
    base = datetime(2026, 5, 10, tzinfo=timezone.utc)
    _seed(session_factory(), _gen(rng, 50, 0.0, 1.0), base)

    with session_factory() as session:
        report = detect_drift(session, recent=200, reference=200)

    assert report.sufficient_data is False
    assert report.drifted_features == []
    assert report.flagged_rows == 0
