import odmlib.odm_element as OE
import odmlib.typed as T
import odmlib.ns_registry as NS

NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0", is_default=True)
NS.NamespaceRegistry(prefix="xs", uri="http://www.w3.org/2001/XMLSchema-instance")
NS.NamespaceRegistry(prefix="xml", uri="http://www.w3.org/XML/1998/namespace")
NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")


class TranslatedText(OE.ODMElement):
    """A piece of text in a specific language, used inside Description and similar elements.

    Attributes:
        lang (str): BCP 47 language tag (xml:lang attribute), e.g. "en".
        Type (str, required): Media-type qualifier for the text (XSD type
            ``text``, free-text, ``use="required"``), e.g. ``"text/plain"``.
            Required by the ODM 2.0 schema.
        _content (str, required): The actual text content.
    """

    lang = T.String(namespace="xml")
    Type = T.String(required=True)
    _content = T.String(required=True)


class Description(OE.ODMElement):
    """A human-readable description composed of one or more language-tagged text blocks.

    Attributes:
        TranslatedText (list, required): One or more TranslatedText children
            providing the description in different languages.
    """

    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class Title(OE.ODMElement):
    _content = T.String(required=False)


class Leaf(OE.ODMElement):
    ID = T.ID(required=True)
    href = T.String(required=True, namespace="xlink")
    Title = T.ODMObject(element_class=Title)


class PDFPageRef(OE.ODMElement):
    Type = T.ValueSetString(required=True)
    PageRefs = T.String()
    FirstPage = T.PositiveInteger()
    LastPage = T.PositiveInteger()


class DocumentRef(OE.ODMElement):
    leafID = T.IDRef(required=True)
    PDFPageRef = T.ODMListObject(element_class=PDFPageRef)


class AnnotatedCRF(OE.ODMElement):
    DocumentRef = T.ODMObject(required=True, element_class=DocumentRef)


class SupplementalDoc(OE.ODMElement):
    DocumentRef = T.ODMObject(required=True, element_class=DocumentRef)


class CommentDef(OE.ODMElement):
    OID = T.OID(required=True)
    Description = T.ODMObject(element_class=Description)
    DocumentRef = T.ODMObject(element_class=DocumentRef)


class Coding(OE.ODMElement):
    Code = T.String(required=False)
    System = T.String(required=True)
    SystemName = T.String()
    SystemVersion = T.String()
    Label = T.String()
    href = T.String()
    ref = T.String()
    CommentOID = T.OIDRef(required=False)


class Alias(OE.ODMElement):
    """An alternative name or identifier for an ODM element in an external context.

    Attributes:
        Context (str, required): The context in which the alias applies,
            e.g. the name of an external system or standard.
        Name (str, required): The alias value in that context.
    """

    Context = T.String(required=True)
    Name = T.String(required=True)


# class StudyDescription(OE.ODMElement):
#     Description = T.ODMObject(element_class=Description, required=True)


# class ProtocolName(OE.ODMElement):
#     _content = T.String(required=True)
#
#
# class StudyName(OE.ODMElement):
#     _content = T.String(required=True)


class Include(OE.ODMElement):
    """Includes the metadata from another study's MetaDataVersion into this one.

    Attributes:
        StudyOID (str, required): OID reference to the study whose metadata
            is being included.
        MetaDataVersionOID (str, required): OID reference to the specific
            MetaDataVersion being included.
    """

    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)


