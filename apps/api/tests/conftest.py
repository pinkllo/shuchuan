from collections.abc import Callable, Iterator
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db
from app.core.config import settings
from app.db.base import Base
from app.main import app


@pytest.fixture()
def db_session() -> Iterator[Session]:
    temp_root = Path(".test_tmp")
    temp_root.mkdir(exist_ok=True)
    test_dir = temp_root / uuid4().hex
    test_dir.mkdir()
    uploads_path = test_dir / "uploads"
    engine = create_engine(
        f"sqlite:///{test_dir / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    testing_session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    original_upload_root = settings.upload_root
    settings.upload_root = str(uploads_path)
    Base.metadata.create_all(engine)
    session = testing_session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
        settings.upload_root = original_upload_root
        rmtree(test_dir)


@pytest.fixture()
def client(db_session: Session) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def authenticated_client(
    db_session: Session,
) -> Iterator[Callable[[str], TestClient]]:
    from app.core.security import hash_password
    from app.db.models.user import User, UserRole, UserStatus

    clients: list[TestClient] = []

    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    def factory(role: str) -> TestClient:
        index = len(clients) + 1
        user = User(
            username=f"{role}_{index}",
            display_name=f"{role} 用户",
            password_hash=hash_password("Passw0rd!"),
            email=f"{role}_{index}@example.com",
            role=UserRole(role),
            status=UserStatus.ACTIVE,
        )
        db_session.add(user)
        db_session.commit()

        test_client = TestClient(app)
        clients.append(test_client)
        login_response = test_client.post(
            "/api/auth/login",
            json={"username": user.username, "password": "Passw0rd!"},
        )
        token = login_response.json()["access_token"]
        test_client.headers.update({"Authorization": f"Bearer {token}"})
        return test_client

    yield factory

    for test_client in clients:
        test_client.close()
    app.dependency_overrides.clear()
