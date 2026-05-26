from __future__ import annotations
from typing import Any, List, Optional
from odmlib.odm_element import ODMElement


class TranslatedText(ODMElement):
    lang: Optional[str]
    Type: Optional[str]
    _content: Optional[str]


class Description(ODMElement):
    TranslatedText: List[TranslatedText]


class Alias(ODMElement):
    Context: Optional[str]
    Name: Optional[str]


class Include(ODMElement):
    StudyOID: Optional[str]
    MetaDataVersionOID: Optional[str]


class StudyEventRef(ODMElement):
    StudyEventOID: Optional[str]
    OrderNumber: Optional[int]
    Mandatory: Optional[str]
    CollectionExceptionConditionOID: Optional[str]


class Protocol(ODMElement):
    Description: Optional[Description]
    StudyEventRef: List[StudyEventRef]
    Alias: List[Alias]


class ItemGroupRef(ODMElement):
    ItemGroupOID: Optional[str]
    OrderNumber: Optional[int]
    Mandatory: Optional[str]
    CollectionExceptionConditionOID: Optional[str]


class WorkflowRef(ODMElement):
    WorkflowOID: Optional[str]


class StudyEventDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Repeating: Optional[str]
    Type: Optional[str]
    Category: Optional[str]
    Description: Optional[Description]
    ItemGroupRef: List[ItemGroupRef]
    WorkflowRef: List[WorkflowRef]
    Alias: List[Alias]
    def __len__(self) -> int: ...
    def __getitem__(self, position: int) -> ItemGroupRef: ...
    def __iter__(self): ...


class ArchiveLayout(ODMElement):
    OID: Optional[str]
    PdfFileName: Optional[str]
    PresentationOID: Optional[str]


class PDFPageRef(ODMElement):
    Type: Optional[str]
    PageRefs: Optional[str]
    FirstPage: Optional[int]
    LastPage: Optional[int]


class DocumentRef(ODMElement):
    leafID: Optional[str]
    PDFPageRef: List[PDFPageRef]


class SourceItem(ODMElement):
    leadID: Optional[str]
    ItemGroupOID: Optional[str]
    Resource: Optional[str]
    Attribute: Optional[str]
    Path: Optional[str]
    Label: Optional[str]


class SourceItems(ODMElement):
    SourceItem: List[SourceItem]


class Origin(ODMElement):
    Type: Optional[str]
    Source: Optional[str]
    DocumentRef: List[DocumentRef]
    Description: Optional[Description]
    SourceItems: Optional[SourceItems]


class ItemRef(ODMElement):
    ItemOID: Optional[str]
    OrderNumber: Optional[int]
    Mandatory: Optional[str]
    KeySequence: Optional[int]
    MethodOID: Optional[str]
    Role: Optional[str]
    RoleCodeListOID: Optional[str]
    CollectionExceptionConditionOID: Optional[str]
    UnitsItemOID: Optional[str]
    PreSpecifiedValue: Optional[str]


class ItemGroupDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Repeating: Optional[str]
    Type: Optional[str]
    IsReferenceData: Optional[str]
    DatasetName: Optional[str]
    Domain: Optional[str]
    Purpose: Optional[str]
    CommentOID: Optional[str]
    Description: Optional[Description]
    ItemGroupRef: List[ItemGroupRef]
    ItemRef: List[ItemRef]
    WorkflowRef: List[WorkflowRef]
    Origin: List[Origin]
    Alias: List[Alias]
    def __len__(self) -> int: ...
    def __getitem__(self, position: int) -> ItemRef: ...
    def __iter__(self): ...


class Question(ODMElement):
    TranslatedText: List[TranslatedText]


class ExternalQuestion(ODMElement):
    Dictionary: Optional[str]
    Version: Optional[str]
    Code: Optional[str]


class MeasurementUnitRef(ODMElement):
    MeasurementUnitOID: Optional[str]


class CheckValue(ODMElement):
    _content: Optional[str]


class FormalExpression(ODMElement):
    Context: Optional[str]
    _content: Optional[str]


class ErrorMessage(ODMElement):
    TranslatedText: List[TranslatedText]


class RangeCheck(ODMElement):
    Comparator: Optional[str]
    SoftHard: Optional[str]
    CheckValue: List[CheckValue]
    FormalExpression: List[FormalExpression]
    ErrorMessage: Optional[ErrorMessage]


class CodeListRef(ODMElement):
    CodeListOID: Optional[str]


class ItemDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    DataType: Optional[str]
    Length: Optional[int]
    DisplayFormat: Optional[str]
    VariableSet: Optional[str]
    CommentOID: Optional[str]
    Description: Optional[Description]
    # The element classes below are defined in model.py but have no stub
    # in this partial .pyi (13 of 97 classes are unstubbed); typed as Any
    # to keep this block correct without expanding stub scope.
    Definition: Optional[Any]
    Question: Optional[Question]
    Prompt: Optional[Any]
    CRFCompletionInstructions: Optional[Any]
    ImplementationNotes: Optional[Any]
    CDISCNotes: Optional[Any]
    RangeCheck: List[RangeCheck]
    CodeListRef: Optional[CodeListRef]
    Coding: List[Any]
    Alias: List[Alias]


class Decode(ODMElement):
    TranslatedText: List[TranslatedText]


class CodeListItem(ODMElement):
    CodedValue: Optional[str]
    Rank: Optional[float]
    OrderNumber: Optional[int]
    Decode: Optional[Decode]
    Alias: List[Alias]


class EnumeratedItem(ODMElement):
    CodedValue: Optional[str]
    Rank: Optional[float]
    OrderNumber: Optional[int]
    Alias: List[Alias]


class ExternalCodeList(ODMElement):
    Dictionary: Optional[str]
    Version: Optional[str]
    ref: Optional[str]
    href: Optional[str]


