from anomalyDetector.db.models import Base, Site, Meter, Anomaly, Categorization
from anomalyDetector.db.db import engine


print("CREATING TABLES >>>> ")
Base.metadata.create_all(bind=engine)