class Standard(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.String(required=True)
    Type = T.String(required=True)
    PublishingSet = T.String(required=False)
    Version = T.String(required=True)
    Status = T.String(required=False)
    CommentOID = T.OIDRef(required=False)


class Standards(OE.ODMElement):
    Standard = T.ODMListObject(required=True, element_class=Standard)


class StudyEventRef(OE.ODMElement):
    """A reference to a StudyEventDef within a Protocol or ExceptionEvent.

    Attributes:
        StudyEventOID (str, required): OID of the referenced StudyEventDef.
        OrderNumber (int): Position of this event in the sequence.
        Mandatory (str, required): Whether collection of this event is
            mandatory ("Yes" or "No").
        CollectionExceptionConditionOID (str): OID of a ConditionDef that,
            when true, suppresses collection of this event.
    """

    StudyEventOID = T.OIDRef(required=True)
    OrderNumber = T.Integer(required=False)
    Mandatory = T.ValueSetString(required=True)
    CollectionExceptionConditionOID = T.OIDRef()


class WorkflowRef(OE.ODMElement):
    WorkflowOID = T.OIDRef(required=True)


class Arm(OE.ODMElement):
    """Defines a study arm (treatment arm) in the trial design.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name of the arm.
        Description: Optional description.
        WorkflowRef: Reference to the workflow that defines this arm's event
            sequence.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Description = T.ODMObject(element_class=Description)
    WorkflowRef = T.ODMObject(element_class=WorkflowRef)


class Epoch(OE.ODMElement):
    """Defines a study epoch (a named period of the trial).

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name of the epoch.
        SequenceNumber (int, required): Ordinal position of this epoch in the
            overall trial timeline.
        Description: Optional description.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    SequenceNumber = T.PositiveInteger(required=True)
    Description = T.ODMObject(element_class=Description)


class StudyStructure(OE.ODMElement):
    """Defines the high-level arms and epochs that constitute the study design.

    Attributes:
        Description: Optional description of the study structure.
        Arm (list): One or more arms (treatment groups) in the trial.
        Epoch (list): One or more epochs (time periods) in the trial.
        WorkflowRef (list): References to workflows associated with the
            overall study structure.
    """

    Description = T.ODMObject(element_class=Description)
    Arm = T.ODMListObject(element_class=Arm)
    Epoch = T.ODMListObject(element_class=Epoch)
    WorkflowRef = T.ODMListObject(element_class=WorkflowRef)


class Protocol(OE.ODMElement):
    """Defines the overall structure of the study protocol in ODM 2.0.

    Lists the study events that constitute the protocol, along with any
    aliases.

    Attributes:
        Description: Optional human-readable description.
        StudyEventRef (list): Ordered references to StudyEventDef elements
            that make up this protocol.
        Alias (list): Alternative names for this protocol in external contexts.
    """

    Description = T.ODMObject(element_class=Description)
    StudyStructure = T.ODMObject(element_class=StudyStructure)
    StudyEventRef = T.ODMListObject(element_class=StudyEventRef)
    Alias = T.ODMListObject(element_class=Alias)


class ItemGroupRef(OE.ODMElement):
    """A reference to an ItemGroupDef within a StudyEventDef or ItemGroupDef.

    In ODM 2.0 the FormDef/FormRef layer is removed; StudyEventDef
    references ItemGroupDef directly via ItemGroupRef.

    Attributes:
        ItemGroupOID (str, required): OID of the referenced ItemGroupDef.
        OrderNumber (int): Position of this item group in the sequence.
        Mandatory (str, required): Whether collection of this item group is
            mandatory ("Yes" or "No").
        CollectionExceptionConditionOID (str): OID of a ConditionDef that,
            when true, suppresses collection of this item group.
    """

    ItemGroupOID = T.OIDRef(required=True)
    OrderNumber = T.Integer(required=False)
    Mandatory = T.ValueSetString(required=True)
    CollectionExceptionConditionOID = T.OIDRef()


class StudyEventDef(OE.ODMElement):
    """ represents ODM v2.0 StudyEventDef and can serialize as JSON or XML """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Repeating = T.ValueSetString(required=True)
    Type = T.ValueSetString(required=True)
    Category = T.String(required=False)
    CommentOID = T.OIDRef(required=False)
    Description = T.ODMObject(element_class=Description)
    ItemGroupRef = T.ODMListObject(element_class=ItemGroupRef)
    WorkflowRef = T.ODMListObject(element_class=WorkflowRef)
    Alias = T.ODMListObject(element_class=Alias)

    def __len__(self):
        """ returns the number of ItemGroupRefs in an StudyEventDef object as the length """
        return len(self.ItemGroupRef)

    def __getitem__(self, position):
        """
        creates an iterator from an StudyEventDef object that returns the ItemGroupRef in position
        """
        return self.ItemGroupRef[position]

    def __iter__(self):
        return iter(self.ItemGroupRef)


class ArchiveLayout(OE.ODMElement):
    """Describes a PDF-based presentation layout for an ODM element.

    Attributes:
        OID (str, required): Unique identifier for this archive layout.
        PdfFileName (str, required): Name of the PDF file containing the layout.
        PresentationOID (str): OID reference to the associated Presentation
            element, if any.
    """

    OID = T.OID(required=True)
    PdfFileName = T.FileName(required=True)
    PresentationOID = T.OIDRef(required=False)

    def __len__(self):
        return len(self.ItemGroupRef)

    def __getitem__(self, position):
        return self.ItemGroupRef[position]

    def __iter__(self):
        return iter(self.ItemGroupRef)


class SourceItem(OE.ODMElement):
    """Identifies the source of an item's data within an Origin element.

    Attributes:
        leadID (str): ID reference for the lead source.
        ItemGroupOID (str): OID of the source ItemGroupDef.
        Resource (str): Name of the source resource.
        Attribute (str): Name of the source attribute within the resource.
        Path (str): Path expression locating the source value.
        Label (str): Human-readable label for the source.
    """

    leadID = T.IDRef()
    ItemGroupOID = T.OIDRef()
    Resource = T.String()
    Attribute = T.String()
    Path = T.String()
    Label = T.String()


class SourceItems(OE.ODMElement):
    """A container holding one or more SourceItem elements.

    Attributes:
        SourceItem (list, required): One or more SourceItem children
            describing where the data originated.
    """

    SourceItem = T.ODMListObject(element_class=SourceItem, required=True)


class Origin(OE.ODMElement):
    """Describes the origin or provenance of an item's data.

    Attributes:
        Type (str, required): Category of origin, e.g. "CRF", "Derived",
            "Predecessor", "Protocol", "eDT".
        Source (str): More specific source within the Type category.
        DocumentRef (list): References to source documents.
        Description: Human-readable description of the origin.
        SourceItems: Structured source location details.
    """

    Type = T.ValueSetString(required=True)
    Source = T.ValueSetString()
    DocumentRef = T.ODMListObject(element_class=DocumentRef)
    Description = T.ODMObject(element_class=Description)
    SourceItems = T.ODMObject(element_class=SourceItems)


class WhereClauseRef(OE.ODMElement):
    WhereClauseOID = T.OIDRef(required=True)


class CheckValue(OE.ODMElement):
    """A single value used in a RangeCheck comparison.

    Attributes:
        _content (str, required): The check value as a string.
    """

    _content = T.String(required=True)


class ErrorMessage(OE.ODMElement):
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class FormalExpression(OE.ODMElement):
    """A formal expression (e.g. a computation or condition) in a specified language.

    Attributes:
        Context (str, required): The language or context of the expression,
            e.g. an XPath version string.
        _content (str, required): The expression text.
    """

    Context = T.String(required=True)
    _content = T.String(required=True)


class RangeCheck(OE.ODMElement):
    """ represents ODM v2.0 RangeCheck element that is a child of ItemDef and can serialize as JSON or XML """

    Comparator = T.ValueSetString(required=False)
    SoftHard = T.ValueSetString()
    CheckValue = T.ODMListObject(element_class=CheckValue)
    FormalExpression = T.ODMListObject(element_class=FormalExpression)
    ErrorMessage = T.ODMObject(element_class=ErrorMessage)


class WhereClauseDef(OE.ODMElement):
    OID = T.OID(required=True)
    CommentOID = T.OIDRef(required=False)
    RangeCheck = T.ODMListObject(required=True, element_class=RangeCheck)


class ItemRef(OE.ODMElement):
    """A reference to an ItemDef within an ItemGroupDef.

    Attributes:
        ItemOID (str, required): OID of the referenced ItemDef.
        OrderNumber (int): Position of this item within the item group.
        Mandatory (str, required): Whether collection is mandatory
            ("Yes" or "No").
        KeySequence (int): Position in the composite key, if this item is
            a key variable.
        MethodOID (str): OID of the MethodDef used to derive this item.
        Role (str): Semantic role of this item, e.g. "IDENTIFIER".
        RoleCodeListOID (str): OID of a CodeList that constrains Role values.
        CollectionExceptionConditionOID (str): OID of a ConditionDef that,
            when true, suppresses collection of this item.
        UnitsItemOID (str): OID of the item that carries the units for this item.
        PreSpecifiedValue (str): A pre-specified value for this item.
    """

    ItemOID = T.OIDRef(required=True)
    Mandatory = T.ValueSetString(required=True)
    Core = T.ValueSetString(required=False)
    OrderNumber = T.PositiveInteger(required=False)
    KeySequence = T.PositiveInteger(required=False)
    IsNonStandard = T.ValueSetString(required=False)
    HasNoData = T.ValueSetString(required=False)
    MethodOID = T.OIDRef(required=False)
    UnitsItemOID = T.OIDRef(required=False)
    PreSpecifiedValue = T.String(required=False)
    Repeat = T.ValueSetString(required=False)
    Other = T.ValueSetString(required=False)
    Role = T.String(required=False)
    RoleCodeListOID = T.OIDRef(required=False)
    CollectionExceptionConditionOID = T.OIDRef(required=False)
    Origin = T.ODMListObject(element_class=Origin)
    WhereClauseRef = T.ODMListObject(element_class=WhereClauseRef)


class ValueListDef(OE.ODMElement):
    OID = T.OID(required=True)
    Description = T.ODMObject(required=False, element_class=Description)
    ItemRef = T.ODMListObject(required=True, element_class=ItemRef)


class ItemGroupDef(OE.ODMElement):
    """ represents ODM v2.0 ItemGroupDef and can serialize as JSON or XML"""

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Repeating = T.ValueSetString(required=True)
    RepeatingLimit = T.PositiveInteger(required=False)
    IsReferenceData = T.ValueSetString(required=False)
    DatasetName = T.Name(required=False)
    Domain = T.String(required=False)
    Type = T.ValueSetString(required=True)
    Purpose = T.String(required=False)
    StandardOID = T.OIDRef(required=False)
    IsNonStandard = T.ValueSetString(required=False)
    HasNoData = T.ValueSetString(required=False)
    CommentOID = T.OIDRef(required=False)
    Description = T.ODMObject(element_class=Description)
    ItemGroupRef = T.ODMListObject(element_class=ItemGroupRef)
    ItemRef = T.ODMListObject(element_class=ItemRef)
    Coding = T.ODMListObject(element_class=Coding)
    WorkflowRef = T.ODMListObject(element_class=WorkflowRef)
    Origin = T.ODMListObject(element_class=Origin)
    Alias = T.ODMListObject(element_class=Alias)

    def __len__(self):
        return len(self.ItemRef)

    def __getitem__(self, position):
        return self.ItemRef[position]

    def __iter__(self):
        return iter(self.ItemRef)


class Definition(OE.ODMElement):
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class Question(OE.ODMElement):
    """The question text shown to a data entry operator for an ItemDef.

    Attributes:
        TranslatedText (list, required): One or more language-tagged text
            blocks containing the question text.
    """

    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


# TODO Deprecated
# class ExternalQuestion(OE.ODMElement):
#     """A reference to a question defined in an external dictionary or instrument.
#
#     Attributes:
#         Dictionary (str): Name of the external dictionary or instrument.
#         Version (str): Version of the dictionary or instrument.
#         Code (str): Code that identifies the question within the dictionary.
#     """
#
#     Dictionary = T.String(required=False)
#     Version = T.String(required=False)
#     Code = T.String(required=False)


class Prompt(OE.ODMElement):
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)

