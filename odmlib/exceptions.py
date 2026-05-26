"""
odmlib exception hierarchy.

All odmlib-specific exceptions inherit from OdmlibError, which itself
inherits from Exception. During the v0.2.x transition period, validation
and type exceptions also inherit from ValueError/TypeError respectively
so that existing except clauses continue to work.

Deprecation schedule:
    v0.2.x: New exceptions dual-inherit from ValueError/TypeError.
            All existing ``except ValueError`` and ``except TypeError``
            clauses continue to work unchanged.
    v0.3.0: Remove the ValueError/TypeError base classes.
            Update ``except ValueError`` → ``except OdmlibValidationError``
            and ``except TypeError`` → ``except OdmlibTypeError``.
"""
import warnings


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class OdmlibError(Exception):
    """Base exception for all odmlib errors."""


# ---------------------------------------------------------------------------
# Validation errors (currently raised as ValueError)
# ---------------------------------------------------------------------------

class OdmlibValidationError(OdmlibError, ValueError):
    """Raised when an element fails conformance, OID, or schema validation.

    Attributes:
        element_path: Dot-separated path from root to the failing element,
            e.g. "ODM > Study > MetaDataVersion > ItemGroupDef(OID='IG.VS')"
        hint: Optional human-readable suggestion for fixing the problem.
        attribute: The attribute name that caused the error (if applicable).
        element_type: The class name of the element that failed validation.
    """

    def __init__(self, message, *, element_path=None, hint=None,
                 attribute=None, element_type=None, actual_value=None):
        self.element_path = element_path
        self.hint = hint
        self.attribute = attribute
        self.element_type = element_type
        self.actual_value = actual_value
        self._raw_message = message
        super().__init__(self._format())

    def _format(self):
        parts = [self._raw_message]
        if self.element_path:
            parts.append(f"  Context: {self.element_path}")
        if self.hint:
            parts.append(f"  Hint: {self.hint}")
        return "\n".join(parts)


class OdmlibRequiredAttributeError(OdmlibValidationError):
    """Raised when a required attribute is missing during construction."""


class OdmlibOIDError(OdmlibValidationError):
    """Raised for OID uniqueness or ref/def integrity failures."""


class OdmlibConformanceError(OdmlibValidationError):
    """Raised when Cerberus conformance validation fails.

    Attributes:
        cerberus_errors: The raw Cerberus error dict for programmatic access.
    """

    def __init__(self, message, *, cerberus_errors=None, **kwargs):
        self.cerberus_errors = cerberus_errors or {}
        super().__init__(message, **kwargs)


class OdmlibElementOrderError(OdmlibValidationError):
    """Raised when child elements are not in the order required by the ODM spec."""


class OdmlibSchemaValidationError(OdmlibValidationError):
    """Raised when XSD/XML-Schema validation of an ODM document fails.

    Wraps the underlying ``xmlschema`` exception raised during XSD
    validation (e.g. by :meth:`ODMSchemaValidator.validate_file`). The
    wrapped exception is available at ``args[0]`` (for backward
    compatibility with callers that introspect ``ex.args[0].msg``) and
    via the ``wrapped`` attribute.
    """

    def __init__(self, wrapped_exception, *, hint=None):
        # Bypass OdmlibValidationError.__init__: it would replace args[0]
        # with a formatted string and would crash on a non-string message.
        # Preserve args[0] == wrapped exception for backward compatibility.
        self.wrapped = wrapped_exception
        self.element_path = None
        self.hint = hint
        self.attribute = None
        self.element_type = None
        self.actual_value = None
        self._raw_message = str(wrapped_exception)
        Exception.__init__(self, wrapped_exception)


# ---------------------------------------------------------------------------
# Type errors (currently raised as TypeError)
# ---------------------------------------------------------------------------

