import sys
from pathlib import Path

# Add top-level folder to path so that odmlib and utilities folder can be found
SCRIPT_DIR = Path.cwd()
sys.path.append(str(SCRIPT_DIR))

import datetime
import logging

import click
import pandas as pd

import odmlib.odm_2_0.model as ODM
from config.config import AppSettings as CFG
from odmlib import loader as LO
from odmlib import odm_loader as OL
from utilities.utils import (create_directory, transform_xml_saxonche,
                             validate_odm_xml_file, update_zip_file)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

__config = CFG()

CRF_PATH = Path(__config.crf_path)

CRF_SPECIALIZATIONS_METADATA_EXCEL = Path(__config.crf_specializations_metadata_excel)
CRF_SPECIALIZATIONS_METADATA_EXCEL_SHEET = __config.crf_specializations_metadata_excel_sheet
FORMS_METADATA_EXCEL = Path(__config.forms_metadata_excel)
FORMS_METADATA_EXCEL_SHEET = __config.forms_metadata_excel_sheet

MANDATORY_MAP = {
    "Y": "Yes",
    "N": "No"
}

REPEATING_MAP = {
    "Y": "Simple",
    "N": "No"
}


def create_oid(type, row):
    type = type.upper()
    oid_map = {
        "ODM": lambda r: "ODM.CDASH.POC",
        "STUDY": lambda r: "ODM.CDASH.STUDY",
        "MDV": lambda r: "ODM.CDASH.STUDY.MDV",
        "FORM": lambda r: f"IG.{r['form_id']}",
        "SECTION": lambda r: f"IG.{r['form_section_id']}_{r['form_section_order_number']}",
        "CONCEPT": lambda r: (
            f"IG.{r['form_section_id']}_{r['form_section_order_number']}_"
            f"{r['crf_group_id']}_{r['bc_order_number']}"
        ),
        "ITEM": lambda r: (
            f"IT.{r['form_section_id']}_{r['form_section_order_number']}_"
            f"{r['crf_group_id']}_{r['bc_order_number']}."
            f"{r['crf_item']}"
        ),
        "CODELIST": lambda r: (
            f"CL.{r['form_section_id']}_{r['crf_group_id']}_{r['bc_order_number']}."
            f"{r['crf_item']}.{r['codelist']}"
        ),
        "CODELIST_VL": lambda r: (
            f"CL.{r['form_section_id']}_{r['crf_group_id']}_{r['bc_order_number']}."
            f"{r['crf_item']}"
        ),
    }
    try:
        return oid_map[type](row)
    except KeyError:
        raise ValueError("Invalid type specified")


def create_description(text, lang="en", type="text/plain"):
    description = ODM.Description()
    translatedText = ODM.TranslatedText(_content=text, Type=type, lang=lang)
    description.TranslatedText.append(translatedText)
    return description


def add_coding(codings, system="", **kwargs):
    coding = {}
    coding["System"] = system
    for k, v in kwargs.items():
        if k == "code":
            coding["Code"] = v
        elif k == "systemName":
            coding["SystemName"] = v
        else:
            raise ValueError(f"Invalid argumnent specified: {k} = {v}")

    codings.append(ODM.Coding(**coding))
    return codings


def create_alias(context, name):
    alias = ODM.Alias(Context=context, Name=name)
    return alias


def create_item_group_ref(row, type):
    item_group_ref = ODM.ItemGroupRef(
        ItemGroupOID=create_oid(type.upper(), row),
        OrderNumber=row["bc_order_number"],
        Mandatory="Yes")
    return item_group_ref