# TODO Deprecated
# class MeasurementUnitRef(OE.ODMElement):
#     """A reference to a MeasurementUnit defined in the BasicDefinitions section.
#
#     Attributes:
#         MeasurementUnitOID (str, required): OID of the referenced
#             MeasurementUnit.
#     """
#
#     MeasurementUnitOID = T.String(required=True)

class CRFCompletionInstructions(OE.ODMElement):
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class ImplementationNotes(OE.ODMElement):
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class CDISCNotes(OE.ODMElement):
    """A human-readable error message associated with a RangeCheck.

    Attributes:
        TranslatedText (list, required): One or more language-tagged text
            blocks containing the error message.
    """
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class CodeListRef(OE.ODMElement):
    """A reference from an ItemDef to its associated CodeList.

    Attributes:
        CodeListOID (str, required): OID of the referenced CodeList.
    """

    CodeListOID = T.OIDRef("CodeListOID", required=True)


class ItemDef(OE.ODMElement):
    """ represents ODM v2.0 ItemDef and can serialize as JSON or XML - ordering of properties matters """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    DataType = T.ValueSetString(required=True)
    Length = T.PositiveInteger()
    DisplayFormat = T.String()
    VariableSet = T.String()
    CommentOID = T.OIDRef(required=False)
    Description = T.ODMObject(element_class=Description)
    Definition = T.ODMObject(element_class=Definition)
    Question = T.ODMObject(element_class=Question)
    Prompt = T.ODMObject(element_class=Prompt)
    CRFCompletionInstructions = T.ODMObject(element_class=CRFCompletionInstructions)
    ImplementationNotes = T.ODMObject(element_class=ImplementationNotes)
    CDISCNotes = T.ODMObject(element_class=CDISCNotes)
    RangeCheck = T.ODMListObject(element_class=RangeCheck)
    CodeListRef = T.ODMObject(element_class=CodeListRef)
    Coding = T.ODMListObject(element_class=Coding)
    Alias = T.ODMListObject(element_class=Alias)


