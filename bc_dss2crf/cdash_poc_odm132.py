import logging
import sys
from pathlib import Path

import click

# Add top-level folder to path so that project folder can be found
SCRIPT_DIR = Path.cwd()
sys.path.append(str(SCRIPT_DIR))
import datetime

import pandas as pd
# import pandasgui

import odmlib.odm_1_3_2.model as ODM
from config.config import AppSettings as CFG
from odmlib import loader as LO
from odmlib import odm_loader as OL
from utilities.utils import (create_crf_html, create_directory,
                             transform_xml_saxonche, validate_odm_xml_file,
                             write_html_doc)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

__config = CFG()

CRF_PATH = Path(__config.crf_path)

COLLECTION_DSS_METADATA_EXCEL = Path(__config.collection_dss_metadata_excel)
COLLECTION_DSS_METADATA_EXCEL_SHEET = __config.collection_dss_metadata_excel_sheet
FORMS_METADATA_EXCEL = Path(__config.forms_metadata_excel)
FORMS_METADATA_EXCEL_SHEET = __config.forms_metadata_excel_sheet

ODM_XML_SCHEMA_FILE = Path(__config.odm132_schema)
XSL_FILE = Path(__config.odm132_stylesheet)

MANDATORY_MAP = {
    "Y": "Yes",
    "N": "No"
}

REPEATING_MAP = {
    "Y": "Yes",
    "N": "No"
}

DATATYPE_MAP = {
    "decimal": "float"}


def create_oid(type, row):
    if type.upper() == "ODM":
        return "ODM.CDASH.POC"
    elif type.upper() == "STUDY":
        return "ODM.CDASH.STUDY"
    elif type.upper() == "MDV":
        return "ODM.CDASH.STUDY.MDV"
    elif type.upper() == "FORM":
        return f"IG.{row['form_id']}"
    elif type.upper() == "SECTION":
        return f"IG.{row['form_section_id']}_{row['form_section_order_number']}"
    elif type.upper() == "CONCEPT":
        return (
            f"IG.{row['form_section_id']}_{row['form_section_order_number']}_"
            f"{row['collection_group_id']}_{row['bc_order_number']}"
        )
    elif type.upper() == "ITEM":
        return (
            f"IT.{row['form_section_id']}_{row['form_section_order_number']}_"
            f"{row['collection_group_id']}_{row['bc_order_number']}."
            f"{row['collection_item']}"
        )
    elif type.upper() == "CODELIST":
        return (
            f"CL.{row['form_section_id']}_{row['collection_group_id']}_{row['bc_order_number']}."
            f"{row['collection_item']}.{row['codelist']}"
        )
    elif type.upper() == "CODELIST_VL":
        return (
            f"CL.{row['form_section_id']}_{row['collection_group_id']}_{row['bc_order_number']}."
            f"{row['collection_item']}"
        )
    else:
        raise ValueError("Invalid type specified")


def create_description(text, lang="en", type="text/plain"):
    description = ODM.Description()
    translatedText = ODM.TranslatedText(_content=text, lang=lang)
    description.TranslatedText.append(translatedText)
    return description


def create_alias(context, name):
    alias = ODM.Alias(Context=context, Name=name)
    return alias


def create_item_group_ref(row, type):
    item_group_ref = ODM.ItemGroupRef(
        ItemGroupOID=create_oid(type.upper(), row),
        OrderNumber=row["form_section_order_number"],
        Mandatory="Yes")
    return item_group_ref


def create_item_group_def(row, type, itemrefs=[]):
    item_group_def = ODM.ItemGroupDef(OID=create_oid(type.upper(), row),
                                      Name=row["form_section_label"],
                                      Repeating=REPEATING_MAP[row["form_section_repeating"]],
                                      ItemRef=itemrefs)
    return item_group_def


def create_item_ref(row, counter=0):
    item_ref = ODM.ItemRef(ItemOID=create_oid("ITEM", row),
                           OrderNumber=counter,
                           Mandatory=MANDATORY_MAP[row["mandatory_variable"]])
    return item_ref


