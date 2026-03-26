from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import User, ApiKey, Project, PipelineStep, Asset


def test_user_model_has_required_fields():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(id="user_123", email="test@example.com", name="Test User", plan="free")
        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.id == "user_123"
        assert user.email == "test@example.com"
        assert user.plan == "free"


def test_project_model_with_steps():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(id="user_1", email="u@test.com", name="U")
        session.add(user)
        session.flush()

        project = Project(
            user_id="user_1",
            title="Test Video",
            type="shorts",
            topic="coffee facts",
            pipeline_config={"script": True, "tts": True},
        )
        session.add(project)
        session.flush()

        step = PipelineStep(project_id=project.id, step="script", status="pending")
        session.add(step)
        session.commit()

        session.refresh(project)
        assert project.title == "Test Video"
        assert project.type == "shorts"
        assert len(project.steps) == 1
        assert project.steps[0].step == "script"


def test_api_key_model():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(id="user_2", email="u2@test.com", name="U2")
        session.add(user)
        session.flush()

        api_key = ApiKey(
            user_id="user_2",
            provider="openai",
            encrypted_key=b"encrypted",
            nonce=b"nonce123456x",
            tag=b"tag1234567890123",
        )
        session.add(api_key)
        session.commit()
        session.refresh(api_key)

        assert api_key.provider == "openai"
        assert api_key.is_valid is True


def test_asset_model():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(id="user_3", email="u3@test.com", name="U3")
        session.add(user)
        session.flush()

        project = Project(user_id="user_3", title="V", type="shorts", topic="t")
        session.add(project)
        session.flush()

        asset = Asset(
            project_id=project.id,
            step="video",
            type="video",
            storage_url="s3://bucket/video.mp4",
            file_size=1024000,
            mime_type="video/mp4",
        )
        session.add(asset)
        session.commit()
        session.refresh(asset)

        assert asset.storage_url == "s3://bucket/video.mp4"
        assert asset.mime_type == "video/mp4"
