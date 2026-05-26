"""Validation mode control for odmlib.

This module provides a context-managed permissive loading mode that allows
non-conformant ODM/Define-XML files to be loaded into the object model for
inspection and repair. The mode uses ``contextvars.ContextVar`` with a ``Flag``
enum for graduated control over which validations to bypass.

Quick start::

    from odmlib import permissive

    with permissive():
        loader.open_odm_document("broken.xml")
        odm = loader.root()

    # Mode is back to strict — fix issues, then validate
    errors = odm.validate(collect_errors=True)
"""

import contextvars
from contextlib import contextmanager
from enum import Flag, auto


class ValidationMode(Flag):
    """Flag enum controlling which validation categories are enforced.

    Members can be combined with ``|`` to create targeted relaxation::

        ValidationMode.SKIP_REQUIRED | ValidationMode.SKIP_VALUESET
    """

    STRICT = 0
    """All validation enforced (default, preserves existing behavior)."""

    SKIP_REQUIRED = auto()
    """Omit required-attribute checks during construction and access."""

    SKIP_VALUESET = auto()
    """Omit ``ValidValues`` and ``ExtendedValidValues`` enforcement."""

    SKIP_TYPE = auto()
    """Omit type checks and unknown-attribute rejection."""

    SKIP_FORMAT = auto()
    """Omit format validators (datetime, SAS name, email, URL, etc.)."""

    PERMISSIVE = SKIP_REQUIRED | SKIP_VALUESET | SKIP_TYPE | SKIP_FORMAT
    """Composite flag that skips all validation categories."""


_validation_mode: contextvars.ContextVar[ValidationMode] = contextvars.ContextVar(
    "odmlib_validation_mode", default=ValidationMode.STRICT
)


def get_mode() -> ValidationMode:
    """Return the current validation mode from the ContextVar."""
    return _validation_mode.get()


def set_mode(mode: ValidationMode) -> contextvars.Token:
    """Set the validation mode and return a reset token.

    Args:
        mode: The validation mode to activate.

    Returns:
        A ``contextvars.Token`` that can be passed to
        ``_validation_mode.reset()`` to restore the previous mode.
    """
    return _validation_mode.set(mode)


def is_permissive(flag: ValidationMode) -> bool:
    """Check whether a specific validation flag is active.

    Args:
        flag: The validation category to check (e.g.,
            ``ValidationMode.SKIP_REQUIRED``).

    Returns:
        ``True`` if the flag is active in the current mode.
    """
    return bool(get_mode() & flag)


@contextmanager
def permissive(mode: ValidationMode = ValidationMode.PERMISSIVE):
    """Context manager that activates a permissive validation mode.

    On entry, sets the validation mode to *mode*. On exit (including on
    exception), restores the previous mode via token reset.

    Args:
        mode: The validation mode to activate. Defaults to
            ``ValidationMode.PERMISSIVE`` (skip all validation).

    Example::

        from odmlib import permissive, ValidationMode

        # Skip everything
        with permissive():
            ...

        # Skip only required checks
        with permissive(ValidationMode.SKIP_REQUIRED):
            ...
    """
    token = _validation_mode.set(mode)
    try:
        yield
    finally:
        _validation_mode.reset(token)