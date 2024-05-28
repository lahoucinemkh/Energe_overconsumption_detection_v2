from anomalyDetector.db.db import session
from anomalyDetector.db.models import Meter, Site, Anomaly
import pandas as pd
from sqlalchemy.orm import joinedload


class anomaliesDownload:
    def __init__(self, start, end):
        self.start = start
        self.end = end 
        

    def getAnomalies(self, output_file):
        start = self.start
        end = self.end


        query = session.query(
            Site.site_code,
            Site.name.label('site_name'),
            Site.midseason_threshold,
            Site.margin,
            Site.opening_hour_week,
            Site.closing_hour_week,
            Site.opening_hour_sun,
            Site.closing_hour_sun,
            Anomaly
        ).join(Site, Anomaly.site_id == Site.id).filter(Anomaly.start_date >= start, Anomaly.start_date <= end)


        df = pd.read_sql(query.statement, session.bind)

        df.drop(columns=['id', 'site_id'], inplace=True)

        writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='anomalies', index=False)
        writer.close()


    