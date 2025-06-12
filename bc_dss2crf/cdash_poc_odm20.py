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
    Reads form and collection metadata from Excel files, processes and merges the data, and returns DataFrames for further use.
    Args:
        forms_metadata (str): Path to the Excel file containing forms metadata.
        collection_metadata (str): Path to the Excel file containing collection metadata.
        collection_form (str, optional): Name of the sheet in the forms metadata Excel file to read. Defaults to COLLECTION_FORM.
    Returns:
        tuple:
            - pd.DataFrame: Merged DataFrame containing collection specializations and form information.
            - pd.DataFrame: DataFrame containing unique forms with selected columns.
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

def create_odm(df, df_forms):

    item_group_refs = []
    for i, row in df_forms.iterrows():
        item_group_ref = ODM.ItemGroupRef(
            ItemGroupOID=create_oid("FORM", row),
            OrderNumber=row["order_number_form"],
            Mandatory="Yes")           # Add the FormDef to the list of forms
        item_group_refs.append(item_group_ref)

    form = ODM.ItemGroupDef(
            OID=f"IG.{COLLECTION_FORM}",
            Name=f"{FORM_NAME} Form",
            Repeating="No",
            Type="Form",
            Description=create_description(f"{FORM_NAME} Form"),
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

def main():

    ODM_XML_SCHEMA_FILE = Path(__config.odm20_schema)
    XSL_FILE = Path(__config.odm20_stylesheet)
    ODM_XML_FILE = Path(CRF_PATH).joinpath(f"cdash_demo_v20_{COLLECTION_FORM}.xml")
    ODM_JSON_FILE = Path(CRF_PATH).joinpath(f"cdash_demo_v20_{COLLECTION_FORM}.json")
    ODM_HTML_FILE_XSL = Path(CRF_PATH).joinpath(f"cdash_demo_v20_{COLLECTION_FORM}_xsl.html")

    df, df_forms = create_df_from_excel(FORMS_METADATA_EXCEL, COLLECTION_DSS_METADATA_EXCEL, COLLECTION_FORM)

    odm = create_odm(df, df_forms)

    odm.write_xml(odm_file=ODM_XML_FILE)
    odm.write_json(odm_file=ODM_JSON_FILE)

    validate_odm_xml_file(ODM_XML_FILE, ODM_XML_SCHEMA_FILE, verbose=True)

    transform_xml_saxonche(ODM_XML_FILE, XSL_FILE, ODM_HTML_FILE_XSL)

    loader = LO.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0", ns_uri="http://www.cdisc.org/ns/odm/v2.0"))
    loader.open_odm_document(ODM_XML_FILE)
    odm = loader.load_odm()

if __name__ == "__main__":

    COLLECTION_FORM ="SIXMW1"
    FORM_NAME = "Six Minute Walk Test"
    # COLLECTION_FORM ="EG1"
    # FORM_NAME = "ECG"

    main()
