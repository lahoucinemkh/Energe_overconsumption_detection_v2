from anomalyDetector.db.db import session
from anomalyDetector.db.models import Meter, Site, Anomaly, Categorization
import pandas as pd
from sqlalchemy.orm import joinedload



def delete_existing_anomalies(start_date, end_date):
    session.query(Anomaly).filter(Anomaly.start_date >= start_date, Anomaly.start_date <= end_date).delete()
    session.commit()


def insert_validated_anomalies(df):
    for index, row in df.iterrows():
        site_code = row['Code site']
        site = session.query(Site).filter(Site.site_code == site_code).first()
        if not site:
            continue

        new_anomaly = Anomaly(
            site_id=site.id,
            start_date=row['Début surconsommation'],
            end_date=row['Fin surconsommation'],
            consumption_value=row['Talon déréglé (kW)'],
            nbr_hour_consumption=row['Nb d\'heures'],
            nbr_days_consumption=row['Nb nuits/jours concernés'],
            start_time=row['Horaire Ouv S'],
            impact_consumption=row['Impact conso (kWh)'],
            period_type=row['Période Talon'],
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

# # Exemple d'utilisation
# start_date = datetime(2024, 4, 21)
# end_date = datetime(2024, 4, 25)


#delete_existing_anomalies(start_date, end_date)


df = pd.read_excel('validated_anomalies.xlsx')


insert_validated_anomalies(df)