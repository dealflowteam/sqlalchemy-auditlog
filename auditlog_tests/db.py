from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from auditlog.receivers import save_log_entries_after_commit, track_instances_after_flush
from auditlog_tests import test_conf

engine = create_engine(
    f'postgresql://{test_conf.POSTGRES_USER}:{test_conf.POSTGRES_PASSWORD}@localhost:'
    f'{test_conf.POSTGRES_PORT}/{test_conf.POSTGRES_DB}',
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

event.listen(SessionLocal, "after_flush", track_instances_after_flush)
event.listen(SessionLocal, "after_commit", save_log_entries_after_commit)


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
