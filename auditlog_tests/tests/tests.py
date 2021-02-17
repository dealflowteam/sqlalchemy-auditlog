import datetime
from typing import Any

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from auditlog.context import set_user, set_remote_addr, remove_remote_addr
from auditlog.documents import LogEntry
from auditlog.registry import auditlog
from auditlog_tests import models


class BaseTest:
    model = None

    def create_obj(self, db: Session) -> Any:
        return None

    @pytest.fixture(scope="function")
    def obj(self, db: Session):
        return self.create_obj(db)

    def test_create(self, db: Session, obj, mock_save):
        """Creation is logged correctly."""
        assert mock_save.call_count == 1
        kwargs = mock_save.call_args.args[0]
        assert kwargs['action'] == LogEntry.Action.CREATE
        assert kwargs['object_pk'] == str(inspect(obj).identity[0])
        assert kwargs['object_repr'] == str(obj)
        assert kwargs['table_name'] == self.model.__tablename__

    def test_update(self, db: Session, obj, mock_save):
        obj.boolean = True
        db.add(obj)
        db.commit()
        assert mock_save.call_count == 2
        kwargs = mock_save.call_args.args[0]
        assert kwargs['action'] == LogEntry.Action.UPDATE
        assert kwargs['object_pk'] == str(inspect(obj).identity[0])
        assert kwargs['object_repr'] == str(obj)
        assert kwargs['table_name'] == self.model.__tablename__
        assert kwargs['changes'] == [{"field": "boolean", "old": "False", "new": "True"}]

    def test_delete(self, db: Session, obj, mock_save):
        db.delete(obj)
        db.commit()
        assert mock_save.call_count == 2
        kwargs = mock_save.call_args.args[0]
        assert kwargs['action'] == LogEntry.Action.DELETE
        assert kwargs['object_pk'] == str(inspect(obj).identity[0])
        assert kwargs['object_repr'] == str(obj)
        assert kwargs['table_name'] == self.model.__tablename__

    def test_recreate(self, db: Session, obj, mock_save):
        db.delete(obj)
        db.commit()
        obj2 = self.create_obj(db)
        db.add(obj2)
        db.commit()
        assert mock_save.call_count == 3
        kwargs = mock_save.call_args.args[0]
        assert kwargs['action'] == LogEntry.Action.CREATE
        assert kwargs['object_pk'] == str(inspect(obj2).identity[0])


class TestSimpleModel(BaseTest):
    model = models.SimpleModel

    def create_obj(self, db: Session):
        obj = models.SimpleModel(text="I am not difficult.", boolean=False)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj


class TestAltPrimaryKeyModel(BaseTest):
    model = models.AltPrimaryKeyModel

    def create_obj(self, db: Session) -> Any:
        obj = models.AltPrimaryKeyModel(key=str(datetime.datetime.now()), text='I am strange.')
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj


class TestUUIDPrimaryKeyModel(BaseTest):
    model = models.UUIDPrimaryKeyModel

    def create_obj(self, db: Session) -> Any:
        obj = models.UUIDPrimaryKeyModel(text='I am strange.')
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj


class TestPolymorphicModel(BaseTest):
    model = models.PolymorphicModel

    def create_obj(self, db: Session) -> Any:
        obj = models.PolymorphicModel(text='I am not what you think.')
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj


class TestRelatedModel:
    def test_related(self, db: Session, mock_save) -> Any:
        simple = models.SimpleModel(text='simple')
        db.add(simple)
        db.flush()
        obj = models.RelatedModel(related_id=simple.id)
        db.add(obj)
        db.commit()
        assert mock_save.call_count == 2

    def test_many_related(self, db: Session, mock_save) -> Any:
        simple = models.SimpleModel(text='simple')
        db.add(simple)
        db.flush()
        obj = models.ManyRelatedModel(text='related')
        obj.models.append(simple)
        db.add(obj)
        db.commit()
        assert mock_save.call_count == 2


class TestSimpleIncludeModel:
    def test_register_include_fields(self, db: Session, mock_save):
        obj = models.SimpleIncludeModel(label='Include model', text='Looong text')
        db.add(obj)
        db.commit()
        db.refresh(obj)

        assert mock_save.call_count == 1

        # Change label, record
        obj.label = 'Changed label'
        db.add(obj)
        db.commit()
        db.refresh(obj)
        assert mock_save.call_count == 2

        # Change text, ignore
        obj.text = 'Short text'
        db.add(obj)
        db.commit()
        db.refresh(obj)
        assert mock_save.call_count == 2