def create_item_group_def(row, type, itemrefs=[]):

    item_group_def = None
    if type.upper() == "SECTION":
        item_group_def = ODM.ItemGroupDef(
            OID=create_oid(type.upper(), row),
            Name=row["form_section_label"],
            Repeating=REPEATING_MAP[row["form_section_repeating"]],
            Type=type,
            Description=create_description(row["short_name"]),
            ItemRef=itemrefs
        )
    if type.upper() == "CONCEPT":
        item_group_def = ODM.ItemGroupDef(
            OID=create_oid(type.upper(), row),
            Name=row["short_name"],
            Repeating=REPEATING_MAP[row["bc_repeating"]],
            Type=type,
            Description=create_description(row["short_name"]),
            ItemRef=itemrefs
        )
    codings = []
    if row["bc_id"] != "":
        codings = add_coding(codings, system=f"/mdr/bc/biomedicalconcepts/{row['bc_id']}",
                             code=row["bc_id"],
                             systemName="CDISC Biomedical Concept")
    if row["vlm_group_id"] != "":
        codings = add_coding(
            codings,
            system=f"/mdr/specializations/sdtm/datasetspecializations/{row['vlm_group_id']}",
            code=row["vlm_group_id"],
            systemName="CDISC SDTM Dataset Specialization"
        )
    if item_group_def is not None:
        item_group_def.Coding = codings
    return item_group_def


def create_item_ref(row):
    item_ref = ODM.ItemRef(ItemOID=create_oid("ITEM", row),
                           OrderNumber=row["order_number"],
                           Mandatory=MANDATORY_MAP[row["mandatory_variable"]])
    if row["prepopulated_term"] != "":
        item_ref.PreSpecifiedValue = row["prepopulated_term"]
    # Check if there actually is an ORRESU variable to reference
    if row["variable_name"][-5:] == "ORRES" and row["variable_name_units"] != '':
        if row["variable_name_units"][-6:] == "ORRESU":
            item_ref.UnitsItemOID = create_oid("ITEM", row).replace("ORRES", "ORRESU")
    return item_ref


def create_item_def(row):
    item_def = ODM.ItemDef(
        OID=create_oid("ITEM", row),
        Name=row["crf_item"],
        DataType=row["data_type"]
    )
    if row["data_type"] != "":
        item_def.DataType = row["data_type"]
    if row["length"] != "":
        item_def.Length = int(row["length"])
    if row["question_text"] != "":
        item_def.Question = create_question((row["question_text"]))
    if row["prompt"] != "":
        item_def.Prompt = create_prompt((row["prompt"]))
    if row["codelist"] != "":
        item_def.CodeListRef = ODM.CodeListRef(CodeListOID=create_oid("CODELIST", row))
    elif row["value_display_list"] != "":
        item_def.CodeListRef = ODM.CodeListRef(CodeListOID=create_oid("CODELIST_VL", row))

    alias_list = []
    if row["sdtm_annotation"] != "":
        sdtm_alias = create_alias("SDTM", row["sdtm_annotation"])
        alias_list.append(sdtm_alias)

    if row["crf_item"] != "":
        sdtm_alias = create_alias("CDASH", row["crf_item"])
        alias_list.append(sdtm_alias)

    item_def.Alias = alias_list
    return item_def


def create_question(text, lang="en", type="text/plain"):
    question = ODM.Question()
    translatedText = ODM.TranslatedText(_content=text, Type=type, lang=lang)
    question.TranslatedText.append(translatedText)
    return question


def create_prompt(text, lang="en", type="text/plain"):
    prompt = ODM.Prompt()
    translatedText = ODM.TranslatedText(_content=text, Type=type, lang=lang)
    prompt.TranslatedText.append(translatedText)
    return prompt


def create_decode(text, lang="en", type="text/plain"):
    decode = ODM.Decode()
    translatedText = ODM.TranslatedText(_content=text, Type=type, lang=lang)
    decode.TranslatedText.append(translatedText)
    return decode


