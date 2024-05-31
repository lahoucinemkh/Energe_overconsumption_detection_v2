import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
import calendar
from anomalyDetector.db.models import Anomaly, Site
from anomalyDetector.db.db import session
from anomalyDetector.entity.config_entity import AnomalyOccurrenceConfig
from pathlib import Path

class AnomalyOccurrence:
    def __init__(self, start, end, config: AnomalyOccurrenceConfig):
        # self.start = datetime.strptime(start, '%Y-%m-%d')
        # self.end = datetime.strptime(end, '%Y-%m-%d')
        self.start = start
        self.end = end
        self.config = config

    def check_ANOMALYOCCURRENCE(self):

        start = self.start
        end = self.end
        directory = self.config.root_dir

        weeks = []
        current = start

        first_week_end = current + timedelta(days=(6 - current.weekday()))
        weeks.append((current, min(first_week_end, end)))

        current = first_week_end + timedelta(days=1)
        while current + timedelta(days=6) <= end:
            week_start = current
            week_end = current + timedelta(days=6)
            weeks.append((week_start, week_end))
            current = week_end + timedelta(days=1)

        if current <= end:
            weeks.append((current, end))


        sites = session.query(Site).all()
        data = []

        for site in sites:
            for week_start, week_end in weeks:
                week_num = week_start.isocalendar()[1]

                night_anomalies = session.query(Anomaly).filter(
                    Anomaly.site_id == site.id,
                    Anomaly.start_date >= week_start,
                    Anomaly.start_date <= week_end,
                    Anomaly.period_type == 'Nuit'
                ).count()

                sunday_anomalies = session.query(Anomaly).filter(
                    Anomaly.site_id == site.id,
                    Anomaly.start_date >= week_start,
                    Anomaly.start_date <= week_end,
                    Anomaly.period_type == 'Dim'
                ).count()

                data.append({
                    'site_code': site.site_code,
                    'week_start': week_start.strftime("%Y-%m-%d"),
                    'week_end': week_end.strftime("%Y-%m-%d"),
                    'week_number': week_num,
                    'Nuit': 1 if night_anomalies > 0 else 0,
                    'Dim': 1 if sunday_anomalies > 0 else 0
                })

        df = pd.DataFrame(data)

        if not df.empty:
            file_name = f"{directory}/anomaly_occurrence_{start.strftime('%Y-%m-%d')}_{end.strftime('%Y-%m-%d')}.xlsx"
            df.to_excel(file_name, index=False)
    



