from anomalyDetector import logger
from anomalyDetector.pipeline.stage_01_data_ingestion import DataIngestionTrainingPipeline
from anomalyDetector.db.db import session
from anomalyDetector.db.models import Site


sites_from_db = session.query(Site).all()

id_list=[]
codeRef_list=[]
siteRef_list =[]
brancheRef_list =[]
noDataList=[]

   
    # Iterate over the queried sites
for site in sites_from_db:
    codeRef_list.append(site.site_code)
    siteRef_list.append(site.name)
    brancheRef_list.append(site.branch)
    id_list.append(site.id)

start = '2024-01-09'
end = '2024-01-09'

STAGE_NAME = "Data Ingestion stage"
try:
   logger.info(f">>>>>> stage {STAGE_NAME} started <<<<<<") 
   data_ingestion = DataIngestionTrainingPipeline(start, end, id_list, codeRef_list, siteRef_list, brancheRef_list)
   data_ingestion.main()
   logger.info(f">>>>>> stage {STAGE_NAME} completed <<<<<<\n\nx==========x")
except Exception as e:
        logger.exception(e)
        raise e    