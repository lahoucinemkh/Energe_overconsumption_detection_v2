from anomalyDetector.constants import *
import os
from pathlib import Path
from anomalyDetector.utils.common import read_yaml, create_directories
from anomalyDetector.entity.config_entity import (DataIngestionConfig,
                                                  BaseModelConfig,
                                                  DataAvailabilityConfig)


class ConfigurationManager:
    def __init__(
        self,
        config_filepath = CONFIG_FILE_PATH,
        params_filepath = PARAMS_FILE_PATH):

        self.config = read_yaml(config_filepath)
        self.params = read_yaml(params_filepath)

        create_directories([self.config.artifacts_root])



    def get_data_ingestion_config(self) -> DataIngestionConfig:
        config = self.config.data_ingestion

        
        data_ingestion_config = DataIngestionConfig(
            token_URL=config.token_URL
        )

        return data_ingestion_config  


    def get_base_model_config(self) -> BaseModelConfig:
        

        base_model_config = BaseModelConfig(
            params_time_margin=self.params.TIME_MARGIN,
            params_date_margin=self.params.DATE_MARGIN,
            params_hours_margin=self.params.HOURS_MARGIN
        )

        return base_model_config 


    def get_data_availability_config(self) -> DataAvailabilityConfig:
        config = self.config.data_availability

        create_directories([config.root_dir])

        data_availability_config = DataAvailabilityConfig(
            root_dir=config.root_dir
        )

        return data_availability_config       
