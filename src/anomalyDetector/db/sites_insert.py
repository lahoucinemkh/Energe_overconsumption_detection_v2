from anomalyDetector.db.db import session
from anomalyDetector.db.models import Site, Meter, Anomaly
import pandas as pd
from datetime import time

# Supprimer toutes les entrées existantes dans la table Site
session.query(Anomaly).delete()
session.commit()

# Supprimer toutes les entrées existantes dans la table Site
session.query(Meter).delete()
session.commit()

# Supprimer toutes les entrées existantes dans la table Site
session.query(Site).delete()
session.commit()

bd = pd.read_excel('BD_suiviCPE_new Prog (2).xlsx',  sheet_name='BD_EE052024', header=0, skiprows=0)
for index, row in bd.iterrows():
    # Check if the site with the same site_code already exists in the database
    existing_site = session.query(Site).filter_by(site_code=row['Code site']).first()
    
    if existing_site:
        # Update the existing site with new data
        existing_site.name = row['Site']
        existing_site.branch = row['Branche']
        existing_site.winter_threshold = row['Saison de chauffe']
        existing_site.midseason_threshold = row['Mi-saison']
        existing_site.summer_threshold = row['Saison de climatisation']
        existing_site.margin = row['Margin']
        existing_site.opening_hour_week = row['Horaire Ouv S']
        existing_site.closing_hour_week = row['Horaire Ferm S']
        existing_site.opening_hour_sun = row['Horaire Ouv D']
        existing_site.closing_hour_sun = row['Horaire Ferm D']
    else:
        # Create a new instance of Site
        new_site = Site(
            site_code=row['Code site'],
            name=row['Site'],
            branch=row['Branche'],
            winter_threshold=row['Saison de chauffe'],
            midseason_threshold=row['Mi-saison'],
            summer_threshold=row['Saison de climatisation'],
            margin=row['Margin'],
            opening_hour_week=row['Horaire Ouv S'], 
            closing_hour_week=row['Horaire Ferm S'],
            opening_hour_sun=row['Horaire Ouv D'],
            closing_hour_sun=row['Horaire Ferm D']
        )
        # Add the new instance to the session
        session.add(new_site)

# Commit the changes to the database
session.commit()

# Close the session
session.close()