from anomalyDetector.config.configuration import ConfigurationManager
from anomalyDetector.components.base_model import BaseModel
from anomalyDetector import logger


STAGE_NAME = "base model"

class BaseModelTrainingPipeline:
    def __init__(self, id, start, end, site_code, closing_hour_week, opening_hour_week, threshold, margin, closing_hour_sun, opening_hour_sun):
        self.id = id
        self.start = start
        self.end = end 
        self.site_code = site_code
        self.closing_hour_week = closing_hour_week
        self.opening_hour_week = opening_hour_week
        self.threshold = threshold
        self.margin = margin
        self.closing_hour_sun = closing_hour_sun
        self.opening_hour_sun = opening_hour_sun

    def main(self):
        config = ConfigurationManager()
        base_model_config = config.get_base_model_config()
        base_model = BaseModel(self.id, self.start, self.end, self.site_code, self.closing_hour_week, self.opening_hour_week, self.threshold, self.margin, self.closing_hour_sun, self.opening_hour_sun, config=base_model_config)
        base_model.DETECT()
        