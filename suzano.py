import streamlit as st
import streamlit as st
from streamlit_profiler import Profiler
#from st_files_connection import FilesConnection

import streamlit.components.v1 as components

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
from PIL import Image
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
from docx import Document
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
import csv

import re
import tempfile
import plotly.graph_objects as go

from pandas.tseries.offsets import BDay
import calendar
from google.cloud import documentai
from google.oauth2 import service_account



#credentials = service_account.Credentials.from_service_account_info(st.secrets["gcs_connections"])

#client = documentai.DocumentProcessorServiceClient(credentials=credentials)
gcp_service_account_info = st.secrets["gcs_connections"]

def get_storage_client():
    # Create a storage client using the credentials
    storage_client = storage.Client.from_service_account_info(gcp_service_account_info)
    return storage_client
project_id = "Newsuz"



st.set_page_config(layout="wide")

#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "client_secrets.json"
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = st.secrets['private_key']

target_bucket="new_suzano"
utc_difference=7

def check_password():
    """Returns `True` if the user had a correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if (
            st.session_state["username"] in st.secrets["passwords"]
            and st.session_state["password"]
            == st.secrets["passwords"][st.session_state["username"]]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store username + password
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        user=st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return "No",user
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        user=st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 User not known or password incorrect")
        return "No",user
    else:
        # Password correct.
        return "Yes",user



def output():
    #with open(fr'Suzano_EDI_{a}_{release_order_number}.txt', 'r') as f:
    with open('placeholder.txt', 'r') as f:
        output_text = f.read()
    return output_text

def send_email(subject, body, sender, recipients, password):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)

    # Attach the body of the email as text
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())
    #print("Message sent!")


def send_email_with_attachment(subject, body, sender, recipients, password, file_path,file_name):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)

    # Attach the body of the email as text
    msg.attach(MIMEText(body, 'plain'))

    # Read the file content and attach it as a text file
    with open(file_path, 'r') as f:
        attachment = MIMEText(f.read())
    attachment.add_header('Content-Disposition', 'attachment', filename=file_name)
    msg.attach(attachment)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())
    print("Message sent!")

def gcp_download(bucket_name, source_file_name):
    #storage_client = storage.Client()
    storage_client = get_storage_client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_file_name)
    data = blob.download_as_text()
    return data
# def gcp_download_new(bucket_name, source_file_name):
#     conn = st.connection('gcs', type=FilesConnection)
#     a = conn.read(f"{bucket_name}/{source_file_name}", ttl=600)
#     return a
def gcp_download_x(bucket_name, source_file_name):
    #storage_client = storage.Client()
    storage_client = get_storage_client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_file_name)
    data = blob.download_as_bytes()
    return data

def gcp_csv_to_df(bucket_name, source_file_name):
    #storage_client = storage.Client()
    storage_client = get_storage_client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_file_name)
    data = blob.download_as_bytes()
    df = pd.read_csv(io.BytesIO(data),index_col=None)
    print(f'Pulled down file from bucket {bucket_name}, file name: {source_file_name}')
    return df
@st.cache(allow_output_mutation=True)
def download_model(bucket_name, source_blob_name, destination_file_name):
    """Downloads a model from the bucket."""
    # Initialize a storage client
    storage_client = storage.Client()
    # Get the bucket
    bucket = storage_client.bucket(bucket_name)
    # Construct a blob
    blob = bucket.blob(source_blob_name)
    # Download the blob to a temporary local file
    blob.download_to_filename(destination_file_name)
    print(f"Downloaded storage object {source_blob_name} from bucket {bucket_name} to local file {destination_file_name}.")
    # Load the model
    model = load_model(destination_file_name)
    return model


def upload_cs_file(bucket_name, source_file_name, destination_file_name): 
    #storage_client = storage.Client()
    storage_client = get_storage_client()

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(destination_file_name)
    blob.upload_from_filename(source_file_name)
    return True
    
def upload_json_file(bucket_name, source_file_name, destination_file_name): 
    #storage_client = storage.Client()
    storage_client = get_storage_client()

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(destination_file_name)
    blob.upload_from_filename(source_file_name,content_type="application/json")
    return True
def upload_xl_file(bucket_name, uploaded_file, destination_blob_name):
    #storage_client = storage.Client()
    storage_client = get_storage_client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    uploaded_file.seek(0)

    # Upload the file from the file object provided by st.file_uploader
    blob.upload_from_file(uploaded_file)

def list_cs_files(bucket_name): 
    #storage_client = storage.Client()
    storage_client = get_storage_client()

    file_list = storage_client.list_blobs(bucket_name)
    file_list = [file.name for file in file_list]

    return file_list

def list_cs_files_f(bucket_name, folder_name):
   # storage_client = storage.Client()
    storage_client = get_storage_client()

    # List all blobs in the bucket
    blobs = storage_client.list_blobs(bucket_name)

    # Filter blobs that are within the specified folder
    folder_files = [blob.name for blob in blobs if blob.name.startswith(folder_name)]

    return folder_files

def list_files_in_folder(bucket_name, folder_name):
    #storage_client = storage.Client()
    storage_client = get_storage_client()
    blobs = storage_client.list_blobs(bucket_name, prefix=folder_name)

    # Extract only the filenames without the folder path
    filenames = [blob.name.split("/")[-1] for blob in blobs if "/" in blob.name]

    return filenames

def list_files_in_subfolder(bucket_name, folder_name):
    #storage_client = storage.Client()
    storage_client = get_storage_client()
    blobs = storage_client.list_blobs(bucket_name, prefix=folder_name, delimiter='/')

    # Extract only the filenames without the folder path
    filenames = [blob.name.split('/')[-1] for blob in blobs]

    return filenames
def store_release_order_data(data,release_order_number,destination,po_number,sales_order_item,vessel,batch,ocean_bill_of_lading,grade,dryness,carrier_code,unitized,total):
       
    # Create a dictionary to store the release order data
    data[release_order_number]={
        
        
        'destination':destination,
        "po_number":po_number,
        "complete":False,
        sales_order_item: {
        "vessel":vessel,
        "batch": batch,
        "ocean_bill_of_lading": ocean_bill_of_lading,
        "grade": grade,
        "dryness":dryness,
        "carrier_code": carrier_code,
        "unitized":unitized,
        "total":total,
         "shipped":0,
        "remaining":total       
        }}              
    
    
                         

    # Convert the dictionary to JSON format
    json_data = json.dumps(data)
    return json_data
#release_order_database,release_order_number,sales_order_item_add,vessel_add,batch_add,ocean_bill_of_lading_add,grade_add,dryness_add,carrier_code_add,unitized_add,quantity_add,shipped_add,remaining_add
def add_release_order_data(data,release_order_number,sales_order_item,vessel,batch,ocean_bill_of_lading,grade,dryness,carrier_code,unitized,total,shipped,remaining):
       
    
    if sales_order_item not in data[release_order_number]:
        data[release_order_number][sales_order_item]={}
    data[release_order_number][sales_order_item]["vessel"]= vessel
    data[release_order_number][sales_order_item]["batch"]= batch
    data[release_order_number][sales_order_item]["ocean_bill_of_lading"]= ocean_bill_of_lading
    data[release_order_number][sales_order_item]["grade"]= grade
    data[release_order_number][sales_order_item]["dryness"]= dryness
    data[release_order_number][sales_order_item]["carrier_code"]= carrier_code
    data[release_order_number][sales_order_item]["unitized"]= unitized
    data[release_order_number][sales_order_item]["total"]= total
    data[release_order_number][sales_order_item]["shipped"]= 0
    data[release_order_number][sales_order_item]["remaining"]= total
    
    
       

    # Convert the dictionary to JSON format
    json_data = json.dumps(data)
    return json_data

def edit_release_order_data(data,release_order_number,destination,po_number,sales_order_item,vessel,batch,ocean_bill_of_lading,grade,dryness,carrier_code,unitized,total,shipped,remaining):
       
    # Edit the loaded current dictionary.
    data[release_order_number][sales_order_item]["destination"]= destination
    data[release_order_number][sales_order_item]["po_number"]=po_number
    data[release_order_number][sales_order_item]["vessel"]= vessel
    data[release_order_number][sales_order_item]["batch"]= batch
    data[release_order_number][sales_order_item]["ocean_bill_of_lading"]= ocean_bill_of_lading
    data[release_order_number][sales_order_item]["grade"]= grade
    data[release_order_number][sales_order_item]["dryness"]= dryness
    data[release_order_number][sales_order_item]["carrier_code"]= carrier_code
    data[release_order_number][sales_order_item]["unitized"]= unitized
    data[release_order_number][sales_order_item]["total"]= total
    data[release_order_number][sales_order_item]["shipped"]= shipped
    data[release_order_number][sales_order_item]["remaining"]= remaining
    
    
       

    # Convert the dictionary to JSON format
    json_data = json.dumps(data)
    return json_data

def process():
           
    line1="1HDR:"+a+b+terminal_code
    tsn="01" if medium=="TRUCK" else "02"
    
    tt="0001" if medium=="TRUCK" else "0002"
    if double_load:
        line21="2DTD:"+current_release_order+" "*(10-len(current_release_order))+"000"+current_sales_order+a+tsn+tt+vehicle_id+" "*(20-len(vehicle_id))+str(first_quantity*2000)+" "*(16-len(str(first_quantity*2000)))+"USD"+" "*36+carrier_code+" "*(10-len(carrier_code))+terminal_bill_of_lading+" "*(50-len(terminal_bill_of_lading))+c
        line22="2DTD:"+next_release_order+" "*(10-len(next_release_order))+"000"+next_sales_order+a+tsn+tt+vehicle_id+" "*(20-len(vehicle_id))+str(second_quantity*2000)+" "*(16-len(str(second_quantity*2000)))+"USD"+" "*36+carrier_code+" "*(10-len(carrier_code))+terminal_bill_of_lading+" "*(50-len(terminal_bill_of_lading))+c
    line2="2DTD:"+release_order_number+" "*(10-len(release_order_number))+"000"+sales_order_item+a+tsn+tt+vehicle_id+" "*(20-len(vehicle_id))+str(int(quantity*2000))+" "*(16-len(str(int(quantity*2000))))+"USD"+" "*36+carrier_code+" "*(10-len(carrier_code))+terminal_bill_of_lading+" "*(50-len(terminal_bill_of_lading))+c
               
    loadls=[]
    bale_loadls=[]
    if double_load:
        for i in first_textsplit:
            loadls.append("2DEV:"+current_release_order+" "*(10-len(current_release_order))+"000"+current_sales_order+a+tsn+i[:load_digit]+" "*(10-len(i[:load_digit]))+"0"*16+str(2000))
        for k in second_textsplit:
            loadls.append("2DEV:"+next_release_order+" "*(10-len(next_release_order))+"000"+next_sales_order+a+tsn+k[:load_digit]+" "*(10-len(k[:load_digit]))+"0"*16+str(2000))
    else:
        for k in loads:
            loadls.append("2DEV:"+release_order_number+" "*(10-len(release_order_number))+"000"+sales_order_item+a+tsn+k+" "*(10-len(k))+"0"*(20-len(str(int(loads[k]*2000))))+str(int(loads[k]*2000)))
        
        
    if double_load:
        number_of_lines=len(first_textsplit)+len(second_textsplit)+4
    else:
        number_of_lines=len(loads)+3
    end_initial="0"*(4-len(str(number_of_lines)))
    end=f"9TRL:{end_initial}{number_of_lines}"
     
    with open(f'placeholder.txt', 'w') as f:
        f.write(line1)
        f.write('\n')
        if double_load:
            f.write(line21)
            f.write('\n')
            f.write(line22)
        else:
            f.write(line2)
        f.write('\n')
        
        for i in loadls:
            
            f.write(i)
            f.write('\n')
       
        f.write(end)
def gen_bill_of_lading():
    data=gcp_download(target_bucket,rf"terminal_bill_of_ladings.json")
    bill_of_ladings=json.loads(data)
    list_of_ladings=[]
    try:
        for key in [k for k in bill_of_ladings if len(k)==8]:
            if int(key) % 2 == 0:
                list_of_ladings.append(int(key))
        bill_of_lading_number=max(list_of_ladings)+2
    except:
        bill_of_lading_number=11502400
    return bill_of_lading_number,bill_of_ladings

def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')
    
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
def vectorize(direction,speed):
    Wind_Direction=direction
    Wind_Speed=speed
    wgu = 0.1*Wind_Speed * np.cos((270-Wind_Direction)*np.pi/180)
    wgv= 0.1*Wind_Speed*np.sin((270-Wind_Direction)*np.pi/180)
    return(wgu,wgv)
                
def parse_angle(angle_str):
    angle= mpcalc.parse_angle(angle_str)
    angle=re.findall(f'\d*\.?\d?',angle.__str__())[0]
    return float(angle)
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

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.options.mode.chained_assignment = None  # default='warn'


       
    
with open('configure.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login(fields={'PORT OF OLYMPIA TOS LOGIN', 'main'})

# gcp_service_account_info = st.secrets["gcs_connections"]

# def get_storage_client():
#     # Create a storage client using the credentials
#     storage_client = storage.Client.from_service_account_info(gcp_service_account_info)
#     return storage_client

# def gcp_download(bucket_name, source_file_name):
#     storage_client = get_storage_client()
#     bucket = storage_client.bucket(bucket_name)
#     blob = bucket.blob(source_file_name)
#     data = blob.download_as_text()
#     return data

if authentication_status:
    authenticator.logout('Logout', 'main')
    if username == 'ayilmaz' or username=='gatehouse':
        st.subheader("PORT OF OLYMPIA TOS")
        st.write(f'Welcome *{name}*')
        
        #forecast=get_weather()
        
        select=st.sidebar.radio("SELECT FUNCTION",
            ('ADMIN', 'LOADOUT', 'INVENTORY'))
        # select=st.sidebar.radio("SELECT FUNCTION",
        #     ('ADMIN', 'LOADOUT', 'INVENTORY','LABOR','FINANCE',"GATE CONV.NETWORK","STORAGE"))
        custom_style = """
                    <style>
                        .custom-container {
                            background-color: #f0f0f0;  /* Set your desired background color */
                            padding: 20px;
                            border-radius: 10px;
                            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                        }
                    </style>
                """
        st.markdown(custom_style, unsafe_allow_html=True)

        
        
        if select=="ADMIN" :

            # conn = st.connection('gcs', type=FilesConnection)
            # a = conn.read(f"new_suzano/map.json", ttl=600)
            #st.write(a)
            admin_tab1,admin_tab2,admin_tab3,admin_tab4,admin_tab5=st.tabs(["RELEASE ORDERS","BILL OF LADINGS","EDI'S","AUDIT","VESSEL/MILL/CARRIER ENTRY"])
            
            with admin_tab5:   ###   Vessel Entry
                vessel=st.text_input("ENTER VESSEL NAME/VOY",key="dsd1eqx")
                uploaded_shipping_file = st.file_uploader("Upload the Shipping EDI txt file", type="txt")
                if uploaded_shipping_file:
                    def parse_edi_line(edi_line):
                        fields = {
                            'type': (0, 4),
                            'lot_number': (5, 15),
                            'grade': (15, 24),
                            'remarks': (24, 71),
                            'vessel_name': (61, 91),
                            'voyage_number': (91, 101),
                            'date': (101, 109),
                            'quantity': (109, 116),
                            'batch': (116, 129),
                            'ocean_bill_of_lading': (129, 179),
                            'admt': (179, 195)
                        }
                        
                        # Extract fields using slicing
                        parsed_data = {}
                        for field, (start, end) in fields.items():
                            if field=='quantity':
                                parsed_data[field] = int(edi_line[start:end].strip())
                            else:
                                parsed_data[field] = edi_line[start:end].strip()
                    
                        return parsed_data
                    tons=0
                    bols={}
                    #with open(uploaded_shipping_file, 'r') as infile:
                    for line in uploaded_shipping_file:
                        # Split the line into components based on space or another delimiter
                        line = line.decode('utf-8')
                        components = line.strip()  # Change split argument if using another delimiter
                        #st.write(parse_edi_line(line))
                        #st.write(components)
                        if components[0]=="2":
                            #st.write(components)
                            data=parse_edi_line(components)
                            tons+=data['quantity']
                            if data['ocean_bill_of_lading'] not in bols:
                                bols[data['ocean_bill_of_lading']]={}
                                bols[data['ocean_bill_of_lading']]['grade']=None
                                bols[data['ocean_bill_of_lading']]['grade']=data['grade']
                                bols[data['ocean_bill_of_lading']]['batch']=data['batch'].lstrip('0')
                                bols[data['ocean_bill_of_lading']]['qty']=0
                                bols[data['ocean_bill_of_lading']]['qty']+=data['quantity']/2
                                bols[data['ocean_bill_of_lading']]['admt']=float(data['admt'].lstrip("0"))/1000
                                bols[data['ocean_bill_of_lading']]['lots']=[]
                                bols[data['ocean_bill_of_lading']]['lots'].append(data['lot_number'])
                            else:
                                bols[data['ocean_bill_of_lading']]['qty']+=data['quantity']/2
                                bols[data['ocean_bill_of_lading']]['lots'].append(data['lot_number'])
                    bols_df=pd.DataFrame(bols).T
                    bols_df.columns=[["GRADE","BATCH","QUANTITY","DRYNESS","LOTS"]]
                    st.write(bols_df)
                    if st.button("REGISTER VESSEL AND LOTS",key="ddsaa"):
                        map_vessel=gcp_download(target_bucket,rf"map.json")
                        map_vessel=json.loads(map_vessel)
                        map_vessel['batch_mapping'][vessel]={i:{'batch':bols[i]['batch'],'dryness':bols[i]['admt'],
                                      'grade':bols[i]['grade'][:3],'fit':bols[i]['qty'] ,"damaged":0,"total":bols[i]['qty']} for i in bols}

                        for i in bols:
                            map_vessel['bol_mapping'][i]={'batch':bols[i]['batch'],'dryness':bols[i]['admt'],
                                                              'grade':bols[i]['grade'][:3],'fit':bols[i]['qty'] ,"damaged":0,"total":bols[i]['qty'],
                                                        'FSC':"FSC Certified Products. FSC Mix Credit IMA—COC-001470"} 
                        #st.write(map_vessel)
                        bill_mapping_vessel=gcp_download(target_bucket,rf"bill_mapping.json")
                        bill_mapping_vessel=json.loads(bill_mapping_vessel)
                        if vessel not in bill_mapping_vessel:
                            bill_mapping_vessel[vessel]={}
                        for bill,item in bols.items():
                            for i in item['lots']:
                                bill_mapping_vessel[vessel][i]={'Batch':bols[bill]['batch'],'Ocean_bl':bill}
                        storage_client = get_storage_client()
                        bucket = storage_client.bucket(target_bucket)
                        blob = bucket.blob(rf"map.json")
                        blob.upload_from_string(json.dumps(map_vessel))
                        storage_client = get_storage_client()
                        bucket = storage_client.bucket(target_bucket)
                        blob = bucket.blob(rf"bill_mapping.json")
                        blob.upload_from_string(json.dumps(bill_mapping_vessel))
                        st.success(f"Vessel and BOL data is registered")
                
            
            with admin_tab4:   ###   AUDIT
                if st.button("RUN RECORD AUDIT"):
                    
                    dfb=gcp_download(target_bucket,rf"terminal_bill_of_ladings.json")
                    dfb=json.loads(dfb)
                    dfb=pd.DataFrame.from_dict(dfb).T[1:]
                    suz=gcp_download(target_bucket,rf"suzano_report.json")
                    suz=json.loads(suz)
                    suz_frame=pd.DataFrame(suz).T
                    raw_ro=gcp_download(target_bucket,rf"release_orders/RELEASE_ORDERS.json")
                    raw_ro=json.loads(raw_ro)
                    def dict_compare(d1, d2):
                        d1_keys = set(d1.keys())
                        d2_keys = set(d2.keys())
                        shared_keys = d1_keys.intersection(d2_keys)
                        added = d1_keys - d2_keys
                        removed = d2_keys - d1_keys
                        modified = {o : (d1[o], d2[o]) for o in shared_keys if d1[o] != d2[o]}
                        same = set(o for o in shared_keys if d1[o] == d2[o])
                        return added, removed, modified, same
                    
                    def extract_bol_shipped(data,bol):
                        qt=0
                        sales_group=["001","002","003","004","005"]
                        for ro in data:
                            for sale in data[ro]:
                                if sale in sales_group and data[ro][sale]['ocean_bill_of_lading']==bol:
                                    qt+=data[ro][sale]['shipped']
                        return qt
                    def compare_dict(a, b):
                        # Compared two dictionaries..
                        # Posts things that are not equal..
                        res_compare = []
                        for k in set(list(a.keys()) + list(b.keys())):
                            if isinstance(a[k], dict):
                                z0 = compare_dict(a[k], b[k])
                            else:
                                z0 = a[k] == b[k]
                    
                            z0_bool = np.all(z0)
                            res_compare.append(z0_bool)
                            if not z0_bool:
                                if a==rel_t:
                                    st.markdown(f"**:red[Discrepancy]**")
                                    st.markdown(f"**{k} - Inventory :{a[k]} Units Shipped - BOL Report : {b[k]} Units Shipped**")
                                    
                                else:
                                    st.markdown(f"**:red[Discrepancy]**")
                                    st.markdown(f"**{k} - Suzano Report :{a[k]} Units Shipped - BOL Report : {b[k]} Units Shipped**")
                                    diff = dfb[~dfb.index.isin([str(i) for i in suz_frame['Shipment ID #']]+['11502400', '11503345', 'MF01769573*', '11503871'])].index.to_list()
                                    for i in diff:
                                        st.markdown(f"**...Shipment {i} to {dfb.loc[i,'destination']} is in BOL but not Suzano Report**") 
                        return np.all(res_compare)
               
                    suz_frame["Quantity"]=[float(i) for i in suz_frame["Quantity"]]
                    suz_t=suz_frame.groupby("Ocean BOL#")["Quantity"].sum().to_dict()
                    df_t=dfb.groupby("ocean_bill_of_lading")["quantity"].sum().to_dict()
                    #corrections due to shipment MF01769573 and 1150344 on 12-15 between Kirkenes and Juventas mixed loads.
                    suz_t['GSSWKIR6013E']=suz_t['GSSWKIR6013E']+7
                    suz_t['GSSWKIR6013D']=suz_t['GSSWKIR6013D']+9
                    suz_t['GSSWJUV8556C']=suz_t['GSSWJUV8556C']-9
                    suz_t['GSSWJUV8556A']=suz_t['GSSWJUV8556A']-7
                    
                    rel_t={i:extract_bol_shipped(raw_ro,i) for i in suz_t}
                    aud_col1,aud_col2=st.columns(2)
                    with aud_col1:
                        
                        if compare_dict(suz_t,df_t):
                            st.markdown("**:blue[All Checks Complete !]**")
                            st.markdown("**:blue[SUZANO REPORT match BILL OF LADINGS]**")       
                            st.write(f"{len(suz_frame)} Shipments")
                           

                    with aud_col2:
                        
                        if compare_dict(rel_t,df_t):
                            st.markdown("**:blue[All Checks Complete !]**")
                            st.markdown("**:blue[INVENTORY match BILL OF LADINGS]**")       
                            st.write(f"{len(suz_frame)} Shipments")
                edi_audit=st.toggle("AUDIT TODAYS EDIs AND REPORTS")
                if edi_audit:
                    
                    with st.spinner("Wait for it"):
                        guilty=None
                        def list_files_uploaded_today(bucket_name, folder_name):
                        # Initialize Google Cloud Storage client
                            storage_client = get_storage_client()
                        
                            # Get the current date
                            today = (datetime.datetime.now()-datetime.timedelta(hours=utc_difference)).date()
                            # Get the list of blobs in the specified folder
                            blobs = storage_client.list_blobs(bucket_name, prefix=folder_name)
                        
                            # Extract filenames uploaded today only
                            filenames = []
                            for blob in blobs:
                                # Check if blob's last modification date is today
                                if blob.updated.date() == today:
                                    # Extract only the filenames without the folder path
                                    filename = blob.name.split("/")[-1]
                                    filenames.append(filename)
                                time.sleep(0.001)
                        
                            return filenames
                        today_uploaded_files = list_files_uploaded_today(target_bucket,rf"EDIS/")
                        st.markdown(f"**# of EDIs Uploaded : {len(today_uploaded_files)}**")
                        st.markdown(f"EDIs Uploaded Today : {today_uploaded_files}")
                       
                        
                        base=[]
                        for i in today_uploaded_files:
                            
                            lines=gcp_download(target_bucket, rf"EDIS/{i}").splitlines()
                            
                            
                            # Step 2: Process the contents
                            data = []
                            count=1
                            line_count=0
                            dev_count=0
                            line_tonnage=0
                            unit_count=0
                            for line in lines:
                                if line.startswith("1HDR"):
                                    prefix, data = line.split(':') 
                                    assert prefix=="1HDR" , "Prefix does not match the expected value '1HDR'"
                                    date_str = data[:8]  # YYYYMMDD
                                    time_str = data[8:14]  # HHMMSS
                                    terminal_code = data[14:18]  # 4 letters
                                    datetime_obj = datetime.datetime.strptime(date_str + time_str, '%Y%m%d%H%M%S')
                                    line_count+=1
                                elif line.startswith("2DTD"):
                                    prefix, data = line.split(':') 
                                    release_order = data[:10].strip() 
                                    sales_item = data[10:16].strip() 
                                    date=data[16:24].strip()
                                    date = datetime.datetime.strptime(date, '%Y%m%d').date()
                                    transport_type=data[24:26].strip()
                                    transport_sequential=data[26:30].strip()
                                    vehicle_id=data[30:50].strip()
                                    total_tonnage=int(data[50:66].strip())
                                    carrier_code=data[105:115].strip()
                                    bill_of_lading=data[115:165].strip()
                                    eta_date=data[165:].strip()
                                    eta_date = datetime.datetime.strptime(eta_date, '%Y%m%d').date()
                                    line_count+=1
                                elif line.startswith("2DEV"):
                                    prefix, data = line.split(':')
                                    line_release_order=data[:10]
                                    line_sales_item=data[10:16].strip()
                                    line_date=data[16:24].strip()
                                    line_date = datetime.datetime.strptime(line_date, '%Y%m%d').date()
                                    transport_type=data[24:26].strip()
                                    lot_number=data[26:36].strip()
                                    line_weight=int(data[51:56].strip())
                                    line_unit_count=line_weight/2000
                                    line_tonnage+=line_weight
                                    unit_count+=line_unit_count
                                    dev_count+=1
                                    line_count+=1
                        
                                elif line.startswith("9TRL"):
                                    prefix, data = line.split(':')
                                    edi_line_count=int(data[:4])
                                    line_count+=1
                                    assert edi_line_count==line_count,f"no, line_count is {line_count}"
                                    assert line_tonnage==total_tonnage
                            base.append({'Date Shipped':datetime_obj, 'Vehicle':vehicle_id, 'Shipment ID #':bill_of_lading, 'Release #':release_order,
                                             'Carrier':carrier_code, 'Quantity':unit_count, 'Metric Ton':total_tonnage/1000})
                        
                        edis=pd.DataFrame(base)
                        edis=edis.sort_values(by="Date Shipped")
                        edis.set_index("Shipment ID #",drop=True,inplace=True)
                        
                        suz=gcp_download(target_bucket,rf"suzano_report.json")
                        suz=json.loads(suz)
                        suz_frame=pd.DataFrame(suz).T
                        suz_frame["Date"]=[datetime.datetime.strptime(i,"%Y-%m-%d %H:%M:%S").date() for i in suz_frame["Date Shipped"]]
                        suz_frame_daily=suz_frame[suz_frame.Date==(datetime.datetime.now()-datetime.timedelta(hours=utc_difference)).date()]
                        suz_frame_daily=suz_frame_daily[['Date Shipped', 'Vehicle', 'Shipment ID #', 'Release #', 'Carrier',
                                      'Quantity', 'Metric Ton',]]
                        suz_frame_daily.set_index("Shipment ID #",drop=True,inplace=True)
                        # suz_frame_daily.loc["MF01799999"]={"Date Shipped":"2024-03-28 12:26:58","Vehicle":"3423C",
                        #                                            "Shipment ID #":"MF01799420","Release #":"3172295",
                        #                                        "Carrier":"123456","Quantity":14.0,"Metric Ton":28.0}
                        more=None
                        if len(edis)!=len(suz_frame_daily):
                            diff=abs(len(edis)-len(suz_frame_daily))
                            if len(edis)<len(suz_frame_daily):
                                more=suz_frame_daily.copy()
                                guilty="edis"
                                for i in range(diff):
                                    edis.loc[len(edis)]=None
                            else:
                                more=edis.copy()
                                guilty="suz_frame_daily"
                        
                        
                        difference = (edis.index!=suz_frame_daily.index)
                        
                        
                        
                        if guilty=="edis":
                            more=more[difference]
                            st.markdown("**:red[Following Shipment from Suzano Report is Missing an EDI]**")
                            st.write(more)
                        elif guilty=="suz_frame_daily":
                            more=more[difference]
                            st.markdown("**:red[Following EDI is Missing in Suzano Report]**")
                            st.write(more)
                        else:
                            st.success("All EDIs and Suzano Report Entries are accounted for!! ")  
                            
            with admin_tab2:   #### BILL OF LADINGS
                bill_data=gcp_download(target_bucket,rf"terminal_bill_of_ladings.json")
                bill_data_reverse=json.loads(bill_data)
                admin_bill_of_ladings=pd.DataFrame.from_dict(bill_data_reverse).T[1:]
                admin_bill_of_ladings["St_Date"]=[datetime.datetime.strptime(i,"%Y-%m-%d %H:%M:%S").date() for i in admin_bill_of_ladings["issued"]]
                release_order_database=gcp_download(target_bucket,rf"release_orders/RELEASE_ORDERS.json")
                release_order_database=json.loads(release_order_database)
                suzano_report=gcp_download(target_bucket,rf"suzano_report.json")
                suzano_report=json.loads(suzano_report)
                try:
                    voided_shipments=gcp_download(target_bucket,rf"voided_shipments.json")
                    voided_shipments=json.loads(voided_shipments)
                except:
                    voided_shipments={}
                def convert_df(df):
                    # IMPORTANT: Cache the conversion to prevent computation on every rerun
                    return df.to_csv().encode('utf-8')
                use=True
                if use:
                    now=datetime.datetime.now()-datetime.timedelta(hours=utc_difference)
                    
                    choose = st.radio(
                                    "Select Today's Bill of Ladings or choose by Date or choose ALL",
                                    ["DAILY", "ACCUMULATIVE", "FIND BY DATE"],key="wewas")
                    if choose=="DAILY":
                        display_df=admin_bill_of_ladings[admin_bill_of_ladings["St_Date"]==now.date()]
                        st.dataframe(display_df)
                        file_name=f'OLYMPIA_DAILY_BILL_OF_LADINGS-{datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%m-%d,%Y")}.csv'
                    elif choose=="FIND BY DATE":
                        required_date=st.date_input("CHOOSE DATE",key="dssar")
                        display_df=admin_bill_of_ladings[admin_bill_of_ladings["St_Date"]==required_date]
                        st.dataframe(display_df)
                        file_name=f'OLYMPIA_BILL_OF_LADINGS_FOR-{datetime.datetime.strftime(required_date,"%m-%d,%Y")}.csv'
                    else:
                        display_df=admin_bill_of_ladings
                        st.write("DATA TOO LARGE, DOWNLOAD INSTEAD")
                        file_name=f'OLYMPIA_ALL_BILL_OF_LADINGS to {datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%m-%d,%Y")}.csv'
                    csv=convert_df(display_df)
                    bilo1,bilo2,bilo3=st.columns([3,3,3])
                    with bilo1:
                        st.download_button(
                            label="DOWNLOAD BILL OF LADINGS",
                            data=csv,
                            file_name=file_name,
                            mime='text/csv')
                    with bilo2:
                        if display_df.shape[0]>0:
                            entry=st.selectbox("SELECT SHIPMENT TO CREATE THE EDI", [i for i in display_df.index])
                            entry=display_df.loc[entry].to_dict()
                            terminal_bill_of_lading=entry["edi_no"].split(".")[0]
                            def make_edi(entry):
                                loads={}
                                for load in entry['loads']:
                                    load_=load[:-3]
                                    if load_ not in loads:
                                        loads[load_]=0
                                        loads[load_]=entry["loads"][load]
                                    else:
                                        loads[load_]+=entry["loads"][load]
                                double_load=False
                                terminal_bill_of_lading=entry["edi_no"].split(".")[0]
                                a=datetime.datetime.strptime(entry["issued"], '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d')#%H%M%S')
                                b=datetime.datetime.strptime(entry["issued"], '%Y-%m-%d %H:%M:%S').strftime('%H%M%S')
                                
                                line1="1HDR:"+a+b+"OLYM"
                                tsn="01" 
                                tt="0001"
                                # if double_load:
                                #     line21="2DTD:"+entry["release_order"]+" "*(10-len(current_release_order))+"000"+current_sales_order+a+tsn+tt+vehicle_id+" "*(20-len(vehicle_id))+str(first_quantity*2000)+" "*(16-len(str(first_quantity*2000)))+"USD"+" "*36+carrier_code+" "*(10-len(carrier_code))+terminal_bill_of_lading+" "*(50-len(terminal_bill_of_lading))+c
                                #     line22="2DTD:"+entry["release_order"]+" "*(10-len(next_release_order))+"000"+next_sales_order+a+tsn+tt+vehicle_id+" "*(20-len(vehicle_id))+str(second_quantity*2000)+" "*(16-len(str(second_quantity*2000)))+"USD"+" "*36+carrier_code+" "*(10-len(carrier_code))+terminal_bill_of_lading+" "*(50-len(terminal_bill_of_lading))+c
                                line2="2DTD:"+entry["release_order"]+" "*(10-len(entry["release_order"]))+"000"+entry["sales_order"]+a+tsn+tt+entry["vehicle"]+" "*(20-len(entry["vehicle"]))+str(int(entry["quantity"]*2000))+" "*(16-len(str(int(entry["quantity"]*2000))))+"USD"+" "*36+entry["carrier_id"]+" "*(10-len(str(entry["carrier_id"])))+terminal_bill_of_lading+" "*(50-len(terminal_bill_of_lading))+a
                            
                                loadls=[]
                                bale_loadls=[]
                                if double_load:
                                    for i in first_textsplit:
                                        loadls.append("2DEV:"+current_release_order+" "*(10-len(current_release_order))+"000"+current_sales_order+a+tsn+i[:load_digit]+" "*(10-len(i[:load_digit]))+"0"*16+str(2000))
                                    for k in second_textsplit:
                                        loadls.append("2DEV:"+next_release_order+" "*(10-len(next_release_order))+"000"+next_sales_order+a+tsn+k[:load_digit]+" "*(10-len(k[:load_digit]))+"0"*16+str(2000))
                                else:
                                    for k in loads:
                            
                                        loadls.append("2DEV:"+entry["release_order"]+" "*(10-len(entry["release_order"]))+"000"+entry["sales_order"]+a+tsn+k+" "*(10-len(k))+"0"*(20-len(str(int(loads[k]*2000))))+str(int(loads[k]*2000)))
                            
                            
                                if double_load:
                                    number_of_lines=len(first_textsplit)+len(second_textsplit)+4
                                else:
                                    number_of_lines=len(loadls)+3
                                end_initial="0"*(4-len(str(number_of_lines)))
                                end=f"9TRL:{end_initial}{number_of_lines}"
                            
                                with open(f'{terminal_bill_of_lading}.txt', 'w') as f:
                                    f.write(line1)
                                    f.write('\n')
                                    if double_load:
                                        f.write(line21)
                                        f.write('\n')
                                        f.write(line22)
                                    else:
                                        f.write(line2)
                                    f.write('\n')
                            
                                    for i in loadls:
                            
                                        f.write(i)
                                        f.write('\n')
                            
                                    f.write(end)
                                with open(f'{terminal_bill_of_lading}.txt', 'r') as f:
                                    file_content=f.read()
                                file_name=f'{terminal_bill_of_lading}.txt'
                                return file_content,file_name
                            file_content,file_name=make_edi(entry)
                            st.download_button(
                                label="CREATE EDI FOR THIS SHIPMENT",
                                data=file_content,
                                file_name=file_name,
                                mime='text/csv',key="53432")
                    
                    with bilo3:
                        if display_df.shape[0]>0:
                            
                            to_reverse=st.selectbox("SELECT SHIPMENT TO VOID", [i if len(display_df)>0 else None for i in display_df.index ])
                            
                            if st.button("VOID SHIPMENT"):
                                voided_shipments[to_reverse]={}
                                voided_shipments[to_reverse]=display_df.loc[to_reverse].to_dict()
                                if to_reverse!=None:
                                    to_reverse_data=display_df.loc[to_reverse].to_dict()
                                    ro_to_reverse=to_reverse_data['release_order']
                                    so_to_reverse=to_reverse_data['sales_order']
                                    qty_to_reverse=to_reverse_data['quantity']
                                release_order_database[ro_to_reverse][so_to_reverse]['shipped']-=qty_to_reverse
                                release_order_database[ro_to_reverse][so_to_reverse]['remaining']+=qty_to_reverse
                                
                                
                                storage_client = get_storage_client()
                                bucket = storage_client.bucket(target_bucket)
                                blob = bucket.blob(rf"release_orders/RELEASE_ORDERS.json")
                                blob.upload_from_string(json.dumps(release_order_database))
                                st.success(f"Release order {ro_to_reverse} updated with reversal!")
    
                                del bill_data_reverse[to_reverse]
                                storage_client = get_storage_client()
                                bucket = storage_client.bucket(target_bucket)
                                blob = bucket.blob(rf"terminal_bill_of_ladings.json")
                                blob.upload_from_string(json.dumps(bill_data_reverse))
                                st.success(f"Terminal Bill of Ladings updated with reversal!")
    
                                suz_index=next(key for key, value in suzano_report.items() if value['Shipment ID #'] == to_reverse)
                                del suzano_report[suz_index]
                                suzano_report = {i + 1: v for i, (k, v) in enumerate(suzano_report.items())}
                                
                                storage_client = get_storage_client()
                                bucket = storage_client.bucket(target_bucket)
                                blob = bucket.blob(rf"suzano_report.json")
                                blob.upload_from_string(json.dumps(suzano_report))
                                st.success(f"Suzano Report updated with reversal!")

                                del voided_shipments[to_reverse]['St_Date']
                                storage_client = get_storage_client()
                                bucket = storage_client.bucket(target_bucket)
                                blob = bucket.blob(rf"voided_shipments.json")
                                blob.upload_from_string(json.dumps(voided_shipments))
                                st.success(f"Void recorded in voided shipments!")
    
                                if to_reverse[0]=="M":
                                    mf_numbers=gcp_download(target_bucket,rf"release_orders/mf_numbers.json")
                                    mf_numbers=json.loads(mf_numbers)
                                    mf_numbers[ro_to_reverse].append(to_reverse)
                                    storage_client = get_storage_client()
                                    bucket = storage_client.bucket(target_bucket)
                                    blob = bucket.blob(rf"release_orders/mf_numbers.json")
                                    blob.upload_from_string(json.dumps(mf_numbers))
                                    st.success(f"MF Numbers entered back into RO {ro_to_reverse}!")
                                try:
                                    delete_file_from_gcs(target_bucket, f'EDIS/{to_reverse}.txt')
                                    st.success(f"Deleted EDI {to_reverse}.txt!")
                                except:
                                    st.write("NO Edis found for this shipment")
                    to_print_loads=st.selectbox("SELECT SHIPMENT TO DISPLAY LOADS", [i if len(display_df)>0 else None for i in display_df.index ])
                            
                    if st.button("DISPLAY LOADS"):     
                        st.write([key for key in display_df.loc[to_print_loads]['loads']])

                    if st.button("DISPLAY VOIDED SHIPMENTS"):     
                        st.write(voided_shipments)


                    
            
            with admin_tab3:
                edi_files=list_files_in_subfolder(target_bucket, rf"EDIS/")
                requested_edi_file=st.selectbox("SELECT EDI",edi_files[1:])
                
                display_edi=st.toggle("DISPLAY EDI")
                if display_edi:
                    data=gcp_download(target_bucket, rf"EDIS/{requested_edi_file}")
                    st.text_area("EDI",data,height=400)                                
               
                st.download_button(
                    label="DOWNLOAD EDI",
                    data=gcp_download(target_bucket, rf"EDIS/{requested_edi_file}"),
                    file_name=f'{requested_edi_file}',
                    mime='text/csv')
               
                
                
                
                    
              
                  
            
                            

            
                          
            with admin_tab1:
                map=gcp_download(target_bucket,rf"map.json")
                map=json.loads(map)
                release_order_database=gcp_download(target_bucket,rf"release_orders/RELEASE_ORDERS.json")
                release_order_database=json.loads(release_order_database)
                dispatch=gcp_download(target_bucket,rf"dispatched.json")
                dispatch=json.loads(dispatch)
                
                carrier_list=map['carriers']
                mill_info=map["mill_info"]
                      
                release_order_tab1,release_order_tab2,release_order_tab3=st.tabs(["RELEASE ORDER DATABASE","CREATE RELEASE ORDER","RELEASE ORDER STATUS"])
                
                with release_order_tab2:   ###CREATE RELEASE ORDER
                   
                    add=st.checkbox("CHECK TO ADD TO EXISTING RELEASE ORDER",disabled=False)
                    edit=st.checkbox("CHECK TO EDIT EXISTING RELEASE ORDER")
                   
                    batch_mapping=map['batch_mapping']
                    if edit:
                        
                        release_order_number=st.selectbox("SELECT RELEASE ORDER",([i for i in release_order_database]))
                        po_number_edit=st.text_input("PO No",release_order_database[release_order_number]["po_number"],disabled=False)
                        destination_edit=st.text_input("Destination",release_order_database[release_order_number]["destination"],disabled=False)
                        sales_order_item_edit=st.selectbox("Sales Order Item",[i for i in release_order_database[release_order_number] if i in ["001","002","003","004","005"]] ,disabled=False)
                        vessel_edit=vessel=st.selectbox("SELECT VESSEL",[i for i in map['batch_mapping']],key="poFpoa")
                        ocean_bill_of_lading_edit=st.selectbox("Ocean Bill Of Lading",batch_mapping[vessel_edit].keys(),key="trdfeerw") 
                        grade_edit=st.text_input("Grade",release_order_database[release_order_number][sales_order_item_edit]["grade"],disabled=True)
                        batch_edit=st.text_input("Batch No",release_order_database[release_order_number][sales_order_item_edit]["batch"],disabled=True)
                        dryness_edit=st.text_input("Dryness",release_order_database[release_order_number][sales_order_item_edit]["dryness"],disabled=True)
                        admt_edit=st.text_input("ADMT PER UNIT",round(float(batch_mapping[vessel_edit][ocean_bill_of_lading_edit]["dryness"])/90,6),True)
                        unitized_edit=st.selectbox("UNITIZED/DE-UNITIZED",["UNITIZED","DE-UNITIZED"],disabled=False)
                        quantity_edit=st.number_input("Quantity of Units", 0, disabled=False, label_visibility="visible")
                        tonnage_edit=2*quantity_edit
                        shipped_edit=st.number_input("Shipped # of Units",release_order_database[release_order_number][sales_order_item_edit]["shipped"],disabled=True)
                        remaining_edit=st.number_input("Remaining # of Units",
                                                       quantity_edit-release_order_database[release_order_number][sales_order_item_edit]["shipped"],disabled=True)
                        carrier_code_edit=st.selectbox("Carrier Code",[f"{key}-{item}" for key,item in carrier_list.items()],key="dsfdssa")          
                        
                    elif add:
                        release_order_number=st.selectbox("SELECT RELEASE ORDER",([i for i in release_order_database]))
                        po_number_add=st.text_input("PO No",release_order_database[release_order_number]["po_number"],disabled=False)
                        destination_add=st.text_input("Destination",release_order_database[release_order_number]["destination"],disabled=False)
                        sales_order_item_add=st.text_input("Sales Order Item",disabled=False)
                        vessel_add=vessel=st.selectbox("SELECT VESSEL",[i for i in map['batch_mapping']],key="popoa")
                        ocean_bill_of_lading_add=st.selectbox("Ocean Bill Of Lading",batch_mapping[vessel_add].keys(),key="treerw")  
                        grade_add=st.text_input("Grade",batch_mapping[vessel_add][ocean_bill_of_lading_add]["grade"],disabled=True) 
                        batch_add=st.text_input("Batch No",batch_mapping[vessel_add][ocean_bill_of_lading_add]["batch"],disabled=False)
                        dryness_add=st.text_input("Dryness",batch_mapping[vessel_add][ocean_bill_of_lading_add]["dryness"],disabled=False)
                        admt_add=st.text_input("ADMT PER UNIT",round(float(batch_mapping[vessel_add][ocean_bill_of_lading_add]["dryness"])/90,6),disabled=False)
                        unitized_add=st.selectbox("UNITIZED/DE-UNITIZED",["UNITIZED","DE-UNITIZED"],disabled=False)
                        quantity_add=st.number_input("Quantity of Units", 0, disabled=False, label_visibility="visible")
                        tonnage_add=2*quantity_add
                        shipped_add=0
                        remaining_add=st.number_input("Remaining # of Units", quantity_add,disabled=True)
                        carrier_code_add=st.selectbox("Carrier Code",[f"{key}-{item}" for key,item in carrier_list.items()])            
                    
                    else:  ### If creating new release order
                        
                        release_order_number=st.text_input("Release Order Number")
                        po_number=st.text_input("PO No")
                        destination_list=[i for i in mill_info.keys()]
                        #st.write(destination_list)
                        destination=st.selectbox("SELECT DESTINATION",destination_list)
                        sales_order_item=st.text_input("Sales Order Item")  
                        vessel=st.selectbox("SELECT VESSEL",[i for i in map['batch_mapping']],key="tre")
                        ocean_bill_of_lading=st.selectbox("Ocean Bill Of Lading",batch_mapping[vessel].keys())   #######
                        grade=st.text_input("Grade",batch_mapping[vessel][ocean_bill_of_lading]["grade"],disabled=True)   ##### batch mapping injection
                        batch=st.text_input("Batch No",batch_mapping[vessel][ocean_bill_of_lading]["batch"],disabled=True)   #####
                        dryness=st.text_input("Dryness",batch_mapping[vessel][ocean_bill_of_lading]["dryness"],disabled=True)   #####
                        admt=st.text_input("ADMT PER UNIT",round(float(batch_mapping[vessel][ocean_bill_of_lading]["dryness"])/90,6),disabled=True)  #####
                        unitized=st.selectbox("UNITIZED/DE-UNITIZED",["UNITIZED","DE-UNITIZED"],disabled=False)
                        quantity=st.number_input("Quantity of Units", min_value=1, max_value=5000, value=1, step=1,  key=None, help=None, on_change=None, disabled=False, label_visibility="visible")
                        tonnage=2*quantity
                        carrier_code=st.selectbox("Carrier Code",[f"{key}-{item}" for key,item in carrier_list.items()])            
                    #if edit:
                    #    fsc_verified=st.checkbox(f"**VERIFY RELEASE ORDER FSC CERTIFICATE CODE MATCHES BATCH {batch_edit} STATEMENT : FSC  CERTIFIED PRODUCTS FSC MIX CREDIT SCS-COC-009938**",key="sasa")
                  #  else:
                    #    fsc_verified=st.checkbox(f"**VERIFY RELEASE ORDER FSC CERTIFICATE CODE MATCHES BATCH {batch} STATEMENT : FSC  CERTIFIED PRODUCTS FSC MIX CREDIT SCS-COC-009938**",key="sdasa")
                    create_release_order=st.button("SUBMIT")
                    fsc_verified=True
                    if create_release_order and fsc_verified:
                        
                        if add: 
                            temp=add_release_order_data(release_order_database,release_order_number,sales_order_item_add,vessel_add,batch_add,ocean_bill_of_lading_add,grade_add,dryness_add,carrier_code_add,unitized_add,quantity_add,shipped_add,remaining_add)
                            storage_client = get_storage_client()
                            bucket = storage_client.bucket(target_bucket)
                            blob = bucket.blob(rf"release_orders/RELEASE_ORDERS.json")
                            blob.upload_from_string(temp)
                            st.success(f"ADDED sales order item {sales_order_item_add} to release order {release_order_number}!")
                        elif edit:
                            temp=edit_release_order_data(release_order_database,release_order_number,destination_edit,po_number_edit,sales_order_item_edit,vessel_edit,batch_edit,ocean_bill_of_lading_edit,grade_edit,dryness_edit,carrier_code_edit,unitized_edit,quantity_edit,shipped_edit,remaining_edit)
                            storage_client = get_storage_client()
                            bucket = storage_client.bucket(target_bucket)
                            blob = bucket.blob(rf"release_orders/RELEASE_ORDERS.json")
                            blob.upload_from_string(temp)
                            st.success(f"Edited release order {release_order_number} successfully!")
                            
                        else:
                            temp=store_release_order_data(release_order_database,release_order_number,destination,po_number,sales_order_item,vessel,batch,ocean_bill_of_lading,grade,dryness,carrier_code,unitized,quantity)
                            storage_client = get_storage_client()
                            bucket = storage_client.bucket(target_bucket)
                            blob = bucket.blob(rf"release_orders/RELEASE_ORDERS.json")
                            blob.upload_from_string(temp)
                            st.success(f"Created release order {release_order_number} successfully!")
                        
             
                        
                with release_order_tab1:  ##   RELEASE ORDER DATABASE ##
                    
     
                    rls_tab1,rls_tab2,rls_tab3,rls_tab4=st.tabs(["ACTIVE RELEASE ORDERS","COMPLETED RELEASE ORDERS","SHIPMENT NUMBERS","SCHEDULE"])



                    with rls_tab4:  #####  SCHEDULE
                        schedule=gcp_download(target_bucket,rf"schedule.json")
                        schedule=json.loads(schedule)
                        dfb=pd.DataFrame.from_dict(json.loads(bill_data)).T[1:]
                        scheduled=[]
                        for rol in dispatch:
                            for sale in dispatch[rol]:
                                try:
                                    previous=schedule[dispatch[rol][sale]['destination']]["Scheduled"]
                                except:
                                    previous=0
                                scheduled.append({"Destination":dispatch[rol][sale]['destination'],
                                                  "Release Order":rol,"Sales Item":sale,
                                                  "ISP":release_order_database[rol][sale]['grade'],
                                                  "Prep":release_order_database[rol][sale]['unitized'],
                                                  "Scheduled":previous,"Loaded":0,"Remaining":0})
                        scheduled=pd.DataFrame(scheduled)
                        dfb["St_Date"]=[datetime.datetime.strptime(i,"%Y-%m-%d %H:%M:%S").date() for i in dfb["issued"]]
                        dfb=dfb[dfb["St_Date"]==datetime.datetime.now().date()]
                        for i in scheduled.index:      #### find loads from bill of ladings
                            try:
                                scheduled.loc[i,"Scheduled"]=schedule[scheduled.loc[i,'Destination']]['Scheduled']
                            except:
                                scheduled.loc[i,"Scheduled"]=0
                            rol=scheduled.loc[i,"Release Order"]
                            sale=scheduled.loc[i,"Sales Item"]
                            try:
                                yuk=dfb[(dfb['release_order']==rol)&(dfb['sales_order']==sale)].shape[0]
                            except:
                                yuk=0
                            scheduled.loc[i,"Loaded"]=yuk
                        if len(scheduled)>0:
                            
                            scheduled["Remaining"]=scheduled["Scheduled"]-scheduled["Loaded"]
                            scheduled.loc["Total",["Scheduled","Loaded","Remaining"]]=scheduled[["Scheduled","Loaded","Remaining"]].sum()
                            scheduled.set_index('Destination',drop=True,inplace=True)
                            a=st.data_editor(scheduled)
                            a_=a.iloc[:-1]
                            a_=json.dumps(a_.T.to_dict())
                            if st.button("UPDATE TABLE"):
                                storage_client = get_storage_client()
                                bucket = storage_client.bucket(target_bucket)
                                blob = bucket.blob(rf"schedule.json")
                                blob.upload_from_string(a_)
                                st.success(f"**UPDATED SCHEDULE**")   
                                st.rerun()
                        else:
                            st.write("Nothing Dispatched")

                        
                    with rls_tab1:
                        
                        destinations_of_release_orders=[f"{i} to {release_order_database[i]['destination']}" for i in release_order_database if release_order_database[i]["complete"]!=True]
                        if len(destinations_of_release_orders)==0:
                            st.markdown("**ALL RELEASE ORDERS COMPLETED, REACTIVATE A RELEASE ORDER OR ENTER NEW") 
                         ###       Dropdown menu
                        else:
                            nofile=0
                            requested_file_=st.selectbox("ACTIVE RELEASE ORDERS",destinations_of_release_orders)
                            requested_file=requested_file_.split(" ")[0]
    
                            target=release_order_database[requested_file]
                            destination=target['destination']
                            po_number=target['po_number']
                                        
                            number_of_sales_orders=len([i for i in target if i not in ["destination","po_number"]])   ##### WRONG CAUSE THERE IS NOW DESTINATION KEYS
                            
                            
                           
                            if nofile!=1 :         
                                with st.container(border=True):
                                    rel_ccol1,rel_ccol2,rel_ccol3,rel_ccol4=st.columns([2,2,2,2])
                                    targets=[i for i in target if i in ["001","002","003","004","005"]] 
                                    sales_orders_completed=[k for k in targets if target[k]['remaining']<=0]
                                    with rel_ccol1:
                                        st.markdown(f"**:blue[Release Order Number] : {requested_file}**")
                                    with rel_ccol2:
                                        st.markdown(f"**:blue[Destination] : {target['destination']}**")
                                    with rel_ccol3:
                                        st.markdown(f"**:blue[PO Number] : {target['po_number']}**")
                                    with rel_ccol4:
                                        st.markdown(f"**:blue[...]**")
                                    st.divider()
                                    rel_col1,rel_col2,rel_col3,rel_col4=st.columns([2,2,2,2])
                                    with rel_col1:
                                        
                                        if targets[0] in sales_orders_completed:
                                            st.markdown(f"**:orange[Sales Order Item : {targets[0]} - COMPLETED]**")
                                            target0_done=True
                                            
                                        else:
                                            st.markdown(f"**:blue[Sales Order Item] : {targets[0]}**")
                                        
                                        st.write(f"        Total Quantity: {target[targets[0]]['total']} Units - {2*target[targets[0]]['total']} Tons")
                                        st.write(f"        Ocean Bill Of Lading : {target[targets[0]]['ocean_bill_of_lading']}")
                                        st.write(f"        Batch : {target[targets[0]]['batch']} WIRES : {target[targets[0]]['unitized']}")
                                        st.write(f"        Units Shipped : {target[targets[0]]['shipped']} Units - {2*target[targets[0]]['shipped']} Tons")
                                        if 0<target[targets[0]]['remaining']<=10:
                                            st.markdown(f"**:red[Units Remaining : {target[targets[0]]['remaining']} Units - {2*target[targets[0]]['remaining']} Tons]**")
                                        elif target[targets[0]]['remaining']<=0:
                                            st.markdown(f":orange[Units Remaining : {target[targets[0]]['remaining']} Units - {2*target[targets[0]]['remaining']} Tons]")                                                                        
                                        else:
                                            st.write(f"       Units Remaining : {target[targets[0]]['remaining']} Units - {2*target[targets[0]]['remaining']} Tons")
                                    with rel_col2:
                                        try:
                                            if targets[1] in sales_orders_completed:
                                                st.markdown(f"**:orange[Sales Order Item : {targets[1]} - COMPLETED]**")                                    
                                            else:
                                                st.markdown(f"**:blue[Sales Order Item] : {targets[1]}**")
                                            st.write(f"        Total Quantity : {target[targets[1]]['total']} Units - {2*target[targets[1]]['total']} Tons")                        
                                            st.write(f"        Ocean Bill Of Lading : {target[targets[1]]['ocean_bill_of_lading']}")
                                            st.write(f"        Batch : {target[targets[1]]['batch']} WIRES : {target[targets[1]]['unitized']}")
                                            st.write(f"        Units Shipped : {target[targets[1]]['shipped']} Units - {2*target[targets[1]]['shipped']} Tons")
                                            if 0<target[targets[1]]['remaining']<=10:
                                                st.markdown(f"**:red[Units Remaining : {target[targets[1]]['remaining']} Units - {2*target[targets[1]]['remaining']} Tons]**")
                                            elif target[targets[1]]['remaining']<=0:
                                                st.markdown(f":orange[Units Remaining : {target[targets[1]]['remaining']} Units - {2*target[targets[1]]['remaining']} Tons]")
                                            else:
                                                st.write(f"       Units Remaining : {target[targets[1]]['remaining']} Units - {2*target[targets[1]]['remaining']} Tons")
                                                
                                        except:
                                            pass
                        
                                    with rel_col3:
                                        try:
                                            if targets[2] in sales_orders_completed:
                                                st.markdown(f"**:orange[Sales Order Item : {targets[2]} - COMPLETED]**")
                                            else:
                                                st.markdown(f"**:blue[Sales Order Item] : {targets[2]}**")
                                            st.write(f"        Total Quantity : {target[targets[2]]['total']} Units - {2*target[targets[2]]['total']} Tons")
                                            st.write(f"        Ocean Bill Of Lading : {target[targets[2]]['ocean_bill_of_lading']}")
                                            st.write(f"        Batch : {target[targets[2]]['batch']} WIRES : {target[targets[2]]['unitized']}")
                                            st.write(f"        Units Shipped : {target[targets[2]]['shipped']} Units - {2*target[targets[2]]['shipped']} Tons")
                                            if 0<target[targets[2]]['remaining']<=10:
                                                st.markdown(f"**:red[Units Remaining : {target[targets[2]]['remaining']} Units - {2*target[targets[2]]['remaining']} Tons]**")
                                            elif target[targets[2]]['remaining']<=0:
                                                st.markdown(f":orange[Units Remaining : {target[targets[2]]['remaining']} Units - {2*target[targets[2]]['remaining']} Tons]")
                                            else:
                                                st.write(f"       Units Remaining : {target[targets[2]]['remaining']} Units - {2*target[targets[2]]['remaining']} Tons")
                                            
                                            
                                        except:
                                            pass
                    
                                    with rel_col4:
                                        try:
                                            if targets[3] in sales_orders_completed:
                                                st.markdown(f"**:orange[Sales Order Item : {targets[3]} - COMPLETED]**")
                                            else:
                                                st.markdown(f"**:blue[Sales Order Item] : {targets[3]}**")
                                            st.write(f"        Total Quantity : {target[targets[3]]['total']} Units - {2*target[targets[3]]['total']} Tons")
                                            st.write(f"        Ocean Bill Of Lading : {target[targets[3]]['ocean_bill_of_lading']}")
                                            st.write(f"        Batch : {target[targets[3]]['batch']} WIRES : {target[targets[3]]['unitized']}")
                                            st.write(f"        Units Shipped : {target[targets[3]]['shipped']} Units - {2*target[targets[2]]['shipped']} Tons")
                                            if 0<target[targets[3]]['remaining']<=10:
                                                st.markdown(f"**:red[Units Remaining : {target[targets[3]]['remaining']} Units - {2*target[targets[3]]['remaining']} Tons]**")
                                            elif target[targets[3]]['remaining']<=0:
                                                st.markdown(f":orange[Units Remaining : {target[targets[3]]['remaining']} Units - {2*target[targets[3]]['remaining']} Tons]")
                                            else:
                                                st.write(f"       Units Remaining : {target[targets[3]]['remaining']} Units - {2*target[targets[3]]['remaining']} Tons")
                                            
                                            
                                        except:
                                            pass
                                
                      
                                with st.container(border=True):
                                    dol1,dol2,dol3,dol4=st.columns([2,2,2,2])
                                    with dol1:
                                        hangisi=st.selectbox("**:green[SELECT SALES ORDER ITEM TO DISPATCH]**",([i for i in targets if i not in sales_orders_completed]))
                                        if st.button("DISPATCH TO WAREHOUSE",key="lala"):
                                            try:
                                                last=list(dispatch[requested_file].keys())[-1]
                                             
                                                dispatch[requested_file][hangisi]={"release_order":requested_file,"sales_order":hangisi,"destination":destination}
                                            except:
                                                dispatch[requested_file]={}
                                                dispatch[requested_file][hangisi]={"release_order":requested_file,"sales_order":hangisi,"destination":destination}
                    
                                            
                                            json_data = json.dumps(dispatch)
                                            storage_client =get_storage_client()
                                            bucket = storage_client.bucket(target_bucket)
                                            blob = bucket.blob(rf"dispatched.json")
                                            blob.upload_from_string(json_data)
                                            st.markdown(f"**DISPATCHED Release Order Number {requested_file} Item No : {hangisi} to Warehouse**")
                                    
                                                   
                                    with dol2:  
                                        try:
                                            liste=[]
                                            for i in dispatch.keys():
                                                for k in dispatch[i]:
                                                    liste.append(f"{i}-{k}")
                                            item=st.selectbox("CHOOSE ITEM",liste)
                                            undispatch_rel=item.split("-")[0]
                                            undispatch_sal=item.split("-")[1]
                                            if st.button("UN-DISPATCH ITEM"):                                       
                                                del dispatch[undispatch_rel][undispatch_sal]
                                                json_data = json.dumps(dispatch)
                                                storage_client = get_storage_client()
                                                bucket = storage_client.bucket(target_bucket)
                                                blob = bucket.blob(rf"dispatched.json")
                                                blob.upload_from_string(json_data)
                                                st.markdown(f"**CLEARED DISPATCH ITEM {item}**")   
                                        except:
                                            pass
                                        
                                    with dol3:
                                        if st.button("CLEAR DISPATCH QUEUE!"):
                                            dispatch={}
                                            json_data = json.dumps(dispatch)
                                            storage_client = get_storage_client()
                                            bucket = storage_client.bucket(target_bucket)
                                            blob = bucket.blob(rf"dispatched.json")
                                            blob.upload_from_string(json_data)
                                            st.markdown(f"**CLEARED ALL DISPATCHES**")   
                                        
                                with st.container(border=True):
                                    
                                    st.markdown("**CURRENT DISPATCH QUEUE**")
                                    try:
                                        for dispatched_release in dispatch.keys():
                                            for sales in dispatch[dispatched_release].keys():
                                                st.markdown(f'**Release Order = {dispatched_release}, Sales Item : {sales}, Destination : {dispatch[dispatched_release][sales]["destination"]} .**')
                                    except:
                                        st.write("NO DISPATCH ITEMS")
                            
                            else:
                                st.write("NO RELEASE ORDERS IN DATABASE")
                    with rls_tab2:
                        completed=[i for i in release_order_database if release_order_database[i]["complete"]==True]
                                                    
                        completed_release_order_dest_map={}
                        for i in completed:
                            for sale in [s for s in release_order_database[i] if s in ["001","002","003","004","005"]]:
                                completed_release_order_dest_map[f"{i}-{sale}"]=[sale,release_order_database[i]["destination"],
                                                                     release_order_database[i][sale]["ocean_bill_of_lading"],
                                                                     release_order_database[i][sale]["grade"],
                                                                     release_order_database[i][sale]["vessel"],
                                                                     release_order_database[i][sale]["total"],
                                                                                release_order_database[i][sale]["shipped"],
                                                                                release_order_database[i][sale]["remaining"]]
                      
                        column_names = ["Sale", "Destination", "Ocean Bill of Lading", "Grade", "Vessel", "Total", "Shipped", "Remaining"]

                        # Create DataFrame and assign column names
                        completed_frame = pd.DataFrame(completed_release_order_dest_map).T
                        completed_frame.columns = column_names

                        st.write(completed_frame)
                        activate_list=list(set([i.split("-")[0] for i in completed_release_order_dest_map.keys()]))
                        to_reactivate=st.selectbox("SELECT RELEASE ORDER TO CHANGE FROM COMPLETE TO UNCOMPLETE",activate_list,key="erfdaq")
                        if st.button("ACTIVATE RELEASE ORDER"):
                            release_order_database[to_reactivate]['complete']=False
                            storage_client = get_storage_client()
                            bucket = storage_client.bucket(target_bucket)
                            blob = bucket.blob(rf"release_orders/RELEASE_ORDERS.json")
                            blob.upload_from_string(json.dumps(release_order_database))
                            st.success(f"Reactivated {to_reactivate} successfully!")
                        not_completed=[i for i in release_order_database if release_order_database[i]["complete"]==False]
                        to_deactivate=st.selectbox("SELECT RELEASE ORDER TO CHANGE FROM NOT COMPLETE TO COMPLETE",not_completed,key="erfsdaq")
                        if st.button("DE-ACTIVATE RELEASE ORDER",key="sdasa"):
                            release_order_database[to_deactivate]['complete']=True
                            storage_client = get_storage_client()
                            bucket = storage_client.bucket(target_bucket)
                            blob = bucket.blob(rf"release_orders/RELEASE_ORDERS.json")
                            blob.upload_from_string(json.dumps(release_order_database))
                            st.success(f"Deactivated {to_deactivate} successfully!")
                        
                    with rls_tab3:

                        mf1,mf2=st.tabs(["VIEW/EDIT MF NUMBERS","AUTO UPLOAD"])
                        with mf1:
                            mf_numbers=gcp_download(target_bucket,rf"release_orders/mf_numbers.json")
                            mf_numbers=json.loads(mf_numbers)
                            def check_home(ro):
                                destination=release_order_database[ro]['destination']
                                keys=[sale for sale in release_order_database[ro] if sale in ["001","002","003","004","005"]]
                                remains=[release_order_database[ro][key]["remaining"] for key in keys]
                                if sum(remains)==0:
                                    return False
                                return f"{ro} to {destination}"
                                
                            destinations_of_release_orders=[check_home(i) for i in release_order_database if check_home(i) ]
                            if len(destinations_of_release_orders)==0:
                                st.warning("NO GP RELEASE ORDERS FOR THIS VESSEL")
                            else:
                                
                                release_order_number_mf_=st.selectbox("SELECT RELEASE ORDER FOR SHIPMENT NUMBERS",destinations_of_release_orders,key="tatata")
                                release_order_number_mf=release_order_number_mf_.split(" ")[0]
                                mf_date_str=str(st.date_input("Shipment Date",datetime.datetime.today(),disabled=False,key="popddao3"))
                                carrier_mf=st.selectbox("SELECT CARRIER",[f"{i}-{j}" for i,j in map["carriers"].items()],key="tatpota")
                                input_mf_numbers=st.text_area("**ENTER SHIPMENT NUMBERS**",height=100,key="juy")
                                if input_mf_numbers is not None:
                                    input_mf_numbers = input_mf_numbers.splitlines()
                                    input_mf_numbers=[i for i in input_mf_numbers]####### CAREFUL THIS ASSUMES SAME DIGIT MF EACH TIME
                                if st.button("SUBMIT SHIPMENT NUMBERS",key="ioeru" ):
                                    st.write(carrier_mf)
                                    if release_order_number_mf not in mf_numbers.keys():   
                                        mf_numbers[release_order_number_mf]={}
                                    if mf_date_str not in mf_numbers[release_order_number_mf]:
                                        mf_numbers[release_order_number_mf][mf_date_str]={}
                                    if carrier_mf not in mf_numbers[release_order_number_mf][mf_date_str]:
                                        mf_numbers[release_order_number_mf][mf_date_str][carrier_mf]=[]
                                    mf_numbers[release_order_number_mf][mf_date_str][carrier_mf]+=input_mf_numbers
                                    mf_numbers[release_order_number_mf][mf_date_str][carrier_mf]=list(set(mf_numbers[release_order_number_mf][mf_date_str][carrier_mf]))
                                    mf_data=json.dumps(mf_numbers)
                                    #storage_client = storage.Client()
                                    storage_client = get_storage_client()
                                    bucket = storage_client.bucket(target_bucket)
                                    blob = bucket.blob(rf"release_orders/mf_numbers.json")
                                    blob.upload_from_string(mf_data)
                                    st.success(f"MF numbers entered to {release_order_number_mf} successfully!")
                                if st.button("REMOVE SHIPMENT NUMBERS",key="ioerssu" ):
                                    for i in input_mf_numbers:
                                        for carrier in mf_numbers[release_order_number_mf][mf_date_str]:
                                            if i in mf_numbers[release_order_number_mf][mf_date_str][carrier]:
                                                mf_numbers[release_order_number_mf][mf_date_str][carrier].remove(i)
                                                st.success(f"MF numbers removed from {release_order_number_mf} successfully!")
                                    mf_data=json.dumps(mf_numbers)
                                   # storage_client = storage.Client()
                                    storage_client = get_storage_client()
                                    bucket = storage_client.bucket(target_bucket)
                                    blob = bucket.blob(rf"release_orders/mf_numbers.json")
                                    blob.upload_from_string(mf_data)
                                #st.write(mf_numbers)
                                mfcol1,mfcol2,mfcol3=st.columns([4,4,1])
                                with mfcol1:
                                    mf_frame=pd.DataFrame(mf_numbers)
                                    mf_frame.fillna(0,inplace=True)
                                    mf_frame.sort_index(inplace=True)
                                    mf_frame.columns=[check_home(i) for i in mf_frame.columns]
                                    st.dataframe(mf_frame,width=5000)
                                with mfcol2:
                                    for i in mf_frame.index:
                                        for j in mf_frame:
                                            if mf_frame.loc[i, j]!=0:
                                                count=0
                                                for key in mf_frame.loc[i, j]:
                                                    count+=len(mf_frame.loc[i, j][key])
                                                mf_frame.loc[i, j] = count
                                    mf_frame.sort_index(inplace=True)
                                    st.dataframe(mf_frame,width=5000)
                                    
                        
                        
                        
                        with mf2:
                            col11,col22,col33=st.columns([3,3,4])
                            button=True
                            with col11:
                                
                                st.subheader("SELECT DATES TO UPLOAD")
                                dates1=st.date_input("FROM (INCLUSIVE)",datetime.date.today(),key="r3wsd")
                                dates2=st.date_input("TO (INCLUSIVE)",datetime.date.today()+datetime.timedelta(days=30),key="rz3wsd")
                            with col22:
                                st.subheader("UPLOAD SHIPMENT CSV FILES")
                                suzano_shipment = st.file_uploader("Upload **SUZANO** Shipment CSV", type="csv",key="dsds")
                                kbx_shipment = st.file_uploader("Upload **KBX** Shipment CSV", type="csv",key="dsdfqa")
                            
                            if suzano_shipment and kbx_shipment:
                                st.success("Files uploaded")
                                button=False
                                done=False
                            done=False
                            
                            if st.button("PROCESS FILES",disabled=button):
                            
                                
                                df=pd.read_csv(suzano_shipment)
                                df=df[['Shipment ID', 'Release Order', 'Item',
                                       'Start Time', 'Destination City',
                                       'Destination Province Code', 'Weight', 'Unit Count', 
                                       'Service Provider ID',  'Service Provider']]
                                df['Release Order']=[i[10:] for i in df['Release Order']]
                                df["Pickup"] = df["Start Time"].apply(lambda i: datetime.datetime.strptime(i, "%m/%d/%Y %I:%M %p").date())
                                #df
                                
                                df1=pd.read_csv(kbx_shipment,header=1)
                                df1.drop(0,inplace=True)
                                df1=df1[[ 'Load','SCAC','Pro', 
                                       'Pickup', 'Orig', 'Delivery',
                                       'Dest', 'Dest.1', 'Dest.2', 'Dest.3', 'Dest.4', 'Movement', 'Drop',
                                       'Miles', 'Total', 'Total.1', 'Equip Nbr',  'Created', 'Created.1', 'Last Changed',
                                       'Last Changed.1']]
                                df1["Pickup"] = pd.to_datetime(df1["Pickup"]).dt.date
                                df1=df1[~df1["SCAC"].isna()]
                                df1.rename(columns={"Dest.1":"Destination City"},inplace=True)
                                
                                
                                
                                df=df[(df['Pickup']>=dates1)&(df['Pickup']<=dates2)].sort_values(by="Pickup")
                                df1=df1[df1['Pickup']>=dates1].sort_values(by="Pickup")
                                matches={}
                                days_loads={}
                                kbx_loads={}
                                for i in sorted(df["Pickup"].unique()):
                                    #print(i)
                                    matches[str(i)]={}
                                    days_loads[i]={}
                                    kbx_loads[i]={}
                                    
                                    for dest in df[df["Pickup"]==i]["Destination City"].unique():
                                        #print(dest)
                                        
                                            
                                                                 
                                        
                                        suz=sorted(df.loc[(df["Pickup"] == i) & (df["Destination City"] == dest), "Shipment ID"])
                                        
                                            
                                        transport=df.loc[(df["Pickup"] == i) & (df["Destination City"] == dest), "Service Provider ID"].unique()[0]
                                        if transport=="KBX":
                                            transport="123456-KBX"
                                        else:
                                            transport=f"{str(transport[4:])}-{map_['carriers'][str(transport[4:])]}"
                                        rel=df.loc[(df["Pickup"] == i) & (df["Destination City"] == dest), "Release Order"].unique()[0]
                                        if dest not in ["HALSEY","CLATSKANIE"]:
                                            matches[str(i)][dest]={}
                                            matches[str(i)][dest]["release_order"]=rel
                                            matches[str(i)][dest]["transport"]=transport
                                            matches[str(i)][dest]["loads"]=suz
                                        #print(rel)
                                        
                                        else:
                                            kbx=sorted(df1.loc[(df1["Pickup"] == i) & (df1["Destination City"] == dest), "Load"])
                                            days_loads[i][dest] =suz
                                            kbx_loads[i][dest]=kbx
                                        
                                            mat=[f"{j}|{k}" for j,k in zip(kbx,suz)]
                                            matches[str(i)][dest]={}
                                            matches[str(i)][dest]["release_order"]=rel
                                            matches[str(i)][dest]["transport"]=transport
                                            matches[str(i)][dest]["loads"]=mat
                                done=True
                                if matches not in st.session_state:
                                    st.session_state.matches=matches
                                st.success("SHIPMENTS MATCHED AND LOADED!")
                                if st.button("RECORD SUZANO LIST",disabled=button,key="sdsqawds2"):
                                    suz_=json.dumps(df)
                                    storage_client = get_storage_client()
                                    bucket = storage_client.bucket(target_bucket)
                                    blob = bucket.blob(rf"release_orders/suzano_shipments.json")
                                    blob.upload_from_string(suz_)
                                    st.success(f"Suzano list updated!")
                            cor1,cor2,cor3=st.columns([3,3,4])
                            with cor1:
                                
                                
                                if done:
                                    st.write(dict(matches))
                            with cor2:
                                if st.button("UPLOAD SHIPMENTS TO SYSTEM",key="dsdsdads2"):
                                    matches=st.session_state.matches
                                    for i in matches:
                                        for desti in matches[i]:
                                            
                                            release=matches[i][desti]['release_order']
                                            carrier=matches[i][desti]['transport']
                                            if release not in mf_numbers:
                                                mf_numbers[release]={str(i):{}}
                                            mf_numbers[release][str(i)]={carrier:matches[i][desti]['loads']}
                                    mf_datam=json.dumps(mf_numbers)
                                        #storage_client = storage.Client()
                                    storage_client = get_storage_client()
                                    bucket = storage_client.bucket(target_bucket)
                                    blob = bucket.blob(rf"release_orders/mf_numbers.json")
                                    blob.upload_from_string(mf_datam)
                                    st.success(f"MF numbers updated with schedule!")
                                st.write(mf_numbers)
                with release_order_tab3:  ### RELEASE ORDER STATUS
                    raw_ro=gcp_download(target_bucket,rf"release_orders/RELEASE_ORDERS.json")
                    raw_ro = json.loads(raw_ro)
                    status_dict={}
                    sales_group=["001","002","003","004","005"]
                    for ro in raw_ro:
                        for sale in [i for i in raw_ro[ro] if i in sales_group]:
                            status_dict[f"{ro}-{sale}"]={"Release Order #":ro,"Sales Order #":sale,
                                                "Destination":raw_ro[ro]['destination'],
                                                "Ocean BOL":raw_ro[ro][sale]['ocean_bill_of_lading'],
                                                "Total":raw_ro[ro][sale]['total'],
                                                "Shipped":raw_ro[ro][sale]['shipped'],
                                                "Remaining":raw_ro[ro][sale]['remaining']}
                    status_frame=pd.DataFrame(status_dict).T.set_index("Release Order #",drop=True)
                    active_frame_=status_frame[status_frame["Remaining"]>0]
                    status_frame.loc["Total"]=status_frame[["Total","Shipped","Remaining"]].sum()
                    active_frame=active_frame_.copy()
                    active_frame.loc["Total"]=active_frame[["Total","Shipped","Remaining"]].sum()
                    
                    st.markdown(active_frame.to_html(render_links=True),unsafe_allow_html=True)
    
                    
                    release_orders = status_frame.index[:-1]
                    release_orders = pd.Categorical(release_orders)
                    active_order_names = [f"{i} to {raw_ro[i]['destination']}" for i in active_frame_.index]
                    destinations=[raw_ro[i]['destination'] for i in active_frame_.index]
                    active_orders=[str(i) for i in active_frame.index]
                   
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=active_orders, y=active_frame["Total"], name='Total', marker_color='lightgray'))
                    fig.add_trace(go.Bar(x=active_orders, y=active_frame["Shipped"], name='Shipped', marker_color='blue', opacity=0.7))
                    remaining_data = [remaining if remaining > 0 else None for remaining in active_frame_["Remaining"]]
                    fig.add_trace(go.Scatter(x=active_orders, y=remaining_data, mode='markers', name='Remaining', marker=dict(color='red', size=10)))
                    
                    #annotations = [dict(x=release_order, y=total_quantity, text=destination, showarrow=True, arrowhead=4, ax=0, ay=-30) for release_order, total_quantity, destination in zip(active_orders, active_frame["Total"], destinations)]
                    #fig.update_layout(annotations=annotations)
    
                    # fig.add_annotation(x="3172296", y=800, text="destination",
                    #                        showarrow=True, arrowhead=4, ax=0, ay=-30)
                    
                    fig.update_layout(title='ACTIVE RELEASE ORDERS',
                                      xaxis_title='Release Orders',
                                      yaxis_title='Quantities',
                                      barmode='overlay',
                                      width=1300,
                                      height=700,
                                      xaxis=dict(tickangle=-90, type='category'))
                    
                    st.plotly_chart(fig)
                    
                    
                    duration=st.toggle("Duration Report")
                    if duration:
                        
                        temp_dict={}
                            
                        for rel_ord in raw_ro:
                            for sales in [i for i in raw_ro[rel_ord] if i in ["001","002","003","004","005"]]:
                                temp_dict[rel_ord,sales]={}
                                dest=raw_ro[rel_ord]['destination']
                                vessel=raw_ro[rel_ord][sales]['vessel']
                                total=raw_ro[rel_ord][sales]['total']
                                remaining=raw_ro[rel_ord][sales]['remaining']
                                temp_dict[rel_ord,sales]={'destination': dest,'vessel': vessel,'total':total,'remaining':remaining}
                        temp_df=pd.DataFrame(temp_dict).T
                      
                        temp_df= temp_df.rename_axis(['release_order','sales_order'], axis=0)
                    
                        temp_df['First Shipment'] = temp_df.index.map(admin_bill_of_ladings.groupby(['release_order','sales_order'])['issued'].first())
                        
                        for i in temp_df.index:
                            if temp_df.loc[i,'remaining']<=2:
                                try:
                                    temp_df.loc[i,"Last Shipment"]=admin_bill_of_ladings.groupby(['release_order','sales_order']).issued.last().loc[i]
                                except:
                                    temp_df.loc[i,"Last Shipment"]=datetime.datetime.now()
                                temp_df.loc[i,"Duration"]=(pd.to_datetime(temp_df.loc[i,"Last Shipment"])-pd.to_datetime(temp_df.loc[i,"First Shipment"])).days+1
                        
                        temp_df['First Shipment'] = temp_df['First Shipment'].fillna(datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'))
                        temp_df['Last Shipment'] = temp_df['Last Shipment'].fillna(datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'))
                        
                        ####
                        
                        def business_days(start_date, end_date):
                            return pd.date_range(start=start_date, end=end_date, freq=BDay())
                        temp_df['# of Shipment Days'] = temp_df.apply(lambda row: len(business_days(row['First Shipment'], row['Last Shipment'])), axis=1)
                        df_temp=admin_bill_of_ladings.copy()
                        df_temp["issued"]=[pd.to_datetime(i).date() for i in df_temp["issued"]]
                        for i in temp_df.index:
                            try:
                                temp_df.loc[i,"Utilized Shipment Days"]=df_temp.groupby(["release_order",'sales_order'])[["issued"]].nunique().loc[i,'issued']
                            except:
                                temp_df.loc[i,"Utilized Shipment Days"]=0
                        
                        temp_df['First Shipment'] = temp_df['First Shipment'].apply(lambda x: datetime.datetime.strftime(datetime.datetime.strptime(x,'%Y-%m-%d %H:%M:%S'),'%d-%b,%Y'))
                        temp_df['Last Shipment'] = temp_df['Last Shipment'].apply(lambda x: datetime.datetime.strftime(datetime.datetime.strptime(x,'%Y-%m-%d %H:%M:%S'),'%d-%b,%Y') if type(x)==str else None)
                        liste=['Duration','# of Shipment Days',"Utilized Shipment Days"]
                        for col in liste:
                            temp_df[col] = temp_df[col].apply(lambda x: f" {int(x)} days" if not pd.isna(x) else np.nan)
                        temp_df['remaining'] = temp_df['remaining'].apply(lambda x: int(x))
                        temp_df.columns=['Destination', 'Vessel', 'Total Units', 'Remaining Units', 'First Shipment',
                               'Last Shipment', 'Duration', '# of Calendar Shipment Days',
                               'Utilized Calendar Shipment Days']
                        st.dataframe(temp_df)
                        a=df_temp.groupby(["issued"])[['quantity']].sum()
                        a.index=pd.to_datetime(a.index)
                        labor=gcp_download(target_bucket,rf"trucks.json")
                        labor = json.loads(labor)
                        
                        labor=pd.DataFrame(labor).T
                        labor.index=pd.to_datetime(labor.index)
                        for index in a.index:
                            try:
                                a.loc[index,'cost']=labor.loc[index,'cost']
                            except:
                                pass
                        a['quantity']=2*a['quantity']
                        a['Per_Ton']=a['cost']/a['quantity']
                        trucks=df_temp.groupby(["issued"])[['vehicle']].count().vehicle.values
                        a.insert(0,'trucks',trucks)
                        a['Per_Ton']=round(a['Per_Ton'],1)
                        w=a.copy()
                        m=a.copy()
                        cost_choice=st.radio("Select Daily/Weekly/Monthly Cost Analysis",["DAILY","WEEKLY","MONTHLY"])
                        if cost_choice=="DAILY":
                            a['Per_Ton']=["${:.2f}".format(number) for number in a['Per_Ton']]
                            a['cost']=["${:.2f}".format(number) for number in a['cost']]
                            a.index=[i.date() for i in a.index]
                            a= a.rename_axis('Day', axis=0)
                            a.columns=["# of Trucks","Tons Shipped","Total Cost","Cost Per Ton"]
                            st.dataframe(a)
                        if cost_choice=="WEEKLY":
                            w.columns=["# of Trucks","Tons Shipped","Total Cost","Cost Per Ton"]
                            weekly=w.dropna()
                            weekly=weekly.resample('W').sum()
                            weekly['Cost Per Ton']=round(weekly['Total Cost']/weekly['Tons Shipped'],1)
                            weekly['Cost Per Ton']=["${:.2f}".format(number) for number in weekly['Cost Per Ton']]
                            weekly['Total Cost']=["${:.2f}".format(number) for number in weekly['Total Cost']]
                            weekly.index=[i.date() for i in weekly.index]
                            weekly= weekly.rename_axis('Week', axis=0)
                            st.dataframe(weekly)
                        if cost_choice=="MONTHLY":
                            m.columns=["# of Trucks","Tons Shipped","Total Cost","Cost Per Ton"]
                            monthly=m.dropna()
                            monthly=monthly.resample('M').sum()
                            monthly['Cost Per Ton']=round(monthly['Total Cost']/monthly['Tons Shipped'],1)
                            monthly['Cost Per Ton']=["${:.2f}".format(number) for number in monthly['Cost Per Ton']]
                            monthly['Total Cost']=["${:.2f}".format(number) for number in monthly['Total Cost']]
                            monthly.index=[calendar.month_abbr[k] for k in [i.month for i in monthly.index]]
                            monthly= monthly.rename_axis('Month', axis=0)
                            st.dataframe(monthly)
                        else:
                            #st.write("NO RELEASE ORDER FOR THIS VESSEL IN DATABASE")
                            pass
                        
                                
        
                        
        
        ##########  LOAD OUT  ##############
        
        
        
        if select=="LOADOUT" :
        

            map=gcp_download(target_bucket,rf"map.json")
            map=json.loads(map)
            release_order_database=gcp_download(target_bucket,rf"release_orders/RELEASE_ORDERS.json")
            release_order_database=json.loads(release_order_database)
            dispatched=gcp_download(target_bucket,rf"dispatched.json")
            dispatched=json.loads(dispatched)
            carrier_list=map['carriers']
            mill_info=map["mill_info"]
            
            bill_mapping=gcp_download(target_bucket,"bill_mapping.json")   ###### DOWNLOADS
            bill_mapping=json.loads(bill_mapping)
            mf_numbers_for_load=gcp_download(target_bucket,rf"release_orders/mf_numbers.json")  ###### DOWNLOADS
            mf_numbers_for_load=json.loads(mf_numbers_for_load)

            bill_of_ladings=gcp_download(target_bucket,rf"terminal_bill_of_ladings.json")   ###### DOWNLOADS
            bill_of_ladings=json.loads(bill_of_ladings)
            
            no_dispatch=0
           
            number=None  
            if number not in st.session_state:
                st.session_state.number=number
                           
          
            double_load=False
            
            if len(dispatched.keys())>0 and not no_dispatch:
                loadout,schedule=st.tabs(["LOADOUT","SCHEDULE"])
                with schedule:
                    st.subheader("TODAYS ACTION/SCHEDULE")
                    now=datetime.datetime.now()-datetime.timedelta(hours=utc_difference)
                    schedule=gcp_download(target_bucket,rf"schedule.json")
                    schedule=json.loads(schedule)
                    dfb=pd.DataFrame.from_dict(bill_of_ladings).T[1:]
                    dfb["St_Date"]=[datetime.datetime.strptime(i,"%Y-%m-%d %H:%M:%S").date() for i in dfb["issued"]]
                    dfb=dfb[dfb["St_Date"]==now.date()]
                    scheduled=[]
                    for rol in dispatched:
                        for sale in dispatched[rol]:
                            try:
                                previous=schedule[dispatched[rol][sale]['destination']]["Scheduled"]
                            except:
                                previous=0
                            scheduled.append({"Destination":dispatched[rol][sale]['destination'],
                                              "Release Order":rol,"Sales Item":sale,
                                              "ISP":release_order_database[rol][sale]['grade'],
                                              "Prep":release_order_database[rol][sale]['unitized'],
                                              "Scheduled":previous,"Loaded":0,"Remaining":0})
                    scheduled=pd.DataFrame(scheduled)
                    for i in scheduled.index:
                        rol=scheduled.loc[i,"Release Order"]
                        sale=scheduled.loc[i,"Sales Item"]
                        yuk=dfb[(dfb['release_order']==rol)&(dfb['sales_order']==sale)].shape[0]
                        scheduled.loc[i,"Loaded"]=yuk
                    
                    
                    if len(scheduled)>0:
                    
                        scheduled["Remaining"]=scheduled["Scheduled"]-scheduled["Loaded"]
                        
                        scheduled.set_index('Destination',drop=True,inplace=True)
                        scheduled.loc["Total",["Scheduled","Loaded","Remaining"]]=scheduled[["Scheduled","Loaded","Remaining"]].sum()
                        for col in ["Scheduled", "Loaded", "Remaining"]:
                            scheduled[col] = pd.to_numeric(scheduled[col], errors='coerce').fillna(0).astype(int)
                        scheduled.fillna("",inplace=True)
                        st.dataframe(dfb)
                        st.table(scheduled)
                    else:
                        st.dataframe(dfb)
                        st.write("Nothing Dispatched!")
                      
                
                with loadout:
                    
                    menu_destinations={}
                    
                    for rel_ord in dispatched.keys():
                        for sales in dispatched[rel_ord]:
                            try:
                                menu_destinations[f"{rel_ord} -{sales}"]=dispatched[rel_ord][sales]["destination"]
                            except:
                                pass
                    if 'work_order_' not in st.session_state:
                        st.session_state.work_order_ = None
                        
                    liste=[f"{i} to {menu_destinations[i]}" for i in menu_destinations.keys()]
                
                    work_order_=st.selectbox("**SELECT RELEASE ORDER/SALES ORDER TO WORK**",liste,index=0 if st.session_state.work_order_ else 0) 
                    st.session_state.work_order_=work_order_
                    if work_order_:
                        
                        work_order=work_order_.split(" ")[0]
                        order=["001","002","003","004","005","006"]
                        
                        current_release_order=work_order
                        current_sales_order=work_order_.split(" ")[1][1:]
                        vessel=release_order_database[current_release_order][current_sales_order]["vessel"]
                        destination=release_order_database[current_release_order]['destination']
                        
                        
                        
              
                        try:
                            next_release_order=dispatched['002']['release_order']    #############################  CHECK HERE ######################## FOR MIXED LOAD
                            next_sales_order=dispatched['002']['sales_order']
                            
                        except:
                            
                            pass
                        
        
                        
                            
                        
                        st.markdown(rf'**:blue[CURRENTLY WORKING] :**')
                        load_col1,load_col2=st.columns([9,1])
                        
                        with load_col1:
                            wrap_dict={"ISU":"UNWRAPPED","ISP":"WRAPPED","AEP":"WRAPPED"}
                            wrap=release_order_database[current_release_order][current_sales_order]["grade"]
                            ocean_bill_of_=release_order_database[current_release_order][current_sales_order]["ocean_bill_of_lading"]
                            unitized=release_order_database[current_release_order][current_sales_order]["unitized"]
                            quant_=release_order_database[current_release_order][current_sales_order]["total"]
                            real_quant=int(math.floor(quant_))
                            ship_=release_order_database[current_release_order][current_sales_order]["shipped"]
                            ship_bale=(ship_-math.floor(ship_))*8
                            remaining=release_order_database[current_release_order][current_sales_order]["remaining"]                #######      DEFINED "REMAINING" HERE FOR CHECKS
                            temp={f"<b>Release Order #":current_release_order,"<b>Destination":destination,"<b>VESSEL":vessel}
                            temp2={"<b>Ocean B/L":ocean_bill_of_,"<b>Type":wrap_dict[wrap],"<b>Prep":unitized}
                            temp3={"<b>Total Units":quant_,"<b>Shipped Units":ship_,"<b>Remaining Units":remaining}
                            #temp4={"<b>Total Bales":0,"<b>Shipped Bales":int(8*(ship_-math.floor(ship_))),"<b>Remaining Bales":int(8*(remaining-math.floor(remaining)))}
                            temp5={"<b>Total Tonnage":quant_*2,"<b>Shipped Tonnage":ship_*2,"<b>Remaining Tonnage":quant_*2-(ship_*2)}
        
        
                            
                            sub_load_col1,sub_load_col2,sub_load_col3,sub_load_col4=st.columns([3,3,3,3])
                            
                            with sub_load_col1:   
                                st.markdown(rf'**Release Order-{current_release_order}**')
                                st.markdown(rf'**Destination : {destination}**')
                                st.markdown(rf'**VESSEL-{vessel}**')
                                #st.write (pd.DataFrame(temp.items(),columns=["Inquiry","Data"]).to_html (escape=False, index=False), unsafe_allow_html=True)
                         
                            with sub_load_col2:
                                st.markdown(rf'**Ocean B/L: {ocean_bill_of_}**')
                                st.markdown(rf'**Type : {wrap_dict[wrap]}**')
                                st.markdown(rf'**Prep : {unitized}**')
                                #st.write (pd.DataFrame(temp2.items(),columns=["Inquiry","Data"]).to_html (escape=False, index=False), unsafe_allow_html=True)
                           
                                
                            with sub_load_col3:
            
                                st.markdown(rf'**Total Units : {quant_}**')
                                st.markdown(rf'**Shipped Units : {ship_}**')
                                if remaining<=10:
                                    st.markdown(rf'**:red[CAUTION : Remaining : {remaining} Units]**')
                                else:
                                    st.markdown(rf'**Remaining Units : {remaining}**')
                            with sub_load_col4:
                                
                            
                                #st.write (pd.DataFrame(temp5.items(),columns=["TONNAGE","Data"]).to_html (escape=False, index=False), unsafe_allow_html=True)
                                
                                st.markdown(rf'**Total Tonnage : {quant_*2}**')
                                st.markdown(rf'**Shipped Tonnage : {ship_*2}**')
                                st.markdown(rf'**Remaining Tonnage : {remaining*2}**')
                        
                        with load_col2:
                            if double_load:
                                
                                try:
                                    st.markdown(rf'**NEXT ITEM : Release Order-{next_release_order}**')
                                    st.markdown(rf'**Sales Order Item-{next_sales_order}**')
                                    st.markdown(f'**Ocean Bill Of Lading : {info[vessel][next_release_order][next_sales_order]["ocean_bill_of_lading"]}**')
                                    st.markdown(rf'**Total Quantity : {info[vessel][next_release_order][next_sales_order]["quantity"]}**')
                                except:
                                    pass
        
                        st.divider()
                        ###############    LOADOUT DATA ENTRY    #########
                        
                        col1, col2,col3,col4= st.columns([2,2,2,2])
                        yes=False
                      
                        release_order_number=current_release_order
                        medium="TRUCK"
                        
                        with col1:
                        ######################  LETS GET RID OF INPUT BOXES TO SIMPLIFY LONGSHORE SCREEN
                   
                            terminal_code="OLYM"
                            
                            file_date=datetime.datetime.today()-datetime.timedelta(hours=utc_difference)
                            if file_date not in st.session_state:
                                st.session_state.file_date=file_date
                            file_time = st.time_input('FileTime', datetime.datetime.now()-datetime.timedelta(hours=utc_difference),step=60,disabled=False)
                          
                            delivery_date=datetime.datetime.today()-datetime.timedelta(hours=utc_difference)
                            eta_date=delivery_date
                            
                            carrier_code=release_order_database[current_release_order][current_sales_order]["carrier_code"]
                            vessel=release_order_database[current_release_order][current_sales_order]["vessel"]
                            transport_sequential_number="TRUCK"
                            transport_type="TRUCK"
                            placeholder = st.empty()
                            with placeholder.container():
                                vehicle_id=st.text_input("**:blue[Vehicle ID]**",value="",key=7)
                                manual_bill=st.toggle("Toggle for Manual BOL")
                                if manual_bill:
                                    manual_bill_of_lading_number=st.text_input("ENTER BOL",key="eirufs")
                                mf=True
                                load_mf_number_issued=False
                                if destination=="CLEARWATER-Lewiston,ID":
                                    carrier_code=st.selectbox("Carrier Code",[carrier_code,"310897-Ashley"],disabled=False,key=29)
                                else:
                                    carrier_code=st.text_input("Carrier Code",carrier_code,disabled=True,key=9)
                                    
                                today_str=str(st.date_input("Shipment Date",datetime.datetime.today(),disabled=False,key="popdo3"))
                                
                                if 'load_mf_number' not in st.session_state:
                                    st.session_state.load_mf_number = None
                                    
                                if release_order_number in mf_numbers_for_load.keys():
                                    try:
                                        mf_liste=[i for i in mf_numbers_for_load[release_order_number][today_str][f"{carrier_code.split('-')[0]}-{carrier_code.split('-')[1]}"]]
                                    except:
                                        mf_liste=[]
                                    if len(mf_liste)>0:
                                        try:
                                            load_mf_number = st.selectbox("MF NUMBER", mf_liste, disabled=False, key=14551, index=mf_liste.index(st.session_state.load_mf_number) if st.session_state.load_mf_number else 0)
                                        except:
                                            load_mf_number = st.selectbox("MF NUMBER", mf_liste, disabled=False, key=14551)
                                        mf=True
                                        load_mf_number_issued=True
                                        yes=True
                                        st.session_state.load_mf_number = load_mf_number
                                       
                                    else:
                                        st.write(f"**:red[ASK ADMIN TO PUT SHIPMENT NUMBERS]**")
                                        mf=False
                                        yes=False
                                        load_mf_number_issued=False  
                                else:
                                    st.write(f"**:red[ASK ADMIN TO PUT MF NUMBERS]**")
                                    mf=False
                                    yes=False
                                    load_mf_number_issued=False  
                                   
                                foreman_quantity=st.number_input("**:blue[ENTER Quantity of Units]**", min_value=0, max_value=30, value=0, step=1, help=None, on_change=None, disabled=False, label_visibility="visible",key=8)
                                foreman_bale_quantity=st.number_input("**:blue[ENTER Quantity of Bales]**", min_value=0, max_value=30, value=0, step=1, help=None, on_change=None, disabled=False, label_visibility="visible",key=123)
                            click_clear1 = st.button('CLEAR VEHICLE-QUANTITY INPUTS', key=34)
                            if click_clear1:
                                 with placeholder.container():
                                     vehicle_id=st.text_input("**:blue[Vehicle ID]**",value="",key=17)
                            
                                     mf=True
                                     load_mf_number_issued=False
                                     carrier_code=st.text_input("Carrier Code",info[current_release_order][current_sales_order]["carrier_code"],disabled=True,key=19)
                                    
                                     if carrier_code=="123456-KBX":
                                       if release_order_number in mf_numbers_for_load.keys():
                                           mf_liste=[i for i in mf_numbers_for_load[release_order_number]]
                                           if len(mf_liste)>0:
                                               load_mf_number=st.selectbox("SHIPMENT NUMBER",mf_liste,disabled=False,key=14551)
                                               mf=True
                                               load_mf_number_issued=True
                                               yes=True
                                           else:
                                               st.write(f"**:red[ASK ADMIN TO PUT SHIPMENT NUMBERS]**")
                                               mf=False
                                               yes=False
                                               load_mf_number_issued=False  
                                       else:
                                           st.write(f"**:red[ASK ADMIN TO PUT MF NUMBERS]**")
                                           mf=False
                                           yes=False
                                           load_mf_number_issued=False  
                                     foreman_quantity=st.number_input("**:blue[ENTER Quantity of Units]**", min_value=0, max_value=30, value=0, step=1, help=None, on_change=None, disabled=False, label_visibility="visible",key=18)
                                     foreman_bale_quantity=st.number_input("**:blue[ENTER Quantity of Bales]**", min_value=0, max_value=30, value=0, step=1, help=None, on_change=None, disabled=False, label_visibility="visible",key=1123)
                                     
                                   
                            
                                    
                            
                        with col2:
                            ocean_bol_to_batch = {"GSSWKIR6013D": 45302855,"GSSWKIR6013E": 45305548}
                            if double_load:
                                #release_order_number=st.text_input("Release Order Number",current_release_order,disabled=True,help="Release Order Number without the Item no")
                                release_order_number=current_release_order
                                #sales_order_item=st.text_input("Sales Order Item (Material Code)",current_sales_order,disabled=True)
                                sales_order_item=current_sales_order
                                #ocean_bill_of_lading=st.text_input("Ocean Bill Of Lading",info[current_release_order][current_sales_order]["ocean_bill_of_lading"],disabled=True)
                                ocean_bill_of_lading=info[current_release_order][current_sales_order]["ocean_bill_of_lading"]
                                current_ocean_bill_of_lading=ocean_bill_of_lading
                                next_ocean_bill_of_lading=info[next_release_order][next_sales_order]["ocean_bill_of_lading"]
                                #batch=st.text_input("Batch",info[current_release_order][current_sales_order]["batch"],disabled=True)
                                batch=info[current_release_order][current_sales_order]["batch"]
                                #grade=st.text_input("Grade",info[current_release_order][current_sales_order]["grade"],disabled=True)
                                grade=info[current_release_order][current_sales_order]["grade"]
                                
                                #terminal_bill_of_lading=st.text_input("Terminal Bill of Lading",disabled=False)
                                pass
                            else:
                                release_order_number=current_release_order
                                sales_order_item=current_sales_order
                                ocean_bill_of_lading=release_order_database[current_release_order][current_sales_order]["ocean_bill_of_lading"]
                                
                                batch=release_order_database[current_release_order][current_sales_order]["batch"]
                         
                                grade=release_order_database[current_release_order][current_sales_order]["grade"]
                                
                       
                            updated_quantity=0
                            live_quantity=0
                            if updated_quantity not in st.session_state:
                                st.session_state.updated_quantity=updated_quantity
                            load_digit=-2 if vessel=="KIRKENES-2304" else -3
                            def audit_unit(x):
                                if vessel=="LAGUNA-3142":
                                    return True
                                if vessel=="KIRKENES-2304":
                                    if len(x)>=10:
                                        if bill_mapping[vessel][x[:-2]]["Ocean_bl"]!=ocean_bill_of_lading and bill_mapping[vessel][x[:-2]]["Batch"]!=batch:
                                            st.write("**:red[WRONG B/L, DO NOT LOAD BELOW!]**")
                                            return False
                                        else:
                                            return True
                                else:
                                    if bill_mapping[vessel][x[:-3]]["Ocean_bl"]!=ocean_bill_of_lading and bill_mapping[vessel][x[:-3]]["Batch"]!=batch:
                                        return False
                                    else:
                                        return True
                            def audit_split(release,sales):
                                if vessel=="KIRKENES-2304":
                                    if len(x)>=10:
                                        if bill_mapping[vessel][x[:-2]]["Ocean_bl"]!=ocean_bill_of_lading and bill_mapping[vessel][x[:-2]]["Batch"]!=batch:
                                            st.write("**:red[WRONG B/L, DO NOT LOAD BELOW!]**")
                                            return False
                                        else:
                                            return True
                                else:
                                    if bill_mapping[vessel][x[:-3]]["Ocean_bl"]!=ocean_bill_of_lading and bill_mapping[vessel][x[:-3]]["Batch"]!=batch:
                                            return False
                                    else:
                                        return True
                            
                            flip=False 
                            first_load_input=None
                            second_load_input=None
                            load_input=None
                            bale_load_input=None
                            if double_load:
                                
                                try:
                                    next_item=gcp_download("olym_suzano",rf"release_orders/{dispatched['2']['vessel']}/{dispatched['2']['release_order']}.json")
                                    
                                    first_load_input=st.text_area("**FIRST SKU LOADS**",height=300)
                                    first_quantity=0
                                    second_quantity=0
                                    if first_load_input is not None:
                                        first_textsplit = first_load_input.splitlines()
                                        first_textsplit=[i for i in first_textsplit if len(i)>8]
                                        first_quantity=len(first_textsplit)
                                    second_load_input=st.text_area("**SECOND SKU LOADS**",height=300)
                                    if second_load_input is not None:
                                        second_textsplit = second_load_input.splitlines()
                                        second_textsplit = [i for i in second_textsplit if len(i)>8]
                                        second_quantity=len(second_textsplit)
                                    updated_quantity=first_quantity+second_quantity
                                    st.session_state.updated_quantity=updated_quantity
                                except Exception as e: 
                                    st.write(e)
                                    #st.markdown("**:red[ONLY ONE ITEM IN QUEUE ! ASK NEXT ITEM TO BE DISPATCHED!]**")
                                    pass
                                
                            
                            else:
                                
                
                
                                placeholder1 = st.empty()
                                
                                
                                
                                load_input=placeholder1.text_area("**UNITS**",value="",height=300,key=1)#[:-2]
                            
                                
                        with col3:
                            placeholder2 = st.empty()
                            bale_load_input=placeholder2.text_area("**INDIVIDUAL BALES**",value="",height=300,key=1111)#[:-2]
                            
                                
                        with col2:
                            click_clear = st.button('CLEAR SCANNED INPUTS', key=3)
                            if click_clear:
                                load_input = placeholder1.text_area("**UNITS**",value="",height=300,key=2)#
                                bale_load_input=placeholder2.text_area("**INDIVIDUAL BALES**",value="",height=300,key=1121)#
                            if load_input is not None :
                                textsplit = load_input.splitlines()
                                textsplit=[i for i in textsplit if len(i)>8]
                                updated_quantity=len(textsplit)
                                st.session_state.updated_quantity=updated_quantity
                            if bale_load_input is not None:
                                bale_textsplit = bale_load_input.splitlines()
                                bale_textsplit=[i for i in bale_textsplit if len(i)>8]
                                bale_updated_quantity=len(bale_textsplit)
                                st.session_state.updated_quantity=updated_quantity+bale_updated_quantity*0.125
                           
                        with col4:
                            
                            if double_load:
                                first_faults=[]
                                if first_load_input is not None:
                                    first_textsplit = first_load_input.splitlines()
                                    first_textsplit=[i for i in first_textsplit if len(i)>8]
                                    #st.write(textsplit)
                                    for j,x in enumerate(first_textsplit):
                                        if audit_split(current_release_order,current_sales_order):
                                            st.text_input(f"Unit No : {j+1}",x)
                                            first_faults.append(0)
                                        else:
                                            st.text_input(f"Unit No : {j+1}",x)
                                            first_faults.append(1)
                                second_faults=[]
                                if second_load_input is not None:
                                    second_textsplit = second_load_input.splitlines()
                                    second_textsplit = [i for i in second_textsplit if len(i)>8]
                                    #st.write(textsplit)
                                    for i,x in enumerate(second_textsplit):
                                        if audit_split(next_release_order,next_sales_order):
                                            st.text_input(f"Unit No : {len(first_textsplit)+1+i}",x)
                                            second_faults.append(0)
                                        else:
                                            st.text_input(f"Unit No : {j+1+i+1}",x)
                                            second_faults.append(1)
                
                                loads=[]
                                
                                for k in first_textsplit:
                                    loads.append(k)
                                for l in second_textsplit:
                                    loads.append(l)
                                    
                            ####   IF NOT double load
                            else:
                                
                                past_loads=[]
                                for row in bill_of_ladings.keys():
                                    if row!="11502400":
                                        past_loads+=[load for load in bill_of_ladings[row]['loads'].keys()]
                                faults=[]
                                bale_faults=[]
                                fault_messaging={}
                                bale_fault_messaging={}
                                textsplit={}
                                bale_textsplit={}
                                if load_input is not None:
                                    textsplit = load_input.splitlines()
                                    
                                        
                                    textsplit=[i for i in textsplit if len(i)>8]
                               
                                    seen=set()
                                    alien_units=json.loads(gcp_download(target_bucket,rf"alien_units.json"))
                                    for i,x in enumerate(textsplit):
                                        alternate_vessels=[ship for ship in bill_mapping if ship!=vessel]
                                        if x[:load_digit] in ["ds"]:
                                            st.markdown(f"**:red[Unit No : {i+1}-{x}]**",unsafe_allow_html=True)
                                            faults.append(1)
                                            st.markdown("**:red[THIS LOT# IS FROM THE OTHER VESSEL!]**")
                                        else:
                                                
                                            if x[:load_digit] in bill_mapping[vessel] or vessel=="LAGUNA-3142" :
                                                if audit_unit(x):
                                                    if x in seen:
                                                        st.markdown(f"**:red[Unit No : {i+1}-{x}]**",unsafe_allow_html=True)
                                                        faults.append(1)
                                                        st.markdown("**:red[This unit has been scanned TWICE!]**")
                                                    if x in past_loads:
                                                        st.markdown(f"**:red[Unit No : {i+1}-{x}]**",unsafe_allow_html=True)
                                                        faults.append(1)
                                                        st.markdown("**:red[This unit has been SHIPPED!]**")   
                                                    else:
                                                        st.write(f"**Unit No : {i+1}-{x}**")
                                                        faults.append(0)
                                                else:
                                                    st.markdown(f"**:red[Unit No : {i+1}-{x}]**",unsafe_allow_html=True)
                                                    st.write(f"**:red[WRONG B/L, DO NOT LOAD UNIT {x}]**")
                                                    faults.append(1)
                                                seen.add(x)
                                            else:
                                                #st.markdown(f"**:red[Unit No : {i+1}-{x}]**",unsafe_allow_html=True)
                                                faults.append(1)
                                                #st.markdown("**:red[This LOT# NOT IN INVENTORY!]**")
                                                #st.info(f"VERIFY THIS UNIT CAME FROM {vessel} - {'Unwrapped' if grade=='ISU' else 'wrapped'} piles")
                                                with st.expander(f"**:red[Unit No : {i+1}-{x} This LOT# NOT IN INVENTORY!---VERIFY UNIT {x} CAME FROM {vessel} - {'Unwrapped' if grade=='ISU' else 'wrapped'} piles]**"):
                                                    st.write("Verify that the unit came from the pile that has the units for this release order and click to inventory")
                                                    if st.button("ADD UNIT TO INVENTORY",key=f"{x}"):
                                                        updated_bill=bill_mapping.copy()
                                                        updated_bill[vessel][x[:load_digit]]={"Batch":batch,"Ocean_bl":ocean_bill_of_lading}
                                                        updated_bill=json.dumps(updated_bill)
                                                        #storage_client = storage.Client()
                                                        storage_client = get_storage_client()
                                                        bucket = storage_client.bucket(target_bucket)
                                                        blob = bucket.blob(rf"bill_mapping.json")
                                                        blob.upload_from_string(updated_bill)
        
                                                        alien_units=gcp_download(target_bucket,rf"alien_units.json")
                                                        alien_units=json.loads(alien_units)
                                                        if vessel not in alien_units:
                                                            alien_units[vessel]={}
                                                        alien_units[vessel][x]={}
                                                        alien_units[vessel][x]={"Ocean_Bill_Of_Lading":ocean_bill_of_lading,"Batch":batch,"Grade":grade,
                                                                                "Date_Found":datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%Y,%m-%d %H:%M:%S")}
                                                        alien_units=json.dumps(alien_units)
                                                        #storage_client = storage.Client()
                                                        storage_client = get_storage_client()
                                                        bucket = storage_client.bucket(target_bucket)
                                                        blob = bucket.blob(rf"alien_units.json")
                                                        blob.upload_from_string(alien_units)
                                                        
                                                        
                                                        subject=f"FOUND UNIT {x} NOT IN INVENTORY"
                                                        body=f"Clerk identified an uninventoried {'Unwrapped' if grade=='ISU' else 'wrapped'} unit {x}, and after verifying the physical pile, inventoried it into Ocean Bill Of Lading : {ocean_bill_of_lading} for vessel {vessel}. Unit has been put into alien unit list."
                                                        sender = "warehouseoly@gmail.com"
                                                        #recipients = ["alexandras@portolympia.com","conleyb@portolympia.com", "afsiny@portolympia.com"]
                                                        recipients = ["afsiny@portolympia.com"]
                                                        password = "xjvxkmzbpotzeuuv"
                                                        send_email(subject, body, sender, recipients, password)
                                                        time.sleep(0.1)
                                                        st.success(f"Added Unit {x} to Inventory!",icon="✅")
                                                        st.rerun()
                                        
                                if bale_load_input is not None:
                                
                                    bale_textsplit = bale_load_input.splitlines()                       
                                    bale_textsplit=[i for i in bale_textsplit if len(i)>8]                           
                                    seen=set()
                                    alien_units=json.loads(gcp_download(target_bucket,rf"alien_units.json"))
                                    for i,x in enumerate(bale_textsplit):
                                        alternate_vessel=[ship for ship in bill_mapping if ship!=vessel][0]
                                        if x[:load_digit] in bill_mapping[alternate_vessel]:
                                            st.markdown(f"**:red[Bale No : {i+1}-{x}]**",unsafe_allow_html=True)
                                            faults.append(1)
                                            st.markdown("**:red[THIS BALE LOT# IS FROM THE OTHER VESSEL!]**")
                                        else:
                                            if x[:load_digit] in bill_mapping[vessel]:
                                                if audit_unit(x):
                                                    st.write(f"**Bale No : {i+1}-{x}**")
                                                    faults.append(0)
                                                else:
                                                    st.markdown(f"**:red[Bale No : {i+1}-{x}]**",unsafe_allow_html=True)
                                                    st.write(f"**:red[WRONG B/L, DO NOT LOAD BALE {x}]**")
                                                    faults.append(1)
                                                seen.add(x)
                                            else:
                                                faults.append(1)
                                                with st.expander(f"**:red[Bale No : {i+1}-{x} This LOT# NOT IN INVENTORY!---VERIFY BALE {x} CAME FROM {vessel} - {'Unwrapped' if grade=='ISU' else 'wrapped'} piles]**"):
                                                    st.write("Verify that the bale came from the pile that has the units for this release order and click to inventory")
                                                    if st.button("ADD BALE TO INVENTORY",key=f"{x}"):
                                                        updated_bill=bill_mapping.copy()
                                                        updated_bill[vessel][x[:load_digit]]={"Batch":batch,"Ocean_bl":ocean_bill_of_lading}
                                                        updated_bill=json.dumps(updated_bill)
                                                        #storage_client = storage.Client()
                                                        storage_client = get_storage_client()
                                                        bucket = storage_client.bucket(target_bucket)
                                                        blob = bucket.blob(rf"bill_mapping.json")
                                                        blob.upload_from_string(updated_bill)
        
                                                        alien_units=json.loads(gcp_download(target_bucket,rf"alien_units.json"))
                                                        alien_units[vessel][x]={}
                                                        alien_units[vessel][x]={"Ocean_Bill_Of_Lading":ocean_bill_of_lading,"Batch":batch,"Grade":grade,
                                                                                "Date_Found":datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%Y,%m-%d %H:%M:%S")}
                                                        alien_units=json.dumps(alien_units)
                                                       # storage_client = storage.Client()
                                                        storage_client = get_storage_client()
                                                        bucket = storage_client.bucket(target_bucket)
                                                        blob = bucket.blob(rf"alien_units.json")
                                                        blob.upload_from_string(alien_units)
                                                        
                                                        
                                                        subject=f"FOUND UNIT {x} NOT IN INVENTORY"
                                                        body=f"Clerk identified an uninventoried {'Unwrapped' if grade=='ISU' else 'wrapped'} unit {x}, and after verifying the physical pile, inventoried it into Ocean Bill Of Lading : {ocean_bill_of_lading} for vessel {vessel}. Unit has been put into alien unit list."
                                                        sender = "warehouseoly@gmail.com"
                                                        #recipients = ["alexandras@portolympia.com","conleyb@portolympia.com", "afsiny@portolympia.com"]
                                                        recipients = ["afsiny@portolympia.com"]
                                                        password = "xjvxkmzbpotzeuuv"
                                                        send_email(subject, body, sender, recipients, password)
                                                        time.sleep(0.1)
                                                        st.success(f"Added Unit {x} to Inventory!",icon="✅")
                                                       # st.rerun()
                               
                                   
                                loads={}
                                pure_loads={}
                                yes=True
                                if 1 in faults or 1 in bale_faults:
                                    yes=False
                                
                                if yes:
                                    pure_loads={**{k:0 for k in textsplit},**{k:0 for k in bale_textsplit}}
                                    loads={**{k[:load_digit]:0 for k in textsplit},**{k[:load_digit]:0 for k in bale_textsplit}}
                                    for k in textsplit:
                                        loads[k[:load_digit]]+=1
                                        pure_loads[k]+=1
                                    for k in bale_textsplit:
                                        loads[k[:load_digit]]+=0.125
                                        pure_loads[k]+=0.125
                        with col3:
                            quantity=st.number_input("**Scanned Quantity of Units**",st.session_state.updated_quantity, key=None, help=None, on_change=None, disabled=True, label_visibility="visible")
                            st.markdown(f"**{quantity*2} TONS - {round(quantity*2*2204.62,1)} Pounds**")
                            
                            admt=round(float(release_order_database[current_release_order][current_sales_order]["dryness"])/90*st.session_state.updated_quantity*2,4)
                            st.markdown(f"**ADMT= {admt} TONS**")
                        manual_time=False   
                        #st.write(faults)                  
                        if st.checkbox("Check for Manual Entry for Date/Time"):
                            manual_time=True
                            file_date=st.date_input("File Date",datetime.datetime.today(),disabled=False,key="popo3")
                            a=datetime.datetime.strftime(file_date,"%Y%m%d")
                            a_=datetime.datetime.strftime(file_date,"%Y-%m-%d")
                            file_time = st.time_input('FileTime', datetime.datetime.now()-datetime.timedelta(hours=utc_difference),step=60,disabled=False,key="popop")
                            b=file_time.strftime("%H%M%S")
                            b_=file_time.strftime("%H:%M:%S")
                            c=datetime.datetime.strftime(eta_date,"%Y%m%d")
                        else:     
                            
                            a=datetime.datetime.strftime(file_date,"%Y%m%d")
                            a_=datetime.datetime.strftime(file_date,"%Y-%m-%d")
                            b=file_time.strftime("%H%M%S")
                            b=(datetime.datetime.now()-datetime.timedelta(hours=utc_difference)).strftime("%H%M%S")
                            b_=(datetime.datetime.now()-datetime.timedelta(hours=utc_difference)).strftime("%H:%M:%S")
                            c=datetime.datetime.strftime(eta_date,"%Y%m%d")
                            
                            
                        
                        liste=[(i,datetime.datetime.strptime(bill_of_ladings[i]['issued'],"%Y-%m-%d %H:%M:%S")) for i in bill_of_ladings if i!="11502400"]
                        liste.sort(key=lambda a: a[1])
                        last_submitted=[i[0] for i in liste[-3:]]
                        last_submitted.reverse()
                        st.markdown(f"**Last Submitted Bill Of Ladings (From most recent) : {last_submitted}**")
                        
                        
                        
                        if yes and mf and quantity>0:
                            
                            if st.button('**:blue[SUBMIT EDI]**'):
                             
                                proceed=True
                                if not yes:
                                    proceed=False
                                             
                                if fault_messaging.keys():
                                    for i in fault_messaging.keys():
                                        error=f"**:red[Unit {fault_messaging[i]}]**"
                                        proceed=False
                                if remaining<0:
                                    proceed=False
                                    error="**:red[No more Items to ship on this Sales Order]"
                                    st.write(error)
                                if not vehicle_id: 
                                    proceed=False
                                    error="**:red[Please check Vehicle ID]**"
                                    st.write(error)
                                
                                if quantity!=foreman_quantity+int(foreman_bale_quantity)/8:
                                    proceed=False
                                    error=f"**:red[{updated_quantity} units and {bale_updated_quantity} bales on this truck. Please check. You planned for {foreman_quantity} units and {foreman_bale_quantity} bales!]** "
                                    st.write(error)
                                if proceed:
                                    carrier_code_mf=f"{carrier_code.split('-')[0]}-{carrier_code.split('-')[1]}"
                                    carrier_code=carrier_code.split("-")[0]
                                    
                                    suzano_report=gcp_download(target_bucket,rf"suzano_report.json")
                                    suzano_report=json.loads(suzano_report)
        
                                    consignee=destination.split("-")[0]
                                    consignee_city=mill_info[destination]["city"]
                                    consignee_state=mill_info[destination]["state"]
                                    vessel_suzano,voyage_suzano=vessel.split("-")
                                    if manual_time:
                                        eta=datetime.datetime.strftime(file_date+datetime.timedelta(hours=mill_info[destination]['Driving_Hours']-utc_difference)+datetime.timedelta(minutes=mill_info[destination]['Driving_Minutes']+30),"%Y-%m-%d  %H:%M:%S")
                                    else:
                                        eta=datetime.datetime.strftime(datetime.datetime.now()+datetime.timedelta(hours=mill_info[destination]['Driving_Hours']-utc_difference)+datetime.timedelta(minutes=mill_info[destination]['Driving_Minutes']+30),"%Y-%m-%d  %H:%M:%S")
            
                                    if double_load:
                                        bill_of_lading_number,bill_of_ladings=gen_bill_of_lading()
                                        edi_name= f'{bill_of_lading_number}.txt'
                                        bill_of_ladings[str(bill_of_lading_number)]={"vessel":vessel,"release_order":release_order_number,"destination":destination,"sales_order":current_sales_order,
                                                                                     "ocean_bill_of_lading":ocean_bill_of_lading,"grade":wrap,"carrier_id":carrier_code,"vehicle":vehicle_id,
                                                                                     "quantity":len(first_textsplit),"issued":f"{a_} {b_}","edi_no":edi_name} 
                                        bill_of_ladings[str(bill_of_lading_number+1)]={"vessel":vessel,"release_order":release_order_number,"destination":destination,"sales_order":next_sales_order,
                                                                                     "ocean_bill_of_lading":ocean_bill_of_lading,"grade":wrap,"carrier_id":carrier_code,"vehicle":vehicle_id,
                                                                                     "quantity":len(second_textsplit),"issued":f"{a_} {b_}","edi_no":edi_name} 
                                    
                                    else:
                                        bill_of_lading_number,bill_of_ladings=gen_bill_of_lading()
                                        if load_mf_number_issued:
                                            bill_of_lading_number=st.session_state.load_mf_number
                                        if manual_bill:
                                            bill_of_lading_number=manual_bill_of_lading_number
                                        edi_name= f'{bill_of_lading_number}.txt'
                                        bill_of_ladings[str(bill_of_lading_number)]={"vessel":vessel,"release_order":release_order_number,"destination":destination,"sales_order":current_sales_order,
                                                                                     "ocean_bill_of_lading":ocean_bill_of_lading,"grade":wrap,"carrier_id":carrier_code,"vehicle":vehicle_id,
                                                                                     "quantity":st.session_state.updated_quantity,"issued":f"{a_} {b_}","edi_no":edi_name,"loads":pure_loads} 
                                                        
                                    bill_of_ladings=json.dumps(bill_of_ladings)
                                    #storage_client = storage.Client()
                                    storage_client = get_storage_client()
                                    bucket = storage_client.bucket(target_bucket)
                                    blob = bucket.blob(rf"terminal_bill_of_ladings.json")
                                    blob.upload_from_string(bill_of_ladings)
                                    
                                    
                                    
                                    terminal_bill_of_lading=st.text_input("Terminal Bill of Lading",bill_of_lading_number,disabled=True)
                                    success_container=st.empty()
                                    success_container.info("Uploading Bill of Lading")
                                    time.sleep(0.1) 
                                    success_container.success("Uploaded Bill of Lading...",icon="✅")
                                    process()
                                    #st.toast("Creating EDI...")
                                    try:
                                        suzano_report_keys=[int(i) for i in suzano_report.keys()]
                                        next_report_no=max(suzano_report_keys)+1
                                    except:
                                        next_report_no=1
                                    if double_load:
                                        
                                        suzano_report.update({next_report_no:{"Date Shipped":f"{a_} {b_}","Vehicle":vehicle_id, "Shipment ID #": bill_of_lading_number, "Consignee":consignee,"Consignee City":consignee_city,
                                                             "Consignee State":consignee_state,"Release #":release_order_number,"Carrier":carrier_code,
                                                             "ETA":eta,"Ocean BOL#":ocean_bill_of_lading,"Warehouse":"OLYM","Vessel":vessel_suzano,"Voyage #":voyage_suzano,"Grade":wrap,"Quantity":quantity,
                                                             "Metric Ton": quantity*2, "ADMT":admt,"Mode of Transportation":transport_type}})
                                    else:
                                       
                                        suzano_report.update({next_report_no:{"Date Shipped":f"{a_} {b_}","Vehicle":vehicle_id, "Shipment ID #": bill_of_lading_number, "Consignee":consignee,"Consignee City":consignee_city,
                                                             "Consignee State":consignee_state,"Release #":release_order_number,"Carrier":carrier_code,
                                                             "ETA":eta,"Ocean BOL#":ocean_bill_of_lading,"Batch#":batch,
                                                             "Warehouse":"OLYM","Vessel":vessel_suzano,"Voyage #":voyage_suzano,"Grade":wrap,"Quantity":quantity,
                                                             "Metric Ton": quantity*2, "ADMT":admt,"Mode of Transportation":transport_type}})
                                        suzano_report=json.dumps(suzano_report)
                                        #storage_client = storage.Client()
                                        storage_client = get_storage_client()
                                        bucket = storage_client.bucket(target_bucket)
                                        blob = bucket.blob(rf"suzano_report.json")
                                        blob.upload_from_string(suzano_report)
                                        success_container1=st.empty()
                                        time.sleep(0.1)                            
                                        success_container1.success(f"Updated Suzano Report",icon="✅")
            
                                      
                                        
                                    if double_load:
                                        info[current_release_order][current_sales_order]["shipped"]=info[current_release_order][current_sales_order]["shipped"]+len(first_textsplit)
                                        info[current_release_order][current_sales_order]["remaining"]=info[current_release_order][current_sales_order]["remaining"]-len(first_textsplit)
                                        info[next_release_order][next_sales_order]["shipped"]=info[next_release_order][next_sales_order]["shipped"]+len(second_textsplit)
                                        info[next_release_order][next_sales_order]["remaining"]=info[next_release_order][next_sales_order]["remaining"]-len(second_textsplit)
                                    else:
                                        release_order_database[current_release_order][current_sales_order]["shipped"]=release_order_database[current_release_order][current_sales_order]["shipped"]+quantity
                                        release_order_database[current_release_order][current_sales_order]["remaining"]=release_order_database[current_release_order][current_sales_order]["remaining"]-quantity
                                    if release_order_database[current_release_order][current_sales_order]["remaining"]<=0:
                                        to_delete=[]
                                        for release in dispatched.keys():
                                            if release==current_release_order:
                                                for sales in dispatched[release].keys():
                                                    if sales==current_sales_order:
                                                        to_delete.append((release,sales))
                                        for victim in to_delete:
                                            del dispatched[victim[0]][victim[1]]
                                            if len(dispatched[victim[0]].keys())==0:
                                                del dispatched[victim[0]]
                                        
                                        json_data = json.dumps(dispatched)
                                        #storage_client = storage.Client()
                                        storage_client = get_storage_client()
                                        bucket = storage_client.bucket(target_bucket)
                                        blob = bucket.blob(rf"dispatched.json")
                                        blob.upload_from_string(json_data)       
                                    def check_complete(data,ro):
                                        complete=True
                                        for i in data[ro]:
                                            if i in ["001","002","003","004","005"]:
                                                if data[ro][i]['remaining']>0:
                                                    complete=False
                                        return complete
                                    if check_complete(release_order_database,current_release_order):
                                        release_order_database[current_release_order]['complete']=True
                                    
                                    json_data = json.dumps(release_order_database)
                                    #storage_client = storage.Client()
                                    storage_client = get_storage_client()
                                    bucket = storage_client.bucket(target_bucket)
                                    blob = bucket.blob(rf"release_orders/RELEASE_ORDERS.json")
                                    blob.upload_from_string(json_data)
                                                              
                                    success_container3=st.empty()
                                    time.sleep(0.1)                            
                                    success_container3.success(f"Updated Release Order Database",icon="✅")
                                    with open('placeholder.txt', 'r') as f:
                                        output_text = f.read()
                                    
                                    #st.markdown("**EDI TEXT**")
                                    #st.text_area('', value=output_text, height=600)
                                    with open('placeholder.txt', 'r') as f:
                                        file_content = f.read()
                                    newline="\n"
                                    filename = f'{bill_of_lading_number}'
                                    file_name= f'{bill_of_lading_number}.txt'
                                    
                                    
                                    subject = f'Suzano_EDI_{a}_ R.O:{release_order_number}-Terminal BOL :{bill_of_lading_number}-Destination : {destination}'
                                    body = f"EDI for Below attached.{newline}Release Order Number : {current_release_order} - Sales Order Number:{current_sales_order}{newline} Destination : {destination} Ocean Bill Of Lading : {ocean_bill_of_lading}{newline}Terminal Bill of Lading: {terminal_bill_of_lading} - Grade : {wrap} {newline}{2*quantity} tons {unitized} cargo were loaded to vehicle : {vehicle_id} with Carried ID : {carrier_code} {newline}Truck loading completed at {a_} {b_}"
                                    #st.write(body)           
                                    sender = "warehouseoly@gmail.com"
                                    recipients = ["alexandras@portolympia.com","conleyb@portolympia.com", "afsiny@portolympia.com"]
                                    #recipients = ["afsiny@portolympia.com"]
                                    password = "xjvxkmzbpotzeuuv"
                            
                          
                            
                            
                                    with open('temp_file.txt', 'w') as f:
                                        f.write(file_content)
                            
                                    file_path = 'temp_file.txt'  # Use the path of the temporary file
                            
                                    
                                    upload_cs_file(target_bucket, 'temp_file.txt',rf"EDIS/{file_name}")
                                    success_container5=st.empty()
                                    time.sleep(0.1)                            
                                    success_container5.success(f"Uploaded EDI File",icon="✅")
                                    if load_mf_number_issued:
                                        mf_numbers_for_load[release_order_number][a_][carrier_code_mf].remove(load_mf_number)
                                        mf_numbers_for_load=json.dumps(mf_numbers_for_load)
                                        #storage_client = storage.Client()
                                        storage_client = get_storage_client()
                                        bucket = storage_client.bucket(target_bucket)
                                        blob = bucket.blob(rf"release_orders/mf_numbers.json")
                                        blob.upload_from_string(mf_numbers_for_load)
                                        st.write("Updated MF numbers...")
                                    send_email_with_attachment(subject, body, sender, recipients, password, file_path,file_name)
                                    success_container6=st.empty()
                                    time.sleep(0.1)                            
                                    success_container6.success(f"Sent EDI Email",icon="✅")
                                    st.markdown("**SUCCESS! EDI FOR THIS LOAD HAS BEEN SUBMITTED,THANK YOU**")
                                    st.write(filename,current_release_order,current_sales_order,destination,ocean_bill_of_lading,terminal_bill_of_lading,wrap)
                                    this_shipment_aliens=[]
                                    for i in pure_loads:
                                        try:
                                                
                                            if i in alien_units[vessel]:       
                                                alien_units[vessel][i]={"Ocean_Bill_Of_Lading":ocean_bill_of_lading,"Batch":batch,"Grade":grade,
                                                        "Date_Found":datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%Y,%m-%d %H:%M:%S"),
                                                        "Destination":destination,"Release_Order":current_release_order,"Terminal_Bill_of Lading":terminal_bill_of_lading,"Truck":vehicle_id}
                                                this_shipment_aliens.append(i)
                                            if i not in alien_units[vessel]:
                                                if i[:-2] in [u[:-2] for u in alien_units[vessel]]:
                                                    alien_units[vessel][i]={"Ocean_Bill_Of_Lading":ocean_bill_of_lading,"Batch":batch,"Grade":grade,
                                                        "Date_Found":datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%Y,%m-%d %H:%M:%S"),
                                                        "Destination":destination,"Release_Order":current_release_order,"Terminal_Bill_of Lading":terminal_bill_of_lading,"Truck":vehicle_id}
                                                    this_shipment_aliens.append(i)
                                        except:
                                            pass
                                    alien_units=json.dumps(alien_units)
                                    #storage_client = storage.Client()
                                    storage_client = get_storage_client()
                                    bucket = storage_client.bucket(target_bucket)
                                    blob = bucket.blob(rf"alien_units.json")
                                    blob.upload_from_string(alien_units)   
                                    
                                    if len(this_shipment_aliens)>0:
                                        subject=f"UNREGISTERED UNITS SHIPPED TO {destination} on RELEASE ORDER {current_release_order}"
                                        body=f"{len([i for i in this_shipment_aliens])} unregistered units were shipped on {vehicle_id} to {destination} on {current_release_order}.<br>{[i for i in this_shipment_aliens]}"
                                        sender = "warehouseoly@gmail.com"
                                        recipients = ["alexandras@portolympia.com","conleyb@portolympia.com", "afsiny@portolympia.com"]
                                        #recipients = ["afsiny@portolympia.com"]
                                        password = "xjvxkmzbpotzeuuv"
                                        send_email(subject, body, sender, recipients, password)
                                    
                                else:   ###cancel bill of lading
                                    pass
            
                        
    
        
                    
                    else:
                        st.subheader("**Nothing dispatched!**")
                    
            
                    
                        
        ##########################################################################
        
                
                        
        if select=="INVENTORY" :

            #map=gcp_download_new(target_bucket,rf"map.json")
            map=gcp_download(target_bucket,rf"map.json")
            map=json.loads(map)
            mill_info=map["mill_info"]
            inv_bill_of_ladings=gcp_download(target_bucket,rf"terminal_bill_of_ladings.json")
            inv_bill_of_ladings=pd.read_json(inv_bill_of_ladings).T
         
            raw_ro=gcp_download(target_bucket,rf"release_orders/RELEASE_ORDERS.json")
            raw_ro = json.loads(raw_ro)
            bol_mapping = map["bol_mapping"]
            
            suzano,edi_bank,main_inventory,status,mill_progress=st.tabs(["SUZANO DAILY REPORTS","EDI BANK","MAIN INVENTORY","RELEASE ORDER STATUS","SUZANO MILL SHIPMENT SCHEDULE/PROGRESS"])
            
            with suzano:
                
                def convert_df(df):
                    # IMPORTANT: Cache the conversion to prevent computation on every rerun
                    return df.to_csv().encode('utf-8')
                
                now=datetime.datetime.now()-datetime.timedelta(hours=utc_difference)
                suzano_report_=gcp_download(target_bucket,rf"suzano_report.json")
                suzano_report=json.loads(suzano_report_)
                suzano_report=pd.DataFrame(suzano_report).T
                suzano_report=suzano_report[["Date Shipped","Vehicle", "Shipment ID #", "Consignee","Consignee City","Consignee State","Release #","Carrier","ETA","Ocean BOL#","Batch#","Warehouse","Vessel","Voyage #","Grade","Quantity","Metric Ton", "ADMT","Mode of Transportation"]]
                suzano_report["Shipment ID #"]=[str(i) for i in suzano_report["Shipment ID #"]]
                suzano_report["Batch#"]=[str(i) for i in suzano_report["Batch#"]]
                daily_suzano=suzano_report.copy()
                daily_suzano["Date"]=[datetime.datetime.strptime(i,"%Y-%m-%d %H:%M:%S").date() for i in suzano_report["Date Shipped"]]
                daily_suzano_=daily_suzano[daily_suzano["Date"]==now.date()]
                
                
                choose = st.radio(
                                "Select Daily or Accumulative Report",
                                ["DAILY", "ACCUMULATIVE", "FIND BY DATE","FIND DATE RANGE","BY RELEASE ORDER","BY BATCH"])
                if choose=="DAILY":
                    daily_suzano_=daily_suzano_.reset_index(drop=True)
                    daily_suzano_.index=[i+1 for i in daily_suzano_.index]
                    daily_suzano_.loc["TOTAL"]=daily_suzano_[["Quantity","Metric Ton","ADMT"]].sum()
                    st.dataframe(daily_suzano_)
                    csv=convert_df(daily_suzano_)
                    file_name=f'OLYMPIA_DAILY_REPORT-{datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%m-%d,%Y")}.csv'
                elif choose=="FIND BY DATE":
                    required_date=st.date_input("CHOOSE DATE",key="dssar")
                    filtered_suzano=daily_suzano[daily_suzano["Date"]==required_date]
                    filtered_suzano=filtered_suzano.reset_index(drop=True)
                    filtered_suzano.index=[i+1 for i in filtered_suzano.index]
                    filtered_suzano.loc["TOTAL"]=filtered_suzano[["Quantity","Metric Ton","ADMT"]].sum()
                    st.dataframe(filtered_suzano)
                    csv=convert_df(filtered_suzano)
                    file_name=f'OLYMPIA_SHIPMENT_REPORT-{datetime.datetime.strftime(required_date,"%m-%d,%Y")}.csv'

                elif choose=="BY RELEASE ORDER":
                    report_ro=st.selectbox("SELECT RELEASE ORDER",([i for i in raw_ro]),key="sdgerw")
                    ro_suzano=daily_suzano[daily_suzano["Release #"]==report_ro]
                    ro_suzano=ro_suzano.reset_index(drop=True)
                    ro_suzano.index=[i+1 for i in ro_suzano.index]
                    ro_suzano.loc["TOTAL"]=ro_suzano[["Quantity","Metric Ton","ADMT"]].sum()
                    st.dataframe(ro_suzano)
                    csv=convert_df(ro_suzano)
                    file_name=f'OLYMPIA_SHIPMENT_REPORT-ReleaseOrder-{report_ro}.csv'

                elif choose=="BY BATCH":
                    report_batch=st.selectbox("SELECT BATCH",(daily_suzano["Batch#"].unique()),key="sddgerw")
                    batch_suzano=daily_suzano[daily_suzano["Batch#"]==report_batch]
                    batch_suzano=batch_suzano.reset_index(drop=True)
                    batch_suzano.index=[i+1 for i in batch_suzano.index]
                    batch_suzano.loc["TOTAL"]=batch_suzano[["Quantity","Metric Ton","ADMT"]].sum()
                    st.dataframe(batch_suzano)
                    csv=convert_df(batch_suzano)
                    file_name=f'OLYMPIA_SHIPMENT_REPORT-Batch-{report_batch}.csv'

                elif choose=="FIND DATE RANGE":
                    datecol1,datecol2,datecol3=st.columns([3,3,4])
                    with datecol1:
                        tarih1=st.date_input("FROM",key="dsssaar")
                    with datecol2:
                        tarih2=st.date_input("TO",key="dssdar")
                        
                    range_suzano=daily_suzano[(daily_suzano["Date"]>=tarih1)&(daily_suzano["Date"]<=tarih2)]
                    range_suzano=range_suzano.reset_index(drop=True)
                    range_suzano.index=[i+1 for i in range_suzano.index]
                    range_suzano.loc["TOTAL"]=range_suzano[["Quantity","Metric Ton","ADMT"]].sum()
                    st.dataframe(range_suzano)
                    csv=convert_df(range_suzano)
                    file_name=f'OLYMPIA_SHIPMENT_REPORT-daterange.csv'
                
                else:
                    st.dataframe(suzano_report)
                    csv=convert_df(suzano_report)
                    file_name=f'OLYMPIA_ALL_SHIPMENTS to {datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%m-%d,%Y")}.csv'
                
                
                
               
                
            
                st.download_button(
                    label="DOWNLOAD REPORT AS CSV",
                    data=csv,
                    file_name=file_name,
                    mime='text/csv')
                

            with edi_bank:
                edi_files=list_files_in_subfolder(target_bucket, rf"EDIS/")
                requested_edi_file=st.selectbox("SELECT EDI",edi_files[1:])
                
                display_edi=st.toggle("DISPLAY EDI")
                if display_edi:
                    data=gcp_download(target_bucket, rf"EDIS/{requested_edi_file}")
                    st.text_area("EDI",data,height=400)                                
               
                st.download_button(
                    label="DOWNLOAD EDI",
                    data=gcp_download(target_bucket, rf"EDIS/{requested_edi_file}"),
                    file_name=f'{requested_edi_file}',
                    mime='text/csv')
                
                
                
            with main_inventory:
                
                maintenance=False
                                
                if maintenance:
                    st.title("CURRENTLY UNDER MAINTENANCE, CHECK BACK LATER")
                               
                else:
                    inventory,daily,unregistered=st.tabs(["INVENTORY","DAILY SHIPMENT REPORT","UNREGISTERED LOTS FOUND"])
                    
                    with daily:
                        
                        amount_dict={"KIRKENES-2304":9200,"JUVENTAS-2308":10000,"LYSEFJORD-2308":10000,"LAGUNA-3142":453,"FRONTIER-55VC":9811,"BEIJA_FLOR-88VC":11335}
                        inv_vessel=st.selectbox("Select Vessel",[i for i in map['batch_mapping']])
                        kf=inv_bill_of_ladings.iloc[1:].copy()
                        kf['issued'] = pd.to_datetime(kf['issued'])
                        kf=kf[kf["vessel"]==inv_vessel]
                        
                        kf['Date'] = kf['issued'].dt.date
                        kf['Date'] = pd.to_datetime(kf['Date'])
                        # Create a date range from the minimum to maximum date in the 'issued' column
                        date_range = pd.date_range(start=kf['Date'].min(), end=kf['Date'].max(), freq='D')
                        
                        # Create a DataFrame with the date range
                        date_df = pd.DataFrame({'Date': date_range})
                        # Merge the date range DataFrame with the original DataFrame based on the 'Date' column
                        merged_df = pd.merge(date_df, kf, how='left', on='Date')
                        merged_df['quantity'].fillna(0, inplace=True)
                        merged_df['Shipped Tonnage']=merged_df['quantity']*2
                        merged_df_grouped=merged_df.groupby('Date')[['quantity','Shipped Tonnage']].sum()
                        merged_df_grouped['Accumulated_Quantity'] = merged_df_grouped['quantity'].cumsum()
                        merged_df_grouped["Accumulated_Tonnage"]=merged_df_grouped['Accumulated_Quantity']*2
                        merged_df_grouped["Remaining_Units"]=[amount_dict[inv_vessel]-i for i in merged_df_grouped['Accumulated_Quantity']]
                        merged_df_grouped["Remaining_Tonnage"]=merged_df_grouped["Remaining_Units"]*2
                        merged_df_grouped.rename(columns={'quantity':"Shipped Quantity", 'Accumulated_Quantity':"Shipped Qty To_Date",
                                                          'Accumulated_Tonnage':"Shipped Tonnage To_Date"},inplace=True)
                        merged_df_grouped=merged_df_grouped.reset_index()
                        merged_df_grouped["Date"]=merged_df_grouped['Date'].dt.strftime('%m-%d-%Y, %A')
                        #merged_df_grouped=merged_df_grouped.set_index("Date",drop=True)
                      
                        st.dataframe(merged_df_grouped)
                        csv_inventory=convert_df(merged_df_grouped)
                        st.download_button(
                            label="DOWNLOAD INVENTORY REPORT AS CSV",
                            data=csv_inventory,
                            file_name=f'INVENTORY REPORT-{datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%Y_%m_%d")}.csv',
                            mime='text/csv')   
                        
                            
                    with inventory:
                        def log_inventory_change(bol_to_edit, total_edit, damaged_edit, user, log_type):
                            change_log = {
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "user": user,
                                "log_type": log_type,
                                "ocean_bill_of_lading": bol_to_edit,
                                "new_total": total_edit,
                                "new_damaged": damaged_edit
                                }
                            
                            try:
                                inventory_log=gcp_download(target_bucket,rf"inventory_log.json")
                                inventory_log=json.loads(inventory_log)
                            except :
                                inventory_log = {}
                        
                            if bol_to_edit not in inventory_log:
                                inventory_log[bol_to_edit]=[]
                            inventory_log[bol_to_edit].append(change_log)
                        
                            return inventory_log




                        
                        bols = {}
                        for key, value in raw_ro.items():
                            for item_key, item_value in value.items():
                                if isinstance(item_value, dict):
                                    ocean_bill_of_lading = item_value.get('ocean_bill_of_lading')
                                    if ocean_bill_of_lading:
                                        if ocean_bill_of_lading not in bols:
                                            bols[ocean_bill_of_lading] = []
                                        bols[ocean_bill_of_lading].append(key)
                        for i in map['bol_mapping']:
                            if i not in bols:
                                bols[i]=[]
 
                        inventory={}
                        a=[i for i in map['bol_mapping']]
                        for bill in a:
                            inventory[bill]=[map['bol_mapping'][bill]['total'],map['bol_mapping'][bill]['damaged']]
                            
                        def extract_qt(data,ro,bol):
                            totals=[0,0,0]
                            sales_group=["001","002","003","004","005"]
                            for item in data[ro]:
                                if item in sales_group:
                                    if data[ro][item]['ocean_bill_of_lading']==bol:
                                        totals[0]+=data[ro][item]['total']
                                        totals[1]+=data[ro][item]['shipped']
                                        totals[2]+=data[ro][item]['remaining']
                            return totals
                        
                        final={}
                        for k in inventory.keys():
                            final[k]={"Total":0,"Damaged":0,"Fit To Ship":0,"Allocated to ROs":0,"Shipped":0,
                                     "Remaining in Warehouse":0,"Remaining on ROs":0,"Remaining After ROs":0}
                            vector=np.zeros(3)
                            final[k]["Total"]=inventory[k][0]
                            final[k]["Damaged"]=inventory[k][1]
                            final[k]["Fit To Ship"]=final[k]["Total"]-final[k]["Damaged"]   
                        
                            if k in bols:
                                if len(bols[k])>0:
                                    for ro in set(bols[k]):
                                        a,b,c=extract_qt(raw_ro,ro,k)[0],extract_qt(raw_ro,ro,k)[1],extract_qt(raw_ro,ro,k)[2]
                                        final[k]["Allocated to ROs"]+=a
                                        #final[k]["Shipped"]=inv_bill_of_ladings.groupby("ocean_bill_of_lading")[['quantity']].sum().loc[k,'quantity']
                                        final[k]["Shipped"]+=b
                        
                                        final[k]["Remaining in Warehouse"]=final[k]["Fit To Ship"]-final[k]["Shipped"]
                                        final[k]["Remaining on ROs"]=final[k]["Allocated to ROs"]-final[k]["Shipped"]
                                        final[k]["Remaining After ROs"]=final[k]["Fit To Ship"]-final[k]["Allocated to ROs"]
                                else:
                                    final[k]["Remaining in Warehouse"]=final[k]["Fit To Ship"]
                                    final[k]["Remaining on ROs"]=0
                                    final[k]["Remaining After ROs"]=final[k]["Fit To Ship"]-final[k]["Allocated to ROs"]
                            else:
                                pass
                        temp=pd.DataFrame(final).T
                        temp.loc["TOTAL"]=temp.sum(axis=0)
                        
                        
                        tempo=temp*2

                        inv_col1,inv_col2=st.columns([7,3])
                        with inv_col1:
                            st.subheader("By Ocean BOL,UNITS")
                            st.dataframe(temp)
                            st.subheader("By Ocean BOL,TONS")
                            st.dataframe(tempo)        
                        with inv_col2:
                            edit_inventory_checkbox=st.checkbox("CHECK TO EDIT INVENTORY")
                            if edit_inventory_checkbox:
                                
                                bol_to_edit=st.selectbox("EDIT INVENTORY",[i for i in temp.index])
                                dinv1,dinv2,_=st.columns([3,3,4])
                                with dinv1:
                                    st.write(f"DAMAGED")
                                    st.write(f"TOTAL")
                                with dinv2:
                                    damaged_edit=st.number_input("lala",value=map['bol_mapping'][bol_to_edit]['damaged'],label_visibility='collapsed')
                                    total_edit=st.number_input("tata",value=map['bol_mapping'][bol_to_edit]['total'],label_visibility='collapsed',key="dsd")
                                if st.button("SUBMIT CHANGE",key="t2ds"):
                                    map['bol_mapping'][bol_to_edit]['total']=total_edit
                                    map['bol_mapping'][bol_to_edit]['damaged']=damaged_edit
                                    #storage_client = storage.Client()
                                    storage_client = get_storage_client()
                                    bucket = storage_client.bucket(target_bucket)
                                    blob = bucket.blob(rf"map.json")
                                    blob.upload_from_string(json.dumps(map))
                                    st.success(f"Updated Inventory Database",icon="✅")
                                    
                                    user="admin"
                                    log_type="Warehouse Adjustment"
                                    inventory_log=log_inventory_change(bol_to_edit, total_edit, damaged_edit, user, log_type)
                                    #storage_client = storage.Client()
                                    storage_client = get_storage_client()
                                    bucket = storage_client.bucket(target_bucket)
                                    blob = bucket.blob(rf"inventory_log.json")
                                    blob.upload_from_string(json.dumps(inventory_log))
                                    st.success(f"Logged Inventory Change",icon="✅")
                                    
                                see_inventory_change_checkbox=st.checkbox("SEE INVENTORY EDIT LOGS")
                                if see_inventory_change_checkbox:
                                    try:
                                        inventory_log=gcp_download(target_bucket,rf"inventory_log.json")
                                        inventory_log=json.loads(inventory_log)
                                    except :
                                        inventory_log = []
                                       
                                    st.write(inventory_log[bol_to_edit])


                            
                    with unregistered:
                        alien_units=json.loads(gcp_download(target_bucket,rf"alien_units.json"))
                        alien_vessel=st.selectbox("SELECT VESSEL",["KIRKENES-2304","JUVENTAS-2308","LAGUNA-3142","LYSEFJORD-2308","FRONTIER-55VC"])
                        alien_list=pd.DataFrame(alien_units[alien_vessel]).T
                        alien_list.reset_index(inplace=True)
                        alien_list.index=alien_list.index+1
                        st.markdown(f"**{len(alien_list)} units that are not on the shipping file found on {alien_vessel}**")
                        st.dataframe(alien_list)
                        
                      
            with mill_progress:
                
                mf_numbers=json.loads(gcp_download(target_bucket,rf"release_orders/mf_numbers.json"))
                
                bill_of_ladings=gcp_download(target_bucket,rf"terminal_bill_of_ladings.json")
                bill_of_ladings=json.loads(bill_of_ladings)
                bill=pd.DataFrame(bill_of_ladings).T
                values=[]
                mfs=[]
                for i in bill.index:
                    if len(i.split("|"))>1:
                        values.append(i.split("|")[1])
                        mfs.append(i.split("|")[0])
                    else:
                        values.append(i)
                        mfs.append(i)
                bill.insert(0,"Shipment",values)
                bill.insert(1,"MF",mfs)
                
                suzano_shipment_=gcp_download(target_bucket,rf"release_orders/suzano_shipments.json")
                suzano_shipment=json.loads(suzano_shipment_)
                suzano_shipment=pd.DataFrame(suzano_shipment).T

                suzano_shipment["Shipment ID"]=suzano_shipment["Shipment ID"].astype("str")
                bill["Shipment"]=bill["Shipment"].astype("str")
                suzano_shipment["Pickup"]=pd.to_datetime(suzano_shipment["Pickup"])
                suzano_shipment=suzano_shipment[suzano_shipment["Pickup"]>datetime.datetime(2024, 9, 24)]
                suzano_shipment.reset_index(drop=True,inplace=True)
                for i in suzano_shipment.index:
                    sh=suzano_shipment.loc[i,"Shipment ID"]
                    #print(sh)
                    if sh in bill[~bill["Shipment"].isna()]["Shipment"].to_list():
                        vehicle=bill.loc[bill["Shipment"]==sh,'vehicle'].values[0]
                        bol=str(bill.loc[bill["Shipment"]==sh].index.values[0])
                        suzano_shipment.loc[i,"Transit Status"]="COMPLETED"
                        suzano_shipment.loc[i,"BOL"]=bol
                        suzano_shipment.loc[i,"Vehicle ID"]=vehicle
                for rel,value in mf_numbers.items():
                    for date in value:
                        for carrier,liste in value[date].items():
                            if len(liste)>0:
                                try:
                                    for k in liste:
                                        try:
                                            suzano_shipment.loc[suzano_shipment["Shipment ID"]==k.split("|")[1],"Transit Status"]="SCHEDULED"
                                        except:
                                            suzano_shipment.loc[suzano_shipment["Shipment ID"]==k,"Transit Status"]="SCHEDULED"
                                except:
                                    pass
                st.subheader("SUZANO OTM LIST")
                st.write(suzano_shipment)
                maintenance=False
                if maintenance:
                    st.title("CURRENTLY IN MAINTENANCE, CHECK BACK LATER")
                else:
                    st.subheader("WEEKLY SHIPMENTS BY MILL (IN TONS)")
                    zf=inv_bill_of_ladings.copy()
                    zf['WEEK'] = pd.to_datetime(zf['issued'])
                    zf.set_index('WEEK', inplace=True)
                    
                    def sum_quantity(x):
                        return x.resample('W')['quantity'].sum()*2
                    resampled_quantity = zf.groupby('destination').apply(sum_quantity).unstack(level=0)
                    resampled_quantity=resampled_quantity.fillna(0)
                    resampled_quantity.loc["TOTAL"]=resampled_quantity.sum(axis=0)
                    resampled_quantity["TOTAL"]=resampled_quantity.sum(axis=1)
                    resampled_quantity=resampled_quantity.reset_index()
                    resampled_quantity["WEEK"][:-1]=[i.strftime("%Y-%m-%d") for i in resampled_quantity["WEEK"][:-1]]
                    resampled_quantity.set_index("WEEK",drop=True,inplace=True)
                    st.dataframe(resampled_quantity)
                    
                    st.download_button(
                    label="DOWNLOAD WEEKLY REPORT AS CSV",
                    data=convert_df(resampled_quantity),
                    file_name=f'WEEKLY SHIPMENT REPORT-{datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%Y_%m_%d")}.csv',
                    mime='text/csv')
    
    
                   
                    zf['issued'] = pd.to_datetime(zf['issued'])                   
                   
                    weekly_tonnage = zf.groupby(['destination', pd.Grouper(key='issued', freq='W')])['quantity'].sum() * 2  # Assuming 2 tons per quantity
                    weekly_tonnage = weekly_tonnage.reset_index()                   
                  
                    weekly_tonnage = weekly_tonnage.rename(columns={'issued': 'WEEK', 'quantity': 'Tonnage'})
                  
                    fig = px.bar(weekly_tonnage, x='WEEK', y='Tonnage', color='destination',
                                 title='Weekly Shipments Tonnage per Location',
                                 labels={'Tonnage': 'Tonnage (in Tons)', 'WEEK': 'Week'})
                 
                    fig.update_layout(width=1000, height=700)  # You can adjust the width and height values as needed
                    
                    st.plotly_chart(fig)


            with status:
                
                status_dict={}
                sales_group=["001","002","003","004","005"]
                for ro in raw_ro:
                    for sale in [i for i in raw_ro[ro] if i in sales_group]:
                        status_dict[f"{ro}-{sale}"]={"Release Order #":ro,"Sales Order #":sale,
                                            "Destination":raw_ro[ro]['destination'],
                                            "Ocean BOL":raw_ro[ro][sale]['ocean_bill_of_lading'],
                                            "Total":raw_ro[ro][sale]['total'],
                                            "Shipped":raw_ro[ro][sale]['shipped'],
                                            "Remaining":raw_ro[ro][sale]['remaining']}
                status_frame=pd.DataFrame(status_dict).T.set_index("Release Order #",drop=True)
                active_frame_=status_frame[status_frame["Remaining"]>0]
                status_frame.loc["Total"]=status_frame[["Total","Shipped","Remaining"]].sum()
                active_frame=active_frame_.copy()
                active_frame.loc["Total"]=active_frame[["Total","Shipped","Remaining"]].sum()
                
                st.markdown(active_frame.to_html(render_links=True),unsafe_allow_html=True)

                
                release_orders = status_frame.index[:-1]
                release_orders = pd.Categorical(release_orders)
                active_order_names = [f"{i} to {raw_ro[i]['destination']}" for i in active_frame_.index]
                destinations=[raw_ro[i]['destination'] for i in active_frame_.index]
                active_orders=[str(i) for i in active_frame.index]
               
                # fig = go.Figure()
                # fig.add_trace(go.Bar(x=active_orders, y=active_frame["Total"], name='Total', marker_color='lightgray'))
                # fig.add_trace(go.Bar(x=active_orders, y=active_frame["Shipped"], name='Shipped', marker_color='blue', opacity=0.7))
                # remaining_data = [remaining if remaining > 0 else None for remaining in active_frame_["Remaining"]]
                # fig.add_trace(go.Scatt
                
                #annotations = [dict(x=release_order, y=total_quantity, text=destination, showarrow=True, arrowhead=4, ax=0, ay=-30) for release_order, total_quantity, destination in zip(active_orders, active_frame["Total"], destinations)]
                #fig.update_layout(annotations=annotations)

                # fig.add_annotation(x="3172296", y=800, text="destination",
                #                        showarrow=True, arrowhead=4, ax=0, ay=-30)
                
                # fig.update_layout(title='ACTIVE RELEASE ORDERS',
                #                   xaxis_title='Release Orders',
                #                   yaxis_title='Quantities',
                #                   barmode='overlay',
                #                   width=1300,
                #                   height=700,
                #                   xaxis=dict(tickangle=-90, type='category'))
                
                # st.plotly_chart(fig)
                
                
                duration=st.toggle("Duration Report")
                if duration:
                    
                    temp_dict={}
                        
                    for rel_ord in raw_ro:
                        for sales in [i for i in raw_ro[rel_ord] if i in ["001","002","003","004","005"]]:
                            temp_dict[rel_ord,sales]={}
                            dest=raw_ro[rel_ord]['destination']
                            vessel=raw_ro[rel_ord][sales]['vessel']
                            total=raw_ro[rel_ord][sales]['total']
                            remaining=raw_ro[rel_ord][sales]['remaining']
                            temp_dict[rel_ord,sales]={'destination': dest,'vessel': vessel,'total':total,'remaining':remaining}
                    temp_df=pd.DataFrame(temp_dict).T
                  
                    temp_df= temp_df.rename_axis(['release_order','sales_order'], axis=0)
                
                    temp_df['First Shipment'] = temp_df.index.map(inv_bill_of_ladings.groupby(['release_order','sales_order'])['issued'].first())
                    
                    for i in temp_df.index:
                        if temp_df.loc[i,'remaining']<=2:
                            try:
                                temp_df.loc[i,"Last Shipment"]=inv_bill_of_ladings.groupby(['release_order','sales_order']).issued.last().loc[i]
                            except:
                                temp_df.loc[i,"Last Shipment"]=datetime.datetime.now()
                            temp_df.loc[i,"Duration"]=(pd.to_datetime(temp_df.loc[i,"Last Shipment"])-pd.to_datetime(temp_df.loc[i,"First Shipment"])).days+1
                    
                    temp_df['First Shipment'] = temp_df['First Shipment'].fillna(datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'))
                    temp_df['Last Shipment'] = temp_df['Last Shipment'].fillna(datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'))
                    
                    ####
                    
                    def business_days(start_date, end_date):
                        return pd.date_range(start=start_date, end=end_date, freq=BDay())
                    temp_df['# of Shipment Days'] = temp_df.apply(lambda row: len(business_days(row['First Shipment'], row['Last Shipment'])), axis=1)
                    df_temp=inv_bill_of_ladings.copy()
                    df_temp["issued"]=[pd.to_datetime(i).date() for i in df_temp["issued"]]
                    for i in temp_df.index:
                        try:
                            temp_df.loc[i,"Utilized Shipment Days"]=df_temp.groupby(["release_order",'sales_order'])[["issued"]].nunique().loc[i,'issued']
                        except:
                            temp_df.loc[i,"Utilized Shipment Days"]=0
                    
                    temp_df['First Shipment'] = temp_df['First Shipment'].apply(lambda x: datetime.datetime.strftime(datetime.datetime.strptime(x,'%Y-%m-%d %H:%M:%S'),'%d-%b,%Y'))
                    temp_df['Last Shipment'] = temp_df['Last Shipment'].apply(lambda x: datetime.datetime.strftime(datetime.datetime.strptime(x,'%Y-%m-%d %H:%M:%S'),'%d-%b,%Y') if type(x)==str else None)
                    liste=['Duration','# of Shipment Days',"Utilized Shipment Days"]
                    for col in liste:
                        temp_df[col] = temp_df[col].apply(lambda x: f" {int(x)} days" if not pd.isna(x) else np.nan)
                    temp_df['remaining'] = temp_df['remaining'].apply(lambda x: int(x))
                    temp_df.columns=['Destination', 'Vessel', 'Total Units', 'Remaining Units', 'First Shipment',
                           'Last Shipment', 'Duration', '# of Calendar Shipment Days',
                           'Utilized Calendar Shipment Days']
                    st.dataframe(temp_df)
                   
                



    ########################                                WAREHOUSE                            ####################
    
    elif username == 'warehouse':
        map=gcp_download(target_bucket,rf"map.json")
        map=json.loads(map)
        release_order_database=gcp_download(target_bucket,rf"release_orders/RELEASE_ORDERS.json")
        release_order_database=json.loads(release_order_database)
        dispatched=gcp_download(target_bucket,rf"dispatched.json")
        dispatched=json.loads(dispatched)
        carrier_list=map['carriers']
        mill_info=map["mill_info"]
        
        bill_mapping=gcp_download(target_bucket,"bill_mapping.json")   ###### DOWNLOADS
        bill_mapping=json.loads(bill_mapping)
        mf_numbers_for_load=gcp_download(target_bucket,rf"release_orders/mf_numbers.json")  ###### DOWNLOADS
        mf_numbers_for_load=json.loads(mf_numbers_for_load)

        bill_of_ladings=gcp_download(target_bucket,rf"terminal_bill_of_ladings.json")   ###### DOWNLOADS
        bill_of_ladings=json.loads(bill_of_ladings)
        
        no_dispatch=0
       
        number=None  
        if number not in st.session_state:
            st.session_state.number=number
                       
      
        double_load=False
        
        if len(dispatched.keys())>0 and not no_dispatch:
            loadout,schedule=st.tabs(["LOADOUT","SCHEDULE"])
            
            with schedule:
                st.subheader("TODAYS ACTION/SCHEDULE")
                now=datetime.datetime.now()-datetime.timedelta(hours=utc_difference)
                schedule=gcp_download(target_bucket,rf"schedule.json")
                schedule=json.loads(schedule)
                dfb=pd.DataFrame.from_dict(bill_of_ladings).T[1:]
                dfb["St_Date"]=[datetime.datetime.strptime(i,"%Y-%m-%d %H:%M:%S").date() for i in dfb["issued"]]
                dfb=dfb[dfb["St_Date"]==now.date()]
                scheduled=[]
                for rol in dispatched:
                    for sale in dispatched[rol]:
                        try:
                            previous=schedule[dispatched[rol][sale]['destination']]["Scheduled"]
                        except:
                            previous=0
                        scheduled.append({"Destination":dispatched[rol][sale]['destination'],
                                          "Release Order":rol,"Sales Item":sale,
                                          "ISP":release_order_database[rol][sale]['grade'],
                                          "Prep":release_order_database[rol][sale]['unitized'],
                                          "Scheduled":previous,"Loaded":0,"Remaining":0})
                scheduled=pd.DataFrame(scheduled)
                for i in scheduled.index:
                    rol=scheduled.loc[i,"Release Order"]
                    sale=scheduled.loc[i,"Sales Item"]
                    yuk=dfb[(dfb['release_order']==rol)&(dfb['sales_order']==sale)].shape[0]
                    scheduled.loc[i,"Loaded"]=yuk
                
                if len(scheduled)>0:
                    
                    scheduled["Remaining"]=scheduled["Scheduled"]-scheduled["Loaded"]
                    
                    scheduled.set_index('Destination',drop=True,inplace=True)
                    scheduled.loc["Total",["Scheduled","Loaded","Remaining"]]=scheduled[["Scheduled","Loaded","Remaining"]].sum()
                    for col in ["Scheduled", "Loaded", "Remaining"]:
                        scheduled[col] = pd.to_numeric(scheduled[col], errors='coerce').fillna(0).astype(int)
                    scheduled.fillna("",inplace=True)
                    st.dataframe(dfb)
                    st.table(scheduled)
                else:
                    st.dataframe(dfb)
                    st.write("Nothing Dispatched!")
            with loadout:
                
                menu_destinations={}
                
                for rel_ord in dispatched.keys():
                    for sales in dispatched[rel_ord]:
                        try:
                            menu_destinations[f"{rel_ord} -{sales}"]=dispatched[rel_ord][sales]["destination"]
                        except:
                            pass
                if 'work_order_' not in st.session_state:
                    st.session_state.work_order_ = None
                    
                liste=[f"{i} to {menu_destinations[i]}" for i in menu_destinations.keys()]
            
                work_order_=st.selectbox("**SELECT RELEASE ORDER/SALES ORDER TO WORK**",liste,index=0 if st.session_state.work_order_ else 0) 
                st.session_state.work_order_=work_order_
                
                if work_order_:
                        
                    work_order=work_order_.split(" ")[0]
                    order=["001","002","003","004","005","006"]
                    
                    current_release_order=work_order
                    current_sales_order=work_order_.split(" ")[1][1:]
                    vessel=release_order_database[current_release_order][current_sales_order]["vessel"]
                    destination=release_order_database[current_release_order]['destination']
                    
                    
                    
          
                    try:
                        next_release_order=dispatched['002']['release_order']    #############################  CHECK HERE ######################## FOR MIXED LOAD
                        next_sales_order=dispatched['002']['sales_order']
                        
                    except:
                        
                        pass
                    
    
                    
                        
                    
                    st.markdown(rf'**:blue[CURRENTLY WORKING] :**')
                    load_col1,load_col2=st.columns([9,1])
                    
                    with load_col1:
                        wrap_dict={"ISU":"UNWRAPPED","ISP":"WRAPPED","AEP":"WRAPPED"}
                        wrap=release_order_database[current_release_order][current_sales_order]["grade"]
                        ocean_bill_of_=release_order_database[current_release_order][current_sales_order]["ocean_bill_of_lading"]
                        unitized=release_order_database[current_release_order][current_sales_order]["unitized"]
                        quant_=release_order_database[current_release_order][current_sales_order]["total"]
                        real_quant=int(math.floor(quant_))
                        ship_=release_order_database[current_release_order][current_sales_order]["shipped"]
                        ship_bale=(ship_-math.floor(ship_))*8
                        remaining=release_order_database[current_release_order][current_sales_order]["remaining"]                #######      DEFINED "REMAINING" HERE FOR CHECKS
                        temp={f"<b>Release Order #":current_release_order,"<b>Destination":destination,"<b>VESSEL":vessel}
                        temp2={"<b>Ocean B/L":ocean_bill_of_,"<b>Type":wrap_dict[wrap],"<b>Prep":unitized}
                        temp3={"<b>Total Units":quant_,"<b>Shipped Units":ship_,"<b>Remaining Units":remaining}
                        #temp4={"<b>Total Bales":0,"<b>Shipped Bales":int(8*(ship_-math.floor(ship_))),"<b>Remaining Bales":int(8*(remaining-math.floor(remaining)))}
                        temp5={"<b>Total Tonnage":quant_*2,"<b>Shipped Tonnage":ship_*2,"<b>Remaining Tonnage":quant_*2-(ship_*2)}
    
    
                        
                        sub_load_col1,sub_load_col2,sub_load_col3,sub_load_col4=st.columns([3,3,3,3])
                        
                        with sub_load_col1:   
                            st.markdown(rf'**Release Order-{current_release_order}**')
                            st.markdown(rf'**Destination : {destination}**')
                            st.markdown(rf'**VESSEL-{vessel}**')
                            #st.write (pd.DataFrame(temp.items(),columns=["Inquiry","Data"]).to_html (escape=False, index=False), unsafe_allow_html=True)
                     
                        with sub_load_col2:
                            st.markdown(rf'**Ocean B/L: {ocean_bill_of_}**')
                            st.markdown(rf'**Type : {wrap_dict[wrap]}**')
                            st.markdown(rf'**Prep : {unitized}**')
                            #st.write (pd.DataFrame(temp2.items(),columns=["Inquiry","Data"]).to_html (escape=False, index=False), unsafe_allow_html=True)
                       
                            
                        with sub_load_col3:
        
                            st.markdown(rf'**Total Units : {quant_}**')
                            st.markdown(rf'**Shipped Units : {ship_}**')
                            if remaining<=10:
                                st.markdown(rf'**:red[CAUTION : Remaining : {remaining} Units]**')
                            else:
                                st.markdown(rf'**Remaining Units : {remaining}**')
                        with sub_load_col4:
                            
                        
                            #st.write (pd.DataFrame(temp5.items(),columns=["TONNAGE","Data"]).to_html (escape=False, index=False), unsafe_allow_html=True)
                            
                            st.markdown(rf'**Total Tonnage : {quant_*2}**')
                            st.markdown(rf'**Shipped Tonnage : {ship_*2}**')
                            st.markdown(rf'**Remaining Tonnage : {remaining*2}**')
                    
                    with load_col2:
                        if double_load:
                            
                            try:
                                st.markdown(rf'**NEXT ITEM : Release Order-{next_release_order}**')
                                st.markdown(rf'**Sales Order Item-{next_sales_order}**')
                                st.markdown(f'**Ocean Bill Of Lading : {info[vessel][next_release_order][next_sales_order]["ocean_bill_of_lading"]}**')
                                st.markdown(rf'**Total Quantity : {info[vessel][next_release_order][next_sales_order]["quantity"]}**')
                            except:
                                pass
    
                    st.divider()
                    ###############    LOADOUT DATA ENTRY    #########
                    
                    col1, col2,col3,col4= st.columns([2,2,2,2])
                    yes=False
                  
                    release_order_number=current_release_order
                    medium="TRUCK"
                    
                    with col1:
                    ######################  LETS GET RID OF INPUT BOXES TO SIMPLIFY LONGSHORE SCREEN
               
                        terminal_code="OLYM"
                        
                        file_date=datetime.datetime.today()-datetime.timedelta(hours=utc_difference)
                        if file_date not in st.session_state:
                            st.session_state.file_date=file_date
                        file_time = st.time_input('FileTime', datetime.datetime.now()-datetime.timedelta(hours=utc_difference),step=60,disabled=False)
                      
                        delivery_date=datetime.datetime.today()-datetime.timedelta(hours=utc_difference)
                        eta_date=delivery_date
                        
                        carrier_code=release_order_database[current_release_order][current_sales_order]["carrier_code"]
                        vessel=release_order_database[current_release_order][current_sales_order]["vessel"]
                        transport_sequential_number="TRUCK"
                        transport_type="TRUCK"
                        placeholder = st.empty()
                        with placeholder.container():
                            vehicle_id=st.text_input("**:blue[Vehicle ID]**",value="",key=7)
                            manual_bill=st.toggle("Toggle for Manual BOL")
                            if manual_bill:
                                manual_bill_of_lading_number=st.text_input("ENTER BOL",key="eirufs")
                            mf=True
                            load_mf_number_issued=False
                            if destination=="CLEARWATER-Lewiston,ID":
                                carrier_code=st.selectbox("Carrier Code",[carrier_code,"310897-Ashley"],disabled=False,key=29)
                            else:
                                carrier_code=st.text_input("Carrier Code",carrier_code,disabled=True,key=9)
                            today_str=str(st.date_input("Shipment Date",datetime.datetime.today(),disabled=False,key="popdo3"))
                                
                            if 'load_mf_number' not in st.session_state:
                                st.session_state.load_mf_number = None
                                
                            if release_order_number in mf_numbers_for_load.keys():
                                try:
                                    mf_liste=[i for i in mf_numbers_for_load[release_order_number][today_str][f"{carrier_code.split('-')[0]}-{carrier_code.split('-')[1]}"]]
                                                          
                                except:
                                    mf_liste=[]
                                if len(mf_liste)>0:
                                    try:
                                        load_mf_number = st.selectbox("MF NUMBER", mf_liste, disabled=False, key=14551, index=mf_liste.index(st.session_state.load_mf_number) if st.session_state.load_mf_number else 0)
                                    except:
                                        load_mf_number = st.selectbox("MF NUMBER", mf_liste, disabled=False, key=14551)
                                    mf=True
                                    load_mf_number_issued=True
                                    yes=True
                                    st.session_state.load_mf_number = load_mf_number
                                   
                                else:
                                    st.write(f"**:red[ASK ADMIN TO PUT SHIPMENT NUMBERS]**")
                                    mf=False
                                    yes=False
                                    load_mf_number_issued=False  
                            else:
                                st.write(f"**:red[ASK ADMIN TO PUT MF NUMBERS]**")
                                mf=False
                                yes=False
                                load_mf_number_issued=False  
                               
                            foreman_quantity=st.number_input("**:blue[ENTER Quantity of Units]**", min_value=0, max_value=30, value=0, step=1, help=None, on_change=None, disabled=False, label_visibility="visible",key=8)
                            foreman_bale_quantity=st.number_input("**:blue[ENTER Quantity of Bales]**", min_value=0, max_value=30, value=0, step=1, help=None, on_change=None, disabled=False, label_visibility="visible",key=123)
                        click_clear1 = st.button('CLEAR VEHICLE-QUANTITY INPUTS', key=34)
                        if click_clear1:
                             with placeholder.container():
                                 vehicle_id=st.text_input("**:blue[Vehicle ID]**",value="",key=17)
                        
                                 mf=True
                                 load_mf_number_issued=False
                                 if destination=="CLEARWATER-Lewiston,ID":
                                    carrier_code=st.selectbox("Carrier Code",[carrier_code,"310897-Ashley"],disabled=False,key=29)
                                 else:
                                     carrier_code=st.text_input("Carrier Code",carrier_code,disabled=True,key=9)
                                 if 'load_mf_number' not in st.session_state:
                                         st.session_state.load_mf_number = None
                                 if release_order_number in mf_numbers_for_load.keys():
                                     mf_liste=[i for i in mf_numbers_for_load[release_order_number]]
                                     if len(mf_liste)>0:
                                         try:
                                             load_mf_number = st.selectbox("SHIPMENT NUMBER", mf_liste, disabled=False, key=14551, index=mf_liste.index(st.session_state.load_mf_number) if st.session_state.load_mf_number else 0)
                                         except:
                                             load_mf_number = st.selectbox("SHIPMENT NUMBER", mf_liste, disabled=False, key=14551)
                                         mf=True
                                         load_mf_number_issued=True
                                         yes=True
                                         st.session_state.load_mf_number = load_mf_number
                                       
                                     else:
                                         st.write(f"**:red[ASK ADMIN TO PUT SHIPMENT NUMBERS]**")
                                         mf=False
                                         yes=False
                                         load_mf_number_issued=False  
                                 else:
                                     st.write(f"**:red[ASK ADMIN TO PUT SHIPMENT NUMBERS]**")
                                     mf=False
                                     yes=False
                                     load_mf_number_issued=False    
                                 foreman_quantity=st.number_input("**:blue[ENTER Quantity of Units]**", min_value=0, max_value=30, value=0, step=1, help=None, on_change=None, disabled=False, label_visibility="visible",key=18)
                                 foreman_bale_quantity=st.number_input("**:blue[ENTER Quantity of Bales]**", min_value=0, max_value=30, value=0, step=1, help=None, on_change=None, disabled=False, label_visibility="visible",key=1123)
                                 
                               
                        
                                
                        
                    with col2:
                        ocean_bol_to_batch = {"GSSWKIR6013D": 45302855,"GSSWKIR6013E": 45305548}
                        if double_load:
                            #release_order_number=st.text_input("Release Order Number",current_release_order,disabled=True,help="Release Order Number without the Item no")
                            release_order_number=current_release_order
                            #sales_order_item=st.text_input("Sales Order Item (Material Code)",current_sales_order,disabled=True)
                            sales_order_item=current_sales_order
                            #ocean_bill_of_lading=st.text_input("Ocean Bill Of Lading",info[current_release_order][current_sales_order]["ocean_bill_of_lading"],disabled=True)
                            ocean_bill_of_lading=info[current_release_order][current_sales_order]["ocean_bill_of_lading"]
                            current_ocean_bill_of_lading=ocean_bill_of_lading
                            next_ocean_bill_of_lading=info[next_release_order][next_sales_order]["ocean_bill_of_lading"]
                            #batch=st.text_input("Batch",info[current_release_order][current_sales_order]["batch"],disabled=True)
                            batch=info[current_release_order][current_sales_order]["batch"]
                            #grade=st.text_input("Grade",info[current_release_order][current_sales_order]["grade"],disabled=True)
                            grade=info[current_release_order][current_sales_order]["grade"]
                            
                            #terminal_bill_of_lading=st.text_input("Terminal Bill of Lading",disabled=False)
                            pass
                        else:
                            release_order_number=current_release_order
                            sales_order_item=current_sales_order
                            ocean_bill_of_lading=release_order_database[current_release_order][current_sales_order]["ocean_bill_of_lading"]
                            
                            batch=release_order_database[current_release_order][current_sales_order]["batch"]
                     
                            grade=release_order_database[current_release_order][current_sales_order]["grade"]
                            
                   
                        updated_quantity=0
                        live_quantity=0
                        if updated_quantity not in st.session_state:
                            st.session_state.updated_quantity=updated_quantity
                        load_digit=-2 if vessel=="KIRKENES-2304" else -3
                        def audit_unit(x):
                            if vessel=="LAGUNA-3142":
                                return True
                            if vessel=="KIRKENES-2304":
                                if len(x)>=10:
                                    if bill_mapping[vessel][x[:-2]]["Ocean_bl"]!=ocean_bill_of_lading and bill_mapping[vessel][x[:-2]]["Batch"]!=batch:
                                        st.write("**:red[WRONG B/L, DO NOT LOAD BELOW!]**")
                                        return False
                                    else:
                                        return True
                            else:
                                if bill_mapping[vessel][x[:-3]]["Ocean_bl"]!=ocean_bill_of_lading and bill_mapping[vessel][x[:-3]]["Batch"]!=batch:
                                    return False
                                else:
                                    return True
                        def audit_split(release,sales):
                            if vessel=="KIRKENES-2304":
                                if len(x)>=10:
                                    if bill_mapping[vessel][x[:-2]]["Ocean_bl"]!=ocean_bill_of_lading and bill_mapping[vessel][x[:-2]]["Batch"]!=batch:
                                        st.write("**:red[WRONG B/L, DO NOT LOAD BELOW!]**")
                                        return False
                                    else:
                                        return True
                            else:
                                if bill_mapping[vessel][x[:-3]]["Ocean_bl"]!=ocean_bill_of_lading and bill_mapping[vessel][x[:-3]]["Batch"]!=batch:
                                        return False
                                else:
                                    return True
                        
                        flip=False 
                        first_load_input=None
                        second_load_input=None
                        load_input=None
                        bale_load_input=None
                        if double_load:
                            
                            try:
                                next_item=gcp_download("olym_suzano",rf"release_orders/{dispatched['2']['vessel']}/{dispatched['2']['release_order']}.json")
                                
                                first_load_input=st.text_area("**FIRST SKU LOADS**",height=300)
                                first_quantity=0
                                second_quantity=0
                                if first_load_input is not None:
                                    first_textsplit = first_load_input.splitlines()
                                    first_textsplit=[i for i in first_textsplit if len(i)>8]
                                    first_quantity=len(first_textsplit)
                                second_load_input=st.text_area("**SECOND SKU LOADS**",height=300)
                                if second_load_input is not None:
                                    second_textsplit = second_load_input.splitlines()
                                    second_textsplit = [i for i in second_textsplit if len(i)>8]
                                    second_quantity=len(second_textsplit)
                                updated_quantity=first_quantity+second_quantity
                                st.session_state.updated_quantity=updated_quantity
                            except Exception as e: 
                                st.write(e)
                                #st.markdown("**:red[ONLY ONE ITEM IN QUEUE ! ASK NEXT ITEM TO BE DISPATCHED!]**")
                                pass
                            
                        
                        else:
                            
            
            
                            placeholder1 = st.empty()
                            
                            
                            
                            load_input=placeholder1.text_area("**UNITS**",value="",height=300,key=1)#[:-2]
                        
                            
                    with col3:
                        placeholder2 = st.empty()
                        bale_load_input=placeholder2.text_area("**INDIVIDUAL BALES**",value="",height=300,key=1111)#[:-2]
                        
                            
                    with col2:
                        click_clear = st.button('CLEAR SCANNED INPUTS', key=3)
                        if click_clear:
                            load_input = placeholder1.text_area("**UNITS**",value="",height=300,key=2)#
                            bale_load_input=placeholder2.text_area("**INDIVIDUAL BALES**",value="",height=300,key=1121)#
                        if load_input is not None :
                            textsplit = load_input.splitlines()
                            textsplit=[i for i in textsplit if len(i)>8]
                            updated_quantity=len(textsplit)
                            st.session_state.updated_quantity=updated_quantity
                        if bale_load_input is not None:
                            bale_textsplit = bale_load_input.splitlines()
                            bale_textsplit=[i for i in bale_textsplit if len(i)>8]
                            bale_updated_quantity=len(bale_textsplit)
                            st.session_state.updated_quantity=updated_quantity+bale_updated_quantity*0.125
                       
                    with col4:
                        
                        if double_load:
                            first_faults=[]
                            if first_load_input is not None:
                                first_textsplit = first_load_input.splitlines()
                                first_textsplit=[i for i in first_textsplit if len(i)>8]
                                #st.write(textsplit)
                                for j,x in enumerate(first_textsplit):
                                    if audit_split(current_release_order,current_sales_order):
                                        st.text_input(f"Unit No : {j+1}",x)
                                        first_faults.append(0)
                                    else:
                                        st.text_input(f"Unit No : {j+1}",x)
                                        first_faults.append(1)
                            second_faults=[]
                            if second_load_input is not None:
                                second_textsplit = second_load_input.splitlines()
                                second_textsplit = [i for i in second_textsplit if len(i)>8]
                                #st.write(textsplit)
                                for i,x in enumerate(second_textsplit):
                                    if audit_split(next_release_order,next_sales_order):
                                        st.text_input(f"Unit No : {len(first_textsplit)+1+i}",x)
                                        second_faults.append(0)
                                    else:
                                        st.text_input(f"Unit No : {j+1+i+1}",x)
                                        second_faults.append(1)
            
                            loads=[]
                            
                            for k in first_textsplit:
                                loads.append(k)
                            for l in second_textsplit:
                                loads.append(l)
                                
                        ####   IF NOT double load
                        else:
                            
                            past_loads=[]
                            for row in bill_of_ladings.keys():
                                if row!="11502400":
                                    past_loads+=[load for load in bill_of_ladings[row]['loads'].keys()]
                            faults=[]
                            bale_faults=[]
                            fault_messaging={}
                            bale_fault_messaging={}
                            textsplit={}
                            bale_textsplit={}
                            if load_input is not None:
                                textsplit = load_input.splitlines()
                                
                                    
                                textsplit=[i for i in textsplit if len(i)>8]
                           
                                seen=set()
                                alien_units=json.loads(gcp_download(target_bucket,rf"alien_units.json"))
                                for i,x in enumerate(textsplit):
                                    alternate_vessels=[ship for ship in bill_mapping if ship!=vessel]
                                    if x[:load_digit] in ["ds"]:
                                        st.markdown(f"**:red[Unit No : {i+1}-{x}]**",unsafe_allow_html=True)
                                        faults.append(1)
                                        st.markdown("**:red[THIS LOT# IS FROM THE OTHER VESSEL!]**")
                                    else:
                                            
                                        if x[:load_digit] in bill_mapping[vessel] or vessel=="LAGUNA-3142" :
                                            if audit_unit(x):
                                                if x in seen:
                                                    st.markdown(f"**:red[Unit No : {i+1}-{x}]**",unsafe_allow_html=True)
                                                    faults.append(1)
                                                    st.markdown("**:red[This unit has been scanned TWICE!]**")
                                                if x in past_loads:
                                                    st.markdown(f"**:red[Unit No : {i+1}-{x}]**",unsafe_allow_html=True)
                                                    faults.append(1)
                                                    st.markdown("**:red[This unit has been SHIPPED!]**")   
                                                else:
                                                    st.write(f"**Unit No : {i+1}-{x}**")
                                                    faults.append(0)
                                            else:
                                                st.markdown(f"**:red[Unit No : {i+1}-{x}]**",unsafe_allow_html=True)
                                                st.write(f"**:red[WRONG B/L, DO NOT LOAD UNIT {x}]**")
                                                faults.append(1)
                                            seen.add(x)
                                        else:
                                            #st.markdown(f"**:red[Unit No : {i+1}-{x}]**",unsafe_allow_html=True)
                                            faults.append(1)
                                            #st.markdown("**:red[This LOT# NOT IN INVENTORY!]**")
                                            #st.info(f"VERIFY THIS UNIT CAME FROM {vessel} - {'Unwrapped' if grade=='ISU' else 'wrapped'} piles")
                                            with st.expander(f"**:red[Unit No : {i+1}-{x} This LOT# NOT IN INVENTORY!---VERIFY UNIT {x} CAME FROM {vessel} - {'Unwrapped' if grade=='ISU' else 'wrapped'} piles]**"):
                                                st.write("Verify that the unit came from the pile that has the units for this release order and click to inventory")
                                                if st.button("ADD UNIT TO INVENTORY",key=f"{x}"):
                                                    updated_bill=bill_mapping.copy()
                                                    updated_bill[vessel][x[:load_digit]]={"Batch":batch,"Ocean_bl":ocean_bill_of_lading}
                                                    updated_bill=json.dumps(updated_bill)
                                                    storage_client = get_storage_client()
                                                    bucket = storage_client.bucket(target_bucket)
                                                    blob = bucket.blob(rf"bill_mapping.json")
                                                    blob.upload_from_string(updated_bill)
    
                                                    alien_units=gcp_download(target_bucket,rf"alien_units.json")
                                                    alien_units=json.loads(alien_units)
                                                    if vessel not in alien_units:
                                                        alien_units[vessel]={}
                                                    alien_units[vessel][x]={}
                                                    alien_units[vessel][x]={"Ocean_Bill_Of_Lading":ocean_bill_of_lading,"Batch":batch,"Grade":grade,
                                                                            "Date_Found":datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%Y,%m-%d %H:%M:%S")}
                                                    alien_units=json.dumps(alien_units)
                                                    storage_client = get_storage_client()
                                                    bucket = storage_client.bucket(target_bucket)
                                                    blob = bucket.blob(rf"alien_units.json")
                                                    blob.upload_from_string(alien_units)
                                                    
                                                    
                                                    subject=f"FOUND UNIT {x} NOT IN INVENTORY"
                                                    body=f"Clerk identified an uninventoried {'Unwrapped' if grade=='ISU' else 'wrapped'} unit {x}, and after verifying the physical pile, inventoried it into Ocean Bill Of Lading : {ocean_bill_of_lading} for vessel {vessel}. Unit has been put into alien unit list."
                                                    sender = "warehouseoly@gmail.com"
                                                    #recipients = ["alexandras@portolympia.com","conleyb@portolympia.com", "afsiny@portolympia.com"]
                                                    recipients = ["afsiny@portolympia.com"]
                                                    password = "xjvxkmzbpotzeuuv"
                                                    send_email(subject, body, sender, recipients, password)
                                                    time.sleep(0.1)
                                                    st.success(f"Added Unit {x} to Inventory!",icon="✅")
                                                    st.rerun()
                                    
                            if bale_load_input is not None:
                            
                                bale_textsplit = bale_load_input.splitlines()                       
                                bale_textsplit=[i for i in bale_textsplit if len(i)>8]                           
                                seen=set()
                                alien_units=json.loads(gcp_download(target_bucket,rf"alien_units.json"))
                                for i,x in enumerate(bale_textsplit):
                                    alternate_vessel=[ship for ship in bill_mapping if ship!=vessel][0]
                                    if x[:load_digit] in bill_mapping[alternate_vessel]:
                                        st.markdown(f"**:red[Bale No : {i+1}-{x}]**",unsafe_allow_html=True)
                                        faults.append(1)
                                        st.markdown("**:red[THIS BALE LOT# IS FROM THE OTHER VESSEL!]**")
                                    else:
                                        if x[:load_digit] in bill_mapping[vessel]:
                                            if audit_unit(x):
                                                st.write(f"**Bale No : {i+1}-{x}**")
                                                faults.append(0)
                                            else:
                                                st.markdown(f"**:red[Bale No : {i+1}-{x}]**",unsafe_allow_html=True)
                                                st.write(f"**:red[WRONG B/L, DO NOT LOAD BALE {x}]**")
                                                faults.append(1)
                                            seen.add(x)
                                        else:
                                            faults.append(1)
                                            with st.expander(f"**:red[Bale No : {i+1}-{x} This LOT# NOT IN INVENTORY!---VERIFY BALE {x} CAME FROM {vessel} - {'Unwrapped' if grade=='ISU' else 'wrapped'} piles]**"):
                                                st.write("Verify that the bale came from the pile that has the units for this release order and click to inventory")
                                                if st.button("ADD BALE TO INVENTORY",key=f"{x}"):
                                                    updated_bill=bill_mapping.copy()
                                                    updated_bill[vessel][x[:load_digit]]={"Batch":batch,"Ocean_bl":ocean_bill_of_lading}
                                                    updated_bill=json.dumps(updated_bill)
                                                    storage_client = get_storage_client()
                                                    bucket = storage_client.bucket(target_bucket)
                                                    blob = bucket.blob(rf"bill_mapping.json")
                                                    blob.upload_from_string(updated_bill)
    
                                                    alien_units=json.loads(gcp_download(target_bucket,rf"alien_units.json"))
                                                    alien_units[vessel][x]={}
                                                    alien_units[vessel][x]={"Ocean_Bill_Of_Lading":ocean_bill_of_lading,"Batch":batch,"Grade":grade,
                                                                            "Date_Found":datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%Y,%m-%d %H:%M:%S")}
                                                    alien_units=json.dumps(alien_units)
                                                    storage_client = get_storage_client()
                                                    bucket = storage_client.bucket(target_bucket)
                                                    blob = bucket.blob(rf"alien_units.json")
                                                    blob.upload_from_string(alien_units)
                                                    
                                                    
                                                    subject=f"FOUND UNIT {x} NOT IN INVENTORY"
                                                    body=f"Clerk identified an uninventoried {'Unwrapped' if grade=='ISU' else 'wrapped'} unit {x}, and after verifying the physical pile, inventoried it into Ocean Bill Of Lading : {ocean_bill_of_lading} for vessel {vessel}. Unit has been put into alien unit list."
                                                    sender = "warehouseoly@gmail.com"
                                                    #recipients = ["alexandras@portolympia.com","conleyb@portolympia.com", "afsiny@portolympia.com"]
                                                    recipients = ["afsiny@portolympia.com"]
                                                    password = "xjvxkmzbpotzeuuv"
                                                    send_email(subject, body, sender, recipients, password)
                                                    time.sleep(0.1)
                                                    st.success(f"Added Unit {x} to Inventory!",icon="✅")
                                                   # st.rerun()
                           
                               
                            loads={}
                            pure_loads={}
                            yes=True
                            if 1 in faults or 1 in bale_faults:
                                yes=False
                            
                            if yes:
                                pure_loads={**{k:0 for k in textsplit},**{k:0 for k in bale_textsplit}}
                                loads={**{k[:load_digit]:0 for k in textsplit},**{k[:load_digit]:0 for k in bale_textsplit}}
                                for k in textsplit:
                                    loads[k[:load_digit]]+=1
                                    pure_loads[k]+=1
                                for k in bale_textsplit:
                                    loads[k[:load_digit]]+=0.125
                                    pure_loads[k]+=0.125
                    with col3:
                        quantity=st.number_input("**Scanned Quantity of Units**",st.session_state.updated_quantity, key=None, help=None, on_change=None, disabled=True, label_visibility="visible")
                        st.markdown(f"**{quantity*2} TONS - {round(quantity*2*2204.62,1)} Pounds**")
                        
                        admt=round(float(release_order_database[current_release_order][current_sales_order]["dryness"])/90*st.session_state.updated_quantity*2,4)
                        st.markdown(f"**ADMT= {admt} TONS**")
                    manual_time=False   
                    #st.write(faults)                  
                    if st.checkbox("Check for Manual Entry for Date/Time"):
                        manual_time=True
                        file_date=st.date_input("File Date",datetime.datetime.today(),disabled=False,key="popo3")
                        a=datetime.datetime.strftime(file_date,"%Y%m%d")
                        a_=datetime.datetime.strftime(file_date,"%Y-%m-%d")
                        file_time = st.time_input('FileTime', datetime.datetime.now()-datetime.timedelta(hours=utc_difference),step=60,disabled=False,key="popop")
                        b=file_time.strftime("%H%M%S")
                        b_=file_time.strftime("%H:%M:%S")
                        c=datetime.datetime.strftime(eta_date,"%Y%m%d")
                    else:     
                        
                        a=datetime.datetime.strftime(file_date,"%Y%m%d")
                        a_=datetime.datetime.strftime(file_date,"%Y-%m-%d")
                        b=file_time.strftime("%H%M%S")
                        b=(datetime.datetime.now()-datetime.timedelta(hours=utc_difference)).strftime("%H%M%S")
                        b_=(datetime.datetime.now()-datetime.timedelta(hours=utc_difference)).strftime("%H:%M:%S")
                        c=datetime.datetime.strftime(eta_date,"%Y%m%d")
                        
                        
                    
                    liste=[(i,datetime.datetime.strptime(bill_of_ladings[i]['issued'],"%Y-%m-%d %H:%M:%S")) for i in bill_of_ladings if i!="11502400"]
                    liste.sort(key=lambda a: a[1])
                    last_submitted=[i[0] for i in liste[-3:]]
                    last_submitted.reverse()
                    st.markdown(f"**Last Submitted Bill Of Ladings (From most recent) : {last_submitted}**")
                    
                    
                    
                    if yes and mf and quantity>0:
                        
                        if st.button('**:blue[SUBMIT EDI]**'):
                         
                            proceed=True
                            if not yes:
                                proceed=False
                                         
                            if fault_messaging.keys():
                                for i in fault_messaging.keys():
                                    error=f"**:red[Unit {fault_messaging[i]}]**"
                                    proceed=False
                            if remaining<0:
                                proceed=False
                                error="**:red[No more Items to ship on this Sales Order]"
                                st.write(error)
                            if not vehicle_id: 
                                proceed=False
                                error="**:red[Please check Vehicle ID]**"
                                st.write(error)
                            
                            if quantity!=foreman_quantity+int(foreman_bale_quantity)/8:
                                proceed=False
                                error=f"**:red[{updated_quantity} units and {bale_updated_quantity} bales on this truck. Please check. You planned for {foreman_quantity} units and {foreman_bale_quantity} bales!]** "
                                st.write(error)
                            if proceed:
                                carrier_code_mf=f"{carrier_code.split('-')[0]}-{carrier_code.split('-')[1]}"
                                carrier_code=carrier_code.split("-")[0]
                                
                                suzano_report=gcp_download(target_bucket,rf"suzano_report.json")
                                suzano_report=json.loads(suzano_report)
    
                                consignee=destination.split("-")[0]
                                consignee_city=mill_info[destination]["city"]
                                consignee_state=mill_info[destination]["state"]
                                vessel_suzano,voyage_suzano=vessel.split("-")
                                if manual_time:
                                    eta=datetime.datetime.strftime(file_date+datetime.timedelta(hours=mill_info[destination]['Driving_Hours']-utc_difference)+datetime.timedelta(minutes=mill_info[destination]['Driving_Minutes']+30),"%Y-%m-%d  %H:%M:%S")
                                else:
                                    eta=datetime.datetime.strftime(datetime.datetime.now()+datetime.timedelta(hours=mill_info[destination]['Driving_Hours']-utc_difference)+datetime.timedelta(minutes=mill_info[destination]['Driving_Minutes']+30),"%Y-%m-%d  %H:%M:%S")
        
                                if double_load:
                                    bill_of_lading_number,bill_of_ladings=gen_bill_of_lading()
                                    edi_name= f'{bill_of_lading_number}.txt'
                                    bill_of_ladings[str(bill_of_lading_number)]={"vessel":vessel,"release_order":release_order_number,"destination":destination,"sales_order":current_sales_order,
                                                                                 "ocean_bill_of_lading":ocean_bill_of_lading,"grade":wrap,"carrier_id":carrier_code,"vehicle":vehicle_id,
                                                                                 "quantity":len(first_textsplit),"issued":f"{a_} {b_}","edi_no":edi_name} 
                                    bill_of_ladings[str(bill_of_lading_number+1)]={"vessel":vessel,"release_order":release_order_number,"destination":destination,"sales_order":next_sales_order,
                                                                                 "ocean_bill_of_lading":ocean_bill_of_lading,"grade":wrap,"carrier_id":carrier_code,"vehicle":vehicle_id,
                                                                                 "quantity":len(second_textsplit),"issued":f"{a_} {b_}","edi_no":edi_name} 
                                
                                else:
                                    bill_of_lading_number,bill_of_ladings=gen_bill_of_lading()
                                    if load_mf_number_issued:
                                        bill_of_lading_number=st.session_state.load_mf_number
                                    if manual_bill:
                                        bill_of_lading_number=manual_bill_of_lading_number
                                    edi_name= f'{bill_of_lading_number}.txt'
                                    bill_of_ladings[str(bill_of_lading_number)]={"vessel":vessel,"release_order":release_order_number,"destination":destination,"sales_order":current_sales_order,
                                                                                 "ocean_bill_of_lading":ocean_bill_of_lading,"grade":wrap,"carrier_id":carrier_code,"vehicle":vehicle_id,
                                                                                 "quantity":st.session_state.updated_quantity,"issued":f"{a_} {b_}","edi_no":edi_name,"loads":pure_loads} 
                                                    
                                bill_of_ladings=json.dumps(bill_of_ladings)
                                storage_client = get_storage_client()
                                bucket = storage_client.bucket(target_bucket)
                                blob = bucket.blob(rf"terminal_bill_of_ladings.json")
                                blob.upload_from_string(bill_of_ladings)
                                
                                
                                
                                terminal_bill_of_lading=st.text_input("Terminal Bill of Lading",bill_of_lading_number,disabled=True)
                                success_container=st.empty()
                                success_container.info("Uploading Bill of Lading")
                                time.sleep(0.1) 
                                success_container.success("Uploaded Bill of Lading...",icon="✅")
                                process()
                                #st.toast("Creating EDI...")
                                try:
                                    suzano_report_keys=[int(i) for i in suzano_report.keys()]
                                    next_report_no=max(suzano_report_keys)+1
                                except:
                                    next_report_no=1
                                if double_load:
                                    
                                    suzano_report.update({next_report_no:{"Date Shipped":f"{a_} {b_}","Vehicle":vehicle_id, "Shipment ID #": bill_of_lading_number, "Consignee":consignee,"Consignee City":consignee_city,
                                                         "Consignee State":consignee_state,"Release #":release_order_number,"Carrier":carrier_code,
                                                         "ETA":eta,"Ocean BOL#":ocean_bill_of_lading,"Warehouse":"OLYM","Vessel":vessel_suzano,"Voyage #":voyage_suzano,"Grade":wrap,"Quantity":quantity,
                                                         "Metric Ton": quantity*2, "ADMT":admt,"Mode of Transportation":transport_type}})
                                else:
                                   
                                    suzano_report.update({next_report_no:{"Date Shipped":f"{a_} {b_}","Vehicle":vehicle_id, "Shipment ID #": bill_of_lading_number, "Consignee":consignee,"Consignee City":consignee_city,
                                                         "Consignee State":consignee_state,"Release #":release_order_number,"Carrier":carrier_code,
                                                         "ETA":eta,"Ocean BOL#":ocean_bill_of_lading,"Batch#":batch,
                                                         "Warehouse":"OLYM","Vessel":vessel_suzano,"Voyage #":voyage_suzano,"Grade":wrap,"Quantity":quantity,
                                                         "Metric Ton": quantity*2, "ADMT":admt,"Mode of Transportation":transport_type}})
                                    suzano_report=json.dumps(suzano_report)
                                    storage_client = get_storage_client()
                                    bucket = storage_client.bucket(target_bucket)
                                    blob = bucket.blob(rf"suzano_report.json")
                                    blob.upload_from_string(suzano_report)
                                    success_container1=st.empty()
                                    time.sleep(0.1)                            
                                    success_container1.success(f"Updated Suzano Report",icon="✅")
        
                                  
                                    
                                if double_load:
                                    info[current_release_order][current_sales_order]["shipped"]=info[current_release_order][current_sales_order]["shipped"]+len(first_textsplit)
                                    info[current_release_order][current_sales_order]["remaining"]=info[current_release_order][current_sales_order]["remaining"]-len(first_textsplit)
                                    info[next_release_order][next_sales_order]["shipped"]=info[next_release_order][next_sales_order]["shipped"]+len(second_textsplit)
                                    info[next_release_order][next_sales_order]["remaining"]=info[next_release_order][next_sales_order]["remaining"]-len(second_textsplit)
                                else:
                                    release_order_database[current_release_order][current_sales_order]["shipped"]=release_order_database[current_release_order][current_sales_order]["shipped"]+quantity
                                    release_order_database[current_release_order][current_sales_order]["remaining"]=release_order_database[current_release_order][current_sales_order]["remaining"]-quantity
                                if release_order_database[current_release_order][current_sales_order]["remaining"]<=0:
                                    to_delete=[]
                                    for release in dispatched.keys():
                                        if release==current_release_order:
                                            for sales in dispatched[release].keys():
                                                if sales==current_sales_order:
                                                    to_delete.append((release,sales))
                                    for victim in to_delete:
                                        del dispatched[victim[0]][victim[1]]
                                        if len(dispatched[victim[0]].keys())==0:
                                            del dispatched[victim[0]]
                                    
                                    json_data = json.dumps(dispatched)
                                    storage_client = get_storage_client()
                                    bucket = storage_client.bucket(target_bucket)
                                    blob = bucket.blob(rf"dispatched.json")
                                    blob.upload_from_string(json_data)       
                                def check_complete(data,ro):
                                    complete=True
                                    for i in data[ro]:
                                        if i in ["001","002","003","004","005"]:
                                            if data[ro][i]['remaining']>0:
                                                complete=False
                                    return complete
                                if check_complete(release_order_database,current_release_order):
                                    release_order_database[current_release_order]['complete']=True
                                
                                json_data = json.dumps(release_order_database)
                                storage_client = get_storage_client()
                                bucket = storage_client.bucket(target_bucket)
                                blob = bucket.blob(rf"release_orders/RELEASE_ORDERS.json")
                                blob.upload_from_string(json_data)
                                                          
                                success_container3=st.empty()
                                time.sleep(0.1)                            
                                success_container3.success(f"Updated Release Order Database",icon="✅")
                                with open('placeholder.txt', 'r') as f:
                                    output_text = f.read()
                                
                                #st.markdown("**EDI TEXT**")
                                #st.text_area('', value=output_text, height=600)
                                with open('placeholder.txt', 'r') as f:
                                    file_content = f.read()
                                newline="\n"
                                filename = f'{bill_of_lading_number}'
                                file_name= f'{bill_of_lading_number}.txt'
                                
                                
                                subject = f'Suzano_EDI_{a}_ R.O:{release_order_number}-Terminal BOL :{bill_of_lading_number}-Destination : {destination}'
                                body = f"EDI for Below attached.{newline}Release Order Number : {current_release_order} - Sales Order Number:{current_sales_order}{newline} Destination : {destination} Ocean Bill Of Lading : {ocean_bill_of_lading}{newline}Terminal Bill of Lading: {terminal_bill_of_lading} - Grade : {wrap} {newline}{2*quantity} tons {unitized} cargo were loaded to vehicle : {vehicle_id} with Carried ID : {carrier_code} {newline}Truck loading completed at {a_} {b_}"
                                #st.write(body)           
                                sender = "warehouseoly@gmail.com"
                                recipients = ["alexandras@portolympia.com","conleyb@portolympia.com", "afsiny@portolympia.com"]
                                #recipients = ["afsiny@portolympia.com"]
                                password = "xjvxkmzbpotzeuuv"
                        
                      
                        
                        
                                with open('temp_file.txt', 'w') as f:
                                    f.write(file_content)
                        
                                file_path = 'temp_file.txt'  # Use the path of the temporary file
                        
                                
                                upload_cs_file(target_bucket, 'temp_file.txt',rf"EDIS/{file_name}")
                                success_container5=st.empty()
                                time.sleep(0.1)                            
                                success_container5.success(f"Uploaded EDI File",icon="✅")
                                if load_mf_number_issued:
                                    mf_numbers_for_load[release_order_number][a_][carrier_code_mf].remove(load_mf_number)
                                    mf_numbers_for_load=json.dumps(mf_numbers_for_load)
                                    storage_client = get_storage_client()
                                    bucket = storage_client.bucket(target_bucket)
                                    blob = bucket.blob(rf"release_orders/mf_numbers.json")
                                    blob.upload_from_string(mf_numbers_for_load)
                                    st.write("Updated MF numbers...")
                                send_email_with_attachment(subject, body, sender, recipients, password, file_path,file_name)
                                success_container6=st.empty()
                                time.sleep(0.1)                            
                                success_container6.success(f"Sent EDI Email",icon="✅")
                                st.markdown("**SUCCESS! EDI FOR THIS LOAD HAS BEEN SUBMITTED,THANK YOU**")
                                st.write(filename,current_release_order,current_sales_order,destination,ocean_bill_of_lading,terminal_bill_of_lading,wrap)
                                this_shipment_aliens=[]
                                for i in pure_loads:
                                    try:
                                            
                                        if i in alien_units[vessel]:       
                                            alien_units[vessel][i]={"Ocean_Bill_Of_Lading":ocean_bill_of_lading,"Batch":batch,"Grade":grade,
                                                    "Date_Found":datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%Y,%m-%d %H:%M:%S"),
                                                    "Destination":destination,"Release_Order":current_release_order,"Terminal_Bill_of Lading":terminal_bill_of_lading,"Truck":vehicle_id}
                                            this_shipment_aliens.append(i)
                                        if i not in alien_units[vessel]:
                                            if i[:-2] in [u[:-2] for u in alien_units[vessel]]:
                                                alien_units[vessel][i]={"Ocean_Bill_Of_Lading":ocean_bill_of_lading,"Batch":batch,"Grade":grade,
                                                    "Date_Found":datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%Y,%m-%d %H:%M:%S"),
                                                    "Destination":destination,"Release_Order":current_release_order,"Terminal_Bill_of Lading":terminal_bill_of_lading,"Truck":vehicle_id}
                                                this_shipment_aliens.append(i)
                                    except:
                                        pass
                                alien_units=json.dumps(alien_units)
                                storage_client = get_storage_client()
                                bucket = storage_client.bucket(target_bucket)
                                blob = bucket.blob(rf"alien_units.json")
                                blob.upload_from_string(alien_units)   
                                
                                if len(this_shipment_aliens)>0:
                                    subject=f"UNREGISTERED UNITS SHIPPED TO {destination} on RELEASE ORDER {current_release_order}"
                                    body=f"{len([i for i in this_shipment_aliens])} unregistered units were shipped on {vehicle_id} to {destination} on {current_release_order}.<br>{[i for i in this_shipment_aliens]}"
                                    sender = "warehouseoly@gmail.com"
                                    recipients = ["alexandras@portolympia.com","conleyb@portolympia.com", "afsiny@portolympia.com"]
                                    #recipients = ["afsiny@portolympia.com"]
                                    password = "xjvxkmzbpotzeuuv"
                                    send_email(subject, body, sender, recipients, password)
                                
                            else:   ###cancel bill of lading
                                pass
        
                    

    
                
        else:
            st.subheader("**Nothing dispatched!**")
   
        
                    ###########################       SUZANO INVENTORY BOARD    ###########################
 
    elif username == 'olysuzanodash':
        #map=gcp_download_new(target_bucket,rf"map.json")
        map=gcp_download(target_bucket,rf"map.json")
        map=json.loads(map)
        mill_info=map["mill_info"]
        inv_bill_of_ladings=gcp_download(target_bucket,rf"terminal_bill_of_ladings.json")
        inv_bill_of_ladings=pd.read_json(inv_bill_of_ladings).T
     
        raw_ro=gcp_download(target_bucket,rf"release_orders/RELEASE_ORDERS.json")
        raw_ro = json.loads(raw_ro)
        bol_mapping = map["bol_mapping"]
        
        suzano,edi_bank,main_inventory,status,mill_progress=st.tabs(["SUZANO DAILY REPORTS","EDI BANK","MAIN INVENTORY","RELEASE ORDER STATUS","SUZANO MILL SHIPMENT SCHEDULE/PROGRESS"])
        
        with suzano:
            
            def convert_df(df):
                # IMPORTANT: Cache the conversion to prevent computation on every rerun
                return df.to_csv().encode('utf-8')
            
            now=datetime.datetime.now()-datetime.timedelta(hours=utc_difference)
            suzano_report_=gcp_download(target_bucket,rf"suzano_report.json")
            suzano_report=json.loads(suzano_report_)
            suzano_report=pd.DataFrame(suzano_report).T
            suzano_report=suzano_report[["Date Shipped","Vehicle", "Shipment ID #", "Consignee","Consignee City","Consignee State","Release #","Carrier","ETA","Ocean BOL#","Batch#","Warehouse","Vessel","Voyage #","Grade","Quantity","Metric Ton", "ADMT","Mode of Transportation"]]
            suzano_report["Shipment ID #"]=[str(i) for i in suzano_report["Shipment ID #"]]
            suzano_report["Batch#"]=[str(i) for i in suzano_report["Batch#"]]
            daily_suzano=suzano_report.copy()
            daily_suzano["Date"]=[datetime.datetime.strptime(i,"%Y-%m-%d %H:%M:%S").date() for i in suzano_report["Date Shipped"]]
            daily_suzano_=daily_suzano[daily_suzano["Date"]==now.date()]
            
            choose = st.radio(
                            "Select Daily or Accumulative Report",
                            ["DAILY", "ACCUMULATIVE", "FIND BY DATE","FIND DATE RANGE","BY RELEASE ORDER","BY BATCH"])
            if choose=="DAILY":
                daily_suzano_=daily_suzano_.reset_index(drop=True)
                daily_suzano_.index=[i+1 for i in daily_suzano_.index]
                daily_suzano_.loc["TOTAL"]=daily_suzano_[["Quantity","Metric Ton","ADMT"]].sum()
                st.dataframe(daily_suzano_)
                csv=convert_df(daily_suzano_)
                file_name=f'OLYMPIA_DAILY_REPORT-{datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%m-%d,%Y")}.csv'
            elif choose=="FIND BY DATE":
                required_date=st.date_input("CHOOSE DATE",key="dssar")
                filtered_suzano=daily_suzano[daily_suzano["Date"]==required_date]
                filtered_suzano=filtered_suzano.reset_index(drop=True)
                filtered_suzano.index=[i+1 for i in filtered_suzano.index]
                filtered_suzano.loc["TOTAL"]=filtered_suzano[["Quantity","Metric Ton","ADMT"]].sum()
                st.dataframe(filtered_suzano)
                csv=convert_df(filtered_suzano)
                file_name=f'OLYMPIA_SHIPMENT_REPORT-{datetime.datetime.strftime(required_date,"%m-%d,%Y")}.csv'

            elif choose=="BY RELEASE ORDER":
                report_ro=st.selectbox("SELECT RELEASE ORDER",([i for i in raw_ro]),key="sdgerw")
                ro_suzano=daily_suzano[daily_suzano["Release #"]==report_ro]
                ro_suzano=ro_suzano.reset_index(drop=True)
                ro_suzano.index=[i+1 for i in ro_suzano.index]
                ro_suzano.loc["TOTAL"]=ro_suzano[["Quantity","Metric Ton","ADMT"]].sum()
                st.dataframe(ro_suzano)
                csv=convert_df(ro_suzano)
                file_name=f'OLYMPIA_SHIPMENT_REPORT-ReleaseOrder-{report_ro}.csv'

            elif choose=="BY BATCH":
                report_batch=st.selectbox("SELECT BATCH",(daily_suzano["Batch#"].unique()),key="sddgerw")
                batch_suzano=daily_suzano[daily_suzano["Batch#"]==report_batch]
                batch_suzano=batch_suzano.reset_index(drop=True)
                batch_suzano.index=[i+1 for i in batch_suzano.index]
                batch_suzano.loc["TOTAL"]=batch_suzano[["Quantity","Metric Ton","ADMT"]].sum()
                st.dataframe(batch_suzano)
                csv=convert_df(batch_suzano)
                file_name=f'OLYMPIA_SHIPMENT_REPORT-Batch-{report_batch}.csv'

            elif choose=="FIND DATE RANGE":
                datecol1,datecol2,datecol3=st.columns([3,3,4])
                with datecol1:
                    tarih1=st.date_input("FROM",key="dsssaar")
                with datecol2:
                    tarih2=st.date_input("TO",key="dssdar")
                    
                range_suzano=daily_suzano[(daily_suzano["Date"]>=tarih1)&(daily_suzano["Date"]<=tarih2)]
                range_suzano=range_suzano.reset_index(drop=True)
                range_suzano.index=[i+1 for i in range_suzano.index]
                range_suzano.loc["TOTAL"]=range_suzano[["Quantity","Metric Ton","ADMT"]].sum()
                st.dataframe(range_suzano)
                csv=convert_df(range_suzano)
                file_name=f'OLYMPIA_SHIPMENT_REPORT-daterange.csv'
            
            else:
                st.dataframe(suzano_report)
                csv=convert_df(suzano_report)
                file_name=f'OLYMPIA_ALL_SHIPMENTS to {datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%m-%d,%Y")}.csv'
            
            
            
           
            
        
            st.download_button(
                label="DOWNLOAD REPORT AS CSV",
                data=csv,
                file_name=file_name,
                mime='text/csv')
            

        with edi_bank:
            edi_files=list_files_in_subfolder(target_bucket, rf"EDIS/")
            requested_edi_file=st.selectbox("SELECT EDI",edi_files[1:])
            
            display_edi=st.toggle("DISPLAY EDI")
            if display_edi:
                data=gcp_download(target_bucket, rf"EDIS/{requested_edi_file}")
                st.text_area("EDI",data,height=400)                                
           
            st.download_button(
                label="DOWNLOAD EDI",
                data=gcp_download(target_bucket, rf"EDIS/{requested_edi_file}"),
                file_name=f'{requested_edi_file}',
                mime='text/csv')
            
            
            
        with main_inventory:
            
            maintenance=False
                            
            if maintenance:
                st.title("CURRENTLY UNDER MAINTENANCE, CHECK BACK LATER")
                           
            else:
                inventory,daily,unregistered=st.tabs(["INVENTORY","DAILY SHIPMENT REPORT","UNREGISTERED LOTS FOUND"])
                
                with daily:
                    
                    amount_dict={"KIRKENES-2304":9200,"JUVENTAS-2308":10000,"LYSEFJORD-2308":10000,"LAGUNA-3142":453,"FRONTIER-55VC":9811,"BEIJA_FLOR-88VC":11335}
                    inv_vessel=st.selectbox("Select Vessel",[i for i in map['batch_mapping']])
                    kf=inv_bill_of_ladings.iloc[1:].copy()
                    kf['issued'] = pd.to_datetime(kf['issued'])
                    kf=kf[kf["vessel"]==inv_vessel]
                    
                    kf['Date'] = kf['issued'].dt.date
                    kf['Date'] = pd.to_datetime(kf['Date'])
                    # Create a date range from the minimum to maximum date in the 'issued' column
                    date_range = pd.date_range(start=kf['Date'].min(), end=kf['Date'].max(), freq='D')
                    
                    # Create a DataFrame with the date range
                    date_df = pd.DataFrame({'Date': date_range})
                    # Merge the date range DataFrame with the original DataFrame based on the 'Date' column
                    merged_df = pd.merge(date_df, kf, how='left', on='Date')
                    merged_df['quantity'].fillna(0, inplace=True)
                    merged_df['Shipped Tonnage']=merged_df['quantity']*2
                    merged_df_grouped=merged_df.groupby('Date')[['quantity','Shipped Tonnage']].sum()
                    merged_df_grouped['Accumulated_Quantity'] = merged_df_grouped['quantity'].cumsum()
                    merged_df_grouped["Accumulated_Tonnage"]=merged_df_grouped['Accumulated_Quantity']*2
                    merged_df_grouped["Remaining_Units"]=[amount_dict[inv_vessel]-i for i in merged_df_grouped['Accumulated_Quantity']]
                    merged_df_grouped["Remaining_Tonnage"]=merged_df_grouped["Remaining_Units"]*2
                    merged_df_grouped.rename(columns={'quantity':"Shipped Quantity", 'Accumulated_Quantity':"Shipped Qty To_Date",
                                                      'Accumulated_Tonnage':"Shipped Tonnage To_Date"},inplace=True)
                    merged_df_grouped=merged_df_grouped.reset_index()
                    merged_df_grouped["Date"]=merged_df_grouped['Date'].dt.strftime('%m-%d-%Y, %A')
                    #merged_df_grouped=merged_df_grouped.set_index("Date",drop=True)
                  
                    st.dataframe(merged_df_grouped)
                    csv_inventory=convert_df(merged_df_grouped)
                    st.download_button(
                        label="DOWNLOAD INVENTORY REPORT AS CSV",
                        data=csv_inventory,
                        file_name=f'INVENTORY REPORT-{datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%Y_%m_%d")}.csv',
                        mime='text/csv')   
                    
                        
                with inventory:
                    bols = {}
                    for key, value in raw_ro.items():
                        for item_key, item_value in value.items():
                            if isinstance(item_value, dict):
                                ocean_bill_of_lading = item_value.get('ocean_bill_of_lading')
                                if ocean_bill_of_lading:
                                    if ocean_bill_of_lading not in bols:
                                        bols[ocean_bill_of_lading] = []
                                    bols[ocean_bill_of_lading].append(key)
                    for i in map['bol_mapping']:
                        if i not in bols:
                            bols[i]=[]

                    inventory={}
                    a=[i for i in map['bol_mapping']]
                    for bill in a:
                        inventory[bill]=[map['bol_mapping'][bill]['total'],map['bol_mapping'][bill]['damaged']]
                        
                    def extract_qt(data,ro,bol):
                        totals=[0,0,0]
                        sales_group=["001","002","003","004","005"]
                        for item in data[ro]:
                            if item in sales_group:
                                if data[ro][item]['ocean_bill_of_lading']==bol:
                                    totals[0]+=data[ro][item]['total']
                                    totals[1]+=data[ro][item]['shipped']
                                    totals[2]+=data[ro][item]['remaining']
                        return totals
                    
                    final={}
                    for k in inventory.keys():
                        final[k]={"Total":0,"Damaged":0,"Fit To Ship":0,"Allocated to ROs":0,"Shipped":0,
                                 "Remaining in Warehouse":0,"Remaining on ROs":0,"Remaining After ROs":0}
                        vector=np.zeros(3)
                        final[k]["Total"]=inventory[k][0]
                        final[k]["Damaged"]=inventory[k][1]
                        final[k]["Fit To Ship"]=final[k]["Total"]-final[k]["Damaged"]   
                    
                        if k in bols:
                            if len(bols[k])>0:
                                for ro in set(bols[k]):
                                    a,b,c=extract_qt(raw_ro,ro,k)[0],extract_qt(raw_ro,ro,k)[1],extract_qt(raw_ro,ro,k)[2]
                                    final[k]["Allocated to ROs"]+=a
                                    #final[k]["Shipped"]=inv_bill_of_ladings.groupby("ocean_bill_of_lading")[['quantity']].sum().loc[k,'quantity']
                                    final[k]["Shipped"]+=b
                    
                                    final[k]["Remaining in Warehouse"]=final[k]["Fit To Ship"]-final[k]["Shipped"]
                                    final[k]["Remaining on ROs"]=final[k]["Allocated to ROs"]-final[k]["Shipped"]
                                    final[k]["Remaining After ROs"]=final[k]["Fit To Ship"]-final[k]["Allocated to ROs"]
                            else:
                                final[k]["Remaining in Warehouse"]=final[k]["Fit To Ship"]
                                final[k]["Remaining on ROs"]=0
                                final[k]["Remaining After ROs"]=final[k]["Fit To Ship"]-final[k]["Allocated to ROs"]
                        else:
                            pass
                    temp=pd.DataFrame(final).T
                    temp.loc["TOTAL"]=temp.sum(axis=0)
                    
                    
                    tempo=temp*2

                    inv_col1,inv_col2=st.columns([7,3])
                    with inv_col1:
                        st.subheader("By Ocean BOL,UNITS")
                        st.dataframe(temp)
                        st.subheader("By Ocean BOL,TONS")
                        st.dataframe(tempo)
        
                with status:
                
                    status_dict={}
                    sales_group=["001","002","003","004","005"]
                    for ro in raw_ro:
                        for sale in [i for i in raw_ro[ro] if i in sales_group]:
                            status_dict[f"{ro}-{sale}"]={"Release Order #":ro,"Sales Order #":sale,
                                                "Destination":raw_ro[ro]['destination'],
                                                "Ocean BOL":raw_ro[ro][sale]['ocean_bill_of_lading'],
                                                "Total":raw_ro[ro][sale]['total'],
                                                "Shipped":raw_ro[ro][sale]['shipped'],
                                                "Remaining":raw_ro[ro][sale]['remaining']}
                    status_frame=pd.DataFrame(status_dict).T.set_index("Release Order #",drop=True)
                    active_frame_=status_frame[status_frame["Remaining"]>0]
                    status_frame.loc["Total"]=status_frame[["Total","Shipped","Remaining"]].sum()
                    active_frame=active_frame_.copy()
                    active_frame.loc["Total"]=active_frame[["Total","Shipped","Remaining"]].sum()
                    
                    st.markdown(active_frame.to_html(render_links=True),unsafe_allow_html=True)
    
                    
                    release_orders = status_frame.index[:-1]
                    release_orders = pd.Categorical(release_orders)
                    active_order_names = [f"{i} to {raw_ro[i]['destination']}" for i in active_frame_.index]
                    destinations=[raw_ro[i]['destination'] for i in active_frame_.index]
                    active_orders=[str(i) for i in active_frame.index]
                   
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=active_orders, y=active_frame["Total"], name='Total', marker_color='lightgray'))
                    fig.add_trace(go.Bar(x=active_orders, y=active_frame["Shipped"], name='Shipped', marker_color='blue', opacity=0.7))
                    remaining_data = [remaining if remaining > 0 else None for remaining in active_frame_["Remaining"]]
                    fig.add_trace(go.Scatter(x=active_orders, y=remaining_data, mode='markers', name='Remaining', marker=dict(color='red', size=10)))
                    
                    #annotations = [dict(x=release_order, y=total_quantity, text=destination, showarrow=True, arrowhead=4, ax=0, ay=-30) for release_order, total_quantity, destination in zip(active_orders, active_frame["Total"], destinations)]
                    #fig.update_layout(annotations=annotations)
    
                    # fig.add_annotation(x="3172296", y=800, text="destination",
                    #                        showarrow=True, arrowhead=4, ax=0, ay=-30)
                    
                    fig.update_layout(title='ACTIVE RELEASE ORDERS',
                                      xaxis_title='Release Orders',
                                      yaxis_title='Quantities',
                                      barmode='overlay',
                                      width=1300,
                                      height=700,
                                      xaxis=dict(tickangle=-90, type='category'))
                    
                    st.plotly_chart(fig)
                    
                    
                    duration=st.toggle("Duration Report")
                    if duration:
                        
                        temp_dict={}
                            
                        for rel_ord in raw_ro:
                            for sales in [i for i in raw_ro[rel_ord] if i in ["001","002","003","004","005"]]:
                                temp_dict[rel_ord,sales]={}
                                dest=raw_ro[rel_ord]['destination']
                                vessel=raw_ro[rel_ord][sales]['vessel']
                                total=raw_ro[rel_ord][sales]['total']
                                remaining=raw_ro[rel_ord][sales]['remaining']
                                temp_dict[rel_ord,sales]={'destination': dest,'vessel': vessel,'total':total,'remaining':remaining}
                        temp_df=pd.DataFrame(temp_dict).T
                      
                        temp_df= temp_df.rename_axis(['release_order','sales_order'], axis=0)
                    
                        temp_df['First Shipment'] = temp_df.index.map(inv_bill_of_ladings.groupby(['release_order','sales_order'])['issued'].first())
                        
                        for i in temp_df.index:
                            if temp_df.loc[i,'remaining']<=2:
                                try:
                                    temp_df.loc[i,"Last Shipment"]=inv_bill_of_ladings.groupby(['release_order','sales_order']).issued.last().loc[i]
                                except:
                                    temp_df.loc[i,"Last Shipment"]=datetime.datetime.now()
                                temp_df.loc[i,"Duration"]=(pd.to_datetime(temp_df.loc[i,"Last Shipment"])-pd.to_datetime(temp_df.loc[i,"First Shipment"])).days+1
                        
                        temp_df['First Shipment'] = temp_df['First Shipment'].fillna(datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'))
                        temp_df['Last Shipment'] = temp_df['Last Shipment'].fillna(datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'))
                        
                        ####
                        
                        def business_days(start_date, end_date):
                            return pd.date_range(start=start_date, end=end_date, freq=BDay())
                        temp_df['# of Shipment Days'] = temp_df.apply(lambda row: len(business_days(row['First Shipment'], row['Last Shipment'])), axis=1)
                        df_temp=inv_bill_of_ladings.copy()
                        df_temp["issued"]=[pd.to_datetime(i).date() for i in df_temp["issued"]]
                        for i in temp_df.index:
                            try:
                                temp_df.loc[i,"Utilized Shipment Days"]=df_temp.groupby(["release_order",'sales_order'])[["issued"]].nunique().loc[i,'issued']
                            except:
                                temp_df.loc[i,"Utilized Shipment Days"]=0
                        
                        temp_df['First Shipment'] = temp_df['First Shipment'].apply(lambda x: datetime.datetime.strftime(datetime.datetime.strptime(x,'%Y-%m-%d %H:%M:%S'),'%d-%b,%Y'))
                        temp_df['Last Shipment'] = temp_df['Last Shipment'].apply(lambda x: datetime.datetime.strftime(datetime.datetime.strptime(x,'%Y-%m-%d %H:%M:%S'),'%d-%b,%Y') if type(x)==str else None)
                        liste=['Duration','# of Shipment Days',"Utilized Shipment Days"]
                        for col in liste:
                            temp_df[col] = temp_df[col].apply(lambda x: f" {int(x)} days" if not pd.isna(x) else np.nan)
                        temp_df['remaining'] = temp_df['remaining'].apply(lambda x: int(x))
                        temp_df.columns=['Destination', 'Vessel', 'Total Units', 'Remaining Units', 'First Shipment',
                               'Last Shipment', 'Duration', '# of Calendar Shipment Days',
                               'Utilized Calendar Shipment Days']
                        st.dataframe(temp_df)
        with mill_progress:
            
            mf_numbers=json.loads(gcp_download(target_bucket,rf"release_orders/mf_numbers.json"))
                
            bill_of_ladings=gcp_download(target_bucket,rf"terminal_bill_of_ladings.json")
            bill_of_ladings=json.loads(bill_of_ladings)
            bill=pd.DataFrame(bill_of_ladings).T
            values=[]
            mfs=[]
            for i in bill.index:
                if len(i.split("|"))>1:
                    values.append(i.split("|")[1])
                    mfs.append(i.split("|")[0])
                else:
                    values.append(None)
                    mfs.append(i)
            bill.insert(0,"Shipment",values)
            bill.insert(1,"MF",mfs)
            
            suzano_shipment_=gcp_download(target_bucket,rf"release_orders/suzano_shipments.json")
            suzano_shipment=json.loads(suzano_shipment_)
            suzano_shipment=pd.DataFrame(suzano_shipment).T

            suzano_shipment["Shipment ID"]=suzano_shipment["Shipment ID"].astype("str")
            bill["Shipment"]=bill["Shipment"].astype("str")
            suzano_shipment["Pickup"]=pd.to_datetime(suzano_shipment["Pickup"])
            suzano_shipment=suzano_shipment[suzano_shipment["Pickup"]>datetime.datetime(2024, 9, 24)]
            suzano_shipment.reset_index(drop=True,inplace=True)
            for i in suzano_shipment.index:
                sh=suzano_shipment.loc[i,"Shipment ID"]
                #print(sh)
                if sh in bill[~bill["Shipment"].isna()]["Shipment"].to_list():
                    vehicle=bill.loc[bill["Shipment"]==sh,'vehicle'].values[0]
                    bol=str(bill.loc[bill["Shipment"]==sh].index.values[0])
                    suzano_shipment.loc[i,"Transit Status"]="COMPLETED"
                    suzano_shipment.loc[i,"BOL"]=bol
                    suzano_shipment.loc[i,"Vehicle ID"]=vehicle
            for rel,value in mf_numbers.items():
                for date in value:
                    for carrier,liste in value[date].items():
                        if len(liste)>0:
                            try:
                                for k in liste:
                                    suzano_shipment.loc[suzano_shipment["Shipment ID"]==k.split("|")[1],"Transit Status"]="SCHEDULED"
                            except:
                                pass
            st.subheader("SUZANO OTM LIST")
            st.write(suzano_shipment)

elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')
    
    
    
    
        
     
