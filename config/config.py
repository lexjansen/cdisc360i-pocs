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
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
        config = configparser.ConfigParser()
        config_file = self._get_config_file()
        config.read(config_file)
        self.crf_path = config.get('CRF', 'crf_path')

        self._load_section_options(
            config,
            'Metadata',
            {
                'metadata_path': 'metadata_path',
                'crf_specializations_metadata_excel_remote': 'crf_specializations_metadata_excel_remote',
                'crf_specializations_metadata_excel': 'crf_specializations_metadata_excel',
                'crf_specializations_metadata_excel_sheet': 'crf_specializations_metadata_excel_sheet',
                'forms_metadata_excel': 'forms_metadata_excel',
                'forms_metadata_excel_sheet': 'forms_metadata_excel_sheet',
            }
        )
        self._load_section_options(
            config,
            'Schema',
            {
                'odm132_xml': 'odm132_schema',
                'odm20_xml': 'odm20_schema',
            }
        )
        self._load_section_options(
            config,
            'Stylesheet',
            {
                'odm132_xsl': 'odm132_stylesheet',
                'odm20_xsl': 'odm20_stylesheet',
            }
        )

    def _load_section_options(self, config: configparser.ConfigParser, section: str, option_map: dict):
        """
        Loads configured options from a section and assigns them to AppSettings attributes.
        """
        if not config.has_section(section):
            return

        for option_name, attr_name in option_map.items():
            if config.has_option(section, option_name):
                setattr(self, attr_name, config.get(section, option_name))

    def _get_config_file(self) -> str:
        """
        Gets the path to the configuration file 'config.ini' and checks if the file exists.
        :raises Exception: If 'config.ini' is not found; the application is unable to cannot proceed without it.
        :return: The absolute path to the 'config.ini' configuration file.
        """
        config_file = Path(__file__).parent.joinpath("config.ini")
        if not Path(config_file).absolute().exists():
            message = (
                f"360i {config_file} file not found in the 'config' folder. "
                f"You cannot continue without the config.ini file. "
                f"Either copy config-relative-paths.ini to config.ini, or copy "
                f"config-absolute-paths.ini to config.ini, and edit the paths to match your environment."
            )
            self.logger.error(message)
            exit()
            raise Exception(message)
        return str(config_file)
