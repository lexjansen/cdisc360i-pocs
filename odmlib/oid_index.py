from odmlib.exceptions import OdmlibOIDError


class OIDIndex:
    def __init__(self):
        self.oid_index = {}

    def add_oid(self, oid, element):
        """ odmlib expects all OIDs to be unique within the scope of an ODM document """
        if oid not in self.oid_index:
            self.oid_index[oid] = []
        self.oid_index[oid].append(element)

    def find_all(self, oid):
        if not self.oid_index:
            raise OdmlibOIDError(
                f"The OID index is empty. Build the index prior to using find_all. OID {oid} not found.",
                attribute="OID",
                hint="Call build_oid_index() on the root ODM element before using find_all()",
            )
        elif oid not in self.oid_index:
            raise OdmlibOIDError(
                f"OID {oid} not found in the OID index.",
                attribute="OID",
                hint=f"Verify that an element with OID '{oid}' has been added to the model",
            )
        return self.oid_index[oid]
