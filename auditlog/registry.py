from typing import Optional, List, Tuple, Any

DispatchUID = Tuple[int, str, int]


class AuditlogModelRegistry:
    """
    A registry that keeps track of the models that use Auditlog to track changes.
    """

    def __init__(self):

        self._registry = {}

    def register(
        self, model: Any = None, include_fields: Optional[List[str]] = None,
        exclude_fields: Optional[List[str]] = None,
    ) -> Any:
        """
        Register a model with auditlog. Auditlog will then track mutations on this model's instances.

        :param model: The model to register.
        :param include_fields: The fields to include. Implicitly excludes all other fields.
        :param exclude_fields: The fields to exclude. Overrides the fields to include.

        """

        if include_fields is None:
            include_fields = []
        if exclude_fields is None:
            exclude_fields = []

        def registrar(cls):
            """Register models for a given class."""
            self._registry[cls] = {
                'include_fields': include_fields,
                'exclude_fields': exclude_fields,
            }
            # We need to return the class, as the decorator is basically
            # syntactic sugar for:
            # MyClass = auditlog.register(MyClass)
            return cls

        if model is None:
            # If we're being used as a decorator, return a callable with the
            # wrapper.
            return lambda cls: registrar(cls)
        else:
            # Otherwise, just register the model.
            registrar(model)

    def contains(self, model: Any) -> bool:
        """
        Check if a model is registered with auditlog.

        :param model: The model to check.
        :return: Whether the model has been registered.
        :rtype: bool
        """
        return model in self._registry

    def unregister(self, model: Any) -> None:
        """
        Unregister a model with auditlog. This will not affect the database.

        :param model: The model to unregister.
        """
        try:
            del self._registry[model]
        except KeyError:
            pass

    def get_models(self) -> List:
        return list(self._registry.keys())

    def get_model_fields(self, model: Any):
        return {
            'include_fields': list(self._registry[model]['include_fields']),
            'exclude_fields': list(self._registry[model]['exclude_fields']),
        }


auditlog = AuditlogModelRegistry()
