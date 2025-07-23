import os
import sys
import click
from pathlib import Path

# Add top-level folder to path so that project folder can be found
SCRIPT_DIR = Path.cwd()
sys.path.append(str(SCRIPT_DIR))
import odmlib.odm_2_0.model as ODM
from odmlib import odm_loader as OL, loader as LO

import datetime
import pandas as pd
from utilities.utils import (
    validate_odm_xml_file,
    transform_xml_saxonche
)
from config.config import AppSettings as CFG

__config = CFG()

CRF_PATH = Path(__config.crf_path)

COLLECTION_DSS_METADATA_EXCEL = Path(__config.collection_dss_metadata_excel)
COLLECTION_DSS_METADATA_EXCEL_SHEET = __config.collection_dss_metadata_excel_sheet
FORMS_METADATA_EXCEL = Path(__config.forms_metadata_excel)
FORMS_METADATA_EXCEL_SHEET = __config.forms_metadata_excel_sheet

MANDATORY_MAP = {
    "Y": "Yes",
    "N": "No"}

def create_oid(type, row):
    if type.upper() == "ODM":
        return "ODM.CDASH.POC"
    elif type.upper() == "STUDY":
        return "ODM.CDASH.STUDY"
    elif type.upper() == "MDV":
        return "ODM.CDASH.STUDY.MDV"
    elif type.upper() == "FORM":
        return f"{row['form_section_id']}"
    elif type.upper() == "SECTION":
        return f"IG.CDASH.POC.{row['collection_group_id']}"
    elif type.upper() == "CONCEPT":
        return f"IG.CDASH.POC.{row['collection_group_id']}"
    elif type.upper() == "ITEM":
        return f"IT.{row['collection_group_id']}.{row['collection_item']}"
    elif type.upper() == "CODELIST":
        return f"CL.{row['collection_group_id']}.{row['variable_name']}.{row['codelist']}"
    elif type.upper() == "CODELIST_VL":
        return f"CL.{row['collection_group_id']}.{row['variable_name']}"
    else:
        raise ValueError("Invalid type specified")

def create_description(text, lang="en", type="text/plain"):
    description = ODM.Description()
    translatedText = ODM.TranslatedText(_content=text, Type=type, lang=lang)
    description.TranslatedText.append(translatedText)
    return description

def add_coding(codings, system="", **kwargs):
    coding  = {}
    coding["System"] = system
    for k,v in kwargs.items():
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
        item_group_def = ODM.ItemGroupDef(OID=create_oid(type.upper(), row),
                                        Name=row["form_section_label"],
                                        Repeating="No",
                                        Type=type,
                                        Description=create_description(row["short_name"]),
                                        ItemRef=itemrefs)
    if type.upper() == "CONCEPT":
        item_group_def = ODM.ItemGroupDef(OID=create_oid(type.upper(), row),
                                        Name=row["short_name"],
                                        Repeating="No",
                                        Type=type,
                                        Description=create_description(row["short_name"]),
                                        ItemRef=itemrefs)
    codings = []
    if row["bc_id"] != "":
        codings = add_coding(codings, system=f"/mdr/bc/biomedicalconcepts/{row['bc_id']}",
                                    code=row["bc_id"],
                                    systemName="CDISC Biomedical Concept")
    if row["vlm_group_id"] != "":
        codings = add_coding(codings, system=f"/mdr/specializations/sdtm/datasetspecializations/{row['vlm_group_id']}",
                                    code=row["vlm_group_id"],
                                    systemName="CDISC SDTM Dataset Specialization")
    if item_group_def is not None:
        item_group_def.Coding = codings
    return item_group_def

def create_item_ref(row):
    item_ref = ODM.ItemRef(ItemOID=create_oid("ITEM", row),
                           OrderNumber=row["order_number"],
                           Mandatory=MANDATORY_MAP[row["mandatory_variable"]])
    if row["prepopulated_term"] != "":
        item_ref.PreSpecifiedValue = row["prepopulated_term"]
    return item_ref

def create_item_def(row):
    item_def = ODM.ItemDef(OID=create_oid("ITEM", row),
                        Name = row["collection_item"],
                        DataType = row["data_type"])
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

    if row["sdtm_annotation"] != "":
        alias_list = []
        sdtm_alias = create_alias("SDTM", row["sdtm_annotation"])
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
    codings = []
    if row["value_list"] != "":
        codelist_item_value_list = row["value_list"].split(";")
        codelist_item_value_display_list = row["value_display_list"].split(";")
        for item in codelist_item_value_list:
            codelist_item = ODM.CodeListItem(CodedValue=item)

            decode = create_decode(codelist_item_value_display_list[codelist_item_value_list.index(item)], lang="en", type="text/plain")
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
            codelist_item_codings = add_coding(codelist_item_codings, system="https://www.cdisc.org/standards/terminology",
                                                 code=row["prepopulated_code"],
                                                 systemName="CDISC/NCI CT")
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


