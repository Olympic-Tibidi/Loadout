import streamlit as st
import streamlit.components.v1 as components
#import cv2
import numpy as np
#from st_files_connection import FilesConnection
import gcsfs
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
import streamlit_authenticator as sa
from google.cloud import storage
import os
import io
from io import StringIO
from io import BytesIO
import time
import random
import base64
import streamlit_authenticator as stauth
#from camera_input_live import camera_input_live
import pandas as pd
import datetime
from requests import get
from collections import defaultdict
import json
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt
#from pyzbar import pyzbar
import pickle
import yaml
from yaml.loader import SafeLoader
#from streamlit_extras.dataframe_explorer import dataframe_explorer
import math
import plotly.express as px               #to create interactive charts
import plotly.graph_objects as go         #to create interactive charts
import zipfile
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
#import streamlit_option_menu
#from streamlit_modal import Modal

from helper import gcp_download
from helper import gcp_download_x
from helper import gcp_csv_to_df
from helper import list_cs_files_f
from helper import list_files_in_folder
from helper import list_files_in_subfolder
from helper import get_weather
from helper import get_gov_weather


#import streamlit_option_menu
#from streamlit_modal import Modal

st.set_page_config(layout="wide")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "client_secrets.json"

target_bucket="olym_suzano"
utc_difference=8

dada=True
if dada:
    
    st.header("OLYMPIA TIDES")
    st.subheader("LIVE FROM NOAA API  - STATION 9446969")
    st.write("Don't go further ahead than 1 year")
    
    a1,a2,a3=st.columns([2,2,6])
    with a1:
        begin_date=st.date_input("FROM")
    with a2:
        end_date=st.date_input("TO",key="erresa")
   
    

    begin_date=dt.datetime.strftime(begin_date,"%Y%m%d")
    end_date=dt.datetime.strftime(end_date,"%Y%m%d")
    
    url = f'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date={begin_date}&end_date={end_date}&station=9446969&product=predictions&datum=MLLW&time_zone=lst_ldt&interval=hilo&units=english&application=DataAPI_Sample&format=xml'
    headers = { 
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36', 
                    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 
                    'Accept-Language' : 'en-US,en;q=0.5', 
                    'Accept-Encoding' : 'gzip', 
                    'DNT' : '1', # Do Not Track Request Header 
                    'Connection' : 'close' }
    # Send a GET request to the URL and retrieve the response
    response = requests.get(url,headers=headers)
    soup = BeautifulSoup(response.content, 'html5lib')

    # Find all the <a> tags in the HTML content
    tides=defaultdict()

    link_tags = soup.find_all('pr')
    #print(link_tags)
    tides["Time"]=[]
    tides["Tide"]=[]
    tides["Height"]=[]
    for i in link_tags:
        tides["Time"].append(i.get("t"))
        tides["Tide"].append(i.get("type"))
        tides["Height"].append(i.get("v"))
    tides=pd.DataFrame(tides)
    tides["Tide"]=["Low" if i=="L" else "High" for i in tides["Tide"]]
    #print(tides["Time"].dtype)
    tides["Time"]=[dt.datetime.strftime(dt.datetime.strptime(i,"%Y-%m-%d %H:%M"),"%B-%d,%a--%H:%M") for i in tides["Time"]]
    tides.set_index("Time",drop=True,inplace=True)
    #st.table(tides)
    html_data=tides.to_html()
    st.markdown(html_data, unsafe_allow_html=True)    
    st.download_button(
                        label="Download as HTML",
                        data=html_data,
                        file_name="tides_data.html",
                        mime="text/html"
                    )