def create_codelist(row):
    codelist = ODM.CodeList(OID=create_oid("CODELIST", row),
                            Name=row["codelist_submission_value"],
                            DataType=row["data_type"])
    codelist_items = []
    if row["value_list"] != "":
        codelist_item_value_list = row["value_list"].split(";")
        codelist_item_value_display_list = row["value_display_list"].split(";")
        for item in codelist_item_value_list:
            codelist_item = ODM.CodeListItem(CodedValue=item)
            display_index = codelist_item_value_list.index(item)
            display_value = codelist_item_value_display_list[display_index]
            decode = create_decode(display_value, lang="en", type="text/plain")
            codelist_item.Decode = decode
            codelist_items.append(codelist_item)
            codelist.CodeListItem = codelist_items
    else:
        codelist_item = None
        if row["prepopulated_term"] != "":
            codelist_item = ODM.CodeListItem(CodedValue=row["prepopulated_term"])
        else:
            # Provide a fallback if prepopulated_term is empty
            codelist_item = ODM.CodeListItem(CodedValue="")

        codelist_item_codings = []
        if row["prepopulated_code"] != "":
            codelist_item_codings = add_coding(
                codelist_item_codings,
                system="https://www.cdisc.org/standards/terminology",
                code=row["prepopulated_code"],
                systemName="CDISC/NCI CT"
            )
            codelist_item.Coding = codelist_item_codings
        codelist_items.append(codelist_item)
        codelist.CodeListItem = codelist_items
    if row["codelist"] != "":
        codelist_codings = []
        codelist_codings = add_coding(
            codelist_codings,
            system="https://www.cdisc.org/standards/terminology",
            code=row["codelist"],
            systemName="CDISC/NCI CT"
        )
        codelist.Coding = codelist_codings
    return codelist


def create_codelist_from_valuelist(row):
    if row["vlm_group_id"] != "":
        codelist = ODM.CodeList(OID=create_oid("CODELIST_VL", row),
                                Name=row["vlm_group_id"] + "-" + row["variable_name"],
                                DataType=row["data_type"])
    else:
        codelist = ODM.CodeList(OID=create_oid("CODELIST_VL", row),
                                Name=row["crf_group_id"] + "-" + row["variable_name"],
                                DataType=row["data_type"])
    codelist_items = []
    if row["value_list"] != "":
        codelist_item_value_list = row["value_list"].split(";")
        codelist_item_value_display_list = row["value_display_list"].split(";")
        for item in codelist_item_value_list:
            codelist_item = ODM.CodeListItem(CodedValue=item)

            display_index = codelist_item_value_list.index(item)
            display_value = codelist_item_value_display_list[display_index]
            decode = create_decode(display_value, lang="en", type="text/plain")
            codelist_item.Decode = decode

            codelist_items.append(codelist_item)
            codelist.CodeListItem = codelist_items
    else:
        codelist_item = None
        if row["prepopulated_term"] != "":
            codelist_item = ODM.CodeListItem(CodedValue=row["prepopulated_term"])
        else:
            # Provide a fallback if prepopulated_term is empty
            codelist_item = ODM.CodeListItem(CodedValue="")

        codelist_item_codings = []
        if row["prepopulated_code"] != "":
            codelist_item_codings = add_coding(
                codelist_item_codings,
                system="https://www.cdisc.org/standards/terminology",
                code=row["prepopulated_code"],
                systemName="CDISC/NCI CT"
            )
            codelist_item.Coding = codelist_item_codings
        codelist_items.append(codelist_item)
        codelist.CodeListItem = codelist_items
    if row["codelist"] != "":
        codelist_codings = []
        codelist_codings = add_coding(codelist_codings, system="https://www.cdisc.org/standards/terminology",
                                      code=row["codelist"],
                                      systemName="CDISC/NCI CT")
        codelist.Coding = codelist_codings
    return codelist