def create_item_def(row):
    item_def = ODM.ItemDef(
        OID=create_oid("ITEM", row),
        Name=row["collection_item"],
        DataType=row["data_type"]
    )
    if row["data_type"] in DATATYPE_MAP:
        item_def.DataType = DATATYPE_MAP[row["data_type"]]
    if row["length"] != "":
        item_def.Length = int(row["length"])

    item_def.Description = create_description(row["variable_name"])

    if row["question_text"] != "":
        item_def.Question = create_question((row["question_text"]))
    if row["codelist"] != "":
        item_def.CodeListRef = ODM.CodeListRef(CodeListOID=create_oid("CODELIST", row))
    elif row["value_display_list"] != "":
        item_def.CodeListRef = ODM.CodeListRef(CodeListOID=create_oid("CODELIST_VL", row))

    alias_list = []
    if row["prompt"] != "":
        prompt_alias = create_alias("prompt", row["prompt"])
        alias_list.append(prompt_alias)

    if row["sdtm_annotation"] != "":
        sdtm_alias = create_alias("SDTM", row["sdtm_annotation"])
        alias_list.append(sdtm_alias)
    item_def.Alias = alias_list
    return item_def


def create_question(text, lang="en", type="text/plain"):
    question = ODM.Question()
    translatedText = ODM.TranslatedText(_content=text, lang=lang)
    question.TranslatedText.append(translatedText)
    return question


def create_decode(text, lang="en", type="text/plain"):
    decode = ODM.Decode()
    translatedText = ODM.TranslatedText(_content=text, lang=lang)
    decode.TranslatedText.append(translatedText)
    return decode


def create_codelist(row):
    codelist = ODM.CodeList(OID=create_oid("CODELIST", row),
                            Name=row["codelist_submission_value"],
                            DataType=row["data_type"])
    if row["data_type"] in DATATYPE_MAP:
        codelist.DataType = DATATYPE_MAP[row["data_type"]]
    codelist_items = []
    enumerated_items = []
    if row["value_list"] != "":
        codelist_item_value_list = row["value_list"].split(";")
        codelist_item_value_display_list = row["value_display_list"].split(";")
        for item in codelist_item_value_list:
            codelist_item = ODM.CodeListItem(CodedValue=item)

            decode = create_decode(
                codelist_item_value_display_list[codelist_item_value_list.index(item)],
                lang="en",
                type="text/plain"
            )
            codelist_item.Decode = decode

            codelist_items.append(codelist_item)
            codelist.CodeListItem = codelist_items
    else:
        if row["prepopulated_term"] != "":
            enumerated_item = ODM.EnumeratedItem(CodedValue=row["prepopulated_term"])
            enumerated_items.append(enumerated_item)
        codelist.EnumeratedItem = enumerated_items
    return codelist


def create_codelist_from_valuelist(row):
    if row["vlm_group_id"] != "":
        codelist = ODM.CodeList(OID=create_oid("CODELIST_VL", row),
                                Name=row["vlm_group_id"] + "-" + row["variable_name"],
                                DataType=row["data_type"])
    else:
        codelist = ODM.CodeList(OID=create_oid("CODELIST_VL", row),
                                Name=row["collection_group_id"] + "-" + row["variable_name"],
                                DataType=row["data_type"])
    if row["data_type"] in DATATYPE_MAP:
        codelist.DataType = DATATYPE_MAP[row["data_type"]]
    codelist_items = []
    enumerated_items = []
    if row["value_list"] != "":
        codelist_item_value_list = row["value_list"].split(";")
        codelist_item_value_display_list = row["value_display_list"].split(";")
        for item in codelist_item_value_list:
            codelist_item = ODM.CodeListItem(CodedValue=item)

            decode = create_decode(
                codelist_item_value_display_list[codelist_item_value_list.index(item)],
                lang="en",
                type="text/plain"
            )
            codelist_item.Decode = decode

            codelist_items.append(codelist_item)
            codelist.CodeListItem = codelist_items
    else:
        if row["prepopulated_term"] != "":
            enumerated_item = ODM.EnumeratedItem(CodedValue=row["prepopulated_term"])
            enumerated_items.append(enumerated_item)
        codelist.EnumeratedItem = enumerated_items
    return codelist