class TestSimpleExcludeModel:
    def test_register_include_fields(self, db: Session, mock_save):
        obj = models.SimpleExcludeModel(label='Exclude model', text='Looong text')
        db.add(obj)
        db.commit()
        db.refresh(obj)

        assert mock_save.call_count == 1

        # Change label, ignore
        obj.label = 'Changed label'
        db.add(obj)
        db.commit()
        db.refresh(obj)
        assert mock_save.call_count == 1

        # Change text, record
        obj.text = 'Short text'
        db.add(obj)
        db.commit()
        db.refresh(obj)
        assert mock_save.call_count == 2


class UnregisterTest:
    @pytest.fixture(scope="function")
    def unregistered_obj(self, db: Session):
        auditlog.unregister(models.SimpleModel)
        obj = models.SimpleModel(text="No history")
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def test_unregister_create(self, unregistered_obj: models.SimpleModel, mock_save):
        assert mock_save.call_count == 0

    def test_unregister_update(self, db: Session, unregistered_obj: models.SimpleModel, mock_save):
        unregistered_obj.boolean = True
        unregistered_obj.save()
        db.add(unregistered_obj)
        db.commit()

        assert mock_save.call_count == 0

    def test_unregister_delete(self, db: Session, unregistered_obj: models.SimpleModel, mock_save):
        db.delete(unregistered_obj)
        db.commit()

        assert mock_save.call_count == 0


class TestActor:

    @pytest.fixture(scope="function")
    def db_actor(self, db: Session) -> (Session, models.User):
        user = models.User(email='mail@mail.com')
        db.add(user)
        db.commit()
        db.refresh(user)
        set_user(db, user)
        return db, user

    @pytest.fixture(scope="function")
    def obj(self, db_actor: (Session, models.User)) -> models.SimpleModel:
        db, _ = db_actor
        obj = models.SimpleModel(text="I am not difficult.", boolean=False)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def test_create(self, db_actor: (Session, models.User), obj: models.SimpleModel, mock_save):
        db, user = db_actor
        assert mock_save.call_count == 2
        kwargs = mock_save.call_args.args[0]
        assert kwargs['actor_id'] == user.id
        assert kwargs['actor_email'] == user.email

    def test_update(self, db_actor: (Session, models.User), obj: models.SimpleModel, mock_save):
        db, user = db_actor
        obj.text = 'new text'
        db.add(obj)
        db.commit()
        assert mock_save.call_count == 3
        kwargs = mock_save.call_args.args[0]
        assert kwargs['actor_id'] == user.id
        assert kwargs['actor_email'] == user.email

    def test_delete(self, db_actor: (Session, models.User), obj: models.SimpleModel, mock_save):
        db, user = db_actor
        db.delete(obj)
        db.commit()
        assert mock_save.call_count == 3
        kwargs = mock_save.call_args.args[0]
        assert kwargs['actor_id'] == user.id
        assert kwargs['actor_email'] == user.email


class TestRemoteAddr:
    REMOTE_ADDR = '127.0.0.1'

    @pytest.fixture(scope="function")
    def remote_addr(self, db: Session) -> None:
        token = set_remote_addr(self.REMOTE_ADDR)
        yield
        remove_remote_addr(token)

    @pytest.fixture(scope="function")
    def obj(self, db: Session, remote_addr) -> models.SimpleModel:
        obj = models.SimpleModel(text="I am not difficult.", boolean=False)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def test_create(self, obj: models.SimpleModel, mock_save):
        assert mock_save.call_count == 1
        kwargs = mock_save.call_args.args[0]
        assert kwargs['remote_addr'] == self.REMOTE_ADDR

    def test_update(self, db: Session, obj: models.SimpleModel, mock_save):
        obj.text = 'new text'
        db.add(obj)
        db.commit()
        assert mock_save.call_count == 2
        kwargs = mock_save.call_args.args[0]
        assert kwargs['remote_addr'] == self.REMOTE_ADDR

    def test_delete(self, db: Session, obj: models.SimpleModel, mock_save):
        db.delete(obj)
        db.commit()
        assert mock_save.call_count == 2
        kwargs = mock_save.call_args.args[0]
        assert kwargs['remote_addr'] == self.REMOTE_ADDR


class TestCustomLogEntry:
    def test_create(self, db: Session, mock_save):
        obj = models.SimpleModel(text='custom text')
        db.add(obj)
        db.commit()
        assert mock_save.call_count == 1
        kwargs = mock_save.call_args.args[0]
        assert kwargs['text'] == 'custom text'