def create_codelist_from_valuelist(row):
    codelist = ODM.CodeList(OID=create_oid("CODELIST_VL", row),
                            Name=row["vlm_group_id"]+"-"+row["variable_name"],
                            DataType=row["data_type"])
    codelist_items = []
    codings = []
    if row["value_list"] != "":
        codelist_item_value_list = row["value_list"].split(";")
        codelist_item_value_display_list = row["value_display_list"].split(";")
        for item in codelist_item_value_list:
            codelist_item = ODM.CodeListItem(CodedValue=item)

            decode = create_decode(codelist_item_value_display_list[codelist_item_value_list.index(item)], lang="en", type="text/plain")
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
            codelist_item_codings = add_coding(codelist_item_codings, system="https://www.cdisc.org/standards/terminology",
                                                 code=row["prepopulated_code"],
                                                 systemName="CDISC/NCI CT")
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


def create_df_from_excel(forms_metadata, collection_metadata, collection_form):
    """
    Reads form and collection metadata from Excel files, processes and merges the data, and returns the resulting DataFrames.
    Args:
        forms_metadata (str): Path to the Excel file containing forms metadata.
        collection_metadata (str): Path to the Excel file containing collection metadata.
        collection_form (str): Name of the sheet in the forms metadata Excel file to read.
    Returns:
        tuple:
            - pd.DataFrame: Merged DataFrame of collection specializations and forms.
            - pd.DataFrame: DataFrame of unique forms with selected columns.
            - str: Name of the form corresponding to the collection form.
    Side Effects:
        Prints the processed forms DataFrame and the first 100 rows of the merged DataFrame for inspection.
    """
     # Read forms from Excel
    df_forms_bcs = pd.read_excel(open(forms_metadata, 'rb'), sheet_name=FORMS_METADATA_EXCEL_SHEET, keep_default_na =False)
    df_forms_bcs = df_forms_bcs[df_forms_bcs['form_id'] == collection_form]
    if len(df_forms_bcs) == 0:
        print(f"No data found in the forms metadata for the specified collection form ({collection_form}).")
        sys.exit()

    form_name = None
    for i, row in df_forms_bcs.iterrows():
        if row['form_label'] != "":
            form_name = row['form_label']
            break
    if form_name is None and not df_forms_bcs.empty:
        form_name = df_forms_bcs.iloc[0]['form_label']
    elif form_name is None:
        form_name = ""

    form_annotation = None
    for i, row in df_forms_bcs.iterrows():
        if row['form_annotation'] != "":
            form_annotation = row['form_annotation']
            break
    if form_annotation is None and not df_forms_bcs.empty:
        form_annotation = df_forms_bcs.iloc[0]['form_annotation']
    elif form_annotation is None:
        form_annotation = ""

    df_forms = df_forms_bcs.drop_duplicates(subset=['form_section_id', 'form_section_order_number', 'form_section_label'])
    df_forms = df_forms[df_forms.columns[df_forms.columns.isin(['form_section_id', 'form_section_order_number',
                                                                'form_section_label', 'form_section_annotation', 'form_section_completion_instruction'])]]
    df_forms.sort_values(['form_section_order_number'], ascending=[True], inplace=True)

    # Read Collection Specializations from Excel
    df = pd.read_excel(open(collection_metadata, 'rb'), sheet_name=COLLECTION_DSS_METADATA_EXCEL_SHEET, keep_default_na =False)

    df = df.merge(df_forms_bcs, how='inner', left_on='collection_group_id', right_on='collection_group_id', suffixes=('', '_y'), validate='m:1')
    if len(df) == 0:
        print(f"No data found in the collection metadata for the specified collection form ({collection_form}).")
        sys.exit()
    df.sort_values(['form_section_order_number', 'bc_order_number', 'order_number'], ascending=[True, True, True], inplace=True)

    return df, df_forms, form_name, form_annotation

