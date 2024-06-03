from datetime import datetime, timedelta
from anomalyDetector.db.db import session
import pandas as pd
from anomalyDetector.db.models import Meter, Site
from anomalyDetector.entity.config_entity import DataAvailabilityConfig
from pathlib import Path

class DataAvailability:
    def __init__(self, start, end, config: DataAvailabilityConfig):
        self.start = start
        self.end = end
        self.config = config

    def check_AVAILABILITY(self):


        start = self.start
        end = self.end
        directory = self.config.root_dir

        start_date = datetime.combine(start, datetime.min.time())
        end_date = datetime.combine(end, datetime.min.time())

        
        date_range = [start_date + timedelta(minutes=10*x) for x in range(int((end_date - start_date).total_seconds() / 600) + 1)]

        
        sites = session.query(Site).all()

        anomalies = []

        for site in sites:
            site_id = site.id
            site_code = site.site_code

            site_data = session.query(Meter).filter(Meter.date_time >= start_date, Meter.date_time <= end_date, Meter.site_id == site_id).all()
    
            site_dates = [data.date_time for data in site_data]
            missing_dates = [date for date in date_range if date not in site_dates]
    
            if missing_dates:
                missing_data = pd.DataFrame({'date_time': missing_dates, 'site_code': site_code, 'status': 'missing'})
                anomalies.append(missing_data)
    
            site_df = pd.DataFrame([(data.date_time, data.real_consumption) for data in site_data], columns=['date_time', 'real_consumption'])
            site_df['real_consumption'] = site_df['real_consumption'].fillna(0)  
            site_df['site_code'] = site_code
    
            negative_data = site_df[(site_df['real_consumption'] <= 0)]
            negative_data['status'] = 'Null'  
    
            if not negative_data.empty:
                anomalies.append(negative_data[['date_time', 'site_code', 'status']])
    
        if anomalies:
            anomalies_df = pd.concat(anomalies)
            periods = []
            for site_code, group in anomalies_df.groupby('site_code'):
                for status, status_group in group.groupby('status'):
                    status_group = status_group.sort_values(by='date_time')
                    start_time = status_group.iloc[0]['date_time']
                    end_time = status_group.iloc[0]['date_time']

                    for i in range(1, len(status_group)):
                        current_time = status_group.iloc[i]['date_time']
                        previous_time = status_group.iloc[i - 1]['date_time']

                        if (current_time - previous_time) > timedelta(minutes=10):
                            periods.append({
                                'site_code': site_code,
                                'start_date': start_time,
                                'end_date': end_time,
                                'status': status
                            })
                            start_time = current_time

                        end_time = current_time

                    # Append the last period
                    periods.append({
                        'site_code': site_code,
                        'start_date': start_time,
                        'end_date': end_time,
                        'status': status
                    })

            periods_df = pd.DataFrame(periods)
            file_name = f"{directory}/missing_data_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}.xlsx"
            periods_df.to_excel(file_name, index=False)

