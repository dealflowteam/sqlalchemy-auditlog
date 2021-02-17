import logging
from datetime import datetime
from typing import Any, Optional

from elasticsearch_dsl import Document, connections, Keyword, Date, Nested, InnerDoc, Text

from auditlog import conf
from auditlog.context import get_remote_addr

# Define a default Elasticsearch client
connections.create_connection(hosts=[conf.ELASTICSEARCH_HOST])

MAX = 75


class Change(InnerDoc):
    field = Keyword(required=True)
    old = Text()
    new = Text()


class LogEntry(Document):
    class Action:
        CREATE = 'create'
        UPDATE = 'update'
        DELETE = 'delete'

        choices = (
            (CREATE, CREATE),
            (UPDATE, UPDATE),
            (DELETE, DELETE)
        )

    action = Keyword(required=True)

    table_name = Keyword()

    object_id = Keyword()
    object_pk = Keyword()
    object_repr = Text()

    actor_id = Keyword()
    actor_email = Keyword()
    actor_first_name = Text()
    actor_last_name = Text()

    remote_addr = Text()

    timestamp = Date(required=True)

    changes = Nested(Change)

    class Index:
        name = conf.INDEX_NAME

    @property
    def actor(self):
        if self.actor_email:
            if self.actor_first_name and self.actor_last_name:
                return f'{self.actor_first_name} {self.actor_last_name} ({self.actor_email})'
            return self.actor_email
        return None

    @property
    def changed_fields(self):
        if self.action == LogEntry.Action.DELETE:
            return ''  # delete
        changes = self.changes
        s = '' if len(changes) == 1 else 's'
        fields = ', '.join(change['field'] for change in changes)
        if len(fields) > MAX:
            i = fields.rfind(' ', 0, MAX)
            fields = fields[:i] + ' ..'
        return '%d change%s: %s' % (len(changes), s, fields)

    def __str__(self):
        if self.action == self.Action.CREATE:
            fstring = "Created {repr:s}"
        elif self.action == self.Action.UPDATE:
            fstring = "Updated {repr:s}"
        elif self.action == self.Action.DELETE:
            fstring = "Deleted {repr:s}"
        else:
            fstring = "Logged {repr:s}"

        return fstring.format(repr=self.object_repr)

    @classmethod
    def log_create(cls, kwargs) -> Optional['LogEntry']:
        """
        Helper method to create a new log entry.
        :param kwargs: Field overrides for the :py:class:`LogEntry` object.
        :return: The new log entry or `None` if there were no changes.
        :rtype: LogEntry
        """
        if kwargs is not None:
            log_entry = cls(**kwargs)
            log_entry.save()
            return log_entry
        return None

    def save(self, using=None, index=None, validate=True, skip_empty=True, **kwargs):
        try:
            return super().save(using, index, validate, skip_empty, **kwargs)
        except Exception:
            logging.exception(
                "Error when saving log to elasticsearch",
                extra={'log_entry': self.to_dict()}
            )

    @classmethod
    def _get_pk_value(cls, instance: Any):
        """
        Get the primary key field value for a model instance.
        Only supports one column primary keys
        :param instance: The model instance to get the primary key for.
        :type instance: Model
        :return: The primary key value of the given model instance.
        """
        name = instance.__table__.primary_key.columns.values()[0].name
        return getattr(instance, name)

    @classmethod
    def get_fields(cls, instance: Any, **kwargs) -> Optional[dict]:
        changes = kwargs.get('changes', None)
        pk = cls._get_pk_value(instance)

        if changes is not None:
            kwargs.setdefault('object_pk', str(pk))
            kwargs.setdefault('object_repr', str(instance))
            kwargs.setdefault('timestamp', datetime.now())
            kwargs.setdefault('table_name', instance.__tablename__)
            kwargs.setdefault('remote_addr', get_remote_addr())
            if isinstance(pk, int):
                kwargs.setdefault('object_id', pk)
            return kwargs
        return None

    @classmethod
    def set_user_fields(cls, user: Any, kwargs) -> None:
        kwargs.setdefault('actor_id', user.id)
        kwargs.setdefault('actor_email', user.email)
        kwargs.setdefault('actor_first_name', user.first_name)
        kwargs.setdefault('actor_last_name', user.last_name)


def register_log_entry_class(cls):
    """
    Register new log entry class
    """
    if not issubclass(cls, LogEntry):
        raise ValueError(f"`{cls.__name__}` must inherit from `LogEntry` class")
    LogEntry.subclass = cls
    return cls


def log_entry_class():
    return getattr(LogEntry, 'subclass', LogEntry)