def create_odm(df, df_forms, collection_form, form_name, form_annotation):
    """
    Creates an ODM (Operational Data Model) object from the provided dataframes and form information.
    This function constructs an ODM-compliant metadata structure using the input dataframes for forms and items,
    and additional parameters specifying the collection form and form name. It builds the necessary ODM elements
    such as ItemGroupDefs, ItemDefs, CodeLists, and assembles them into a complete ODM object representing the
    study metadata.
    Args:
        df (pd.DataFrame): DataFrame containing item-level metadata, including collection groups, items, and codelists.
        df_forms (pd.DataFrame): DataFrame containing form-level metadata, including form labels and order numbers.
        collection_form (str): Identifier for the collection form to be used as the main form.
        form_name (str): Name of the form to be used in the ODM metadata.
        form_annotation (str): Annotation on the form to be used in the ODM metadata.
    Returns:
        odm (ODM.ODM): An ODM object populated with the study metadata, including forms, item groups, items, and codelists.
    Notes:
        - Assumes the existence of helper functions such as `create_oid`, `create_description`, `create_item_ref`,
          `create_item_group_def`, `create_item_group_ref`, `create_item_def`, and `create_codelist`.
        - Relies on the ODM Python library (e.g., odmlib) for ODM element classes.
        - The function prints collection group transitions for debugging purposes.
    """
    item_group_refs = []
    for i, row in df_forms.iterrows():
        item_group_ref = ODM.ItemGroupRef(
            ItemGroupOID=create_oid("FORM", row),
            OrderNumber=row["form_section_order_number"],
            Mandatory="Yes")           # Add the FormDef to the list of forms
        item_group_refs.append(item_group_ref)

    form = ODM.ItemGroupDef(
            OID=f"IG.{collection_form}",
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
            OID=create_oid("FORM", row),
            Name=row["form_section_label"],
            Repeating="No",
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
    collection_group_id = ""
    form_section_id = ""
    bc_id = ""
    item_group_def = None
    for i, row in df.iterrows():

        if row["collection_group_id"] != collection_group_id: # New Collection Group
            print(row["form_section_id"] + " - " + row["form_section_label"] + " - " + row["collection_group_id"] + " - " + str(row["bc_id"]))

            if collection_group_id:
                item_group_defs.append(item_group_def)

            collection_group_id = row["collection_group_id"]
            form_section_id = row["form_section_id"]
            bc_id = row["bc_id"]
            item_refs = []

            if row["display_hidden"] != "Y":
                item_ref = create_item_ref(row)
                item_refs.append(item_ref)

            item_group_def = create_item_group_def(row, "Concept", itemrefs=item_refs)
            item_group_ref = create_item_group_ref(row, "Section")

            forms[row["form_section_id"]].ItemGroupRef.append(item_group_ref)

        else:
            if row["display_hidden"] != "Y":
                item_ref = create_item_ref(row)
                item_refs.append(item_ref)

        if row["collection_item"] != "":
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
    odm = ODM.ODM(FileOID=create_oid("ODM", []),
                Granularity="Metadata",
                AsOfDateTime=current_datetime,
                CreationDateTime=current_datetime,
                ODMVersion="2.0",
                FileType="Snapshot",
                Originator="Lex Jansen",
                SourceSystem="odmlib",
                SourceSystemVersion="0.1")


    mdv = []
    mdv.append(ODM.MetaDataVersion(OID=create_oid("MDV", []),
                            Name="CDISC360i CDASH POC Study Metadata Version",
                            Description=create_description("CDISC360i CDASH ODM 2.0 metadata version")))

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

    study = ODM.Study(OID=create_oid("STUDY", []),
                    StudyName="CDISC360i CDASH POC Study",
                    Description=create_description("CDISC360i CDASH POC Study"),
                    ProtocolName="CDISC360i CDASH POC Study protocol",
                    MetaDataVersion = mdv)

    odm.Study.append(study)

    return odm

@click.command(help="Generate eCRF renditions")
@click.option(
    "--form",
    "-f",
    "collection_form",
    default="SIXMW1",
    help="The ID of the coleection form to process."
    )

def main(collection_form: str):
    """
    Main function to generate, validate, and transform an ODM 2.0 XML file from Excel metadata.
    Args:
        collection_form (str): The name or identifier of the collection form to process.
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

    ODM_XML_SCHEMA_FILE = Path(__config.odm20_schema)
    XSL_FILE = Path(__config.odm20_stylesheet)
    ODM_XML_FILE = Path(CRF_PATH).joinpath(f"cdash_demo_v20_{collection_form}.xml")
    ODM_JSON_FILE = Path(CRF_PATH).joinpath(f"cdash_demo_v20_{collection_form}.json")
    ODM_HTML_FILE_XSL = Path(CRF_PATH).joinpath(f"cdash_demo_v20_{collection_form}_xsl.html")

    df, df_forms, form_name, form_annotation = create_df_from_excel(FORMS_METADATA_EXCEL, COLLECTION_DSS_METADATA_EXCEL, collection_form)

    odm = create_odm(df, df_forms, collection_form, form_name, form_annotation)

    odm.write_xml(odm_file=ODM_XML_FILE)
    odm.write_json(odm_file=ODM_JSON_FILE)

    validate_odm_xml_file(ODM_XML_FILE, ODM_XML_SCHEMA_FILE, verbose=True)

    transform_xml_saxonche(ODM_XML_FILE, XSL_FILE, ODM_HTML_FILE_XSL)

    loader = LO.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0", ns_uri="http://www.cdisc.org/ns/odm/v2.0"))
    loader.open_odm_document(ODM_XML_FILE)
    odm = loader.load_odm()

if __name__ == "__main__":

    main()
    # main("SIXMW1")
    # main("ECG1")
    # main("QS_EQ5D02")