class Decode(OE.ODMElement):
    """The decoded (display) text for a CodeListItem value.

    Attributes:
        TranslatedText (list, required): One or more language-tagged text
            blocks with the decoded label for the coded value.
    """

    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class CodeListItem(OE.ODMElement):
    """ represents ODM CodeListItem element that is a child of CodeList and can serialize as JSON or XML """

    CodedValue = T.String(required=True)
    Rank = T.Float(required=False)
    Other = T.ValueSetString(required=False)
    OrderNumber = T.PositiveInteger(required=False)
    CommentOID = T.OIDRef(required=False)
    Description = T.ODMObject(element_class=Description)
    Decode = T.ODMObject(element_class=Decode)
    Coding = T.ODMListObject(element_class=Coding)
    Alias = T.ODMListObject(element_class=Alias)


# TODO Deprecated
# class ExternalCodeList(OE.ODMElement):
#     """A reference to a code list defined externally, outside the ODM document.
#
#     Attributes:
#         Dictionary (str): Name of the external dictionary or terminology.
#         Version (str): Version of the external dictionary.
#         ref (str): A reference identifier within the external dictionary.
#         href (str): A URL pointing to the external code list resource.
#     """
#
#     Dictionary = T.String(required=False)
#     Version = T.String(required=False)
#     ref = T.String(required=False)
#     href = T.String(required=False)

class CodeList(OE.ODMElement):
    """ represents ODM CodeList element that can serialize as JSON or XML """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    DataType = T.ValueSetString(required=True)
    CommentOID = T.OIDRef(required=False)
    StandardOID = T.OIDRef(required=False)
    IsNonStandard = T.ValueSetString(required=False)
    Description = T.ODMObject(element_class=Description)
    CodeListItem = T.ODMListObject(element_class=CodeListItem)
    Coding = T.ODMListObject(element_class=Coding)
    Alias = T.ODMListObject(element_class=Alias)


class ConditionDef(OE.ODMElement):
    """Defines a Boolean condition used to control collection of items or events.

    ConditionDef is referenced by CollectionExceptionConditionOID attributes
    on ItemRef, ItemGroupRef, StudyEventRef, and StudyEventGroupRef.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        Description: Optional description.
        FormalExpression (list): One or more formal expressions encoding the
            condition logic.
        Alias (list): Alternative identifiers in external contexts.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    CommentOID = T.OIDRef(required=False)
    Description = T.ODMObject(element_class=Description)
    FormalExpression = T.ODMListObject(element_class=FormalExpression)
    Alias = T.ODMListObject(element_class=Alias)


class Parameter(OE.ODMElement):
    """Declares an input parameter for a MethodDef signature.

    Attributes:
        Name (str, required): Name of the parameter.
        Definition (str): Human-readable definition of the parameter.
        DataType (str, required): Data type of the parameter value.
        OrderNumber (int): Position of this parameter in the signature.
    """

    Name = T.Name(required=True)
    Definition = T.String()
    DataType = T.ValueSetString(required=True)
    OrderNumber = T.PositiveInteger()


class ReturnValue(OE.ODMElement):
    """Declares a return value for a MethodDef signature.

    Attributes:
        Name (str, required): Name of the return value.
        Definition (str): Human-readable definition of the return value.
        DataType (str, required): Data type of the return value.
        OrderNumber (int): Position of this return value in the signature.
    """

    Name = T.Name(required=True)
    Definition = T.String()
    DataType = T.ValueSetString(required=True)
    OrderNumber = T.PositiveInteger()


class MethodSignature(OE.ODMElement):
    """Describes the formal input/output signature of a MethodDef.

    Attributes:
        Parameter (list): Zero or more input parameters.
        ReturnValue (list): Zero or more return values.
    """

    Parameter = T.ODMListObject(element_class=Parameter)
    ReturnValue = T.ODMListObject(element_class=ReturnValue)


class MethodDef(OE.ODMElement):
    """ represents ODM v2.0 MethodDef and can serialize as JSON or XML """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Type = T.ValueSetString(required=True)
    CommentOID = T.OIDRef(required=False)
    Description = T.ODMObject(required=True, element_class=Description)
    MethodSignature = T.ODMObject(element_class=MethodSignature)
    FormalExpression = T.ODMListObject(element_class=FormalExpression)
    Alias = T.ODMListObject(element_class=Alias)


class StudyEventGroupRef(OE.ODMElement):
    """A reference to a StudyEventGroupDef within an ExceptionEvent or similar element.

    Attributes:
        StudyEventGroupOID (str, required): OID of the referenced
            StudyEventGroupDef.
        OrderNumber (int): Position of this reference in the sequence.
        Mandatory (str, required): Whether this study event group is
            mandatory ("Yes" or "No").
        CollectionExceptionConditionOID (str): OID of a ConditionDef that,
            when true, suppresses collection of this event group.
        Description: Optional description.
    """

    StudyEventGroupOID = T.OIDRef(required=True)
    OrderNumber = T.Integer()
    Mandatory = T.ValueSetString(required=True)
    CollectionExceptionConditionOID = T.OIDRef()
    Description = T.ODMObject(element_class=Description)


class ExceptionEvent(OE.ODMElement):
    """Defines an exceptional study event that occurs outside the normal workflow.

    An ExceptionEvent is triggered when a specified condition is met and
    links to a workflow, study event groups, and study events that should
    be collected in that circumstance.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        ConditionOID (str, required): OID of the ConditionDef that triggers
            this exception event.
        Description: Optional description.
        WorkflowRef: Reference to the workflow governing this exception.
        StudyEventGroupRef (list): Study event groups associated with this
            exception.
        StudyEventRef (list): Individual study events associated with this
            exception.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    ConditionOID = T.OIDRef(required=True)
    Description = T.ODMObject(element_class=Description)
    WorkflowRef = T.ODMObject(element_class=WorkflowRef)
    StudyEventGroupRef = T.ODMListObject(element_class=StudyEventGroupRef)
    StudyEventRef = T.ODMListObject(element_class=StudyEventRef)


