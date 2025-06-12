import odmlib.odm_2_0.model as ODM
from odmlib import odm_loader as OL, loader as LO
from pathlib import Path
import os
import sys
import datetime
import pandas as pd
from utilities.utils import (
    validate_odm_xml_file,
    transform_xml_saxonche
)

SCRIPT_PATH = Path.cwd()
sys.path.append(str(SCRIPT_PATH))
from config.config import AppSettings as CFG

__config = CFG()

CRF_PATH = Path(__config.crf_path)

COLLECTION_DSS_METADATA_EXCEL = Path(__config.collection_dss_metadata_excel)
FORMS_METADATA_EXCEL = Path(__config.forms_metadata_excel)

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
        return f"{row['form_id']}"
    elif type.upper() == "SECTION":
        return f"IG.CDASH.POC.{row['collection_group_id']}"
    elif type.upper() == "CONCEPT":
        return f"IG.CDASH.POC.{row['collection_group_id']}"
    elif type.upper() == "ITEM":
        return f"IT.{row['collection_group_id']}.{row['collection_item']}"
    elif type.upper() == "CODELIST":
        return f"CL.{row['collection_group_id']}.{row['variable_name']}.{row['codelist']}"
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
        OrderNumber=row["order_number_bc"],
        Mandatory="Yes")
    return item_group_ref

def create_item_group_def(row, type, itemrefs=[]):

    if type.upper() == "SECTION":
        item_group_def = ODM.ItemGroupDef(OID=create_oid(type.upper(), row),
                                        Name=row["form_label"],
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
        if row["prepopulated_term"] != "":
           codelist_item = ODM.CodeListItem(CodedValue=row["prepopulated_term"])
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
    Side Effects:
        Prints the processed forms DataFrame and the first 100 rows of the merged DataFrame for inspection.
    """
     # Read forms from Excel
    df_forms_bcs = pd.read_excel(open(forms_metadata, 'rb'), sheet_name=collection_form, keep_default_na =False)
    df_forms = df_forms_bcs.drop_duplicates(subset=['form_id', 'order_number_form', 'form_label'])
    df_forms = df_forms[df_forms.columns[df_forms.columns.isin(['form_id', 'order_number_form', 'form_label'])]]
    print(df_forms)

    # Read Collection Specializations from Excel
    df = pd.read_excel(open(collection_metadata, 'rb'), sheet_name='Collection Specializations', keep_default_na =False)

    # Merge Collection Specializations with forms
    df = df.merge(df_forms_bcs, how='inner', left_on='collection_group_id', right_on='collection_group_id', suffixes=('', '_y'), validate='m:1')
    df.sort_values(['form_id', 'order_number_bc', 'collection_group_id', 'order_number'], ascending=[True, True, True, True], inplace=True)
    print(df.head(100))

    return df, df_forms

def create_odm(df, df_forms, collection_form, form_name):
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
            OrderNumber=row["order_number_form"],
            Mandatory="Yes")           # Add the FormDef to the list of forms
        item_group_refs.append(item_group_ref)

    form = ODM.ItemGroupDef(
            OID=f"IG.{collection_form}",
            Name=f"{form_name} Form",
            Repeating="No",
            Type="Form",
            Description=create_description(f"{form_name} Form"),
            ItemGroupRef=item_group_refs)

    forms = {}
    for i, row in df_forms.iterrows():
        # Define a FormDef
        form_def = ODM.ItemGroupDef(
            OID=create_oid("FORM", row),
            Name=row["form_label"],
            Repeating="No",
            Type="Section",
            Description=create_description(row["form_label"])
        )
        # Add the FormDef to the list of forms
        forms[row["form_id"]] = form_def

    item_group_refs = []
    item_group_defs = []
    item_refs = []
    item_defs = []
    codelists = []
    collection_group_id = ""
    form_id = ""
    bc_id = ""
    for i, row in df.iterrows():

        if row["collection_group_id"] != collection_group_id: # New Collection Group
            print(row["collection_group_id"] + " " + str(row["bc_id"]))

            if collection_group_id:
                item_group_defs.append(item_group_def)

            collection_group_id = row["collection_group_id"]
            form_id = row["form_id"]
            bc_id = row["bc_id"]
            item_refs = []

            if row["display_hidden"] != "Y":
                item_ref = create_item_ref(row)
                item_refs.append(item_ref)

            item_group_def = create_item_group_def(row, "Concept", itemrefs=item_refs)
            item_group_ref = create_item_group_ref(row, "Section")

            forms[row["form_id"]].ItemGroupRef.append(item_group_ref)

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

def main(collection_form, form_name):
    """
    Main function to generate, validate, and transform an ODM 2.0 XML file from Excel metadata.
    Args:
        collection_form (str): The name or identifier of the collection form to process.
        form_name (str): The name of the form to be used in the ODM document.
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

    df, df_forms = create_df_from_excel(FORMS_METADATA_EXCEL, COLLECTION_DSS_METADATA_EXCEL, collection_form)

    odm = create_odm(df, df_forms, collection_form, form_name)

    odm.write_xml(odm_file=ODM_XML_FILE)
    odm.write_json(odm_file=ODM_JSON_FILE)

    validate_odm_xml_file(ODM_XML_FILE, ODM_XML_SCHEMA_FILE, verbose=True)

    transform_xml_saxonche(ODM_XML_FILE, XSL_FILE, ODM_HTML_FILE_XSL)

    loader = LO.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0", ns_uri="http://www.cdisc.org/ns/odm/v2.0"))
    loader.open_odm_document(ODM_XML_FILE)
    odm = loader.load_odm()

if __name__ == "__main__":

    main("SIXMW1", "Six Minute Walk Test")
    # main("EG1", "ECG")
