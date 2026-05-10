"""Synthetic dataset generation and deterministic splitting.

The shape mirrors `PredictPayload` (two continuous features and one
categorical column) so the trained artifact is wire-compatible with the
inference path. Real data versioning lands in Phase 6 via DVC.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

DEFAULT_SEED: int = 42
N_SAMPLES: int = 2000
N_FEATURES: int = 3
TEST_FRACTION: float = 0.2
VAL_FRACTION: float = 0.2


@dataclass(frozen=True)
class Dataset:
    x_train: np.ndarray
    x_val: np.ndarray
    x_test: np.ndarray
    y_train: np.ndarray
    y_val: np.ndarray
    y_test: np.ndarray


def generate_dataset(
    seed: int = DEFAULT_SEED, n_samples: int = N_SAMPLES
) -> tuple[np.ndarray, np.ndarray]:
    x, y = make_classification(
        n_samples=n_samples,
        n_features=N_FEATURES,
        n_informative=N_FEATURES,
        n_redundant=0,
        n_classes=2,
        random_state=seed,
    )
    cat_edges = np.linspace(x[:, 2].min(), x[:, 2].max(), 6)
    x[:, 2] = np.digitize(x[:, 2], cat_edges[1:-1]).astype(float)
    return x, y


def split_dataset(x: np.ndarray, y: np.ndarray, seed: int = DEFAULT_SEED) -> Dataset:
    x_train_full, x_test, y_train_full, y_test = train_test_split(
        x, y, test_size=TEST_FRACTION, random_state=seed, stratify=y
    )
    x_train, x_val, y_train, y_val = train_test_split(
        x_train_full,
        y_train_full,
        test_size=VAL_FRACTION,
        random_state=seed,
        stratify=y_train_full,
    )
    return Dataset(
        x_train=x_train,
        x_val=x_val,
        x_test=x_test,
        y_train=y_train,
        y_val=y_val,
        y_test=y_test,
    )
