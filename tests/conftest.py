import pytest
from app import app as flask_app
from models.application import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services import application_service, auth_service
from models.user import User
from sqlalchemy import select
from security import verify_password

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setitem(flask_app.config, "TESTING", True)

    with flask_app.test_client() as client:
        yield client

@pytest.fixture(scope="session")
def test_engine():
    # create an isolated engine in memory
    engine = create_engine("sqlite:///:memory:", connect_args={"autocommit": False})

    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture
def test_session_factory(test_engine):
    # create a session for each test
    connection = test_engine.connect()
    outer_transaction = connection.begin()

    TestSessionFactory = sessionmaker(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
        )

    try:
        yield TestSessionFactory
    finally:
        if outer_transaction.is_active:
            outer_transaction.rollback()
        connection.close()

@pytest.fixture(autouse=True)
def patch_session_factory(monkeypatch, test_session_factory):
    # replaces real factory with test one before testing
    monkeypatch.setattr(application_service,
     "SessionFactory", test_session_factory)

@pytest.fixture(autouse=True)
def patch_user_factory(monkeypatch, test_session_factory):
    # replaces real factory with test one before testing
    monkeypatch.setattr(auth_service,
     "SessionFactory", test_session_factory)

@pytest.fixture
def existing_user(client):
    """Creates a valid user for the current test. Also tests password whitespace preservation."""
    payload = {
        "email": "test@gmail.com", 
        "password": "     TEST PASSWORD123"
    }
    response = client.post("/auth/register", json=payload)

    with auth_service.SessionFactory() as session:
        stored_user = session.scalar(
            select(User).where(User.email == "test@gmail.com")
        )

    # user_data = {k:v for k, v in stored_user.__dict__.items() if k != '_sa_instance_state'}
    # print(user_data)

    assert stored_user is not None
    assert response.status_code == 201
    assert verify_password(stored_user.password_hash, "     TEST PASSWORD123")

    return response.json

@pytest.fixture
def auth_headers(client, existing_user):
    login_payload = {
        "email": "test@gmail.com", 
        "password": "     TEST PASSWORD123"
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 200
    token = response.json["access_token"]
    return {"Authorization": f"Bearer {token}"}