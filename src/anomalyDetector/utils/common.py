import os
from box.exceptions import BoxValueError
import numpy as np
from sklearn.base import BaseEstimator, ClusterMixin
import pandas as pd
import yaml
from anomalyDetector import logger
import json
import joblib
from ensure import ensure_annotations
from box import ConfigBox
from pathlib import Path
from typing import Any
import base64
import calendar
from datetime import datetime


@ensure_annotations
def read_yaml(path_to_yaml: Path) -> ConfigBox:
    """reads yaml file and returns

    Args:
        path_to_yaml (str): path like input

    Raises:
        ValueError: if yaml file is empty
        e: empty file

    Returns:
        ConfigBox: ConfigBox type
    """
    try:
        with open(path_to_yaml) as yaml_file:
            content = yaml.safe_load(yaml_file)
            logger.info(f"yaml file: {path_to_yaml} loaded successfully")
            return ConfigBox(content)
    except BoxValueError:
        raise ValueError("yaml file is empty")
    except Exception as e:
        raise e
    


@ensure_annotations
def create_directories(path_to_directories: list, verbose=True):
    """create list of directories

    Args:
        path_to_directories (list): list of path of directories
        ignore_log (bool, optional): ignore if multiple dirs is to be created. Defaults to False.
    """
    for path in path_to_directories:
        os.makedirs(path, exist_ok=True)
        if verbose:
            logger.info(f"created directory at: {path}")


@ensure_annotations
def save_json(path: Path, data: dict):
    """save json data

    Args:
        path (Path): path to json file
        data (dict): data to be saved in json file
    """
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

    logger.info(f"json file saved at: {path}")




@ensure_annotations
def load_json(path: Path) -> ConfigBox:
    """load json files data

    Args:
        path (Path): path to json file

    Returns:
        ConfigBox: data as class attributes instead of dict
    """
    with open(path) as f:
        content = json.load(f)

    logger.info(f"json file loaded succesfully from: {path}")
    return ConfigBox(content)


@ensure_annotations
def save_bin(data: Any, path: Path):
    """save binary file

    Args:
        data (Any): data to be saved as binary
        path (Path): path to binary file
    """
    joblib.dump(value=data, filename=path)
    logger.info(f"binary file saved at: {path}")


@ensure_annotations
def load_bin(path: Path) -> Any:
    """load binary data

    Args:
        path (Path): path to binary file

    Returns:
        Any: object stored in the file
    """
    data = joblib.load(path)
    logger.info(f"binary file loaded from: {path}")
    return data

@ensure_annotations
def get_size(path: Path) -> str:
    """get size in KB

    Args:
        path (Path): path of the file

    Returns:
        str: size in KB
    """
    size_in_kb = round(os.path.getsize(path)/1024)
    return f"~ {size_in_kb} KB"


def decodeImage(imgstring, fileName):
    imgdata = base64.b64decode(imgstring)
    with open(fileName, 'wb') as f:
        f.write(imgdata)
        f.close()


def encodeImageIntoBase64(croppedImagePath):
    with open(croppedImagePath, "rb") as f:
        return base64.b64encode(f.read())


def toZero(x):
    try:
        converted_value = int(x)
    except ValueError:
        converted_value = 0
    return converted_value

def findDay(date):
    day, month, year = (int(i) for i in date.split('/'))
    dayNumber = calendar.weekday(year, month, day)
    return dayNumber

def arrondir_multiple_de_5(nombre):
    multiple_de_5 = round(nombre / 5) * 5
    return multiple_de_5    


def meme_semaine(date1, date2):
    # Convertir les chiffres en objets datetime
    dt1 = datetime.strptime(" ".join(map(lambda x: str(int(x)), date1)), "%m %d %Y")
    dt2 = datetime.strptime(" ".join(map(lambda x: str(int(x)), date2)), "%m %d %Y")

    # Vérifier si les deux dates appartiennent à la même semaine
    return dt1.isocalendar()[1] == dt2.isocalendar()[1] and dt1.year == dt2.year

    
def custom_clustering(X, date_margin, consumption_margin, hours_margin):
    clusters = []
    remaining_points = X.copy()

    while len(remaining_points) > 0:
        current_point = remaining_points[0]
        cluster = [current_point]
        remaining_points = np.delete(remaining_points, 0, axis=0)
        i = 0


        while i < len(remaining_points):
            point = remaining_points[i]
            d1 = [current_point[5], current_point[4], current_point[6]]
            d2 = [point[5], point[4], point[6]]


            if (abs(point[1] - current_point[1]) == date_margin and
                abs(point[2] - current_point[2]) <= consumption_margin and
                abs(point[3] - current_point[3]) <= hours_margin and
                meme_semaine(d1, d2)):

                current_point = point
                cluster.append(point)
                remaining_points = np.delete(remaining_points, i, axis=0)
            else:
                i += 1

            

        clusters.append(cluster)

    return clusters
def create_cluster_dataframe(clusters):
    cluster_data=[]
    for cluster in clusters:
        consomption_mean = np.mean([point[2] for point in cluster])
        hours_mean = np.mean([point[3] for point in cluster])
        count = len(cluster)
        cluster_data.append([consomption_mean ,hours_mean , count])
    df = pd.DataFrame(cluster_data, columns=['Mean Consomption' , 'Mean Hours', 'Count'])
    return df    


class TimeMarginClustering(BaseEstimator, ClusterMixin):
    def __init__(self, time_margin=10, value_margin=20):
        self.time_margin = time_margin
        self.value_margin = value_margin
        self.labels_ = None

    def fit(self, df):

        # Sort the data based on the datetime column
        df["date_time"] = pd.to_datetime(df["date_time"])
        df = df.sort_values("date_time").reset_index(drop=True)

        # Initialize variables for clustering
        cluster_labels = np.zeros(len(df), dtype=int)
        current_cluster = 0
        prev_time = df.loc[0, "date_time"]
        prev_value = df.loc[0, "real_consumption"]

        # Iterate over the sorted data and assign cluster labels
        for i in range(len(df)):
            time = df.loc[i, "date_time"]
            value = df.loc[i, "real_consumption"]

            # Check if the time difference exceeds the time margin
            time_diff = (time - prev_time).seconds // 60  # Convert timedelta to minutes
            if time_diff > self.time_margin:
                current_cluster += 1

            # Check if the value difference exceeds the value margin
            value_diff = abs(value - prev_value)
            if time_diff <= self.time_margin and value_diff > self.value_margin:
                current_cluster += 1

            # Assign the cluster label
            cluster_labels[i] = current_cluster

            # Update previous time and value
            prev_time = time
            prev_value = value

        # Assign the cluster labels to the algorithm's attribute
        self.labels_ = cluster_labels
        return self

    def fit_predict(self, X):
        self.fit(X)
        return self.labels_

    def predict(self, X):
        return self.fit_predict(X)