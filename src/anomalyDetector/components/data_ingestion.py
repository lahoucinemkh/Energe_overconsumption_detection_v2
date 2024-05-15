import os
import urllib.request as request
from anomalyDetector import logger
from anomalyDetector.entity.config_entity import DataIngestionConfig
from pathlib import Path
import io
import requests
import json
import base64
import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile
from collections import Counter
import io
from datetime import datetime, timedelta
import datetime
from dateutil.parser import parse
import math
from sqlalchemy import create_engine
from datetime import datetime
from anomalyDetector.db.db import session
from anomalyDetector.db.models import Meter
from dotenv import load_dotenv


load_dotenv()

client_id = os.getenv("CLIENT_ID")
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")


class DataIngestion:
    def __init__(self, start, end, id_list, codeRef_list, siteRef_list, brancheRef_list, config: DataIngestionConfig):
        self.config = config
        self.id_list = id_list
        self.codeRef_list = codeRef_list
        self.siteRef_list = siteRef_list
        self.brancheRef_list = brancheRef_list
        self.start = start
        self.end = end

    
    def get_DATA(self):

        token_url = self.config.token_URL

        start = self.start
        end = self.end

        #get token for access

        authorization = base64.b64encode(bytes(client_id, "ISO-8859-1")).decode("ascii")
        headers = {"Authorization": f"Basic {authorization}",
            "Content-Type": "application/x-www-form-urlencoded"
            }

        body = {"grant_type": "password",
            # "username" : username,    
            # "password" : password,
            # "client_id" : client_id,
            "username" : "rawaservices",
            "password" : "A6QCx3Canuz&GP",
            "client_id" : "easyvision-webapp",
           }

        response = requests.post("https://auth.greenyellow.com/realms/gy-prod/protocol/openid-connect/token", data=body, headers=headers)
        res = response.json()
        TOKEN = res['access_token']


        # Create an empty DataFrame
        all_sites = pd.DataFrame()

        noDataList=[]

        id_list=self.id_list
        codeRef_list=self.codeRef_list
        siteRef_list =self.siteRef_list
        brancheRef_list =self.brancheRef_list

        # Loop through each site
        for i in range(0,len(codeRef_list)):
            siteCode = codeRef_list[i]
            energyType = "ELECTRICITY"
            siteName = siteRef_list[i]
            site_id = id_list[i]

            url = f"https://easyvision-api.greenyellow.com/public/api/v1/consumption/find-by-site-code/{siteCode}/{energyType}/{start}/{end}?calculations=CONSO_REAL&calculations=WEATHER"
            r = requests.get(url, headers={"Authorization": f"Bearer {TOKEN}"})
            # import data into a dataframe
            #print(r.json())

            try:
                data = r.json()
                calculations = data['calculations']

                # Initialisation des listes pour les données
                site_id_list = []
                datetime_list = []
                site_code_list = []
                site_name_list = []
                energy_type_list = []
                consumption_list = []
                meter_id_list = []
                temperature_list = []

                calculation_conso = []

                for calculation in calculations:
                    if calculation['name'] == 'CONSO_REAL':
                        calculation_conso.append(calculation)

        
                calculation_tem = []

                for calculation in calculations:
                    if calculation['name'] == 'WEATHER':
                        calculation_tem.append(calculation)

                #print(calculation_tem)    
                calculation_temp = calculation_tem[0]['values']
                calculation_temp = [{'value': item['value'], 'dateTime': datetime.strptime(item['dateTime'], '%Y-%m-%d %H:%M:%S').replace(minute=0)} for item in calculation_temp]
                #print(calculation_temp)    
        

                for calculation in calculation_conso:
                    for value in calculation['values']:
                        site_id_list.append(site_id)
                        datetime_list.append(value['dateTime'])
                        site_code_list.append(siteCode)
                        energy_type_list.append(energyType)
                        site_name_list.append(siteName)
                        consumption_list.append(value['value'])
                        meter_id_list.append(calculation['meterId'])


                        date_string = value['dateTime']
                        # Convertir la chaîne en objet datetime
                        original_datetime = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')

                        # Ajuster les minutes à 0
                        adjusted_datetime = original_datetime.replace(minute=0) 
                        #print(adjusted_datetime)
                        # Find the dictionary with matching datetime
                        matching_dict = [item for item in calculation_temp if item['dateTime'] == adjusted_datetime]
                        #print(matching_dict)

                        # Check if a match is found
                        if matching_dict:
                            desired_value = matching_dict[0]['value']

                        #temp = calculation_temp[calculation_temp[0]['dateTime'] == adjusted_datetime]
                        temperature_list.append(desired_value)
                 
        
                  
                df = pd.DataFrame({
                    'site_id': site_id_list,
                    'site_code': site_code_list,
                    'site_name': site_name_list,
                    'energy_source': energy_type_list,
                    'date_time': datetime_list,
                    'real_consumption': consumption_list,
                    'meter_id': meter_id_list,
                    'temperature': temperature_list,
                 })

                
                 # sum the  two values of consumption
                if len(Counter(df['meter_id']).keys())>1:
                    conso=df.groupby(['energy_source','date_time'])['real_consumption'].sum()
                    conso=pd.DataFrame(conso).reset_index()
                    
                    df=pd.merge(df, conso, on=['energy_source','date_time'],how='inner')
            
                # create NBmeter
                # data cleaning

                df1=df.groupby('energy_source')['meter_id'].apply(lambda x: list(x.unique())).reset_index().assign(nb_meter=lambda d: d['meter_id'].str.len())
                df1=df1.drop('meter_id', axis=1)
                df=pd.merge(df, df1, on='energy_source', how='right')
                
                df=df.drop_duplicates()
                df=df.drop('meter_id', axis=1)
                print(df.head())
                all_sites = pd.concat([all_sites, df])

            except Exception as e:

                print(' - '+siteCode+' - not found')
                noDataList.append(siteCode+'-'+siteName)    

    
        # Reset the index
        all_sites = all_sites.reset_index(drop=True)

        all_sites.to_csv('pool_P10.csv', encoding='utf-8', index=True)
        all_sites = all_sites.loc[:,['site_id', 'site_code','energy_source','date_time','real_consumption', 'temperature', 'nb_meter']]
        print(all_sites.head(10))

        for index, row in all_sites.iterrows():
            meter_instance = Meter(
                site_id=row['site_id'],
                site_code=row['site_code'],
                energy_source=row['energy_source'],
                date_time=row['date_time'],
                real_consumption=row['real_consumption'],
                temperature=row['temperature'],
                nbmeter=row['nb_meter']
            )

            # add to the session instance
            session.add(meter_instance)

        # Commit the changes to the db
        session.commit()

        # close the session
        session.close()

        print('Sites introuvables sur Easyvision :')
        print(noDataList)

        return noDataList