def create_df_from_excel(forms_metadata, collection_metadata, collection_form):
    """
    Reads form and collection metadata from Excel files, processes and merges them into DataFrames.
    Args:
        forms_metadata (str): Path to the Excel file containing form metadata.
        collection_metadata (str): Path to the Excel file containing collection metadata.
        collection_form (str): Name of the sheet in the forms metadata Excel file to read.
    Returns:
        tuple:
            - pd.DataFrame: Merged DataFrame containing collection specializations and form metadata.
            - pd.DataFrame: DataFrame containing unique forms with selected columns.
            - str: Name of the form corresponding to the collection form.
    Side Effects:
        Prints the intermediate DataFrames for debugging purposes.
    """
    # Read forms from Excel
    df_forms_bcs = pd.read_excel(
        open(forms_metadata, 'rb'),
        sheet_name=FORMS_METADATA_EXCEL_SHEET,
        keep_default_na=False
    )
    df_forms_bcs = df_forms_bcs[df_forms_bcs['form_id'] == collection_form].reset_index(drop=True)
    if len(df_forms_bcs) == 0:
        logger.error(
            f"No data found in the forms metadata ({FORMS_METADATA_EXCEL}) "
            f"for the specified collection form ({collection_form})."
        )
        sys.exit()

    form_name = df_forms_bcs.loc[0, 'form_label']
    form_annotation = df_forms_bcs.loc[0, 'form_annotation']

    df_forms = df_forms_bcs.drop_duplicates(
        subset=[
            'form_section_id',
            'form_section_order_number',
            'form_section_label'
        ]
    )
    df_forms = df_forms[
        df_forms.columns[
            df_forms.columns.isin([
                'form_id',
                'form_section_id',
                'form_section_order_number',
                'form_section_repeating',
                'form_section_label',
                'form_section_annotation',
                'form_section_completion_instruction'
            ])
        ]
    ]
    df_forms.sort_values(['form_section_order_number'], ascending=[True], inplace=True)

    # Read Collection Specializations from Excel
    df = pd.read_excel(
        open(collection_metadata, 'rb'),
        sheet_name=COLLECTION_DSS_METADATA_EXCEL_SHEET,
        keep_default_na=False
    )

    # Merge Collection Specializations with forms
    df = df.merge(
        df_forms_bcs,
        how='inner',
        left_on='collection_group_id',
        right_on='collection_group_id',
        suffixes=('', '_y'),
        validate='m:m'
    )
    df.sort_values(
        ['form_section_order_number', 'bc_order_number', 'order_number'],
        ascending=[True, True, True],
        inplace=True
    )

    # pandasgui.show(df)

    return df, df_forms, form_name, form_annotation


