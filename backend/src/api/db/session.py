"""Engine + sessionmaker factory.

The API never imports a process-global engine; instead `create_app` builds
one from `Settings.database_url` at startup and stores the `sessionmaker`
on `app.state`. Tests inject their own factory (typically a sqlite
in-memory engine) via `create_app(session_factory=...)`.
"""

from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

SessionFactory = sessionmaker[Session]


def build_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True, future=True)


def build_session_factory(engine: Engine) -> SessionFactory:
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
