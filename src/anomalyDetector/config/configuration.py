from anomalyDetector.constants import *
import os
from pathlib import Path
from anomalyDetector.utils.common import read_yaml
from anomalyDetector.entity.config_entity import (DataIngestionConfig)


class ConfigurationManager:
    def __init__(
        self,
        config_filepath = CONFIG_FILE_PATH,
        params_filepath = PARAMS_FILE_PATH):

        self.config = read_yaml(config_filepath)
        self.params = read_yaml(params_filepath)



    def get_data_ingestion_config(self) -> DataIngestionConfig:
        config = self.config.data_ingestion

        
        data_ingestion_config = DataIngestionConfig(
            token_URL=config.token_URL
        )

        return data_ingestion_config    