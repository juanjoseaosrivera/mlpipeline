"""Drift detection over `inference_logs`.

Reads a recent window and a reference window of inference rows from the
`inference_logs` table, runs a per-feature two-sample Kolmogorov–Smirnov
test, and — if any feature's p-value falls below `ALPHA` — marks every
recent row's `is_drift_detected = TRUE`.

Exits with status code 2 when drift is detected so the retraining
workflow (or any cron caller) can branch on the exit code; status 0
means no drift, status 1 means insufficient data.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass, field

import numpy as np
from scipy import stats
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.api.config import settings
from src.api.db.models import InferenceLog
from src.api.db.session import build_engine, build_session_factory

logger = logging.getLogger(__name__)

ALPHA: float = 0.01
FEATURE_NAMES: tuple[str, ...] = ("feature_1", "feature_2", "category")

EXIT_NO_DRIFT = 0
EXIT_INSUFFICIENT_DATA = 1
EXIT_DRIFT_DETECTED = 2


@dataclass(frozen=True)
class DriftReport:
    drifted_features: list[str] = field(default_factory=list)
    p_values: dict[str, float] = field(default_factory=dict)
    flagged_rows: int = 0
    sufficient_data: bool = True


def _extract_features(rows: list[InferenceLog]) -> dict[str, np.ndarray]:
    return {
        "feature_1": np.array([float(r.input_payload["feature_1"]) for r in rows]),
        "feature_2": np.array([float(r.input_payload["feature_2"]) for r in rows]),
        "category": np.array([float(r.input_payload["category"]) for r in rows]),
    }


def detect_drift(
    session: Session,
    recent: int = 500,
    reference: int = 500,
    alpha: float = ALPHA,
) -> DriftReport:
    stmt = (
        select(InferenceLog)
        .order_by(InferenceLog.timestamp.desc())
        .limit(recent + reference)
    )
    rows: list[InferenceLog] = list(session.execute(stmt).scalars().all())

    if len(rows) < recent + reference:
        logger.info(
            "insufficient data for drift check: have=%d need=%d", len(rows), recent + reference
        )
        return DriftReport(sufficient_data=False)

    recent_rows = rows[:recent]
    reference_rows = rows[recent : recent + reference]

    recent_x = _extract_features(recent_rows)
    reference_x = _extract_features(reference_rows)

    p_values: dict[str, float] = {}
    drifted: list[str] = []
    for name in FEATURE_NAMES:
        result = stats.ks_2samp(recent_x[name], reference_x[name])
        p_values[name] = float(result.pvalue)
        if result.pvalue < alpha:
            drifted.append(name)

    flagged = 0
    if drifted:
        recent_ids = [r.id for r in recent_rows]
        session.execute(
            update(InferenceLog)
            .where(InferenceLog.id.in_(recent_ids))
            .values(is_drift_detected=True)
        )
        session.commit()
        flagged = len(recent_ids)
        logger.warning(
            "drift detected features=%s p_values=%s flagged=%d", drifted, p_values, flagged
        )
    else:
        logger.info("no drift p_values=%s", p_values)

    return DriftReport(
        drifted_features=drifted,
        p_values=p_values,
        flagged_rows=flagged,
        sufficient_data=True,
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Detect drift over inference_logs.")
    parser.add_argument("--recent", type=int, default=500)
    parser.add_argument("--reference", type=int, default=500)
    parser.add_argument("--alpha", type=float, default=ALPHA)
    args = parser.parse_args()

    engine = build_engine(settings.database_url)
    factory = build_session_factory(engine)
    try:
        with factory() as session:
            report = detect_drift(
                session,
                recent=args.recent,
                reference=args.reference,
                alpha=args.alpha,
            )
    finally:
        engine.dispose()

    if not report.sufficient_data:
        return EXIT_INSUFFICIENT_DATA
    if report.drifted_features:
        return EXIT_DRIFT_DETECTED
    return EXIT_NO_DRIFT


if __name__ == "__main__":
    sys.exit(main())
