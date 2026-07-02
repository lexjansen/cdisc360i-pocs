"""Global registry for XML namespace prefix-to-URI mappings.

This module provides :class:`Borg` and :class:`NamespaceRegistry` for
managing XML namespace declarations used in ODM and Define-XML documents.

The Borg pattern ensures that all instances of :class:`NamespaceRegistry`
share the same state, providing a convenient global registry without
requiring a strict singleton or global variable.

Example::

    import odmlib.ns_registry as NS

    NS.NamespaceRegistry(prefix="odm",
        uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True, is_reset=True)
    NS.NamespaceRegistry(prefix="def",
        uri="http://www.cdisc.org/ns/def/v2.1")
"""
import validators
from odmlib.exceptions import OdmlibNamespaceError


class Borg:
    """Borg pattern base class providing shared state across instances.

    All instances of subclasses share the same ``namespaces`` and
    ``default_namespace`` dictionaries, enabling a singleton-like
    namespace registry without requiring a true singleton.

    Class Attributes:
        namespaces (dict): Maps prefix to URI for all registered namespaces.
        default_namespace (dict): Maps the default namespace prefix to URI.
    """

    namespaces = {}
    default_namespace = {}

    @classmethod
    def reset(cls):
        """Reset all shared namespace state to empty dicts.

        Should be called between tests or when reinitializing the registry
        from scratch to prevent cross-test state leakage.
        """
        cls.namespaces = {}
        cls.default_namespace = {}


class NamespaceRegistry(Borg):
    """Global registry for XML namespace prefix-to-URI mappings.

    Uses the Borg pattern so all instances share state. Manages namespace
    prefix registration and provides methods for XML serialization.

    Args:
        prefix (str): Namespace prefix (e.g., "odm", "def", "xs").
        uri (str): Namespace URI (must be a valid URL).
        is_default (bool): If True, this becomes the default namespace
            (used for xmlns= in XML output).
        is_reset (bool): If True, clears all existing entries first.

    Raises:
        OdmlibNamespaceError: If the URI is not a valid URL.

    Example::

        import odmlib.ns_registry as NS
        NS.NamespaceRegistry(prefix="odm",
            uri="http://www.cdisc.org/ns/odm/v1.3",
            is_default=True, is_reset=True)
    """

    def __init__(self, prefix=None, uri=None, is_default=False, is_reset=False):
        if is_reset:
            super().reset()
        if prefix is not None and uri is not None:
            if validators.url(uri):
                self._update_registry(prefix, uri, is_default)
            else:
                raise OdmlibNamespaceError(
                    f"Namespace uri is not a valid url: {uri}",
                    hint="Provide a valid URI, e.g., 'http://www.cdisc.org/ns/odm/v1.3'",
                )

    def get_odm_namespace_entries(self):
        """Return namespace entries as xmlns= strings for XML serialization.

        Returns:
            list[str]: A list of strings like ``["xmlns=http://...", "xmlns:def=http://..."]``.
                The first entry is always the default namespace.
        """
        entries = ["xmlns=" + list(self.default_namespace.values())[0]]
        for prefix, uri in self.namespaces.items():
            if prefix != list(self.default_namespace.keys())[0]:
                entries.append("xmlns:" + prefix + "=" + uri)
        return entries

    def get_ns_entry_dict(self, prefix):
        """Return a ``{prefix: uri}`` dict for the given prefix, or ``{}`` if not found.

        Used by loaders to build the ``namespaces`` dict for ElementTree
        ``find`` and ``findall`` calls.

        Args:
            prefix (str): Namespace prefix to look up.

        Returns:
            dict: ``{prefix: uri}`` if registered, otherwise ``{}``.
        """
        if prefix in self.namespaces:
            return {prefix: self.namespaces[prefix]}
        else:
            return {}

    def get_ns_attribute_name(self, name, prefix):
        """Return the full ElementTree-style attribute name with namespace braces.

        For the default namespace, returns the bare ``name``. For
        non-default namespaces, returns ``{uri}name``.

        Args:
            name (str): The local attribute name.
            prefix (str): The namespace prefix.

        Returns:
            str: The qualified attribute name (e.g., ``"{http://...}lang"``
                or ``"lang"`` for the default namespace).

        Raises:
            OdmlibNamespaceError: If ``prefix`` has not been registered.
        """
        if prefix in self.namespaces:
            if prefix in self.default_namespace:
                return name
            else:
                return "{" + self.namespaces[prefix] + "}" + name
        else:
            raise OdmlibNamespaceError(
                f"Error: Namespace with prefix {prefix} has not been registered",
                hint=f"Register the namespace first: NamespaceRegistry(prefix='{prefix}', uri='...')",
            )

    def get_prefix_ns_from_uri(self, uri):
        """Return the prefix for a given namespace URI.

        Args:
            uri (str): The namespace URI to look up (case-insensitive match).

        Returns:
            str: The registered prefix for that URI.

        Raises:
            OdmlibNamespaceError: If no prefix is registered for ``uri``.
        """
        for prefix, ns_uri in self.namespaces.items():
            if uri.lower() == ns_uri.lower():
                return prefix
        raise OdmlibNamespaceError(
            f"Error: Namespace with URI {uri} has not been registered",
            hint="Register the namespace URI first via NamespaceRegistry(prefix=..., uri=...)",
        )

    def set_odm_namespace_attributes(self, odm_elem):
        """Set xmlns attributes on an ElementTree root element.

        Adds ``xmlns`` for the default namespace and ``xmlns:prefix``
        for each additional namespace to the element's ``attrib`` dict.

        Args:
            odm_elem (ET.Element): The root XML element to annotate.
        """
        odm_elem.attrib["xmlns"] = list(self.default_namespace.values())[0]
        for prefix, uri in self.namespaces.items():
            if prefix != list(self.default_namespace.keys())[0]:
                odm_elem.attrib["xmlns:" + prefix] = uri

    def set_odm_namespace_attributes_string(self, odm_str):
        """Add xmlns attributes to an ODM XML string.

        Replaces the opening ``<ODM`` tag in ``odm_str`` with a version
        that includes all registered namespace declarations.

        Args:
            odm_str (str): An ODM XML string whose root element is ``<ODM>``.

        Returns:
            str: The modified XML string with xmlns attributes injected.
        """
        ns_str = "<ODM xmlns=\"" + list(self.default_namespace.values())[0] + "\""
        for prefix, uri in self.namespaces.items():
            if prefix != list(self.default_namespace.keys())[0]:
                ns_str += " xmlns:" + prefix + "=\"" + uri + "\""
        odm_ns_str = odm_str.replace("<ODM", ns_str)
        return odm_ns_str

    def _update_registry(self, prefix, uri, is_default):
        """Add or update an entry in the shared namespace registry.

        Args:
            prefix (str): Namespace prefix.
            uri (str): Namespace URI.
            is_default (bool): If True, also records this as the default namespace.
        """
        self.namespaces[prefix] = uri
        if is_default:
            self.default_namespace[prefix] = uri

    def remove_registry_entry(self, prefix):
        """Remove a namespace entry by prefix.

        Removes the prefix from both ``namespaces`` and
        ``default_namespace`` (if present).

        Args:
            prefix (str): The namespace prefix to remove.
        """
        if prefix in self.namespaces:
            self.namespaces.pop(prefix)
        if prefix in self.default_namespace:
            self.default_namespace.pop(prefix)
