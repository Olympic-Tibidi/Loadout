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


st.caption("Live Data for Olympia From Weather.gov API")
gov_forecast=get_weather()
data=dict()
for day in forecast['forecast']['forecastday']:
    data[day['date']]={}
    data[day['date']]['DAY']={}
    data[day['date']]['ASTRO']={}
    for item in day['day']:
        data[day['date']]['DAY'][item]=day['day'][item]
    for astro in day['astro']:
        data[day['date']]['ASTRO'][astro]=day['astro'][astro]
    for dic in day['hour']:
        data[day['date']][dic['time']]={}
        for measure in dic:
            if measure=='condition':
                data[day['date']][dic['time']][measure]=dic[measure]['text']
                data[day['date']][dic['time']]['condition_png']=dic[measure]['icon']
            else:
                data[day['date']][dic['time']][measure]=dic[measure]
index=[]
temperatures=[]
condition=[]
wind=[]
wind_dir=[]
pressure=[]
cloud=[]
rain=[]
dew_point=[]
will_rain=[]
chance_rain=[]
for day in data:
    for hour in data[day]:
        if hour not in ['DAY','ASTRO']:
            #print(hour)
            index.append(hour)
            temperatures.append(data[day][hour]['temp_f'])
            condition.append(data[day][hour]['condition'])
            wind.append(data[day][hour]['wind_mph'])
            wind_dir.append(data[day][hour]['wind_dir'])
            pressure.append(data[day][hour]['pressure_mb'])
            cloud.append(data[day][hour]['cloud'])
            rain.append(data[day][hour]['precip_in'])
            will_rain.append(True if data[day][hour]['will_it_rain']==1 else False)
            chance_rain.append(data[day][hour]['chance_of_rain'])
            dew_point.append(data[day][hour]['dewpoint_f'])    
weather_tab1,weather_tab2=st.tabs(["TABULAR","GRAPH"])
with weather_tab1:
    temperatures_=["{:.1f}".format(number)for number in temperatures]
    rain_=["{:.2f}".format(number)for number in rain]
    weather_df=pd.DataFrame({'Temperature':temperatures_,"Sky":condition,'Rain Amount':rain_,
    'Chance of Rain':chance_rain,"Wind":[f"{i}-{j}" for i,j in zip(wind_dir,wind)]
    },index=index)
    
    st.table(weather_df)
with weather_tab2:
    st.markdown('Powered by <a href="https://www.weatherapi.com/" title="Free Weather API">WeatherAPI.com</a>',unsafe_allow_html=True)
    
    
    fig = go.Figure()

    # Add traces for each weather parameter
    fig.add_trace(go.Bar(x=index, y=temperatures, name='Temperature'))
    fig.add_trace(go.Scatter(x=index, y=wind, mode='markers', name='Wind Speed'))
    fig.add_trace(go.Scatter(x=index, y=pressure, mode='lines', name='Pressure'))
    fig.add_trace(go.Bar(x=index, y=rain, name='Rain Amount'))
    fig.add_trace(go.Bar(x=index, y=chance_rain,name='Chance of Rain'))
    fig.add_trace(go.Scatter(x=index, y=cloud, mode='lines', name='Cloud Cover'))
    # Add traces for other weather parameters...
    rain_threshold = 0.02
    fig.add_shape(
        dict(
            type='line',
            x0=min(index),
            x1=max(index),
            y0=rain_threshold,
            y1=rain_threshold,
            line=dict(color='red', width=2),
            visible='Rain Amount' in [trace.name for trace in fig.data],  # Show only when Rain graph is selected
        )
    )
    fig.add_annotation(
            go.layout.Annotation(
                x=0.5,  # Set x to the middle of the x-axis (adjust as needed)
                y=rain_threshold+0.005,
                xref='paper',
                yref='y',
                text=f'{rain_threshold} inches/h',
                showarrow=False,
                font=dict(color='red', size=14),
            )
        )
    # Create a dropdown menu for selecting weather parameters
    button_list = []
    for parameter in ['Temperature', 'Wind Speed','Rain Amount','Chance of Rain','Cloud Cover', 'Pressure']:
        button_list.append(dict(label=parameter, method='update', args=[{'visible': [trace.name == parameter for trace in fig.data]}]))
    
    # Add a "Show All" button
    button_list.append(dict(label='Show All', method='update', args=[{'visible': [True] * len(fig.data)}]))
    
    # Update layout to include the dropdown menu
    fig.update_layout(
        updatemenus=[
            dict(
                type='dropdown',
                showactive=True,
                buttons=button_list,
                x=0.5,
                xanchor='left',
                y=1.15,
                yanchor='top',
            ),
        ]
    )
    
    # Update layout for better readability
    fig.update_layout(title='PORT OF OLYMPIA Weather Forecast',
                      xaxis_title='Hour',
                      yaxis_title='Value',
                      template='plotly_white',
                      width=900, 
                      height=600)
    st.plotly_chart(fig)
