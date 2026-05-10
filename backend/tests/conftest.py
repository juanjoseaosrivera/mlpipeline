"""Shared test fixtures.

The session factory is sqlite-in-memory with a shared connection so the
schema persists for the lifetime of the test. The ORM `JSONB` column has
a `JSON` variant for sqlite — no Postgres needed for unit / integration
tests.
"""

from __future__ import annotations

from typing import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.db.models import Base
from src.api.db.session import SessionFactory


@pytest.fixture
def sqlite_engine() -> Iterator[Engine]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def session_factory(sqlite_engine: Engine) -> SessionFactory:
    return sessionmaker(
        bind=sqlite_engine, autocommit=False, autoflush=False, expire_on_commit=False
    )
