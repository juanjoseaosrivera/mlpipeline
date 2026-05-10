# Models

Training, evaluation, and MLflow registry interaction for the baseline classifier.

## Train and register

```bash
cd backend
python -m src.models.train --seed 42
```

The script generates the synthetic dataset, splits it deterministically, fits a `RandomForestClassifier`, evaluates against the held-out test set, and — if test accuracy clears the baseline (`BASELINE_TEST_ACCURACY = 0.70`) — registers a new version of `ProductionModel` in the MLflow registry. Hyperparameters and metrics are logged to the run.

`MLFLOW_TRACKING_URI` is read from the environment via `src.api.config.Settings`. Inside docker-compose, the URI is `http://mlflow:5000`; locally it defaults to the same.

## Determinism

Training is seeded (default `42`). The same seed produces the same split, the same model artifact, and the same metrics. The seed is recorded as a parameter on the MLflow run.

## Stage transition (Staging → Production)

A newly registered version lands in the `None` stage. Promotion is a manual two-step process — the platform never auto-promotes.

1. **Promote to Staging** once the run's metrics in the MLflow UI look acceptable:

   ```python
   import mlflow

   client = mlflow.MlflowClient()
   client.transition_model_version_stage(
       name="ProductionModel",
       version="<new-version>",
       stage="Staging",
   )
   ```

2. **Promote to Production** once smoke tests pass and the inference API has been exercised against the staged version. Archive the previous Production version in the same call:

   ```python
   client.transition_model_version_stage(
       name="ProductionModel",
       version="<new-version>",
       stage="Production",
       archive_existing_versions=True,
   )
   ```

The API loads `models:/ProductionModel/latest` (overridable via the `MODEL_URI` env var). Contributors who want stage-pinned loads in production can set `MODEL_URI=models:/ProductionModel/Production`.
