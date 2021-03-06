from sqlalchemy.orm import Session

from auditlog.diff import set_entry_attributes
from auditlog.documents import log_entry_class


def track_instances_after_flush(session: Session, context):
    entry_attrs = session.info.setdefault('entry_attrs', list())
    user = session.info.get('user')
    for obj in session.new:
        set_entry_attributes(
            obj,
            log_entry_class().Action.CREATE,
            entry_attrs,
            user
        )
    for obj in session.dirty:
        set_entry_attributes(
            obj,
            log_entry_class().Action.UPDATE,
            entry_attrs,
            user
        )
    for obj in session.deleted:
        set_entry_attributes(
            obj,
            log_entry_class().Action.DELETE,
            entry_attrs,
            user
        )


def save_log_entries_after_commit(session: Session):
    entry_attrs = session.info.get('entry_attrs')
    if entry_attrs:
        for kwargs in entry_attrs:
            log_entry_class().log_create(kwargs)
        del session.info['entry_attrs']

