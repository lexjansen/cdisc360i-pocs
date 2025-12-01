"""
This module contains utility functions
that can be reused.
"""
import os
from odmlib import odm_parser as P
from odmlib import odm_loader as OL, loader as LO
import xmlschema as XSD
from lxml import etree
from saxonche import PySaxonProcessor
from dominate import document
from dominate.tags import *
import logging
import zipfile
import tempfile

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


def create_directory(directory_path):
    if not os.path.exists(directory_path):
        logger.info(f"Directory '{directory_path}' will be created.")
    try:
        os.makedirs(directory_path, exist_ok=True)
    except OSError as e:
        logger.error(f"Error creating directory: {e}")


def validate_odm_xml_file(odm_file, schema_file, verbose=False):
    validator = P.ODMSchemaValidator(schema_file)
    try:
        validator.validate_file(odm_file)
    except XSD.validators.exceptions.XMLSchemaChildrenValidationError as ve:
        logger.error(f"schema validation errors: {ve}")
    else:
        if verbose:
            logger.info("ODM XML schema validation completed successfully...")


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


def transform_xml_saxonche(file_path, xsl_path, output_path, **kwargs):

    saxonhe = PySaxonProcessor(license=False)
    logger.info(f"Saxon-HE version: {saxonhe.version}")

    saxonproc = saxonhe.new_xslt30_processor()

    for key, value in kwargs.items():
        parameter_value = saxonhe.make_integer_value(value)
        saxonproc.set_parameter(key, parameter_value)

    executable = saxonproc.compile_stylesheet(stylesheet_file=str(xsl_path))

    document = saxonhe.parse_xml(xml_file_name=str(file_path))

    executable.transform_to_file(output_file=str(output_path), xdm_node=document)

    logger.info(f"HTML transformation completed successfully... {output_path}")


def create_crf_html(odm_file, verbose=False):
    loader = LO.ODMLoader(OL.XMLODMLoader())
    loader.open_odm_document(odm_file)
    odm = loader.load_odm()
    study = loader.Study()
    mdv = study.MetaDataVersion[0]
    form_def = mdv.FormDef[0]
    if verbose:
        logger.info(f"Generating HTML CRF from {odm_file}")

    # Create HTML document
    doc = document(title=f'{form_def.Name}', lang="en")

    with doc.head:
        # Add some basic styling
        style('''
            body { font-family: Arial, sans-serif; margin: 20px; }
            .study-section {max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);}
            h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 30px; background: #ecf0f1; padding: 10px; border-left: 4px solid #3498db; }
            h3 { color: #2980b9; margin-top: 20px; }
            .form-section { margin: 20px 0; padding: 10px; border: 1px solid #ccc; }
            .item-group { margin: 10px 0; padding: 5px; background-color: #f9f9f9; }
            .item { margin: 5px 0; }
            label { display: inline-block; min-width: 200px; }
        ''')

    with doc.body:
        with div(cls='study-section'):
            # h1(f'Study: {study.GlobalVariables.StudyName}')

            # Process MetaDataVersion
            mdv = study.MetaDataVersion[0]
            globalVariables = study.GlobalVariables
            with div(cls='metadata-version'):
                # paragraph = p()
                # paragraph += strong('Protocol: ')
                # paragraph += f'{globalVariables.ProtocolName}'
                # paragraph = p()
                # paragraph += strong('Description: ')
                # paragraph += f'{globalVariables.StudyDescription}'
                # paragraph = p()
                # paragraph += strong('Metadata Version: ')
                # paragraph += f'{mdv.Description}'
                form_def = mdv.FormDef[0]
                with div(cls='form-section'):
                    h2(f'{form_def.Description.TranslatedText[0]._content}')

                    # Process ItemGroups
                    for ig_ref in form_def.ItemGroupRef:
                        ig_def = mdv.find("ItemGroupDef", "OID", ig_ref.ItemGroupOID),
                        if ig_def:
                            with div(cls='item-group'):
                                h3(f'{ig_def[0].Name}')

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
        logger.info(f"Writing HTML CRF to {output_file_path}")
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


def update_zip_file(zip_path, file_to_replace, new_file_path):
    if os.path.exists(zip_path):
        # Create a temporary file to build the new ZIP archive
        temp_zip_path = os.path.join(tempfile.gettempdir(), os.path.basename(zip_path) + ".tmp")

        with zipfile.ZipFile(zip_path, 'r') as original_zip, \
                zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:

            # Add the new/updated file to the new ZIP archive
            new_zip.write(new_file_path, arcname=file_to_replace)

            # Copy all other files from the original ZIP to the new ZIP
            for item in original_zip.infolist():
                if item.filename != file_to_replace:
                    new_zip.writestr(item, original_zip.read(item.filename))

        # Replace the original ZIP file with the new one
        os.remove(zip_path)
        os.rename(temp_zip_path, zip_path)
    else:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(new_file_path, file_to_replace)
