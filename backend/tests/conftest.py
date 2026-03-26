import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.dependencies import get_encryption_service
from app.main import app
from app.models.user import User
from app.models.api_key import ApiKey
from app.models.project import Project
from app.services.encryption import EncryptionService

TEST_MASTER_KEY = os.urandom(32).hex()

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=engine)


@pytest.fixture()
def test_db():
    Base.metadata.create_all(engine)
    db = TestSessionLocal()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    def override_get_encryption():
        return EncryptionService(TEST_MASTER_KEY)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_encryption_service] = override_get_encryption

    yield db

    db.close()
    Base.metadata.drop_all(engine)
    app.dependency_overrides.clear()


@pytest.fixture()
def test_user(test_db: Session) -> User:
    user = User(id="test_user_1", email="test@example.com", name="Test User")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture()
def test_api_key(test_db: Session, test_user: User) -> ApiKey:
    enc = EncryptionService(TEST_MASTER_KEY)
    encrypted, nonce, tag = enc.encrypt("sk-test-key-123")
    api_key = ApiKey(
        user_id=test_user.id,
        provider="openai",
        encrypted_key=encrypted,
        nonce=nonce,
        tag=tag,
    )
    test_db.add(api_key)
    test_db.commit()
    test_db.refresh(api_key)
    return api_key


@pytest.fixture()
def test_project(test_db: Session, test_user: User) -> Project:
    project = Project(
        user_id=test_user.id,
        title="Test Video",
        type="shorts",
        topic="coffee facts",
        pipeline_config={"script": True, "tts": True, "video": True},
    )
    test_db.add(project)
    test_db.commit()
    test_db.refresh(project)
    return project


@pytest.fixture()
def client():
    return TestClient(app)