class WorkflowStart(OE.ODMElement):
    """Identifies the starting point of a WorkflowDef.

    Attributes:
        StartOID (str, required): OID reference to the first study event
            group or study event in the workflow.
    """

    StartOID = T.OIDRef(required=True)


class Transition(OE.ODMElement):
    """Defines a directed edge (transition) between two nodes in a workflow.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        SourceOID (str, required): OID reference to the source workflow node.
        TargetOID (str, required): OID reference to the target workflow node.
        StartConditionOID (str): OID of a ConditionDef that must be true to
            enter this transition.
        EndConditionOID (str): OID of a ConditionDef that must be true to
            leave this transition.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    SourceOID = T.OIDRef(required=True)
    TargetOID = T.OIDRef(required=True)
    StartConditionOID = T.OIDRef()
    EndConditionOID = T.OIDRef()


class TargetTransition(OE.ODMElement):
    """Associates a conditional transition with a branching decision point.

    Attributes:
        TargetTransitionOID (str, required): OID reference to the Transition
            that should be taken.
        ConditionOID (str, required): OID of the ConditionDef that must be
            true to take this transition.
    """

    TargetTransitionOID = T.OIDRef(required=True)
    ConditionOID = T.OIDRef(required=True)


class DefaultTransition(OE.ODMElement):
    """Specifies the fallback transition taken when no other branch condition is met.

    Attributes:
        TargetTransitionOID (str, required): OID reference to the Transition
            used when none of the conditional branches apply.
    """

    TargetTransitionOID = T.OIDRef(required=True)


class Branching(OE.ODMElement):
    """Defines a branching decision point within a workflow.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        Type (str, required): Branching type; controls whether one or
            multiple branches may be taken simultaneously.
        TargetTransition (list, required): One or more conditional
            transitions that may be taken at this branch.
        DefaultTransition (list): Zero or more default transitions taken
            when no conditional branch applies.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Type = T.ValueSetString(required=True)
    TargetTransition = T.ODMListObject(element_class=TargetTransition, required=True)
    DefaultTransition = T.ODMListObject(element_class=DefaultTransition)


class WorkflowEnd(OE.ODMElement):
    """Identifies an endpoint of a WorkflowDef.

    Attributes:
        EndOID (str, required): OID reference to the last study event group
            or study event in this workflow path.
    """

    EndOID = T.OIDRef(required=True)


class WorkflowDef(OE.ODMElement):
    """Defines a workflow (sequence of study events) in ODM 2.0.

    A workflow defines the possible paths through study events,
    including transitions, branching, and timing constraints.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        Description: Optional description.
        WorkflowStart (required): Starting point OID reference.
        Transition (list): Directed edges between workflow nodes.
        Branching (list): Decision points where the path may branch.
        WorkflowEnd (list, required): One or more workflow end points.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Description = T.ODMObject(element_class=Description)
    WorkflowStart = T.ODMObject(element_class=WorkflowStart, required=True)
    Transition = T.ODMListObject(element_class=Transition)
    Branching = T.ODMListObject(element_class=Branching)
    WorkflowEnd = T.ODMListObject(element_class=WorkflowEnd, required=True)


class AbsoluteTimingConstraint(OE.ODMElement):
    """Defines an absolute time-based constraint for a study event.

    Specifies when a study event should occur relative to an absolute
    date/time, with allowed pre- and post-windows.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        StudyEventGroupOID (str): OID of the constrained study event group.
        StudyEventOID (str): OID of the constrained study event.
        TimepointTarget (str, required): Incomplete datetime target for when
            the event should occur.
        TimepointPreWindow (str, required): ISO 8601 duration for the
            allowable window before the target.
        TimepointPostWindow (str, required): ISO 8601 duration for the
            allowable window after the target.
        Description: Optional description.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    StudyEventGroupOID = T.OIDRef()
    StudyEventOID = T.OIDRef()
    TimepointTarget = T.IncompleteDateTimeString(required=True)
    TimepointPreWindow = T.DurationDateTimeString(required=True)
    TimepointPostWindow = T.DurationDateTimeString(required=True)
    Description = T.ODMObject(element_class=Description)


