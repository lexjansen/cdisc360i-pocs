import warnings
from odmlib.valueset import ValueSet as _ValueSet

warnings.warn(
    "odmlib.odm_2_0.valueset is deprecated. Valuesets are now "
    "automatically selected based on model version. "
    "Use odmlib.valueset.ValueSet instead.",
    DeprecationWarning,
    stacklevel=2
)


class ValueSet:
    """Deprecated: Redirects to new valueset system"""
    @classmethod
    def value_set(cls, attribute):
        """Redirect to new valueset system with ODM 2.0 version"""
        return _ValueSet.value_set(attribute, version='odm_2_0')