class CodeList(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    DataType: Optional[str]
    SASFormatName: Optional[str]
    Description: Optional[Description]
    CodeListItem: List[CodeListItem]
    EnumeratedItem: List[EnumeratedItem]
    ExternalCodeList: Optional[ExternalCodeList]
    Alias: List[Alias]


class ConditionDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Description: Optional[Description]
    FormalExpression: List[FormalExpression]
    Alias: List[Alias]


class Parameter(ODMElement):
    Name: Optional[str]
    Definition: Optional[str]
    DataType: Optional[str]
    OrderNumber: Optional[int]


class ReturnValue(ODMElement):
    Name: Optional[str]
    Definition: Optional[str]
    DataType: Optional[str]
    OrderNumber: Optional[int]


class MethodSignature(ODMElement):
    Parameter: List[Parameter]
    ReturnValue: List[ReturnValue]


class MethodDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Type: Optional[str]
    Description: Optional[Description]
    MethodSignature: Optional[MethodSignature]
    FormalExpression: List[FormalExpression]
    Alias: List[Alias]


class StudyEventGroupRef(ODMElement):
    StudyEventGroupOID: Optional[str]
    OrderNumber: Optional[int]
    Mandatory: Optional[str]
    CollectionExceptionConditionOID: Optional[str]
    Description: Optional[Description]


class ExceptionEvent(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    ConditionOID: Optional[str]
    Description: Optional[Description]
    WorkflowRef: Optional[WorkflowRef]
    StudyEventGroupRef: List[StudyEventGroupRef]
    StudyEventRef: List[StudyEventRef]


class Arm(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Description: Optional[Description]
    WorkflowRef: Optional[WorkflowRef]


class Epoch(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    SequenceNumber: Optional[int]
    Description: Optional[Description]


class StudyStructure(ODMElement):
    Description: Optional[Description]
    Arm: List[Arm]
    Epoch: List[Epoch]
    WorkflowRef: List[WorkflowRef]


class WorkflowStart(ODMElement):
    StartOID: Optional[str]


class Transition(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    SourceOID: Optional[str]
    TargetOID: Optional[str]
    StartConditionOID: Optional[str]
    EndConditionOID: Optional[str]


class TargetTransition(ODMElement):
    TargetTransitionOID: Optional[str]
    ConditionOID: Optional[str]


class DefaultTransition(ODMElement):
    TargetTransitionOID: Optional[str]


class Branching(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Type: Optional[str]
    TargetTransition: List[TargetTransition]
    DefaultTransition: List[DefaultTransition]


class WorkflowEnd(ODMElement):
    EndOID: Optional[str]


class WorkflowDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Description: Optional[Description]
    WorkflowStart: Optional[WorkflowStart]
    Transition: List[Transition]
    Branching: List[Branching]
    WorkflowEnd: List[WorkflowEnd]


class AbsoluteTimingConstraint(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    StudyEventGroupOID: Optional[str]
    StudyEventOID: Optional[str]
    TimepointTarget: Optional[str]
    TimepointPreWindow: Optional[str]
    TimepointPostWindow: Optional[str]
    Description: Optional[Description]


class RelativeTimingConstraint(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    PredecessorStudyEventGroupOID: Optional[str]
    PredecessorStudyEventOID: Optional[str]
    SuccessorStudyEventGroupOID: Optional[str]
    SuccessorStudyEventOID: Optional[str]
    Type: Optional[str]
    TimepointRelativeTarget: Optional[str]
    TimepointPreWindow: Optional[str]
    TimepointPostWindow: Optional[str]
    Description: Optional[Description]


class TransitionTimingConstraint(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    TransitionOID: Optional[str]
    TimepointRelativeTarget: Optional[str]
    MethodOID: Optional[str]
    TimepointPreWindow: Optional[str]
    TimepointPostWindow: Optional[str]
    Description: Optional[Description]


class DurationTimingConstraint(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    StructuralElementOID: Optional[str]
    DurationTarget: Optional[str]
    DurationPreWindow: Optional[str]
    DurationPostWindow: Optional[str]
    Description: Optional[Description]


class StudyTiming(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    AbsoluteTimingConstraint: List[AbsoluteTimingConstraint]
    RelativeTimingConstraint: List[RelativeTimingConstraint]
    TransitionTimingConstraint: Optional[TransitionTimingConstraint]
    DurationTimingConstraint: List[DurationTimingConstraint]


class StudyEventGroupDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    ArmOID: Optional[str]
    EpochOID: Optional[str]
    Description: Optional[Description]


class MetaDataVersion(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Description: Optional[Description]
    Include: Optional[Include]
    Protocol: Optional[Protocol]
    StudyStructure: Optional[StudyStructure]
    WorkflowDef: List[WorkflowDef]
    StudyTiming: Optional[StudyTiming]
    StudyEventGroupDef: List[StudyEventGroupDef]
    StudyEventDef: List[StudyEventDef]
    ItemGroupDef: List[ItemGroupDef]
    ItemDef: List[ItemDef]
    CodeList: List[CodeList]
    ConditionDef: List[ConditionDef]
    MethodDef: List[MethodDef]


class LoginName(ODMElement):
    _content: Optional[str]


class DisplayName(ODMElement):
    _content: Optional[str]


class FullName(ODMElement):
    _content: Optional[str]


class FirstName(ODMElement):
    _content: Optional[str]


class LastName(ODMElement):
    _content: Optional[str]


class Organization(ODMElement):
    _content: Optional[str]


class StreetName(ODMElement):
    _content: Optional[str]


class City(ODMElement):
    _content: Optional[str]


class StateProv(ODMElement):
    _content: Optional[str]


class Country(ODMElement):
    _content: Optional[str]


class PostalCode(ODMElement):
    _content: Optional[str]


class OtherText(ODMElement):
    _content: Optional[str]


class Address(ODMElement):
    StreetName: List[StreetName]
    City: Optional[City]
    StateProv: Optional[StateProv]
    Country: Optional[Country]
    PostalCode: Optional[PostalCode]
    OtherText: Optional[OtherText]


class Email(ODMElement):
    _content: Optional[str]


class Picture(ODMElement):
    PictureFileName: Optional[str]
    ImageType: Optional[str]


class Pager(ODMElement):
    _content: Optional[str]


class Fax(ODMElement):
    _content: Optional[str]


class Phone(ODMElement):
    _content: Optional[str]


class LocationRef(ODMElement):
    LocationOID: Optional[str]


class Certificate(ODMElement):
    _content: Optional[str]


class User(ODMElement):
    OID: Optional[str]
    UserType: Optional[str]
    LoginName: Optional[LoginName]
    DisplayName: Optional[DisplayName]
    FullName: Optional[FullName]
    FirstName: Optional[FirstName]
    LastName: Optional[LastName]
    Organization: Optional[Organization]
    Address: List[Address]
    Email: List[Email]
    Pager: Optional[Pager]
    Fax: List[Fax]
    Phone: List[Phone]
    LocationRef: List[LocationRef]
    Certificate: List[Certificate]


class MetaDataVersionRef(ODMElement):
    StudyOID: Optional[str]
    MetaDataVersionOID: Optional[str]
    EffectiveDate: Optional[str]


class Location(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    LocationType: Optional[str]
    MetaDataVersionRef: List[MetaDataVersionRef]


class Meaning(ODMElement):
    _content: Optional[str]


class LegalReason(ODMElement):
    _content: Optional[str]


class SignatureDef(ODMElement):
    OID: Optional[str]
    Methodology: Optional[str]
    Meaning: Optional[Meaning]
    LegalReason: Optional[LegalReason]


class AdminData(ODMElement):
    StudyOID: Optional[str]
    User: List[User]
    Location: List[Location]
    SignatureDef: List[SignatureDef]


class Study(ODMElement):
    OID: Optional[str]
    StudyName: Optional[str]
    ProtocolName: Optional[str]
    Description: Optional[Description]
    MetaDataVersion: List[MetaDataVersion]


class ODM(ODMElement):
    Description: Optional[str]
    FileType: Optional[str]
    Granularity: Optional[str]
    Archival: Optional[str]
    FileOID: Optional[str]
    CreationDateTime: Optional[str]
    PriorFileOID: Optional[str]
    AsOfDateTime: Optional[str]
    ODMVersion: Optional[str]
    Originator: Optional[str]
    SourceSystem: Optional[str]
    SourceSystemVersion: Optional[str]
    Study: List[Study]
