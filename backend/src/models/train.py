"""Train the baseline classifier and register it in MLflow as ProductionModel.

Usage::

    cd backend
    python -m src.models.train --seed 42

Reads `MLFLOW_TRACKING_URI` from the environment via `src.api.config.Settings`.
A new registered version lands in the `None` stage; promotion to `Staging` /
`Production` is a manual MLflow stage transition (see this package's README).
"""

from __future__ import annotations

import argparse
import logging
import sys

import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score

from src.api.config import settings
from src.models.data import DEFAULT_SEED, generate_dataset, split_dataset

logger = logging.getLogger(__name__)

BASELINE_TEST_ACCURACY: float = 0.70


def train_and_register(seed: int = DEFAULT_SEED, n_estimators: int = 200) -> str:
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.experiment_name)

    x, y = generate_dataset(seed=seed)
    data = split_dataset(x, y, seed=seed)

    with mlflow.start_run() as run:
        mlflow.log_params(
            {
                "seed": seed,
                "n_estimators": n_estimators,
                "n_train": len(data.x_train),
                "n_val": len(data.x_val),
                "n_test": len(data.x_test),
            }
        )

        model = RandomForestClassifier(n_estimators=n_estimators, random_state=seed)
        model.fit(data.x_train, data.y_train)

        val_pred = model.predict(data.x_val)
        test_pred = model.predict(data.x_test)
        val_acc = float(accuracy_score(data.y_val, val_pred))
        test_acc = float(accuracy_score(data.y_test, test_pred))
        test_f1 = float(f1_score(data.y_test, test_pred))

        mlflow.log_metrics(
            {"val_accuracy": val_acc, "test_accuracy": test_acc, "test_f1": test_f1}
        )

        if test_acc < BASELINE_TEST_ACCURACY:
            raise RuntimeError(
                f"Test accuracy {test_acc:.3f} below baseline "
                f"{BASELINE_TEST_ACCURACY:.3f}; refusing to register."
            )

        result = mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            registered_model_name=settings.model_name,
        )

        logger.info(
            "registered model=%s version=%s run_id=%s test_accuracy=%.3f",
            settings.model_name,
            result.registered_model_version,
            run.info.run_id,
            test_acc,
        )
        return str(result.registered_model_version)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Train and register the baseline classifier.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--n-estimators", type=int, default=200)
    args = parser.parse_args()

    train_and_register(seed=args.seed, n_estimators=args.n_estimators)
    return 0


if __name__ == "__main__":
    sys.exit(main())
