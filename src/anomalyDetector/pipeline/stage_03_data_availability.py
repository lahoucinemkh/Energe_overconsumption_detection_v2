from anomalyDetector.config.configuration import ConfigurationManager
from anomalyDetector.components.data_availability import DataAvailability
from anomalyDetector import logger

STAGE_NAME = "data availability stage"

class DataAvailabilityTrainingPipeline:
    def __init__(self, start, end):
        self.start = start
        self.end = end 


    def main(self):
        config = ConfigurationManager()
        data_availability_config = config.get_data_availability_config()
        data_availability = DataAvailability(self.start, self.end, config=data_availability_config)
        data_availability.check_AVAILABILITY()    