class RelativeTimingConstraint(OE.ODMElement):
    """Defines a relative time-based constraint between two study events.

    Specifies when a successor event should occur relative to a predecessor
    event, with allowed pre- and post-windows.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        PredecessorStudyEventGroupOID (str): OID of the predecessor study
            event group.
        PredecessorStudyEventOID (str): OID of the predecessor study event.
        SuccessorStudyEventGroupOID (str): OID of the successor study event
            group.
        SuccessorStudyEventOID (str): OID of the successor study event.
        Type (str): The type of relative timing relationship.
        TimepointRelativeTarget (str, required): ISO 8601 duration from the
            predecessor to the target timepoint.
        TimepointPreWindow (str, required): ISO 8601 duration for the
            allowable window before the target.
        TimepointPostWindow (str, required): ISO 8601 duration for the
            allowable window after the target.
        Description: Optional description.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    PredecessorStudyEventGroupOID = T.OIDRef()
    PredecessorStudyEventOID = T.OIDRef()
    SuccessorStudyEventGroupOID = T.OIDRef()
    SuccessorStudyEventOID = T.OIDRef()
    Type = T.ValueSetString()
    TimepointRelativeTarget = T.DurationDateTimeString(required=True)
    TimepointPreWindow = T.DurationDateTimeString(required=True)
    TimepointPostWindow = T.DurationDateTimeString(required=True)
    Description = T.ODMObject(element_class=Description)


class TransitionTimingConstraint(OE.ODMElement):
    """Defines a timing constraint on a workflow transition.

    Specifies how long after a predecessor event a given workflow
    transition should occur.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        TransitionOID (str, required): OID of the Transition being constrained.
        TimepointRelativeTarget (str, required): ISO 8601 duration for the
            nominal timepoint relative to the predecessor.
        MethodOID (str): OID of a MethodDef used to compute the target time.
        TimepointPreWindow (str, required): ISO 8601 duration for the
            allowable window before the target.
        TimepointPostWindow (str, required): ISO 8601 duration for the
            allowable window after the target.
        Description: Optional description.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    TransitionOID = T.OIDRef(required=True)
    TimepointRelativeTarget = T.DurationDateTimeString(required=True)
    MethodOID = T.OIDRef()
    TimepointPreWindow = T.DurationDateTimeString(required=True)
    TimepointPostWindow = T.DurationDateTimeString(required=True)
    Description = T.ODMObject(element_class=Description)


class DurationTimingConstraint(OE.ODMElement):
    """Defines a constraint on the expected duration of a structural element.

    Specifies the nominal duration for an arm, epoch, or similar structural
    element, with allowed pre- and post-windows.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        StructuralElementOID (str, required): OID of the structural element
            (e.g. an Arm or Epoch) whose duration is constrained.
        DurationTarget (str, required): ISO 8601 duration for the expected
            length of the structural element.
        DurationPreWindow (str, required): ISO 8601 duration for the
            allowable window before the target duration.
        DurationPostWindow (str, required): ISO 8601 duration for the
            allowable window after the target duration.
        Description: Optional description.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    StructuralElementOID = T.OIDRef(required=True)
    DurationTarget = T.DurationDateTimeString(required=True)
    DurationPreWindow = T.DurationDateTimeString(required=True)
    DurationPostWindow = T.DurationDateTimeString(required=True)
    Description = T.ODMObject(element_class=Description)


class StudyTiming(OE.ODMElement):
    """A named container grouping all timing constraints for a study.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        AbsoluteTimingConstraint (list): Absolute time-based constraints.
        RelativeTimingConstraint (list): Relative time-based constraints
            between events.
        TransitionTimingConstraint: A timing constraint on a workflow
            transition.
        DurationTimingConstraint (list): Duration constraints on structural
            elements.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    AbsoluteTimingConstraint = T.ODMListObject(element_class=AbsoluteTimingConstraint)
    RelativeTimingConstraint = T.ODMListObject(element_class=RelativeTimingConstraint)
    TransitionTimingConstraint = T.ODMObject(element_class=TransitionTimingConstraint)
    DurationTimingConstraint = T.ODMListObject(element_class=DurationTimingConstraint)


class StudyEventGroupDef(OE.ODMElement):
    """Defines a group of study events associated with a specific arm and epoch.

    StudyEventGroupDef maps a set of study events to their position in the
    trial by linking them to a particular Arm and Epoch.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        ArmOID (str, required): OID of the Arm this event group belongs to.
        EpochOID (str, required): OID of the Epoch this event group belongs to.
        Description: Optional description.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    ArmOID = T.OIDRef(required=True)
    EpochOID = T.OIDRef(required=True)
    Description = T.ODMObject(element_class=Description)


class MetaDataVersion(OE.ODMElement):
    """A versioned snapshot of all metadata for a study in ODM 2.0.

    MetaDataVersion holds the complete metadata definition including
    the protocol, study structure, workflows, timing, event/item group/item
    definitions, code lists, conditions, and methods.

    Attributes:
        OID (str, required): Unique identifier for this metadata version.
        Name (str, required): Human-readable name.
        Description: Optional description.
        Include: Reference to metadata imported from another study.
        Protocol: The protocol defining the ordered set of study events.
        StudyStructure: Arms and epochs that make up the study design.
        WorkflowDef (list): Workflow definitions.
        StudyTiming: Container for all timing constraints.
        StudyEventGroupDef (list): Study event group definitions.
        StudyEventDef (list): Study event definitions.
        ItemGroupDef (list): Item group (dataset) definitions.
        ItemDef (list): Item (variable) definitions.
        CodeList (list): Controlled terminology code lists.
        ConditionDef (list): Condition definitions used for collection
            exception logic.
        MethodDef (list): Method (derivation/computation) definitions.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    CommentOID = T.OIDRef(required=False)
    Description = T.ODMObject(element_class=Description)
    Include = T.ODMObject(element_class=Include)
    Standards = T.ODMListObject(element_class=Standards)
    Protocol = T.ODMObject(element_class=Protocol)
    WorkflowDef = T.ODMListObject(element_class=WorkflowDef)
    StudyTiming = T.ODMObject(element_class=StudyTiming)
    StudyEventGroupDef = T.ODMListObject(element_class=StudyEventGroupDef)
    StudyEventDef = T.ODMListObject(element_class=StudyEventDef)
    ItemGroupDef = T.ODMListObject(element_class=ItemGroupDef)
    ItemDef = T.ODMListObject(element_class=ItemDef)
    CodeList = T.ODMListObject(element_class=CodeList)
    ConditionDef = T.ODMListObject(element_class=ConditionDef)
    MethodDef = T.ODMListObject(element_class=MethodDef)


class UserName(OE.ODMElement):
    """The login name (username) used by a User to authenticate.

    Attributes:
        _content (str, required): The login name string.
    """

    _content = T.String(required=True)


