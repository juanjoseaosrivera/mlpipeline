"""FastAPI inference service.

Loads `ProductionModel` from the MLflow registry once at startup as a
process-local singleton, exposes `POST /api/predict`, persists every
successful inference to PostgreSQL (`inference_logs`), and measures
latency strictly around the inference call so the 150 ms budget
(PRD Section 4.2) applies to the model, not to request parsing or
downstream side effects.

The only public surfaces are `GET /health` and `POST /api/predict`.
Swagger docs are off by default (`enable_docs=False`) to satisfy the
"no introspection endpoints" rule from `architecture-context.md`.
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator, Callable, Generator
from contextlib import asynccontextmanager
from typing import Any

import mlflow
import mlflow.sklearn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from mlflow.tracking import MlflowClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.api.config import Settings, settings
from src.api.db.models import InferenceLog
from src.api.db.session import SessionFactory, build_engine, build_session_factory
from src.api.schemas import PredictPayload, PredictResponse

logger = logging.getLogger(__name__)

ModelLoader = Callable[[Settings], tuple[Any, str]]


def _default_model_loader(cfg: Settings) -> tuple[Any, str]:
    mlflow.set_tracking_uri(cfg.mlflow_tracking_uri)
    client = MlflowClient(tracking_uri=cfg.mlflow_tracking_uri)
    versions = client.get_latest_versions(cfg.model_name)
    if not versions:
        raise RuntimeError(f"No registered versions for model {cfg.model_name!r}")
    latest = versions[0]
    model = mlflow.sklearn.load_model(f"models:/{cfg.model_name}/{latest.version}")
    return model, str(latest.version)


def create_app(
    cfg: Settings | None = None,
    model_loader: ModelLoader | None = None,
    session_factory: SessionFactory | None = None,
) -> FastAPI:
    cfg = cfg or settings
    loader = model_loader or _default_model_loader

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        try:
            model, version = loader(cfg)
            app.state.model = model
            app.state.model_version = version
            logger.info("model loaded: name=%s version=%s", cfg.model_name, version)
        except Exception as exc:
            # No model registered yet (or MLflow unreachable). Stay up so
            # /health and DB migrations work; /api/predict returns 503 via
            # get_model until a model is trained.
            app.state.model = None
            app.state.model_version = None
            logger.warning("model load failed; serving 503 from /api/predict: %s", exc)

        if session_factory is None:
            engine = build_engine(cfg.database_url)
            app.state.engine = engine
            app.state.session_factory = build_session_factory(engine)
        else:
            app.state.engine = None
            app.state.session_factory = session_factory

        yield

        app.state.model = None
        app.state.model_version = None
        if app.state.engine is not None:
            app.state.engine.dispose()

    app = FastAPI(
        title="MLOps Prediction API",
        lifespan=lifespan,
        docs_url="/docs" if cfg.enable_docs else None,
        redoc_url="/redoc" if cfg.enable_docs else None,
        openapi_url="/openapi.json" if cfg.enable_docs else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(cfg.allowed_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    def get_model(request: Request) -> Any:
        model = getattr(request.app.state, "model", None)
        if model is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        return model

    def get_model_version(request: Request) -> str:
        return str(getattr(request.app.state, "model_version", "unknown"))

    def get_db(request: Request) -> Generator[Session, None, None]:
        factory: SessionFactory = request.app.state.session_factory
        db = factory()
        try:
            yield db
        finally:
            db.close()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/predict", response_model=PredictResponse)
    async def predict(
        data: PredictPayload,
        model: Any = Depends(get_model),
        model_version: str = Depends(get_model_version),
        db: Session = Depends(get_db),
    ) -> PredictResponse:
        features = [[data.feature_1, data.feature_2, float(data.category)]]
        start = time.perf_counter()
        try:
            prediction = model.predict(features)
            probability = float(model.predict_proba(features).max())
        except Exception:
            logger.exception("inference error model_version=%s", model_version)
            raise HTTPException(status_code=500, detail="Inference Error") from None
        latency_ms = int((time.perf_counter() - start) * 1000)

        prediction_int = int(prediction[0])
        row = InferenceLog(
            model_version=model_version,
            input_payload=data.model_dump(),
            prediction=prediction_int,
            probability=probability,
            latency_ms=latency_ms,
        )
        try:
            db.add(row)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            logger.exception("inference_logs insert failed model_version=%s", model_version)
            raise HTTPException(status_code=500, detail="Persistence Error") from None

        return PredictResponse(
            prediction=prediction_int,
            probability=probability,
            latency_ms=latency_ms,
            model_version=model_version,
        )

    return app


app = create_app()