def create_df_from_excel(forms_metadata, crf_metadata, crf_form):
    """
    Reads form and CRF metadata from Excel files, processes and merges the data,
    and returns the resulting DataFrames.
    Args:
        forms_metadata (str): Path to the Excel file containing forms metadata.
        crf_metadata (str): Path to the Excel file containing CRF metadata.
        crf_form (str): Name of the sheet in the forms metadata Excel file to read.
    Returns:
        tuple:
            - pd.DataFrame: Merged DataFrame of CRF specializations and forms.
            - pd.DataFrame: DataFrame of unique forms with selected columns.
            - str: Name of the form corresponding to the CRF.
    Side Effects:
        Prints the processed forms DataFrame and the first 100 rows of the merged DataFrame for inspection.
    """
    # Read forms from Excel
    df_forms_bcs = pd.read_excel(
        open(forms_metadata, 'rb'),
        sheet_name=FORMS_METADATA_EXCEL_SHEET,
        keep_default_na=False
    )
    df_forms_bcs = df_forms_bcs[df_forms_bcs['form_id'] == crf_form].reset_index(drop=True)
    if len(df_forms_bcs) == 0:
        logger.error(
            f"No data found in the forms metadata ({FORMS_METADATA_EXCEL}) "
            f"for the specified CRF ({crf_form})."
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
    df_forms = df_forms[df_forms.columns[df_forms.columns.isin(
        ['form_id', 'form_section_id', 'form_section_order_number',
         'form_section_label', 'form_section_repeating', 'form_section_annotation',
         'form_section_completion_instruction']
    )]]
    df_forms.sort_values(['form_section_order_number'], ascending=[True], inplace=True)

    # Read Collection Specializations from Excel
    df = pd.read_excel(
        open(crf_metadata, 'rb'),
        sheet_name=CRF_SPECIALIZATIONS_METADATA_EXCEL_SHEET,
        keep_default_na=False
    )

    df = df.merge(
        df_forms_bcs,
        how='inner',
        left_on='crf_group_id',
        right_on='crf_group_id',
        suffixes=('', '_y'),
        validate='m:m'
    )

    df_units = df[df['variable_name'].str.endswith('ORRESU')]
    df_units = df_units[[
        'crf_group_id', 'variable_name', 'prepopulated_term',
        'value_list', 'value_display_list'
    ]]

    df = df.merge(
        df_units,
        how='left',
        left_on='crf_group_id',
        right_on='crf_group_id',
        suffixes=('', '_units'),
        validate='m:1'
    )
    df.variable_name_units = df.variable_name_units.fillna('')

    if len(df) == 0:
        logger.error(f"No data found in the CRF metadata for the specified CRF ({crf_form}).")
        sys.exit()

    df.sort_values(
        ['form_section_order_number', 'bc_order_number', 'order_number'],
        ascending=[True, True, True],
        inplace=True
    )

    return df, df_forms, form_name, form_annotation


def create_odm(df, df_forms, crf_form, form_name, form_annotation):
    """
    Creates an ODM (Operational Data Model) object from the provided dataframes and form information.
    This function constructs an ODM-compliant metadata structure using the input dataframes for forms and items,
    and additional parameters specifying the CRF and form name. It builds the necessary ODM elements
    such as ItemGroupDefs, ItemDefs, CodeLists, and assembles them into a complete ODM object representing the
    study metadata.
    Args:
        df (pd.DataFrame): DataFrame containing item-level metadata, including CRF groups, items, and codelists.
        df_forms (pd.DataFrame): DataFrame containing form-level metadata, including form labels and order numbers.
        crf_form (str): Identifier for the CRF to be used as the main form.
        form_name (str): Name of the form to be used in the ODM metadata.
        form_annotation (str): Annotation on the form to be used in the ODM metadata.
    Returns:
        odm (ODM.ODM): An ODM object populated with the study metadata, including forms, item groups,
            items, and codelists.
    Notes:
        - Assumes the existence of helper functions such as `create_oid`, `create_description`, `create_item_ref`,
          `create_item_group_def`, `create_item_group_ref`, `create_item_def`, and `create_codelist`.
        - Relies on the ODM Python library (e.g., odmlib) for ODM element classes.
        - The function prints CRF group transitions for debugging purposes.
    """
    item_group_refs = []
    for i, row in df_forms.iterrows():
        item_group_ref = ODM.ItemGroupRef(
            ItemGroupOID=create_oid("SECTION", row),
            OrderNumber=row["form_section_order_number"],
            Mandatory="Yes")           # Add the FormDef to the list of forms
        item_group_refs.append(item_group_ref)

    form = ODM.ItemGroupDef(
        OID=f"IG_FORM.{crf_form}",
        Name=f"{form_name}",
        Repeating="No",
        Type="Form",
        Description=create_description(f"{form_name}"),
        ItemGroupRef=item_group_refs)

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
            Type="Section",
            Description=create_description(row["form_section_label"])
        )

        # Add the FormDef to the list of forms
        forms[row["form_section_id"]] = form_def

    item_group_refs = []
    item_group_defs = []
    item_refs = []
    item_defs = []
    codelists = []
    crf_group_id = ""
    item_group_def = None
    for i, row in df.iterrows():

        if row["crf_group_id"] != crf_group_id:  # New Collection Group
            logger.info(
                f"{row['form_section_id']} - {row['form_section_label']} - "
                f"{row['crf_group_id']} - {row['bc_id']}"
            )

            if crf_group_id:
                item_group_defs.append(item_group_def)

            crf_group_id = row["crf_group_id"]
            item_refs = []

            if row["display_hidden"] != "Y":
                item_ref = create_item_ref(row)
                item_refs.append(item_ref)

            item_group_ref = create_item_group_ref(row, "Concept")
            forms[row["form_section_id"]].ItemGroupRef.append(item_group_ref)

            item_group_def = create_item_group_def(row, "Concept", itemrefs=item_refs)

        else:
            if row["display_hidden"] != "Y":
                item_ref = create_item_ref(row)
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

    for i, row in df_forms.iterrows():
        alias_list = []
        if row["form_section_annotation"] != "":
            form_alias = create_alias("formSectionAnnotation", row["form_section_annotation"])
            alias_list.append(form_alias)
        if row["form_section_completion_instruction"] != "":
            form_alias = create_alias("formSectionCompletionInstruction", row["form_section_completion_instruction"])
            alias_list.append(form_alias)
        forms[row["form_section_id"]].Alias = alias_list

    item_group_defs.append(item_group_def)

    # Create a new ODM object
    current_datetime = datetime.datetime.now(datetime.UTC).isoformat()
    odm = ODM.ODM(
        FileOID=create_oid("ODM", []),
        Granularity="Metadata",
        CreationDateTime=current_datetime,
        ODMVersion="2.0",
        FileType="Snapshot",
        Originator="Lex Jansen",
        SourceSystem="odmlib",
        SourceSystemVersion="0.1"
    )

    mdv = []
    mdv.append(ODM.MetaDataVersion(
        OID=create_oid("MDV", []),
        Name=f"{form_name}",
        Description=create_description(f"{form_name}")
    ))

    mdv[0].ItemGroupDef.append(form)

    # Add the ItemGroupDef to the MetaDataVersion
    for value in forms.values():
        # Add the Form to the ItemGroupDef
        mdv[0].ItemGroupDef.append(value)

    for item_group_def in item_group_defs:
        mdv[0].ItemGroupDef.append(item_group_def)
    for item_def in item_defs:
        mdv[0].ItemDef.append(item_def)
    for codelist in codelists:
        mdv[0].CodeList.append(codelist)

    study = ODM.Study(
        OID=create_oid("STUDY", []),
        StudyName=f"{form_name}",
        Description=create_description(f"{form_name}"),
        ProtocolName=f"{form_name}",
        MetaDataVersion=mdv
    )

    odm.Study.append(study)

    return odm