class DisplayName(OE.ODMElement):
    """The display name shown in user interfaces for a User.

    Attributes:
        _content (str, required): The display name string.
    """

    _content = T.String(required=True)


class FullName(OE.ODMElement):
    """The full legal name of a User.

    Attributes:
        _content (str, required): The full name string.
    """

    _content = T.String(required=True)


class GivenName(OE.ODMElement):
    """The first (given) name of a User.

    Attributes:
        _content (str, required): The first name string.
    """

    _content = T.String(required=True)


class FamilyName(OE.ODMElement):
    """The last (family) name of a User.

    Attributes:
        _content (str, required): The last name string.
    """

    _content = T.String(required=True)


class Organization(OE.ODMElement):
    """The organization or institution that a User belongs to.

    Attributes:
        _content (str, required): The organization name string.
    """

    _content = T.String(required=True)


class StreetName(OE.ODMElement):
    """A line of a street address for a User's Address.

    Attributes:
        _content (str, required): One street address line.
    """

    _content = T.String(required=True)


class City(OE.ODMElement):
    """The city component of a User's Address.

    Attributes:
        _content (str, required): The city name.
    """

    _content = T.String(required=True)


class StateProv(OE.ODMElement):
    """The state or province component of a User's Address.

    Attributes:
        _content (str, required): The state or province name or code.
    """

    _content = T.String(required=True)


class Country(OE.ODMElement):
    """The country component of a User's Address.

    Attributes:
        _content (str, required): ISO 3166-1 alpha-2 country code.
    """

    _content = T.ValueSetString(required=True)


class PostalCode(OE.ODMElement):
    """The postal or ZIP code component of a User's Address.

    Attributes:
        _content (str, required): The postal code string.
    """

    _content = T.String(required=True)


class OtherText(OE.ODMElement):
    """Additional free-form address text not captured by other Address children.

    Attributes:
        _content (str, required): Free-form address text.
    """

    _content = T.String(required=True)


class Address(OE.ODMElement):
    """A postal address for a User.

    Attributes:
        StreetName (list): One or more street address lines.
        City: City name.
        StateProv: State or province.
        Country: Country code.
        PostalCode: Postal or ZIP code.
        OtherText: Any additional address information.
    """

    StreetName = T.ODMListObject(element_class=StreetName)
    City = T.ODMObject(element_class=City)
    StateProv = T.ODMObject(element_class=StateProv)
    Country = T.ODMObject(element_class=Country)
    PostalCode = T.ODMObject(element_class=PostalCode)
    OtherText = T.ODMObject(element_class=OtherText)


class Email(OE.ODMElement):
    """An email address for a User.

    Attributes:
        _content (str, required): The email address string; must be a valid
            RFC 5321 email address.
    """

    _content = T.Email(required=True)


class Picture(OE.ODMElement):
    """A picture or photo associated with a User.

    Attributes:
        PictureFileName (str, required): Filename of the picture file.
        ImageType (str): MIME type or format descriptor of the image.
    """

    PictureFileName = T.FileName(required=True)
    ImageType = T.Name()


class Pager(OE.ODMElement):
    """A pager number for a User.

    Attributes:
        _content (str, required): The pager number string.
    """

    _content = T.String(required=True)


class Fax(OE.ODMElement):
    """A fax number for a User.

    Attributes:
        _content (str, required): The fax number string.
    """

    _content = T.String(required=True)


class Phone(OE.ODMElement):
    """A telephone number for a User.

    Attributes:
        _content (str, required): The phone number string.
    """

    _content = T.String(required=True)


class LocationRef(OE.ODMElement):
    """A reference to a Location where a User is associated.

    Attributes:
        LocationOID (str, required): OID of the referenced Location.
    """

    LocationOID = T.OIDRef(required=True)


# TODO deprecated
# class Certificate(OE.ODMElement):
#     """A digital certificate associated with a User for signature purposes.
#
#     Attributes:
#         _content (str, required): The certificate data (typically base64-encoded).
#     """
#
#     _content = T.String(required=True)


class Image(OE.ODMElement):
    """An image associated with a User."""
    ImageFileName = T.FileName(required=False)
    href = T.String(required=False)
    MimeType = T.String(required=False)

# TODO ensure the type information for TelecomType is there
class Telecom(OE.ODMElement):
    """Telecommunications contact information for a User."""
    TelecomType = T.ValueSetString(required=True)
    value = T.String(required=True)


class User(OE.ODMElement):
    """A user (person) who can be referenced in an ODM administrative context.

    User records appear in the AdminData section and are referenced by
    AuditRecord and Signature elements within clinical data.

    Attributes:
        OID (str, required): Unique identifier.
        UserType (str): Role category of the user, e.g. "Sponsor",
            "Investigator", "Lab", "Other".
        UserName: The user's login name.
        DisplayName: Name shown in user interfaces.
        FullName: Full legal name.
        GivenName: Given (first) name.
        FamilyName: Family (last) name.
        Organization: Affiliated organization.
        Address (list): One or more postal addresses.
        Email (list): One or more email addresses.
        Pager: Pager number.
        Fax (list): One or more fax numbers.
        Phone (list): One or more phone numbers.
        LocationRef (list): Locations associated with the user.
        Certificate (list): Digital certificates for the user.
    """

    OID = T.OID(required=True)
    UserType = T.ValueSetString()
    OrganizationOID = T.OIDRef()
    LocationOID = T.OIDRef()
    UserName = T.ODMObject(element_class=UserName)
    Prefix = T.String()
    Suffix = T.String()
    DisplayName = T.ODMObject(element_class=DisplayName)
    FullName = T.ODMObject(element_class=FullName)
    GivenName = T.ODMObject(element_class=GivenName)
    FamilyName = T.ODMObject(element_class=FamilyName)
    Image = T.ODMObject(element_class=Image)
    Address = T.ODMListObject(element_class=Address)
    Telecom = T.ODMListObject(element_class=Telecom)


