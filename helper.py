import functools

import numpy as np
#from st_files_connection import FilesConnection
import gcsfs

from google.cloud import storage
import os
import io
from io import StringIO
from io import BytesIO
import time
import random
import base64

import pandas as pd

from requests import get
from collections import defaultdict
import json
import xml.etree.ElementTree as ET

import datetime as dt
#from pyzbar import pyzbar

#from streamlit_extras.dataframe_explorer import dataframe_explorer
import math

import requests
from bs4 import BeautifulSoup
from PIL import Image
import plotly.graph_objects as go
import re
import tempfile
import plotly.graph_objects as go
import pydeck as pdk
from pandas.tseries.offsets import BDay
import calendar
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
#from IPython.display import IFrame
from reportlab.platypus import Table, TableStyle
import pypdfium2 as pdfium

@functools.lru_cache
def gcp_download(bucket_name, source_file_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_file_name)
    data = blob.download_as_text()
    return data


@functools.lru_cache
def gcp_download_x(bucket_name, source_file_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_file_name)
    data = blob.download_as_bytes()
    return data
@functools.lru_cache
def gcp_csv_to_df(bucket_name, source_file_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_file_name)
    data = blob.download_as_bytes()
    df = pd.read_csv(io.BytesIO(data),index_col=None)
    print(f'Pulled down file from bucket {bucket_name}, file name: {source_file_name}')
    return df
@functools.lru_cache
def list_cs_files_f(bucket_name, folder_name):
    storage_client = storage.Client()

    # List all blobs in the bucket
    blobs = storage_client.list_blobs(bucket_name)

    # Filter blobs that are within the specified folder
    folder_files = [blob.name for blob in blobs if blob.name.startswith(folder_name)]

    return folder_files
@functools.lru_cache
def list_files_in_folder(bucket_name, folder_name):
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(bucket_name, prefix=folder_name)

    # Extract only the filenames without the folder path
    filenames = [blob.name.split("/")[-1] for blob in blobs if "/" in blob.name]

    return filenames

@functools.lru_cache
def list_files_in_subfolder(bucket_name, folder_name):
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(bucket_name, prefix=folder_name, delimiter='/')

    # Extract only the filenames without the folder path
    filenames = [blob.name.split('/')[-1] for blob in blobs]

    return filenames
@functools.lru_cache
def get_weather():
    weather=defaultdict(int)
    headers = { 
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36', 
            'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 
            'Accept-Language' : 'en-US,en;q=0.5', 
            'Accept-Encoding' : 'gzip', 
            'DNT' : '1', # Do Not Track Request Header 
            'Connection' : 'close' }

    url='http://api.weatherapi.com/v1/forecast.json?key=5fa3f1f7859a415b9e6145743230912&q=98501&days=7'
    #response = get(url,headers=headers)
    response=get(url,headers=headers)
    #data = json.loads(response.text)
    data=json.loads(response.text)
    print(data)
    return data
@functools.lru_cache
def get_gov_weather():
    weather=defaultdict(int)
    headers = { 
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36', 
            'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 
            'Accept-Language' : 'en-US,en;q=0.5', 
            'Accept-Encoding' : 'gzip', 
            'DNT' : '1', # Do Not Track Request Header 
            'Connection' : 'close' }
    url ='https://api.weather.gov/gridpoints/SEW/117,51/forecast/hourly'
    #url='https://api.weather.gov/points/47.0379,-122.9007'   #### check for station info with lat/long
    durl='https://api.weather.gov/alerts?zone=WAC033'
    response = get(url,headers=headers)
    desponse=get(durl)
    data = json.loads(response.text)
    datan=json.loads(desponse.text)
    #print(data)

    for period in data['properties']['periods']:
        #print(period)
        date=datetime.datetime.strptime(period['startTime'],'%Y-%m-%dT%H:%M:%S-08:00')
        date_f=datetime.datetime.strftime(datetime.datetime.strptime(period['startTime'],'%Y-%m-%dT%H:%M:%S-08:00'),"%b-%d,%a %H:%M")
        weather[date_f]={'Wind_Direction':f'{period["windDirection"]}','Wind_Speed':f'{period["windSpeed"]}',
                      'Temperature':f'{period["temperature"]}','Sky':f'{period["shortForecast"]}',
                       'Rain_Chance':f'{period["probabilityOfPrecipitation"]["value"]}'
                      }
        

    forecast=pd.DataFrame.from_dict(weather,orient='index')
    forecast.Wind_Speed=[int(re.findall(f'\d+',i)[0]) for i in forecast.Wind_Speed.values]
    #forecast['Vector']=[vectorize(parse_angle(i),j) for i,j in zip(forecast.Wind_Direction.values,forecast.Wind_Speed.values)]
    return forecast
