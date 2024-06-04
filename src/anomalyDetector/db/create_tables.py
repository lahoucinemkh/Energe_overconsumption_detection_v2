from anomalyDetector.db.models import Base, Site, Meter, Anomaly, Categorization, User
from anomalyDetector.db.db import engine


print("CREATING TABLES >>>> ")
Base.metadata.create_all(bind=engine)

# print("CREATING TABLE User >>>> ")
# User.__table__.create(bind=engine)