def create_odm(df, df_forms, collection_form, form_name, form_annotation):
    """
    Creates an ODM (Operational Data Model) object representing study metadata, forms, item groups,
    items, and codelists.
    Args:
        df (pandas.DataFrame): DataFrame containing item-level metadata, including form, group, item,
            and codelist information.
        df_forms (pandas.DataFrame): DataFrame containing form-level metadata.
        collection_form (str): Identifier for the collection form to be used in the ODM FormDef OID.
        form_name (str): Name of the form to be used in the ODM FormDef Name and Description.
        form_annotation (str): Annotation on the form to be used in the ODM metadata.
    Returns:
        odm (odmlib.ODM): An ODM object populated with study metadata, forms, item groups, items, and codelists.
    Notes:
        - Relies on several helper functions (e.g., create_item_group_ref, create_description,
          create_oid, create_item_ref, create_item_group_def, create_item_def, create_codelist).
        - Assumes the presence of an ODM Python library (e.g., odmlib) for ODM object construction.
        - The function builds the ODM structure according to CDISC 1.3.2 standards.
    """

    item_group_refs = []
    for i, row in df_forms.iterrows():
        item_group_ref = create_item_group_ref(row, "SECTION")           # Add the FormDef to the list of forms
        item_group_refs.append(item_group_ref)

    form = ODM.FormDef(
        OID=f"FORM.{collection_form}",
        Name=f"{form_name}",
        Repeating="No",
        Description=create_description(f"{form_name}"),
        ItemGroupRef=item_group_refs
    )

    if form_annotation != "":
        alias_list = []
        form_alias = create_alias("formAnnotation", form_annotation)
        alias_list.append(form_alias)
        form.Alias = alias_list

    forms = {}
    for i, row in df_forms.iterrows():
        # Define a FormDef
        form_def = ODM.ItemGroupDef(
            OID=create_oid("SECTION", row),
            Name=row["form_section_label"],
            Repeating=REPEATING_MAP[row["form_section_repeating"]],
            Description=create_description(row["form_section_label"])
        )

        # Add the FormDef to the list of forms
        forms[row["form_section_id"]] = form_def

    item_group_refs = []
    item_group_defs = []
    item_refs = []
    item_defs = []
    codelists = []
    # collection_group_id = ""
    form_section_id = ""
    item_group_def = None
    counter = 0
    for i, row in df.iterrows():

        if row["form_section_id"] != form_section_id:  # New Collection Group
            counter = 1
            logger.info(
                row["form_section_id"]
                + " - " + row["form_section_label"]
                + " - " + row["collection_group_id"]
                + " - " + str(row["bc_id"])
            )

            if form_section_id and item_group_def is not None:
                item_group_defs.append(item_group_def)

            # collection_group_id = row["collection_group_id"]
            form_section_id = row["form_section_id"]
            item_refs = []

            if row["display_hidden"] != "Y":
                item_ref = create_item_ref(row, counter=counter)
                item_refs.append(item_ref)

            item_group_def = create_item_group_def(row, "Section", itemrefs=item_refs)

            alias_list = []
            if row["form_section_annotation"] != "":
                form_alias = create_alias("formSectionAnnotation", row["form_section_annotation"])
                alias_list.append(form_alias)
            if row["form_section_completion_instruction"] != "":
                form_alias = create_alias(
                    "formSectionCompletionInstruction",
                    row["form_section_completion_instruction"]
                )
                alias_list.append(form_alias)
            item_group_def.Alias = alias_list

        else:
            counter += 1
            if row["display_hidden"] != "Y":
                item_ref = create_item_ref(row, counter=counter)
                item_refs.append(item_ref)

        if row["display_hidden"] != "Y":
            item_def = create_item_def(row)
            item_defs.append(item_def)

        if row["codelist"] != "":
            codelist = create_codelist(row)
            codelists.append(codelist)
        elif row["value_display_list"] != "":
            codelist = create_codelist_from_valuelist(row)
            codelists.append(codelist)

    item_group_defs.append(item_group_def)

    # Create a new ODM object
    current_datetime = datetime.datetime.now(datetime.UTC).isoformat()
    odm = ODM.ODM(
        FileOID=create_oid("ODM", []),
        Granularity="Metadata",
        CreationDateTime=current_datetime,
        ODMVersion="1.3.2",
        FileType="Snapshot",
        Originator="Lex Jansen",
        SourceSystem="odmlib",
        SourceSystemVersion="0.1"
    )

    mdv = []
    mdv.append(ODM.MetaDataVersion(
        OID=create_oid("MDV", []),
        Name="CDISC360i CDASH POC Study Metadata Version",
        Description="CDISC360i CDASH ODM 1.3.2 metadata version"
    ))

    mdv[0].ItemGroupDef.append(form)

    for item_group_def in item_group_defs:
        mdv[0].ItemGroupDef.append(item_group_def)
    for item_def in item_defs:
        mdv[0].ItemDef.append(item_def)
    for codelist in codelists:
        mdv[0].CodeList.append(codelist)

    globalVariables = ODM.GlobalVariables(
        StudyName=ODM.StudyName(_content="CDISC360i CDASH POC Study"),
        StudyDescription=ODM.StudyDescription(_content="CDISC360i CDASH POC Study"),
        ProtocolName=ODM.ProtocolName(_content="CDISC360i CDASH POC Study protocol")
    )

    study = ODM.Study(
        OID=create_oid("STUDY", []),
        GlobalVariables=globalVariables,
        MetaDataVersion=mdv
    )

    odm.Study.append(study)

    return odm


