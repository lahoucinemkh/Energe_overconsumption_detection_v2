from anomalyDetector import logger
from anomalyDetector.pipeline.stage_01_data_ingestion import DataIngestionTrainingPipeline
from anomalyDetector.pipeline.stage_02_base_model import BaseModelTrainingPipeline
from anomalyDetector.db.db import session
from anomalyDetector.db.models import Site
import pandas as pd


# sites_from_db = session.query(Site).all()

# id_list=[]
# codeRef_list=[]
# siteRef_list =[]
# brancheRef_list =[]
# noDataList=[]

# start = '2024-03-17'
# end = '2024-03-31'

   
#     # Iterate over the queried sites
# for site in sites_from_db:
#     codeRef_list.append(site.site_code)
#     siteRef_list.append(site.name)
#     brancheRef_list.append(site.branch)
#     id_list.append(site.id)


# STAGE_NAME = "Data Ingestion stage"
# try:
#    logger.info(f">>>>>> stage {STAGE_NAME} started <<<<<<") 
#    data_ingestion = DataIngestionTrainingPipeline(start, end, id_list, codeRef_list, siteRef_list, brancheRef_list)
#    data_ingestion.main()
#    logger.info(f">>>>>> stage {STAGE_NAME} completed <<<<<<\n\nx==========x")
# except Exception as e:
#         logger.exception(e)
#         raise e  

start = '2024-03-17 00:00:00'
end = '2024-03-31 00:00:00'

# Convertir en datetime
start = pd.to_datetime(start)
end = pd.to_datetime(end)

sites_from_db = session.query(Site).all()

codeRef_list=[]
fer_list = []
ouv_list = []
tal_list = []
marg = []
dfer_list = []
douv_list = []



# Iterate over the queried sites
for site in sites_from_db:
    codeRef_list.append(site.site_code)
    fer_list.append(site.closing_hour_week)
    ouv_list.append(site.opening_hour_week)
    tal_list.append(site.winter_threshold)
    marg.append((site.margin)+5)
    dfer_list.append(site.closing_hour_sun)
    douv_list.append(site.opening_hour_sun)

for i in range(len(codeRef_list)):
    site_code = codeRef_list[i]    
    # Définition des heures d'ouverture et de fermeture de l'entreprise
    opening_hour_week = ouv_list[i]
    closing_hour_week = fer_list[i]

    closing_hour_sun = dfer_list[i]
    opening_hour_sun = douv_list[i]

    # Définition du talon de consommation
    threshold = tal_list[i]
    margin = marg[i]    
 

    STAGE_NAME = "base model"
    try: 
        logger.info(f"*******************")
        logger.info(f">>>>>> stage {STAGE_NAME} started <<<<<<")
        prepare_base_model = BaseModelTrainingPipeline(start, end, site_code, closing_hour_week, opening_hour_week, threshold, margin, closing_hour_sun, opening_hour_sun)
        prepare_base_model.main()
        logger.info(f">>>>>> stage {STAGE_NAME} completed <<<<<<\n\nx==========x")
    except Exception as e:
        logger.exception(e)
        raise e  