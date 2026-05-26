"""Base descriptor protocol for ODM element attributes.

This module provides the :class:`Descriptor` base class that implements
the Python descriptor protocol for ODM element attributes. All odmlib
attribute types inherit from this class.
"""
from __future__ import annotations
from typing import Any, Optional
from odmlib.exceptions import OdmlibRequiredAttributeError
import odmlib.mode as _mode


class Descriptor:
    """Base descriptor for all ODM element attributes.

    Implements the Python descriptor protocol (``__get__``, ``__set__``,
    ``__delete__``). When accessed on a class, returns the descriptor
    itself. When accessed on an instance, returns the value from the
    instance's ``__dict__``.

    For required attributes without a set value, raises
    :exc:`~odmlib.exceptions.OdmlibRequiredAttributeError`.
    For optional list attributes without a value, auto-initializes to [].
    For optional element attributes without a value, auto-instantiates
    the element class.

    Args:
        name (str): Attribute name (set by :class:`ODMMeta` during class creation).
        required (bool): If True, attribute must be provided at construction.
        element_class (type): For child element descriptors, the expected class.
        valid_values (list): List of permitted values (empty = any value).
        namespace (str): XML namespace prefix (default: "odm").
    """

    def __init__(self, name: Optional[str] = None, required: bool = False,
                 element_class: Optional[type] = None,
                 valid_values: Optional[list] = None,
                 namespace: str = "odm") -> None:
        self.name = name
        self.required = required
        self.element_class = element_class
        self.valid_values = valid_values if valid_values is not None else []
        self.namespace = namespace

    def __get__(self, instance: Any, cls: type) -> Any:
        """Return the descriptor itself (class access) or the stored value (instance access).

        Args:
            instance: The object instance, or None if accessed on the class.
            cls: The owner class.

        Returns:
            The descriptor itself when accessed on the class, or the stored
            attribute value when accessed on an instance.

        Raises:
            OdmlibRequiredAttributeError: If the attribute is required and has
                not been set on the instance.
        """
        if instance is None:
            return self
        if self.name in instance.__dict__:
            return instance.__dict__[self.name]
        # Attribute not set on instance — raise only for plain required attributes
        # (not ODMObject/ODMListObject, which have element_class set and auto-initialize)
        if self.required and self.element_class is None:
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_REQUIRED):
                raise OdmlibRequiredAttributeError(
                    f"Missing attribute or element {self.name} in {cls.__name__}",
                    attribute=self.name,
                    element_type=cls.__name__,
                    hint=f"Attribute '{self.name}' is required when constructing {cls.__name__}",
                )
            else:
                return None
        # Auto-initialize optional attributes
        if isinstance(self, list):
            self.__set__(instance, [])
        else:
            if self.element_class is None:
                instance.__dict__[self.name] = self.element_class
            else:
                try:
                    instance.__dict__[self.name] = self.element_class()
                except ValueError:
                    instance.__dict__[self.name] = None
        return instance.__dict__[self.name]

    def __set__(self, instance: Any, value: Any) -> None:
        """Store ``value`` in the instance's ``__dict__`` under this descriptor's name.

        Args:
            instance: The object instance on which to set the value.
            value: The value to store.
        """
        instance.__dict__[self.name] = value

    def __delete__(self, instance: Any) -> None:
        """Remove this attribute from the instance's ``__dict__``.

        Args:
            instance: The object instance from which to remove the attribute.
        """
        del instance.__dict__[self.name]
