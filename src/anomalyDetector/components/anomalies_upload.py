from anomalyDetector.db.db import session
from anomalyDetector.db.models import Meter, Site, Anomaly, Categorization
import pandas as pd
from datetime import datetime

class AnomaliesUpload:
    def __init__(self, start_date, end_date, dataframe):
        self.start_date = start_date
        self.end_date = end_date
        self.dataframe = dataframe

    def delete_existing_anomalies(self):
        """
        Supprime les anomalies existantes et leurs catégorisations dans la période spécifiée.
        """
        anomalies_to_delete = session.query(Anomaly.id).filter(
            Anomaly.start_date >= self.start_date, 
            Anomaly.end_date <= self.end_date
        ).subquery()

        session.query(Categorization).filter(Categorization.anomaly_id.in_(anomalies_to_delete)).delete(synchronize_session=False)
        session.commit()

        session.query(Anomaly).filter(Anomaly.start_date >= self.start_date, Anomaly.start_date <= self.end_date).delete(synchronize_session=False)
        session.commit()

    def insert_validated_anomalies(self):
        """
        Insère les anomalies validées à partir du dataframe fourni.
        """
        for index, row in self.dataframe.iterrows():
            site_code = row['Code site']
            site = session.query(Site).filter(Site.site_code == site_code).first()
            if not site:
                continue

            new_anomaly = Anomaly(
                site_id=site.id,
                start_date=row['Début surconsommation'],
                end_date=row['Fin surconsommation'],
                consumption_value=row['DP Surconso'],
                nbr_hour_consumption=row["Nb d'heures"],
                nbr_days_consumption=row['Nb nuits/jours concernés'],
                impact_consumption=row['Impact conso (kWh)'],
                period_type=row["Période d'alerte"],
                comments=row['Commentaires']
            )
            session.add(new_anomaly)
            session.commit()

            new_categorization = Categorization(
                anomaly_id=new_anomaly.id,
                anomaly_type=row['Type de surconso'],
                category=row['Catégorie'],
                justification=row['Justification']
            )
            session.add(new_categorization)
        session.commit()

