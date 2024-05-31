from anomalyDetector.config.configuration import ConfigurationManager
from anomalyDetector.components.anomaly_occurrence import AnomalyOccurrence
from anomalyDetector import logger

STAGE_NAME = "anomaly occurrence stage"

class AnomalyOccurrenceTrainingPipeline:
    def __init__(self, start, end):
        self.start = start
        self.end = end 


    def main(self):
        config = ConfigurationManager()
        anomaly_occurrence_config = config.get_anomaly_occurrence_config()
        anomaly_occurrence = AnomalyOccurrence(self.start, self.end, config=anomaly_occurrence_config)
        anomaly_occurrence.check_ANOMALYOCCURRENCE()