import os
import urllib.request as request
import pandas as pd
import numpy as np
from anomalyDetector.db.db import session
from pandas import ExcelWriter
import xlsxwriter
from pandas import ExcelFile
from anomalyDetector.db.models import Meter, Site, Anomaly
from datetime import datetime, timedelta
from anomalyDetector.utils.common import TimeMarginClustering, create_cluster_dataframe, custom_clustering, meme_semaine, arrondir_multiple_de_5
from anomalyDetector.entity.config_entity import BaseModelConfig

class BaseModel:
    def __init__(self, id, start, end, site_code, closing_hour_week, opening_hour_week, threshold, margin, closing_hour_sun, opening_hour_sun, config: BaseModelConfig):
        self.id = id
        self.config = config
        self.start = start
        self.end = end 
        self.site_code = site_code
        self.closing_hour_week = closing_hour_week
        self.opening_hour_week = opening_hour_week
        self.threshold = threshold
        self.margin = margin
        self.closing_hour_sun = closing_hour_sun
        self.opening_hour_sun = opening_hour_sun


    def DETECT(self):
        time_margin = self.config.params_time_margin 
        date_margin = self.config.params_date_margin
        hours_margin = self.config.params_hours_margin 
        Code_list=[]
        Date1_list=[]
        TalonRef_list=[]
        Date2_list=[]
        heurev_list=[]
        heuref_list=[]
        NbrHeure_list=[]
        defrence_list=[]
        surconso_identifie=[]
        Energie=[]
        Marge_list=[]
        startt_list = []

        id = self.id  
        code = self.site_code    
        # Définition des heures d'ouverture et de fermeture de l'entreprise
        heure_ouverture = self.opening_hour_week
        heure_fermeture = self.closing_hour_week

        closing_hour_sun = self.closing_hour_sun
        opening_hour_sun = self.opening_hour_sun

        # Définition du talon de consommation
        talon_consommation = self.threshold
        marg = self.margin

        start = self.start
        end = self.end

        if closing_hour_sun == datetime.strptime('00:00:00', '%H:%M:%S').time():
            closing_hour_sun = heure_fermeture
            opening_hour_sun = heure_ouverture

    
        # Convertissez le résultat en un DataFrame pandas
        df = pd.read_sql(session.query(Meter).filter(Meter.site_code == code).filter(Meter.date_time >= start).filter(Meter.date_time <= end).statement, session.bind)
        df['date_time'] = pd.to_datetime(df['date_time'])

        df1 = df.copy()
        df2 = df.copy()


        df_dim =  df1[df1['date_time'].dt.dayofweek == 6]
        df_sem = df1[df1['date_time'].dt.dayofweek != 6]

            # Filtrer les données pour les heures en dehors des heures d'ouverture de l'entreprise
        if heure_fermeture.hour in [0, 1, 2]:
            donnees_filtrees_sem = df_sem[(df_sem['date_time'].dt.time > heure_fermeture) & (df_sem['date_time'].dt.time <= heure_ouverture)]
            #donnees_filtrees = df[(df['date_time'].apply(lambda x: x.hour) > heure_fermeture.hour) & (df['date_time'].apply(lambda x: x.hour) <= heure_ouverture.hour)]
        else:
            donnees_filtrees_sem = df_sem[(df_sem['date_time'].dt.time > heure_fermeture) | (df_sem['date_time'].dt.time <= heure_ouverture)]
            #donnees_filtrees = df[(df['date_time'].apply(lambda x: x.hour) > heure_fermeture.hour) | (df['date_time'].apply(lambda x: x.hour) <= heure_ouverture.hour)]

        # Filtrer les données pour les heures en dehors des heures d'ouverture de l'entreprise
        if closing_hour_sun.hour in [0, 1, 2]:
            donnees_filtrees_dim = df_dim[(df_dim['date_time'].dt.time > closing_hour_sun) & (df_dim['date_time'].dt.time <= opening_hour_sun)]
            #donnees_filtrees = df[(df['date_time'].apply(lambda x: x.hour) > heure_fermeture.hour) & (df['date_time'].apply(lambda x: x.hour) <= heure_ouverture.hour)]
        else:
            donnees_filtrees_dim = df_dim[(df_dim['date_time'].dt.time > closing_hour_sun) | (df_dim['date_time'].dt.time <= opening_hour_sun)]
            #donnees_filtrees = df[(df['date_time'].apply(lambda x: x.hour) > heure_fermeture.hour) | (df['date_time'].apply(lambda x: x.hour) <= heure_ouverture.hour)] 
    
        donnees_filtrees = pd.concat([donnees_filtrees_sem, donnees_filtrees_dim])       

        # Filtrer les heures de surconsommation (différence > talon_consommation * 0.08)
        heures_surconsommation = donnees_filtrees[donnees_filtrees['real_consumption'] > (talon_consommation + (talon_consommation * 0.08))]


        # Liste des dates uniques dans votre DataFrame
        dates_uniques = (df1['date_time'].dt.date).unique()
        dates_uniques_1 = (df1['date_time']).unique()
        
        # Parcourir chaque date et effectuer le clustering
        for i in range(len(dates_uniques) - 1):
            date_actuelle = dates_uniques[i]
            date_suivante = dates_uniques[i + 1]

            if dates_uniques_1[i].dayofweek == 6 and closing_hour_sun>=datetime.strptime('16:00:00', '%H:%M:%S').time():
                heure_fermeture_1 = closing_hour_sun
            else:
                heure_fermeture_1 = heure_fermeture

            if dates_uniques_1[i + 1].dayofweek == 6:
                heure_ouverture_1 = opening_hour_sun
            else:
                heure_ouverture_1 = heure_ouverture            

            # Filtrer les données pour la date actuelle et la date suivante
            heures_nuit = heures_surconsommation[
                ((heures_surconsommation['date_time'].dt.date) == date_actuelle) &
                (heures_surconsommation['date_time'].dt.time > heure_fermeture_1)
            ]

            heures_nuit_suivante = heures_surconsommation[
                (heures_surconsommation['date_time'].dt.date == date_suivante) &
                (heures_surconsommation['date_time'].dt.time < heure_ouverture_1)
            ]


            # Combiner les données de la nuit actuelle et de la nuit suivante
            if heure_fermeture_1.hour in [0, 1, 2]:
                heures_date = heures_nuit_suivante
            else:
                heures_date = pd.concat([heures_nuit, heures_nuit_suivante])

            if heures_date.size == 0:
             continue
            else:
                # Créer l'objet DBSCAN
                clustering_algo = TimeMarginClustering(time_margin=time_margin, value_margin=marg)


                labels = clustering_algo.fit_predict(heures_date)

                # Ajouter les labels de clustering comme une nouvelle colonne
                heures_date['Cluster'] = labels

                # Calculer la valeur moyenne de l'impact pour chaque cluster
                clusters_moyenne = heures_date.groupby('Cluster')['real_consumption'].mean().reset_index()

                # Compter le nombre d'heures regroupées dans chaque cluster
                clusters_compte = heures_date.groupby('Cluster')['date_time'].count().reset_index()
                clusters_compte = clusters_compte.rename(columns={'date_time': 'Nombre d\'heures regroupées'})

                # Fusionner les informations de valeur moyenne et de compte dans un seul DataFrame
                clusters_info = clusters_moyenne.merge(clusters_compte, on='Cluster')

                # Ajouter la colonne start_time pour chaque cluster (en utilisant l'heure)
                start_times = heures_date.groupby('Cluster')['date_time'].min().reset_index()
                start_times['start_time'] = start_times['date_time'].dt.time
                start_times = start_times.drop(columns=['date_time'])  # Supprimer la colonne de date_time
                clusters_info = clusters_info.merge(start_times, on='Cluster')


                #print(clusters_info)

                #saver dans un excel
                for index, row in clusters_info.iterrows():
                    heuref_list.append(heure_fermeture)
                    Code_list.append(code)
                    Energie.append('Electricité')
                    TalonRef_list.append(talon_consommation)
                    date1 = dates_uniques[i]
                    #date1 = datetime.datetime.strptime(date1, '%Y-%m-%d').date()
                    Date1_list.append(date1)
                    date2 = dates_uniques[i + 1]
                    #date2 = datetime.datetime.strptime(date2, '%Y-%m-%d').date()
                    Date2_list.append(date2)
                    heurev_list.append(heure_ouverture)
                    NbrHeure_list.append((row['Nombre d\'heures regroupées'])/6)
                    defrence_list.append(int(row['real_consumption']-talon_consommation))
                    surconso_identifie.append(int(row['real_consumption']))
                    Marge_list.append(marg)
                    startt_list.append(row['start_time'])

        df_NuitOut = pd.DataFrame({'Code':Code_list, 'Energie': Energie,'heure ouverture':heurev_list,'heure fermetur':heuref_list, 'TalonRef':TalonRef_list, 'Début surconsommation':Date1_list, 'Fin surconsommation':Date2_list, 'Talon surconso identifie':surconso_identifie, 'impact':defrence_list,'NbrHeures':NbrHeure_list, 'Marge':Marge_list, 'Start_time':startt_list})

        # Assume que votre DataFrame s'appelle df
        df_NuitOut['Day_Debut_surconso'] = pd.to_datetime(df_NuitOut['Début surconsommation']).dt.day
        df_NuitOut['Day_fin_surconso'] = pd.to_datetime(df_NuitOut['Fin surconsommation']).dt.day
        df_NuitOut['month_fin_surconso'] = pd.to_datetime(df_NuitOut['Fin surconsommation']).dt.month
        df_NuitOut['year_fin_surconso'] = pd.to_datetime(df_NuitOut['Fin surconsommation']).dt.year

        Code_list=[]
        TalonRef_list=[]
        Date1_list=[]
        Date2_list=[]
        heurev_list=[]
        heuref_list=[]
        NbrHeure_list=[]
        defrence_list=[]
        surconso_identifie=[]
        Energie=[]
        NbrNuit_list=[]
        NImpact_conso = []
        NperSurconso = []
        NPeriode = []
        startt_list = []



        for code in df_NuitOut["Code"].unique():
            df_Nuit = df_NuitOut[df_NuitOut["Code"] == code]
            # Votre code précédent ici...

            # Créer un tableau Numpy à partir des colonnes spécifiées
            X = np.column_stack((df_Nuit.index, df_Nuit['Day_Debut_surconso'], df_Nuit['Talon surconso identifie'], df_Nuit['NbrHeures'], df_Nuit['Day_fin_surconso'], df_Nuit['month_fin_surconso'], df_Nuit['year_fin_surconso']))

            print(X)
            marge=df_Nuit['Marge'].iloc[0]
   
            clusters = custom_clustering(X , date_margin=date_margin , consumption_margin=marge , hours_margin=hours_margin )
    
            df = create_cluster_dataframe(clusters)
            print(df.head(5))

            for (index, row), cluster in zip(df.iterrows(), clusters):
                Energie.append('Electricité')
                heuref_list.append(df_Nuit['heure fermetur'].iloc[0])
                Code_list.append(code)
                TalonRef_list.append(df_Nuit['TalonRef'].iloc[0])
                first_index = int(cluster[0][0])
                Date1_list.append(df_NuitOut['Début surconsommation'].iloc[first_index])
                last_index = int(cluster[-1][0])
                Date2_list.append(df_NuitOut['Fin surconsommation'].iloc[last_index])
                heurev_list.append(df_Nuit['heure ouverture'].iloc[0])
                surconso_identifie.append(arrondir_multiple_de_5(int(row['Mean Consomption'])))
                defrence_list.append(int(row['Mean Consomption']) - df_Nuit['TalonRef'].iloc[0])
                NbrHeure_list.append("{:.2f}".format(row['Mean Hours']))
                NbrNuit_list.append(row['Count'])
                surconso = int((row['Mean Hours']) * (int(row['Mean Consomption']) - df_Nuit['TalonRef'].iloc[0]) * row['Count'])
                NImpact_conso.append(surconso)

                persurconso = ((int(row['Mean Consomption']) - df_Nuit['TalonRef'].iloc[0]) /  df_Nuit['TalonRef'].iloc[0])*100
                persurconso = int(persurconso)
                persurconso = str(persurconso)
                persurconso = persurconso + '%'
                NperSurconso.append(persurconso)
                NPeriode.append('Nuit')
                startt_list.append(df_NuitOut['Start_time'].iloc[first_index])

        df_Fusion = pd.DataFrame({'Code':Code_list, 'Energie': Energie,'heure ouverture':heurev_list,'heure fermetur':heuref_list, 'TalonRef':TalonRef_list, 'Début surconsommation':Date1_list, 'Fin surconsommation':Date2_list, 'Talon surconso identifie':surconso_identifie, 'impact':defrence_list,'NbrHeures':NbrHeure_list, 'NbrNuits':NbrNuit_list, 'Impact conso (kWh)':NImpact_conso, '% Surconso':NperSurconso, "Période d'alerte":NPeriode, 'Start_time':startt_list})
        # grouped_df = df_Fusion.groupby("Code").size().reset_index(name="Nombre de lignes")
        # grouped_df["Pourcentage de précision"] = np.maximum(30, 100 - (grouped_df["Nombre de lignes"] - 1) * 10)
        # df = df_Fusion.merge(grouped_df[["Code", "Pourcentage de précision"]], on="Code", how="left")
        # df['Pourcentage de précision'] = df['Pourcentage de précision'].astype(str) + '%'
        # df = process_data(df , 5)

        df_Fusion['duree_fermeture'] = round(((pd.to_datetime(df_Fusion['heure ouverture'], format='%H:%M:%S')+ pd.Timedelta(days=1)) - pd.to_datetime(df_Fusion['heure fermetur'], format='%H:%M:%S')).dt.total_seconds() / 3600, 2)   


        dCode_list=[]
        dTalonRef_list=[]
        dDate1_list=[]
        dDate2_list=[]
        dheurev_list=[]
        dheuref_list=[]
        dNbrHeure_list=[]
        ddefrence_list=[]
        dsurconso_identifie=[]
        dEnergie=[]
        dNbrNuit=[]
        Impact_conso = []
        perSurconso = []
        Periode = []
        dstartt_list = []

        code = self.site_code    
        # Définition des heures d'ouverture et de fermeture de l'entreprise
        heure_ouverture = self.opening_hour_week
        heure_fermeture = self.closing_hour_week

        closing_hour_sun = self.closing_hour_sun
        opening_hour_sun = self.opening_hour_sun

        # Définition du talon de consommation
        talon_consommation = self.threshold
        marg = self.margin

        start = self.start
        end = self.end

        if closing_hour_sun == datetime.strptime('00:00:00', '%H:%M:%S').time():
            closing_hour_sun = heure_fermeture
            opening_hour_sun = heure_ouverture

        df2['Date'] = df2['date_time'].dt.date

    


        # Convert 'Date' column to datetime type if needed
        df2['Date'] = pd.to_datetime(df2['Date'])

        # Filter the data to keep only Sundays
        sundays_data = df2[df2['Date'].dt.weekday == 6]

        # Print the filtered data
        #print(sundays_data.head(30))
        df2 = sundays_data

        # Filter the data for hours outside the company's opening hours
        if closing_hour_sun == heure_fermeture or closing_hour_sun == datetime.strptime('00:00:00', '%H:%M:%S').time():
            donnees_filtrees = df2[(df2['date_time'].dt.time > heure_ouverture) & (df2['date_time'].dt.time <= heure_fermeture)]
    
        elif closing_hour_sun<datetime.strptime('16:00:00', '%H:%M:%S').time():
            #time = datetime.strptime("14:00:00", "%H:%M:%S").time()
            donnees_filtrees = df2[(df2['date_time'].dt.time > closing_hour_sun) & (df2['date_time'].dt.time <= heure_fermeture)]
        elif (closing_hour_sun>=datetime.strptime('16:00:00', '%H:%M:%S').time()) and (closing_hour_sun != heure_fermeture) :
            donnees_filtrees = pd.DataFrame()
            
    
        if len(donnees_filtrees) > 0:
            # Filtrer les heures de surconsommation (différence > talon_consommation * 0.08)
            heures_surconsommation = donnees_filtrees[donnees_filtrees['real_consumption'] > (talon_consommation + (talon_consommation * 0.08))]


            # Print the hours of overconsumption
            if len(heures_surconsommation) > 0:
                print(heures_surconsommation)

            print("\n")
            print("\n")
            print("l'analyse de site : {}", code)
            print("\n")
            print("\n")

            # Supprimer les lignes en double basées sur les colonnes 'site_code' et 'date_time'
            heures_surconsommation = heures_surconsommation.drop_duplicates(subset=['site_code', 'date_time'])

            print(len(heures_surconsommation))

            # Liste des dates uniques dans votre DataFrame
            dates_uniques = heures_surconsommation['Date'].dt.strftime('%Y-%m-%d').unique()
            print(dates_uniques)
        
            # Parcourir chaque date et effectuer le clustering
            for i in range(len(dates_uniques)):
                date = dates_uniques[i]
            
                print(f'la date num {i} est {date}')

                heures_date = heures_surconsommation[(heures_surconsommation['Date'] == date)]
                print(heures_date.head(10))

            
                # Créer l'objet DBSCAN
                clustering_algo = TimeMarginClustering(time_margin=time_margin, value_margin=marg)

                labels = clustering_algo.fit_predict(heures_date)

                # Ajouter les labels de clustering comme une nouvelle colonne
                heures_date['Cluster'] = labels

                # Calculer la valeur moyenne de l'impact pour chaque cluster
                clusters_moyenne = heures_date.groupby('Cluster')['real_consumption'].mean().reset_index()

                # Compter le nombre d'heures regroupées dans chaque cluster
                clusters_compte = heures_date.groupby('Cluster')['date_time'].count().reset_index()
                clusters_compte = clusters_compte.rename(columns={'date_time': 'Nombre d\'heures regroupées'})

                # Fusionner les informations de valeur moyenne et de compte dans un seul DataFrame
                clusters_info = clusters_moyenne.merge(clusters_compte, on='Cluster')

                # Ajouter la colonne start_time pour chaque cluster (en utilisant l'heure)
                start_times = heures_date.groupby('Cluster')['date_time'].min().reset_index()
                start_times['start_time'] = start_times['date_time'].dt.time
                start_times = start_times.drop(columns=['date_time'])  # Supprimer la colonne de date_time
                clusters_info = clusters_info.merge(start_times, on='Cluster')
            
                print(clusters_info)

                #saver dans un excel
                for index, row in clusters_info.iterrows():
                    dheuref_list.append(heure_fermeture)
                    dCode_list.append(code)
                    dEnergie.append('Electricité')
                    dTalonRef_list.append(talon_consommation)
                    date1 = dates_uniques[i]
                    dDate1_list.append(date1)
                # date_string = np.datetime_as_string(dates_uniques[i+1], unit='D')
                    #date2 = datetime.datetime.strptime(date_string, '%Y-%m-%d').date()
                    dDate2_list.append(date1)
                    dheurev_list.append(heure_ouverture)
                    dNbrHeure_list.append("{:.2f}".format(row['Nombre d\'heures regroupées']/6))
                    ddefrence_list.append(int(row['real_consumption']-talon_consommation))
                    dsurconso_identifie.append((int(row['real_consumption'])))
                    surconso = row['Nombre d\'heures regroupées'] * int(row['real_consumption']-talon_consommation)
                    dNbrNuit.append(1)
                    Impact_conso.append(surconso)

                    persurconso = (int(row['real_consumption']-talon_consommation) /  talon_consommation)*100
                    persurconso = int(persurconso)
                    persurconso = str(persurconso)
                    persurconso = persurconso + '%'
                    perSurconso.append(persurconso)
                    Periode.append('Dim')
                    dstartt_list.append(row['start_time'])

        df_dimOut = pd.DataFrame({'Code':dCode_list, 'Energie': dEnergie,'heure ouverture':dheurev_list,'heure fermetur':dheuref_list, 'TalonRef':dTalonRef_list, 'Début surconsommation':dDate1_list, 'Fin surconsommation':dDate2_list, 'Talon surconso identifie':dsurconso_identifie, 'impact':ddefrence_list,'NbrHeures':dNbrHeure_list, 'NbrNuits':dNbrNuit, 'Impact conso (kWh)':Impact_conso, '% Surconso':perSurconso, "Période d'alerte":Periode, 'Start_time':dstartt_list})

        for index, row in df_Fusion.iterrows():
            anomaly_instance = Anomaly(
                site_id=id,
                start_date=row['Début surconsommation'],
                end_date=row['Fin surconsommation'],
                consumption_value=row['Talon surconso identifie'],
                nbr_hour_consumption=row['NbrHeures'],
                nbr_days_consumption=row['NbrNuits'],
                start_time=row['Start_time'],
                impact_consumption=row['Impact conso (kWh)'],
                period_type=row["Période d'alerte"]
            )

            # add to the session instance
            session.add(anomaly_instance)

        # Commit the changes to the db
        session.commit()

        for index, row in df_dimOut.iterrows():
            anomaly_instance = Anomaly(
                site_id=id,
                start_date=row['Début surconsommation'],
                end_date=row['Fin surconsommation'],
                consumption_value=row['Talon surconso identifie'],
                nbr_hour_consumption=row['NbrHeures'],
                nbr_days_consumption=row['NbrNuits'],
                start_time=row['Start_time'],
                impact_consumption=row['Impact conso (kWh)'],
                period_type=row["Période d'alerte"]
            )

            # add to the session instance
            session.add(anomaly_instance)

        # Commit the changes to the db
        session.commit()



        # close the session
        session.close()
        
        # writer = pd.ExcelWriter(f'{code}.xlsx', engine='xlsxwriter')

        # df_dimOut.to_excel(writer, sheet_name='dim', index=False)
        # df_Fusion.to_excel(writer, sheet_name='Nuit', index=False)

        # #writer.save()
        # writer.close()


           