@click.command(help="Generate ODM v2.0 eCRFs and their HTML renditions")
@click.option(
    "--form",
    "-f",
    "crf_form",
    required=True,
    default=None,
    prompt=True,
    help="The ID of the CRF to process."
)
@click.option(
    "--prefix",
    "-p",
    "file_name_prefix",
    required=False,
    help=(
        "The lowercase prefix to use for the output filenames. "
        "When not specified, the lowercase CRF ID will be used."
    )
)
def main(crf_form: str, file_name_prefix: str):
    """
    Main function to generate, validate, and transform an ODM 2.0 XML file from Excel metadata.
    Args:
        crf_form (str): The name or identifier of the CRF to process.
    Workflow:
        1. Loads configuration for schema, stylesheet, and output file paths.
        2. Reads metadata from Excel files and creates DataFrames.
        3. Generates an ODM object from the metadata.
        4. Writes the ODM object to XML and JSON files.
        5. Validates the generated XML file against the ODM 2.0 schema.
        6. Transforms the XML file to HTML using the provided XSL stylesheet.
        7. Loads and parses the ODM XML file using the specified loader.
    Raises:
        Any exceptions raised by the underlying functions (e.g., file I/O, validation, transformation).
    """

    if file_name_prefix is None:
        file_name_prefix = crf_form.lower().replace(" ", "_")
    else:
        file_name_prefix = file_name_prefix.lower().replace(" ", "_")

    ODM_XML_SCHEMA_FILE = Path(__config.odm20_schema)
    XSL_FILE = Path(__config.odm20_stylesheet)
    ODM_XML_FILE = Path(CRF_PATH).joinpath(f"{crf_form}", f"{file_name_prefix}_odmv2-0.xml")
    ODM_JSON_FILE = Path(CRF_PATH).joinpath(f"{crf_form}", f"{file_name_prefix}_odmv2-0.json")
    ODM_HTML_FILE_XSL = Path(CRF_PATH).joinpath(f"{crf_form}", f"{file_name_prefix}_odmv2-0_crf.html")
    ODM_HTML_FILE_XSL_ANNOTATED = Path(CRF_PATH).joinpath(
        f"{crf_form}", f"{file_name_prefix}_odmv2-0_acrf.html"
    )

    df, df_forms, form_name, form_annotation = create_df_from_excel(
        FORMS_METADATA_EXCEL,
        CRF_SPECIALIZATIONS_METADATA_EXCEL,
        crf_form
    )

    odm = create_odm(df, df_forms, crf_form, form_name, form_annotation)

    create_directory(Path(CRF_PATH).joinpath(f"{crf_form}"))

    odm.write_xml(odm_file=ODM_XML_FILE)
    odm.write_json(odm_file=ODM_JSON_FILE)

    validate_odm_xml_file(ODM_XML_FILE, ODM_XML_SCHEMA_FILE, verbose=True)

    transform_xml_saxonche(ODM_XML_FILE, XSL_FILE, ODM_HTML_FILE_XSL, displayAnnotations=0)
    transform_xml_saxonche(ODM_XML_FILE, XSL_FILE, ODM_HTML_FILE_XSL_ANNOTATED)

    loader = LO.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0", ns_uri="http://www.cdisc.org/ns/odm/v2.0"))
    loader.open_odm_document(ODM_XML_FILE)
    odm = loader.load_odm()

    ZIP_FILE = Path(CRF_PATH).joinpath(f"{crf_form}", f"{file_name_prefix}_odm.zip")
    update_zip_file(ZIP_FILE, ODM_XML_FILE.name, ODM_XML_FILE)
    update_zip_file(ZIP_FILE, ODM_JSON_FILE.name, ODM_JSON_FILE)
    update_zip_file(ZIP_FILE, ODM_HTML_FILE_XSL.name, ODM_HTML_FILE_XSL)
    update_zip_file(ZIP_FILE, ODM_HTML_FILE_XSL_ANNOTATED.name, ODM_HTML_FILE_XSL_ANNOTATED)


if __name__ == "__main__":

    main()
    # main("SIXMW1")
    # main("ECG1")
    # main("QS_EQ5D02")
