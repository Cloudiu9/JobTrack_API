import pytest
from app import app as flask_app
from models.application import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services import application_service, auth_service

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