class MetaDataVersionRef(OE.ODMElement):
    """Associates a Location with a specific MetaDataVersion and its effective date.

    Attributes:
        StudyOID (str, required): OID reference to the Study whose metadata
            is referenced.
        MetaDataVersionOID (str, required): OID reference to the
            MetaDataVersion.
        EffectiveDate (str, required): ISO 8601 date from which this metadata
            version became effective at the location.
    """

    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)
    EffectiveDate = T.DateString(required=True)


class Location(OE.ODMElement):
    """Defines a physical or logical location (e.g. a site) in the administrative data.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name of the location.
        LocationType (str): Category of location, e.g. "Sponsor", "Site",
            "CRO", "Lab".
        MetaDataVersionRef (list, required): One or more references to the
            metadata versions effective at this location.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Role = T.String(required=False)
    MetaDataVersionRef = T.ODMListObject(required=True, element_class=MetaDataVersionRef)


class Meaning(OE.ODMElement):
    """A human-readable description of the meaning of an electronic signature.

    Attributes:
        _content (str, required): Text describing what the signature signifies,
            e.g. "Approval" or "Author".
    """

    _content = T.String(required=True)


class LegalReason(OE.ODMElement):
    """The legal basis or reason for an electronic signature.

    Attributes:
        _content (str, required): Text describing the legal reason for the
            signature, e.g. "I approve this document".
    """

    _content = T.String(required=True)


class SignatureDef(OE.ODMElement):
    """Defines the type and meaning of an electronic signature in an ODM document.

    Attributes:
        OID (str, required): Unique identifier.
        Methodology (str): The methodology used (e.g. "Electronic" or
            "Digital").
        Meaning (required): Human-readable meaning of the signature.
        LegalReason (required): Legal reason text presented to the signer.
    """

    OID = T.OID(required=True)
    Methodology = T.ValueSetString()
    Meaning = T.ODMObject(required=True, element_class=Meaning)
    LegalReason = T.ODMObject(required=True, element_class=LegalReason)


class AdminData(OE.ODMElement):
    """Administrative data for a study, including users, locations, and signatures.

    Attributes:
        StudyOID (str): OID reference to the Study this admin data belongs to.
        User (list): User (person) records.
        Location (list): Location (site) records.
        SignatureDef (list): Signature definition records.
    """

    StudyOID = T.OIDRef()
    User = T.ODMListObject(element_class=User)
    Location = T.ODMListObject(element_class=Location)
    SignatureDef = T.ODMListObject(element_class=SignatureDef)


class Study(OE.ODMElement):
    """The root study element in an ODM 2.0 document.

    In ODM 2.0, StudyName and ProtocolName are scalar string attributes on
    Study itself rather than child elements, making the structure flatter
    than ODM 1.3.2.

    Attributes:
        OID (str, required): Unique identifier for the study.
        StudyName (str, required): Short name of the study.
        ProtocolName (str, required): Name of the protocol governing the study.
        Description: Optional human-readable description.
        MetaDataVersion (list): One or more versioned metadata snapshots.
    """

    OID = T.OID(required=True)
    StudyName = T.Name(required=True)
    ProtocolName = T.Name(required=True)
    VersionID = T.Name(required=False)
    VersionName = T.Name(required=False)
    Status = T.Name(required=False)
    Description = T.ODMObject(required=False, element_class=Description)
    MetaDataVersion = T.ODMListObject(required=False, element_class=MetaDataVersion)


class ODM(OE.ODMElement):
    """The root element of an ODM 2.0 document.

    The ODM element carries file-level metadata (file type, creation time,
    originating system) and contains the Study elements that hold all
    study data and metadata. Uses namespace
    ``http://www.cdisc.org/ns/odm/v2.0``.

    Attributes:
        Description (str): A human-readable description of the file.
        FileType (str, required): "Snapshot" for a complete file or
            "Transactional" for an incremental update.
        Granularity (str): Level of data included, e.g. "All", "Metadata",
            "AdminData", "ReferenceData", "AllClinicalData".
        Archival (str): Whether this file is intended for archival ("Yes"
            or "No").
        FileOID (str, required): A globally unique OID for this specific file.
        CreationDateTime (str, required): ISO 8601 datetime when the file
            was created.
        PriorFileOID (str): OID of the preceding file in a sequence.
        AsOfDateTime (str): ISO 8601 datetime indicating the currency of
            the data.
        ODMVersion (str): Version of the ODM standard, e.g. "2.0".
        Originator (str): Name of the organization that created the file.
        SourceSystem (str): Name of the software system that generated the
            file.
        SourceSystemVersion (str): Version of the source system.
        Description (Description): Human-readable description of the file.
        Study (list): One or more Study elements.
        AdminData: Administrative data for the study.
    """
    FileType = T.ValueSetString(required=True)
    Granularity = T.ValueSetString(required=False)
    Archival = T.ValueSetString(required=False)
    Context = T.ValueSetString(required=False)
    FileOID = T.OID(required=True)
    CreationDateTime = T.DateTimeString(required=True)
    PriorFileOID = T.OIDRef(required=False)
    AsOfDateTime = T.DateTimeString(required=False)
    ODMVersion = T.ValueSetString(required=False)
    Originator = T.String(required=False)
    SourceSystem = T.String(required=False)
    SourceSystemVersion = T.String(required=False)
    Description = T.ODMObject(required=False, element_class=Description)
    Study = T.ODMListObject(required=False, element_class=Study)
    AdminData = T.ODMListObject(required=False, element_class=AdminData)
    # ReferenceData = T.ODMListObject(element_class=ReferenceData)
    # ClinicalData = T.ODMListObject(element_class=ClinicalData)
    # Association = T.ODMListObject(element_class=Association)