@click.command(help="Generate ODM v1.3.2 eCRFs and their HTML renditions")
@click.option(
    "--form",
    "-f",
    "collection_form",
    required=True,
    default=None,
    prompt=True,
    help="The ID of the collection form to process."
)
@click.option(
    "--prefix",
    "-p",
    "file_name_prefix",
    help="The lowercase prefix to use for the output filenames."
)
def main(collection_form: str, file_name_prefix: str):
    """
    Main function to generate and process ODM files for a given collection form and form name.
    This function performs the following steps:
    1. Constructs file paths for XML, JSON, and HTML outputs based on the collection form.
    2. Loads metadata from Excel files and creates dataframes for forms and form metadata.
    3. Generates an ODM object from the metadata and writes it to XML and JSON files.
    4. Validates the generated ODM XML file against a schema.
    5. Transforms the XML file into an HTML file using XSLT.
    6. Creates a CRF HTML document from the ODM XML and writes it to file.
    7. Loads the ODM XML file using an ODM loader for further processing.
    Args:
        collection_form (str): The identifier for the collection form to process.
        form_name (str): The name of the form to generate.
    Returns:
        None
    """

    if file_name_prefix is None:
        file_name_prefix = collection_form.lower().replace(" ", "_")
    else:
        file_name_prefix = file_name_prefix.lower().replace(" ", "_")

    ODM_XML_FILE = Path(CRF_PATH).joinpath(f"{collection_form}", f"{file_name_prefix}_odmv1-3-2.xml")
    ODM_JSON_FILE = Path(CRF_PATH).joinpath(f"{collection_form}", f"{file_name_prefix}_odmv1-3-2.json")
    ODM_HTML_FILE_DOM = Path(CRF_PATH).joinpath(f"{collection_form}", f"{file_name_prefix}_odmv1-3-2_crf_dom.html")
    ODM_HTML_FILE_XSL = Path(CRF_PATH).joinpath(f"{collection_form}", f"{file_name_prefix}_odmv1-3-2_crf.html")
    ODM_HTML_FILE_XSL_ANNOTATED = Path(CRF_PATH).joinpath(
        f"{collection_form}", f"{file_name_prefix}_odmv1-3-2_acrf.html"
    )

    df, df_forms, form_name, form_annotation = create_df_from_excel(
        FORMS_METADATA_EXCEL,
        COLLECTION_DSS_METADATA_EXCEL,
        collection_form
    )

    odm = create_odm(df, df_forms, collection_form, form_name, form_annotation)

    create_directory(Path(CRF_PATH).joinpath(f"{collection_form}"))

    odm.write_xml(odm_file=ODM_XML_FILE)
    odm.write_json(odm_file=ODM_JSON_FILE)

    validate_odm_xml_file(ODM_XML_FILE, ODM_XML_SCHEMA_FILE, verbose=True)
    transform_xml_saxonche(ODM_XML_FILE, XSL_FILE, ODM_HTML_FILE_XSL, displayAnnotations=0)
    transform_xml_saxonche(ODM_XML_FILE, XSL_FILE, ODM_HTML_FILE_XSL_ANNOTATED)

    doc = create_crf_html(ODM_XML_FILE, verbose=True)
    # write_html_doc(doc, ODM_HTML_FILE_DOM, verbose=True)

    loader = LO.ODMLoader(OL.XMLODMLoader())
    loader.open_odm_document(ODM_XML_FILE)
    odm = loader.load_odm()


if __name__ == "__main__":

    main()
    # main("SIXMW1")
    # main("ECG1")
    # main("QS_EQ5D02")
