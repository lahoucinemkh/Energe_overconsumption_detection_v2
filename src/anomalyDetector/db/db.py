import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Utiliser os.getenv pour obtenir les valeurs des variables d'environnement
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")


# Configurer la connexion à la base de données
db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(db_url, echo=True)

# Configurer la session SQLAlchemy
session = Session(bind=engine)