class OdmlibTypeError(OdmlibError, TypeError):
    """Raised when a value has the wrong type for an attribute.

    Attributes:
        attribute: The attribute name.
        expected_type: The expected type description.
        actual_value: The value that was provided.
        element_path: Path from root to the failing element (if known).
        hint: Optional human-readable suggestion for fixing the problem.
    """

    def __init__(self, message, *, attribute=None, expected_type=None,
                 actual_value=None, element_path=None, hint=None,
                 element_type=None):
        self.attribute = attribute
        self.expected_type = expected_type
        self.actual_value = actual_value
        self.element_path = element_path
        self.hint = hint
        self.element_type = element_type
        self._raw_message = message
        super().__init__(self._format())

    def _format(self):
        parts = [self._raw_message]
        if self.element_path:
            parts.append(f"  Context: {self.element_path}")
        if self.hint:
            parts.append(f"  Hint: {self.hint}")
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Parsing errors
# ---------------------------------------------------------------------------

class OdmlibParsingError(OdmlibError):
    """Raised when an XML or JSON document cannot be parsed into the model."""

    def __init__(self, message, *, hint=None):
        self.hint = hint
        self._raw_message = message
        parts = [message]
        if hint:
            parts.append(f"  Hint: {hint}")
        super().__init__("\n".join(parts))


class OdmlibLoaderStateError(OdmlibParsingError, ValueError):
    """Raised when a loader method is called before the document is opened.

    Also inherits from ValueError for backward compatibility with code that
    catches ValueError from loader calls.
    """


# ---------------------------------------------------------------------------
# Serialization errors
# ---------------------------------------------------------------------------

class OdmlibSerializationError(OdmlibError):
    """Raised when an in-memory model cannot be written to XML or JSON."""


# ---------------------------------------------------------------------------
# Namespace errors
# ---------------------------------------------------------------------------

class OdmlibNamespaceError(OdmlibError, ValueError):
    """Raised for namespace registration or lookup failures."""

    def __init__(self, message, *, hint=None):
        self.hint = hint
        self._raw_message = message
        parts = [message]
        if hint:
            parts.append(f"  Hint: {hint}")
        super().__init__("\n".join(parts))


# ---------------------------------------------------------------------------
# Warnings
# ---------------------------------------------------------------------------

class OdmlibWarning(UserWarning):
    """Base warning for all odmlib non-fatal issues."""


class OdmlibDeprecationWarning(OdmlibWarning, DeprecationWarning):
    """Issued when a deprecated odmlib feature is used."""


class OdmlibInteroperabilityWarning(OdmlibWarning):
    """Issued for constructs that are valid but may cause interoperability issues."""


# ---------------------------------------------------------------------------
# Error collector for collect-all-errors mode
# ---------------------------------------------------------------------------

class ErrorCollector:
    """Accumulates validation errors instead of raising immediately.

    Pass to :meth:`~odmlib.odm_element.ODMElement.validate` with
    ``collect_errors=True`` to gather all errors in a single pass rather
    than stopping at the first failure.

    Example::

        collector = ErrorCollector()
        errors = odm.validate(collect_errors=True, oid_checker=checker)
        if errors:
            for err in errors:
                print(err)

    Attributes:
        errors: List of :class:`OdmlibError` instances collected so far.
        warnings: List of :class:`OdmlibWarning` instances collected so far.
    """

    def __init__(self):
        self.errors = []
        self.warnings = []

    @property
    def has_errors(self):
        """True if any errors have been collected."""
        return len(self.errors) > 0

    def add_error(self, error):
        """Add an :class:`OdmlibError` to the collection."""
        self.errors.append(error)

    def add_warning(self, warning):
        """Add an :class:`OdmlibWarning` to the collection."""
        self.warnings.append(warning)

    def raise_if_errors(self):
        """Raise if any errors were collected.

        Raises the single collected error directly if only one exists, or a
        new :class:`OdmlibValidationError` summarising all errors otherwise.
        """
        if not self.has_errors:
            return
        if len(self.errors) == 1:
            raise self.errors[0]
        msg = f"{len(self.errors)} validation errors found:\n"
        msg += "\n".join(f"  {i + 1}. {err}" for i, err in enumerate(self.errors))
        raise OdmlibValidationError(msg)
