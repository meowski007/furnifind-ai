from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.services.ingestion import IngestionPipeline
from app.services.registry import registry

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    session_factory = sessionmaker(bind=eng)
    with session_factory() as session:
        pipeline = IngestionPipeline(session)
        pipeline.ingest_file(settings.SAMPLE_CATALOGUE_PATH, force_reload=True)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture(scope="session")
def db_session(engine) -> Generator[Session, None, None]:
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture(scope="session")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # Initialize once for the test session
    registry.initialize(db_session)

    test_client = TestClient(app, raise_server_exceptions=True)
    yield test_client

    app.dependency_overrides.clear()
