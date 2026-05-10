"""Prepare stage of the DVC pipeline.

Generates the synthetic dataset and writes it to `data/raw/dataset.csv`.
Once a real upstream dataset lands, the body of `main()` is the only thing
that changes — read from S3 / cloud storage instead of `generate_dataset`
and the rest of the pipeline (DVC, `train.py`) stays untouched.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from src.models.data import DEFAULT_SEED, generate_dataset

logger = logging.getLogger(__name__)

RAW_DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "raw" / "dataset.csv"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    x, y = generate_dataset(seed=DEFAULT_SEED)
    arr = np.column_stack([x, y.astype(float)])
    RAW_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(
        RAW_DATA_PATH,
        arr,
        delimiter=",",
        header="feature_1,feature_2,category,label",
        comments="",
        fmt="%.6f",
    )
    logger.info("wrote %s shape=%s", RAW_DATA_PATH, arr.shape)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
