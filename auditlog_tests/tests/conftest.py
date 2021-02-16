from typing import Generator
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine.base import Connection
from sqlalchemy.orm import sessionmaker

from auditlog.receivers import save_log_entries_after_commit, track_instances_after_flush
from auditlog_tests import test_conf
from auditlog_tests.models import Base

engine = create_engine(
    f'postgresql://{test_conf.POSTGRES_USER}:{test_conf.POSTGRES_PASSWORD}@localhost:'
    f'{test_conf.POSTGRES_PORT}/{test_conf.POSTGRES_DB}_test',
    pool_pre_ping=True
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

event.listen(TestSession, "after_flush", track_instances_after_flush)
event.listen(TestSession, "after_commit", save_log_entries_after_commit)


@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """
  Init a clean database on every test case.
  """
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)  # Create the tables.
    yield  # Run the tests.


@pytest.fixture(scope="session")
def connection() -> Connection:
    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture(scope="function", autouse=True)
def db(connection: Connection) -> Generator:
    transaction = connection.begin()
    session = TestSession(bind=connection)
    try:
        yield session
    finally:
        transaction.rollback()
        session.close()


@pytest.fixture(scope="function", autouse=True)
def mock_save():
    with patch('auditlog.documents.LogEntry.log_create') as mock:
        yield mock
