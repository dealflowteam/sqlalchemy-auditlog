import weakref
from typing import Any, List

from sqlalchemy import inspect
from sqlalchemy.orm import object_mapper, ColumnProperty

from auditlog.documents import log_entry_class


def get_fields_in_model(instance: Any) -> List:
    """
    Returns the list of fields in the given model instance.

    :param instance: The model instance to get the fields for
    :return: The list of fields for the given model (instance)
    """
    from auditlog.registry import auditlog

    attrs = object_mapper(instance).iterate_properties
    model_attrs = auditlog.get_model_fields(instance.__class__)
    if model_attrs['include_fields']:
        attrs = (attr for attr in attrs if attr.key in model_attrs['include_fields'])
    if model_attrs['exclude_fields']:
        attrs = (attr for attr in attrs if attr.key not in model_attrs['exclude_fields'])

    return attrs


def model_instance_diff(obj: Any):
    """
    Find difference between two model instances.
    :param obj: changed model instance
    :return: List of dictionary with old and new values
    """
    diff = []
    for mapper_property in get_fields_in_model(obj):
        if isinstance(mapper_property, ColumnProperty):
            key = mapper_property.key
            attribute_state = inspect(obj).attrs.get(key)
            history = attribute_state.history
            if history.has_changes():
                diff.append({
                    'field': key,
                    'old': str(history.deleted[0]) if history.deleted else None,
                    'new': str(attribute_state.value)
                })
    return diff


def set_entry_attributes(
    obj: Any, action: log_entry_class().Action, entry_attrs: list, user_ref: weakref.ref
) -> None:
    from auditlog.registry import auditlog

    if auditlog.contains(obj.__class__):
        changes = model_instance_diff(obj)
        if changes or action == log_entry_class().Action.DELETE:
            # create log entry only if there are any changes in tracked fields
            kwargs = log_entry_class().get_fields(
                obj,
                action=action,
                changes=changes,
            )
            if user_ref and user_ref():
                log_entry_class().set_user_fields(user_ref(), kwargs)
            entry_attrs.append(kwargs)
