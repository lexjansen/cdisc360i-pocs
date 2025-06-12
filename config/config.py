"""
config.py loads the configuration settings for the 360i programs from config.ini
"""
import configparser
from pathlib import Path
import logging

class AppSettings:
    """
    Provides the configuration settings for the 360i code. Loads the settings from config.ini
    """
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        config = configparser.ConfigParser()
        config_file = self._get_config_file()
        config.read(config_file)
        self.crf_path = config.get('CRF', 'crf_path')
        if config.has_section('Metadata'):
            if config.has_option('Metadata', 'collection_dss_metadata_excel'):
                self.collection_dss_metadata_excel = config.get('Metadata', 'collection_dss_metadata_excel')
            if config.has_option('Metadata', 'forms_metadata_excel'):
                self.forms_metadata_excel = config.get('Metadata', 'forms_metadata_excel')
        if config.has_section('Schema'):
            if config.has_option('Schema', 'odm132_xml'):
                self.odm132_schema = config.get('Schema', 'odm132_xml')
            if config.has_option('Schema', 'odm20_xml'):
                self.odm20_schema = config.get('Schema', 'odm20_xml')
        if config.has_section('Stylesheet'):
            if config.has_option('Stylesheet', 'odm132'):
                self.odm132_stylesheet = config.get('Stylesheet', 'odm132')
            if config.has_option('Stylesheet', 'odm20'):
                self.odm20_stylesheet = config.get('Stylesheet', 'odm20')


    def _get_config_file(self) -> str:
        """
        Gets the path to the configuration file 'config.ini' and checks if the file exists.
        :raises Exception: If 'config.ini' is not found; the application is unable to cannot proceed without it.
        :return: The absolute path to the 'config.ini' configuration file.
        """
        config_file =  Path(__file__).parent.joinpath("config.ini")
        if not Path(config_file).absolute().exists():
            self.logger.error(f"360i {config_file} file not found. You cannot continue without the config.ini file.")
            raise Exception("config.ini file not found. You cannot continue with the config.ini file.")
        return config_file
