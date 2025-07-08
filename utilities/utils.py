"""
This module contains utility functions
that can be reused.
"""
import os
from odmlib import odm_parser as P
from odmlib import odm_loader as OL, loader as LO
from lxml import etree
from saxonche import PySaxonProcessor
from dominate import document
from dominate.tags import *


def validate_odm_xml_file(odm_file, schema_file, verbose=False):
    validator = P.ODMSchemaValidator(schema_file)
    try:
        validator.validate_file(odm_file)
    except XSD.validators.exceptions.XMLSchemaChildrenValidationError as ve:
        print(f"schema validation errors: {ve}")
    else:
        if verbose:
            print("ODM XML schema validation completed successfully...")


def transform_xml(xml_path, xsl_path, output_path):
    """
    Transforms an XML file using an XSLT stylesheet.

    Args:
        xml_path (str): Path to the XML file.
        xsl_path (str): Path to the XSLT stylesheet file.
        output_path (str, optional): Path to save the transformed XML.
                                    If None, prints to console.
    """
    xml_tree = etree.parse(xml_path, parser=etree.XMLParser())
    xsl_tree = etree.parse(xsl_path, parser=etree.XMLParser())
    transform = etree.XSLT(xsl_tree)
    result_tree = transform(xml_tree)

    if output_path:
        with open(output_path, 'wb') as f:
            f.write(etree.tostring(result_tree))
    else:
        print(etree.tostring(result_tree).decode())


def transform_xml_saxonche(file_path, xsl_path, output_path):
    saxonhe = PySaxonProcessor(license=False)
    print(saxonhe.version)

    saxonproc = saxonhe.new_xslt30_processor()

    executable = saxonproc.compile_stylesheet(stylesheet_file=str(xsl_path))


    document = saxonhe.parse_xml(xml_file_name=str(file_path))

    executable.transform_to_file(output_file=str(output_path), xdm_node=document)


def create_crf_html(odm_file, verbose):
    loader = LO.ODMLoader(OL.XMLODMLoader())
    loader.open_odm_document(odm_file)
    odm = loader.load_odm()
    study = loader.Study()
    if verbose:
        print(f"Generating HTML CRF from {odm_file}")

    # Create HTML document
    doc = document(title='360i ODM CRF View')

    with doc.head:
        # Add some basic styling
        style('''
            body { font-family: Arial, sans-serif; margin: 20px; }
            .form-section { margin: 20px 0; padding: 10px; border: 1px solid #ccc; }
            .item-group { margin: 10px 0; padding: 5px; background-color: #f9f9f9; }
            .item { margin: 5px 0; }
            label { display: inline-block; min-width: 200px; }
        ''')

    with doc.body:
        h1('360i ODM CRFs')
        with div(cls='study-section'):
            h2(f'Study: {study.GlobalVariables.StudyName}')

            # Process MetaDataVersion
            mdv = study.MetaDataVersion[0]
            with div(cls='metadata-version'):
                h3(f'Metadata Version: {mdv.Name}')
                form_def = mdv.FormDef[0]
                with div(cls='form-section'):
                    h5(f'Form: {form_def.Description.TranslatedText[0]._content}')

                    # Process ItemGroups
                    for ig_ref in form_def.ItemGroupRef:
                        ig_def = mdv.find("ItemGroupDef", "OID", ig_ref.ItemGroupOID),
                        if ig_def:
                            with div(cls='item-group'):
                                h5(f'{ig_def[0].Name}')

                                # Process Items
                                for item_ref in ig_def[0].ItemRef:
                                    item_def = mdv.find("ItemDef", "OID", item_ref.ItemOID)
                                    # if item_def:
                                    with div(cls='item'):
                                        if item_def.Question.TranslatedText:
                                            label(f"{item_def.Question.TranslatedText[0]._content}")
                                        for alias in item_def.Alias:
                                            if alias.Context == "prompt":
                                                label(f"{alias.Name}")
                                        if item_def.CodeListRef:
                                            cl = mdv.find("CodeList", "OID", item_def.CodeListRef.CodeListOID),
                                            options_list = gen_codelist_items(cl[0])
                                            with select(name=cl[0].Name):
                                                for opt in options_list:
                                                    option(opt[0], value=opt[1])
                                        else:
                                            input_(type='text',
                                                   name=item_def.OID,
                                                   placeholder=item_def.Name)
                                        for alias in item_def.Alias:
                                            if alias.Context == "CDASH" or alias.Context == "SDTM":
                                                input_(type="text",
                                                       name=item_def.OID + "." + alias.Context,
                                                       placeholder=alias.Context + ": " + alias.Name,
                                                       style="background-color: LightYellow; border: 1px solid #ccc; field-sizing: content;")
    return doc


def write_html_doc(doc, output_file_path, verbose=False):
    if verbose:
        print(f"Writing HTML CRF to {output_file_path}")
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(str(doc))

def gen_codelist_items(cl) -> list:
    options_list = [["--select--", ""]]
    if cl.EnumeratedItem:
        for ei in cl.EnumeratedItem:
            options_list.append([ei.CodedValue, ei.CodedValue])
    elif cl.CodeListItem:
        for cli in cl.CodeListItem:
            options_list.append([cli.Decode.TranslatedText[0]._content, cli.CodedValue])
    return options_list
