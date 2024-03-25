from anomalyDetector.config.configuration import ConfigurationManager
from anomalyDetector.components.data_ingestion import DataIngestion
from anomalyDetector import logger


STAGE_NAME = "Data Ingestion stage"

class DataIngestionTrainingPipeline:
    def __init__(self, start, end, id_list, codeRef_list, siteRef_list, brancheRef_list):
        self.id_list = id_list
        self.codeRef_list = codeRef_list
        self.siteRef_list = siteRef_list
        self.brancheRef_list = brancheRef_list
        self.start = start
        self.end = end

    def main(self):
        config = ConfigurationManager()
        data_ingestion_config = config.get_data_ingestion_config()
        data_ingestion = DataIngestion(self.start, self.end, self.id_list, self.codeRef_list, self.siteRef_list, self.brancheRef_list, config=data_ingestion_config)
        data_ingestion.get_DATA()
        



