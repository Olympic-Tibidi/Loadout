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


def upload_cs_file(bucket_name, source_file_name, destination_file_name): 
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(destination_file_name)
    blob.upload_from_filename(source_file_name)
    return True
def upload_json_file(bucket_name, source_file_name, destination_file_name): 
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(destination_file_name)
    blob.upload_from_filename(source_file_name,content_type="application/json")
    return True
def upload_xl_file(bucket_name, uploaded_file, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    uploaded_file.seek(0)

    # Upload the file from the file object provided by st.file_uploader
    blob.upload_from_file(uploaded_file)
# define function that list files in the bucket

def store_release_order_data(release_order_number,destination,po_number,sales_order_item,vessel,batch,ocean_bill_of_lading,wrap,dryness,unitized,quantity,tonnage,transport_type,carrier_code):
       
    # Create a dictionary to store the release order data
    release_order_data = { release_order_number:{
        
        
        'destination':destination,
        "po_number":po_number,
        sales_order_item: {
        "vessel":vessel,
        "batch": batch,
        "ocean_bill_of_lading": ocean_bill_of_lading,
        "grade": wrap,
        "dryness":dryness,
        "transport_type": transport_type,
        "carrier_code": carrier_code,
        "unitized":unitized,
        "quantity":quantity,
        "tonnage":tonnage,
        "shipped":0,
        "remaining":quantity       
        }}              
    }
    
                         

    # Convert the dictionary to JSON format
    json_data = json.dumps(release_order_data)
    return json_data

def add_release_order_data(file,release_order_number,destination,po_number,sales_order_item,vessel,batch,ocean_bill_of_lading,wrap,dryness,unitized,quantity,tonnage,transport_type,carrier_code):
       
    # Edit the loaded current dictionary.
    file[release_order_number]["destination"]= destination
    file[release_order_number]["po_number"]= po_number
    if sales_order_item not in file[release_order_number]:
        file[release_order_number][sales_order_item]={}
    file[release_order_number][sales_order_item]["vessel"]= vessel
    file[release_order_number][sales_order_item]["batch"]= batch
    file[release_order_number][sales_order_item]["ocean_bill_of_lading"]= ocean_bill_of_lading
    file[release_order_number][sales_order_item]["grade"]= wrap
    file[release_order_number][sales_order_item]["dryness"]= dryness
    file[release_order_number][sales_order_item]["transport_type"]= transport_type
    file[release_order_number][sales_order_item]["carrier_code"]= carrier_code
    file[release_order_number][sales_order_item]["unitized"]= unitized
    file[release_order_number][sales_order_item]["quantity"]= quantity
    file[release_order_number][sales_order_item]["tonnage"]= tonnage
    file[release_order_number][sales_order_item]["shipped"]= 0
    file[release_order_number][sales_order_item]["remaining"]= quantity
    
    
       

    # Convert the dictionary to JSON format
    json_data = json.dumps(file)
    return json_data

def edit_release_order_data(file,sales_order_item,quantity,tonnage,shipped,remaining,carrier_code):
       
    # Edit the loaded current dictionary.
    
    file[release_order_number][sales_order_item]["quantity"]= quantity
    file[release_order_number][sales_order_item]["tonnage"]= tonnage
    file[release_order_number][sales_order_item]["shipped"]= shipped
    file[release_order_number][sales_order_item]["remaining"]= remaining
    file[release_order_number][sales_order_item]["carrier_code"]= carrier_code
    
    
       

    # Convert the dictionary to JSON format
    json_data = json.dumps(file)
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


if authentication_status:
    authenticator.logout('Logout', 'main')
    if username == 'ayilmaz' or username=='gatehouse':
        st.subheader("PORT OF OLYMPIA TOS")
        st.write(f'Welcome *{name}*')
        st.set_page_config(
                    page_title="Hello",
                    page_icon="👋",
                )
      
                



    ########################                                WAREHOUSE                            ####################
    
    elif username == 'warehouse':
        bill_mapping=gcp_download(target_bucket,"bill_mapping.json")
        bill_mapping=json.loads(bill_mapping)
        mill_info_=gcp_download(target_bucket,rf"mill_info.json")
        mill_info=json.loads(mill_info_)
        mf_numbers_for_load=gcp_download(target_bucket,rf"release_orders/mf_numbers.json")
        mf_numbers_for_load=json.loads(mf_numbers_for_load)
        no_dispatch=0
        number=None
        if number not in st.session_state:
            st.session_state.number=number
        try:
            dispatched=gcp_download(target_bucket,"dispatched.json")
            dispatched=json.loads(dispatched)
        except:
            no_dispatch=1
            pass
       
        
        double_load=False
        
        if len(dispatched.keys())>0 and not no_dispatch:
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
            #st.write(liste)
            work_order_=st.selectbox("**SELECT RELEASE ORDER/SALES ORDER TO WORK**",liste,index=0 if st.session_state.work_order_ else 0) 
            st.session_state.work_order_=work_order_
            work_order=work_order_.split(" ")[0]
            order=["001","002","003","004","005","006"]
            
            current_release_order=work_order
            current_sales_order=work_order_.split(" ")[1][1:]
            vessel=dispatched[work_order][current_sales_order]["vessel"]
            destination=dispatched[work_order][current_sales_order]['destination']
            
            
            
           #for i in order:                   ##############HERE we check all the sales orders in dispatched[releaseordernumber] dictionary. it breaks after it finds the first sales order
           #     if i in dispatched[work_order].keys():
           #         current_release_order=work_order
            #        current_sales_order=i
             #       vessel=dispatched[work_order][i]["vessel"]
              #      destination=dispatched[work_order][i]['destination']
              #      break
              #  else:
              #      pass
            try:
                next_release_order=dispatched['002']['release_order']    #############################  CHECK HERE ######################## FOR MIXED LOAD
                next_sales_order=dispatched['002']['sales_order']
                
            except:
                
                pass
            info=gcp_download(target_bucket,rf"release_orders/ORDERS/{work_order}.json")
            info=json.loads(info)
            
            vessel=info[current_release_order][current_sales_order]["vessel"]
            #if st.checkbox("CLICK TO LOAD MIXED SKU"):
            #    try:
              #      next_item=gcp_download("olym_suzano",rf"release_orders/{dispatched['2']['vessel']}/{dispatched['2']['release_order']}.json")
              #      double_load=True
             #   except:
               #     st.markdown("**:red[ONLY ONE ITEM IN QUEUE ! ASK NEXT ITEM TO BE DISPATCHED!]**")
                
            
            st.markdown(rf'**:blue[CURRENTLY WORKING] :**')
            load_col1,load_col2=st.columns([9,1])
            
            with load_col1:
                wrap_dict={"ISU":"UNWRAPPED","ISP":"WRAPPED","AEP":"WRAPPED"}
                wrap=info[current_release_order][current_sales_order]["grade"]
                ocean_bill_of_=info[current_release_order][current_sales_order]["ocean_bill_of_lading"]
                unitized=info[current_release_order][current_sales_order]["unitized"]
                quant_=info[current_release_order][current_sales_order]["quantity"]
                real_quant=int(math.floor(quant_))
                ship_=info[current_release_order][current_sales_order]["shipped"]
                ship_bale=(ship_-math.floor(ship_))*8
                remaining=info[current_release_order][current_sales_order]["remaining"]                #######      DEFINED "REMAINING" HERE FOR CHECKS
                temp={f"<b>Release Order #":current_release_order,"<b>Destination":destination,"<b>VESSEL":vessel}
                temp2={"<b>Ocean B/L":ocean_bill_of_,"<b>Type":wrap_dict[wrap],"<b>Prep":unitized}
                temp3={"<b>Total Units":quant_,"<b>Shipped Units":ship_,"<b>Remaining Units":remaining}
                #temp4={"<b>Total Bales":0,"<b>Shipped Bales":int(8*(ship_-math.floor(ship_))),"<b>Remaining Bales":int(8*(remaining-math.floor(remaining)))}
                temp5={"<b>Total Tonnage":quant_*2,"<b>Shipped Tonnage":ship_*2,"<b>Remaining Tonnage":quant_*2-(ship_*2)}


                
                sub_load_col1,sub_load_col2,sub_load_col3,sub_load_col4=st.columns([3,3,3,3])
                
                with sub_load_col1:   
                    #st.markdown(rf'**Release Order-{current_release_order}**')
                    #st.markdown(rf'**Destination : {destination}**')
                    #st.markdown(rf'**VESSEL-{vessel}**')
                    st.write (pd.DataFrame(temp.items(),columns=["Inquiry","Data"]).to_html (escape=False, index=False), unsafe_allow_html=True)
                with sub_load_col2:
                    st.write (pd.DataFrame(temp2.items(),columns=["Inquiry","Data"]).to_html (escape=False, index=False), unsafe_allow_html=True)
                    
                with sub_load_col3:
                    
                    #st.markdown(rf'**Total Quantity : {quant_} Units - {quant_*2} Tons**')
                    #st.markdown(rf'**Shipped : {ship_} Units - {ship_*2} Tons**')
                    
                    if remaining<=10:
                        st.markdown(rf'**:red[CAUTION : Remaining : {remaining} Units]**')

                    a=pd.DataFrame(temp3.items(),columns=["UNITS","Data"])
                    a["Data"]=a["Data"].astype("float")
                    st.write (a.to_html (escape=False, index=False), unsafe_allow_html=True)
               
                with sub_load_col4:
                
                    st.write (pd.DataFrame(temp5.items(),columns=["TONNAGE","Data"]).to_html (escape=False, index=False), unsafe_allow_html=True)
            
            
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
            if info[current_release_order][current_sales_order]["transport_type"]=="TRUCK":
                medium="TRUCK"
            else:
                medium="RAIL"
            
            with col1:
            ######################  LETS GET RID OF INPUT BOXES TO SIMPLIFY LONGSHORE SCREEN
                #terminal_code=st.text_input("Terminal Code","OLYM",disabled=True)
                terminal_code="OLYM"
                #file_date=st.date_input("File Date",datetime.datetime.today()-datetime.timedelta(hours=utc_difference),key="file_dates",disabled=True)
                file_date=datetime.datetime.today()-datetime.timedelta(hours=utc_difference)
                if file_date not in st.session_state:
                    st.session_state.file_date=file_date
                file_time = st.time_input('FileTime', datetime.datetime.now()-datetime.timedelta(hours=utc_difference),step=60,disabled=False)
               #delivery_date=st.date_input("Delivery Date",datetime.datetime.today()-datetime.timedelta(hours=utc_difference),key="delivery_date",disabled=True,visible=False)
                delivery_date=datetime.datetime.today()-datetime.timedelta(hours=utc_difference)
               #eta_date=st.date_input("ETA Date (For Trucks same as delivery date)",delivery_date,key="eta_date",disabled=True)
                eta_date=delivery_date
                carrier_code=info[current_release_order][current_sales_order]["carrier_code"]
                vessel=info[current_release_order][current_sales_order]["vessel"]
                transport_sequential_number="TRUCK"
                transport_type="TRUCK"
                placeholder = st.empty()
                with placeholder.container():
                    vehicle_id=st.text_input("**:blue[Vehicle ID]**",value="",key=7)
                
                    mf=True
                    load_mf_number_issued=False
                    if destination=="CLEARWATER-Lewiston,ID":
                        carrier_code=st.selectbox("Carrier Code",[info[current_release_order][current_sales_order]["carrier_code"],"310897-Ashley"],disabled=False,key=29)
                    else:
                        carrier_code=st.text_input("Carrier Code",info[current_release_order][current_sales_order]["carrier_code"],disabled=True,key=9)
                    if carrier_code=="123456-KBX":
                        if 'load_mf_number' not in st.session_state:
                            st.session_state.load_mf_number = None
                        if release_order_number in mf_numbers_for_load.keys():
                            mf_liste=[i for i in mf_numbers_for_load[release_order_number]]
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
                                st.write(f"**:red[ASK ADMIN TO PUT MF NUMBERS]**")
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
                                   load_mf_number=st.selectbox("MF NUMBER",mf_liste,disabled=False,key=14551)
                                   mf=True
                                   load_mf_number_issued=True
                                   yes=True
                               else:
                                   st.write(f"**:red[ASK ADMIN TO PUT MF NUMBERS]**")
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
                    #release_order_number=st.text_input("Release Order Number",current_release_order,disabled=True,help="Release Order Number without the Item no")
                    release_order_number=current_release_order
                    #sales_order_item=st.text_input("Sales Order Item (Material Code)",current_sales_order,disabled=True)
                    sales_order_item=current_sales_order
                    #ocean_bill_of_lading=st.text_input("Ocean Bill Of Lading",info[current_release_order][current_sales_order]["ocean_bill_of_lading"],disabled=True)
                    ocean_bill_of_lading=info[current_release_order][current_sales_order]["ocean_bill_of_lading"]
                    
                     #batch=st.text_input("Batch",info[current_release_order][current_sales_order]["batch"],disabled=True)
                    batch=info[current_release_order][current_sales_order]["batch"]
                    #grade=st.text_input("Grade",info[current_release_order][current_sales_order]["grade"],disabled=True)
                    grade=info[current_release_order][current_sales_order]["grade"]
                    
           
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
                    units_shipped=gcp_download(target_bucket,rf"terminal_bill_of_ladings.json")
                    units_shipped=pd.read_json(units_shipped).T
                    load_dict={}
                    for row in units_shipped.index[1:]:
                        for unit in units_shipped.loc[row,'loads'].keys():
                            load_dict[unit]={"BOL":row,"RO":units_shipped.loc[row,'release_order'],"destination":units_shipped.loc[row,'destination'],
                                             "OBOL":units_shipped.loc[row,'ocean_bill_of_lading'],
                                             "grade":units_shipped.loc[row,'grade'],"carrier_Id":units_shipped.loc[row,'carrier_id'],
                                             "vehicle":units_shipped.loc[row,'vehicle'],"date":units_shipped.loc[row,'issued'] }
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
                            alternate_vessel=[ship for ship in bill_mapping if ship!=vessel][0]
                            if x[:load_digit] in bill_mapping[alternate_vessel]:
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
                                        if x in load_dict.keys():
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
                                            storage_client = storage.Client()
                                            bucket = storage_client.bucket(target_bucket)
                                            blob = bucket.blob(rf"bill_mapping.json")
                                            blob.upload_from_string(updated_bill)

                                            alien_units=json.loads(gcp_download(target_bucket,rf"alien_units.json"))
                                            alien_units[vessel][x]={}
                                            alien_units[vessel][x]={"Ocean_Bill_Of_Lading":ocean_bill_of_lading,"Batch":batch,"Grade":grade,
                                                                    "Date_Found":datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%Y,%m-%d %H:%M:%S")}
                                            alien_units=json.dumps(alien_units)
                                            storage_client = storage.Client()
                                            bucket = storage_client.bucket(target_bucket)
                                            blob = bucket.blob(rf"alien_units.json")
                                            blob.upload_from_string(alien_units)
                                            
                                            
                                            subject=f"FOUND UNIT {x} NOT IN INVENTORY"
                                            body=f"Clerk identified an uninventoried {'Unwrapped' if grade=='ISU' else 'wrapped'} unit {x}, and after verifying the physical pile, inventoried it into Ocean Bill Of Lading : {ocean_bill_of_lading} for vessel {vessel}. Unit has been put into alien unit list."
                                            sender = "warehouseoly@gmail.com"
                                            recipients = ["alexandras@portolympia.com","conleyb@portolympia.com", "afsiny@portolympia.com"]
                                            #recipients = ["afsiny@portolympia.com"]
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
                                            storage_client = storage.Client()
                                            bucket = storage_client.bucket(target_bucket)
                                            blob = bucket.blob(rf"bill_mapping.json")
                                            blob.upload_from_string(updated_bill)

                                            alien_units=json.loads(gcp_download(target_bucket,rf"alien_units.json"))
                                            alien_units[vessel][x]={}
                                            alien_units[vessel][x]={"Ocean_Bill_Of_Lading":ocean_bill_of_lading,"Batch":batch,"Grade":grade,
                                                                    "Date_Found":datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%Y,%m-%d %H:%M:%S")}
                                            alien_units=json.dumps(alien_units)
                                            storage_client = storage.Client()
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
                
                admt=round(float(info[current_release_order][current_sales_order]["dryness"])/90*st.session_state.updated_quantity*2,4)
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
                
                
            
            load_bill_data=gcp_download(target_bucket,rf"terminal_bill_of_ladings.json")
            load_admin_bill_of_ladings=json.loads(load_bill_data)
            load_admin_bill_of_ladings=pd.DataFrame.from_dict(load_admin_bill_of_ladings).T[1:]
            load_admin_bill_of_ladings=load_admin_bill_of_ladings.sort_values(by="issued")
            last_submitted=load_admin_bill_of_ladings.index[-3:].to_list()
            last_submitted.reverse()
            st.markdown(f"**Last Submitted Bill Of Ladings (From most recent) : {last_submitted}**")

            ####  BOL CREATION
            
            bol,bill_of_ladings=gen_bill_of_lading()
            if load_mf_number_issued:
                bol=st.session_state.load_mf_number
            bol_obl=ocean_bill_of_lading
            bol_ro=release_order_number
            bol_carrier=carrier_code
            if bol_carrier=="432602-NOLAN TRANSPORTATION GROUP":
                bol_carrier="432602-NTG"
            bol_customer_po=f"{info[current_release_order]['po_number']} OLYM"
            bol_date=datetime.datetime.strftime(datetime.datetime.now(),"%b %d,%Y %H:%M")
            
            bol_admt=admt=round(float(info[current_release_order][current_sales_order]["dryness"])/90*st.session_state.updated_quantity*2,4)
            bol_weight=round(quantity*2*2204.62,1)
            bol_vehicle=vehicle_id
            bol_batch=batch
            bol_grade=wrap
            bol_dryness=f"{info[current_release_order][current_sales_order]['dryness']}%"
            bol_mt=quantity*2
            bol_bales=quantity*8
            bol_destination=info[current_release_order]["destination"]
           
            
            def create_pdf():
                mill_data=json.loads(gcp_download(target_bucket,rf"new_mill_database.json"))
                
                # Create a PDF document
                buffer = io.BytesIO()
                c = canvas.Canvas("example.pdf", pagesize=letter)
                
                # Set title and draw text
                c.setTitle("Sample PDF")
                c.setFont("Helvetica", 16)  # Set the default font family and size
                c.drawString(30, 750, "STRAIGHT BILL OF LADING")
                c.setFont("Times-Bold", 16)
                
                c.drawString(420, 750, f"BOL #: {bol}")
                
                
                
                data1 = [
                    ['VESSEL', vessel,'LOAD DATE',f'{bol_date}'],
                    [ 'OBL', f'{bol_obl}','GROSS WEIGHT',f'{bol_weight}'],
                    [ 'RELEASE ORDER',f'{bol_ro}','VEHICLE ID',f'{bol_vehicle}'],
                    [ 'CARRIER', f'{bol_carrier}','ADMT',f'{bol_admt}'],
                ]
            
                # Create a table
                col_widths = [100, 200, 100, 135]
                table1 = Table(data1,colWidths=col_widths,rowHeights=25)
            
                # Add style to the table
                style = TableStyle([
                                    ('BACKGROUND', (0, 0), (0, 3), (0.8, 0.7, 0.6)),  # Background color
                                    ('BACKGROUND', (2, 0), (-2, -1), (0.8, 0.7, 0.6)),  # Background color
                                    ('INNERGRID', (0, 0), (-1, -1), 0.25, (0.2, 0.2, 0.2)),  # Inner grid style
                                    ('BOX', (0, 0), (-1, -1), 0.25, (0.2, 0.2, 0.2)),  # Box style
                                    ('WORDWRAP', (3, 1), (3, -1), True),  # Enable text wrapping
                                ])
                table1.setStyle(style)
                # Draw the table on the canvas
                table1.wrapOn(c, 0, 0)
                table1.drawOn(c, 30, 630)  # Position the table at (100, 500)
                
                # Draw a rectangle
                c.rect(30, 525 ,270, 100)
                c.rect(300, 525 ,270, 100)
                
                c.setFont("Times-Bold", 13)
                c.drawString(35, 610, "SHIP FROM :")
                c.drawString(315, 610, "SHIP TO :")
                c.setFont("Helvetica", 13)
                c.drawString(120, 590, "Port Of Olympia")
                c.drawString(120, 570, "915 Washington St NE")
                c.drawString(120, 550, "Olympia,WA 98501")
                c.drawString(120, 530, "United States")
                c.drawString(340, 590, mill_data[destination]["BOL_Name"])
                c.drawString(340, 570, mill_data[destination]["BOL_Name_2"])
                c.drawString(340, 550, mill_data[destination]["BOL_Addr_1"])
                c.drawString(340, 530, mill_data[destination]["BOL_Addr_2"])
                
                data2 = [
                    ['Batch #', 'Grade','Dryness','MT','Bales'],
                    [ bol_batch, bol_grade,bol_dryness,bol_mt,bol_bales]
                    
                ]
            
                table2= Table(data2,colWidths=108,rowHeights=25)
                table2.setStyle(TableStyle([('BACKGROUND', (0, 0), (4, 0), (0.8, 0.7, 0.6))]))
                table2.setStyle(style)
                table2.wrapOn(c, 0, 0)
                table2.drawOn(c, 30, 470)  # Position the table at (100, 500)
                
                c.drawString(150, 430, "FSC Certified Products. FSC Mix Credit. SCS-COC-009938")
                
                c.setFont("Helvetica-Bold", 13)
                c.rect(30,300,537,100)
                c.drawString(200, 380, "Truck Inspection Record")
                c.setFont("Helvetica", 13)
                c.drawString(110, 360, "Truck is clean and deemed suitable for transporting product.")
                c.line(50,325,200,325)
                c.line(360,325,500,325)
                c.drawString(115, 310, "Sign")
                c.drawString(400, 310, "Print Name")
                
                
                c.rect(30, 250, 250, 50)
                c.rect(280, 250, 287, 50)
                c.drawString(350, 270, "Corrective action if answer “NO”")
                c.drawString(35, 280, "If trailer is in poor condition, do not load!")
                c.drawString(35, 260,"The Port will contact the customer.")
                
                c.rect(30, 220, 250, 30)
                c.rect(280, 220, 30, 30)
                c.rect(310, 220, 30, 30)
                c.rect(340, 220, 227, 30)
                c.drawString(290, 232, "Y")
                c.drawString(320, 232, "N")
                c.drawString(32, 230, "Is the Trailer clean?")
                
                c.rect(30, 190, 250, 30)
                c.rect(280, 190, 30, 30)
                c.rect(310, 190, 30, 30)
                c.rect(340, 190, 227, 30)
                c.drawString(290, 202, "Y")
                c.drawString(320, 202, "N")
                c.drawString(32, 200, "Is the trailer free of debris?")
                
                c.rect(30, 160, 250, 30)
                c.rect(280, 160, 30, 30)
                c.rect(310, 160, 30, 30)
                c.rect(340, 160, 227, 30)
                c.drawString(290, 172, "Y")
                c.drawString(320, 172, "N")
                c.drawString(32, 170, "Is the trailer free of pest/rodent activity?")
                
                c.rect(30, 130, 250, 30)
                c.rect(280, 130, 30, 30)
                c.rect(310, 130, 30, 30)
                c.rect(340, 130, 227, 30)
                c.drawString(290, 142, "Y")
                c.drawString(320, 142, "N")
                c.drawString(32, 140, "Is the trailer free of odors?")
                
                c.setFont("Helvetica-Bold", 6)
                c.drawString(32, 120,"ATTN Trucker: Your signature will acknowledge receipt of the correct description, (size and grade) AND total amount of ______ pieces. THIS WAREHOUSE will NOT be responsible if shipment")
                c.drawString(32, 110,"of incorrect product is made for the loading and securing of product. Trucker is responsible for providing or approving the load plan and for securing the product for over-the-road transportation.")
                
                c.setFont("Helvetica-Bold", 11)
                data3 = [
                    ['', f'                                                                 {bol_date}'],
                    ['', f'                                                                 {bol_date}']   ]
                
                table3= Table(data3,colWidths=280,rowHeights=30)
                table3.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 1), (0.8, 0.7, 0.6))]))
                table3.setStyle(style)
                table3.wrapOn(c, 0, 0)
                table3.drawOn(c, 20, 45)  # Position the table at (100, 500)
                c.drawString(32, 82,"Carrier Signature/ Pick up date")
                c.drawString(32, 52,"Warehouse Signature/ Pick up date")
                
                
                
                # Save the PDF document
                c.save()
                # pdf_bytes = buffer.getvalue()
                # buffer.close()
                with open("example.pdf", "rb") as pdf_file:
                    PDFbyte = pdf_file.read()
                return PDFbyte
               # return "example.pdf"
            
            #pdf_file = create_pdf()
            
            
            st.download_button(label="CREATE/DOWNLOAD BOL", 
                    data=create_pdf(),
                    file_name=f"{calendar.month_name[datetime.datetime.now().month][:3]}-{datetime.datetime.now().day}-{destination}-{bol}.pdf",
                    mime='application/octet-stream')
            
            if yes and mf:
                
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
                        carrier_code=carrier_code.split("-")[0]
                        try:
                            suzano_report_=gcp_download(target_bucket,rf"suzano_report.json")
                            suzano_report=json.loads(suzano_report_)
                        except:
                            suzano_report={}
                        consignee=destination.split("-")[0]
                        consignee_city=mill_info[destination]["city"]
                        consignee_state=mill_info[destination]["state"]
                        vessel_suzano,voyage_suzano=vessel.split("-")
                        if manual_time:
                            eta=datetime.datetime.strftime(file_date+datetime.timedelta(hours=mill_info[destination]['hours']-utc_difference)+datetime.timedelta(minutes=mill_info[destination]['minutes']+30),"%Y-%m-%d  %H:%M:%S")
                        else:
                            eta=datetime.datetime.strftime(datetime.datetime.now()+datetime.timedelta(hours=mill_info[destination]['hours']-utc_difference)+datetime.timedelta(minutes=mill_info[destination]['minutes']+30),"%Y-%m-%d  %H:%M:%S")

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
                            edi_name= f'{bill_of_lading_number}.txt'
                            bill_of_ladings[str(bill_of_lading_number)]={"vessel":vessel,"release_order":release_order_number,"destination":destination,"sales_order":current_sales_order,
                                                                         "ocean_bill_of_lading":ocean_bill_of_lading,"grade":wrap,"carrier_id":carrier_code,"vehicle":vehicle_id,
                                                                         "quantity":st.session_state.updated_quantity,"issued":f"{a_} {b_}","edi_no":edi_name,"loads":pure_loads} 
                                            
                        bill_of_ladings=json.dumps(bill_of_ladings)
                        storage_client = storage.Client()
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
                            storage_client = storage.Client()
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
                            info[current_release_order][current_sales_order]["shipped"]=info[current_release_order][current_sales_order]["shipped"]+quantity
                            info[current_release_order][current_sales_order]["remaining"]=info[current_release_order][current_sales_order]["remaining"]-quantity
                        if info[current_release_order][current_sales_order]["remaining"]<=0:
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
                            storage_client = storage.Client()
                            bucket = storage_client.bucket(target_bucket)
                            blob = bucket.blob(rf"dispatched.json")
                            blob.upload_from_string(json_data)       
                        
                        json_data = json.dumps(info)
                        storage_client = storage.Client()
                        bucket = storage_client.bucket(target_bucket)
                        blob = bucket.blob(rf"release_orders/ORDERS/{current_release_order}.json")
                        blob.upload_from_string(json_data)
                        success_container2=st.empty()
                        time.sleep(0.1)                            
                        success_container2.success(f"Updated Release Order {current_release_order}",icon="✅")

                        try:
                            release_order_database=gcp_download(target_bucket,rf"release_orders/RELEASE_ORDERS.json")
                            release_order_database=json.loads(release_order_database)
                        except:
                            release_order_database={}
                       
                        release_order_database[current_release_order][current_sales_order]["remaining"]=release_order_database[current_release_order][current_sales_order]["remaining"]-quantity
                        release_order_database=json.dumps(release_order_database)
                        storage_client = storage.Client()
                        bucket = storage_client.bucket(target_bucket)
                        blob = bucket.blob(rf"release_orders/RELEASE_ORDERS.json")
                        blob.upload_from_string(release_order_database)
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
                            mf_numbers_for_load[release_order_number].remove(load_mf_number)
                            mf_numbers_for_load=json.dumps(mf_numbers_for_load)
                            storage_client = storage.Client()
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
                                    
                        alien_units=json.dumps(alien_units)
                        storage_client = storage.Client()
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
        
        data=gcp_download(target_bucket,rf"terminal_bill_of_ladings.json")
        bill_of_ladings=json.loads(data)
        mill_info=json.loads(gcp_download(target_bucket,rf"mill_info.json"))
        inv1,inv2,inv3,inv4,inv5,inv6=st.tabs(["DAILY ACTION","SUZANO DAILY REPORTS","EDI BANK","MAIN INVENTORY","SUZANO MILL SHIPMENT SCHEDULE/PROGRESS","RELEASE ORDER STATUS"])
        with inv1:
            
            daily1,daily2,daily3=st.tabs(["TODAY'SHIPMENTS","TRUCKS ENROUTE","TRUCKS AT DESTINATION"])
            with daily1:
                now=datetime.datetime.now()-datetime.timedelta(hours=7)
                text=f"SHIPPED TODAY ON {datetime.datetime.strftime(now.date(),'%b %d, %Y')} - Indexed By Terminal Bill Of Lading"
                st.markdown(f"<p style='font-family:arial,monospace; color: #0099ff;text-shadow: 2px 2px 4px #99ccff;'>{text}</p>",unsafe_allow_html=True)     
                df_bill=pd.DataFrame(bill_of_ladings).T
                df_bill=df_bill[["vessel","release_order","destination","sales_order","ocean_bill_of_lading","grade","carrier_id","vehicle","quantity","issued"]]
                df_bill.columns=["VESSEL","RELEASE ORDER","DESTINATION","SALES ORDER","OCEAN BILL OF LADING","GRADE","CARRIER ID","VEHICLE NO","QUANTITY (UNITS)","ISSUED"]
                df_bill["Date"]=[None]+[datetime.datetime.strptime(i,"%Y-%m-%d %H:%M:%S").date() for i in df_bill["ISSUED"].values[1:]]
                
                df_today=df_bill[df_bill["Date"]==now.date()]
                df_today.insert(9,"TONNAGE",[i*2 for i in df_today["QUANTITY (UNITS)"]])
                df_today.loc["TOTAL","QUANTITY (UNITS)"]=df_today["QUANTITY (UNITS)"].sum()
                df_today.loc["TOTAL","TONNAGE"]=df_today["TONNAGE"].sum()
                   
                st.dataframe(df_today)

        
            with daily2:
                enroute_vehicles={}
                arrived_vehicles={}
                today_arrived_vehicles={}
                for i in bill_of_ladings:
                    if i!="11502400":
                        date_strings=bill_of_ladings[i]["issued"].split(" ")
                        
                        ship_date=datetime.datetime.strptime(date_strings[0],"%Y-%m-%d")
                        ship_time=datetime.datetime.strptime(date_strings[1],"%H:%M:%S").time()
                        
                        #st.write(bill_of_ladings[i]["issued"])
                        destination=bill_of_ladings[i]['destination']
                        truck=bill_of_ladings[i]['vehicle']
                        distance=mill_info[bill_of_ladings[i]['destination']]["distance"]
                        hours_togo=mill_info[bill_of_ladings[i]['destination']]["hours"]
                        minutes_togo=mill_info[bill_of_ladings[i]['destination']]["minutes"]
                        combined_departure=datetime.datetime.combine(ship_date,ship_time)
                       
                        estimated_arrival=combined_departure+datetime.timedelta(minutes=60*hours_togo+minutes_togo)
                        estimated_arrival_string=datetime.datetime.strftime(estimated_arrival,"%B %d,%Y -- %H:%M")
                        now=datetime.datetime.now()-datetime.timedelta(hours=7)
                        if estimated_arrival>now:
                            
                            enroute_vehicles[truck]={"DESTINATION":destination,"CARGO":bill_of_ladings[i]["ocean_bill_of_lading"],
                                             "QUANTITY":f'{2*bill_of_ladings[i]["quantity"]} TONS',"LOADED TIME":f"{ship_date.date()}---{ship_time}","ETA":estimated_arrival_string}
                        elif estimated_arrival.date()==now.date() and estimated_arrival<now:
                            today_arrived_vehicles[truck]={"DESTINATION":destination,"CARGO":bill_of_ladings[i]["ocean_bill_of_lading"],
                                             "QUANTITY":f'{2*bill_of_ladings[i]["quantity"]} TONS',"LOADED TIME":f"{ship_date.date()}---{ship_time}",
                                                             "ARRIVAL TIME":estimated_arrival_string}
                        else:
                            
                            arrived_vehicles[truck]={"DESTINATION":destination,"CARGO":bill_of_ladings[i]["ocean_bill_of_lading"],
                                             "QUANTITY":f'{2*bill_of_ladings[i]["quantity"]} TONS',"LOADED TIME":f"{ship_date.date()}---{ship_time}",
                                                             "ARRIVAL TIME":estimated_arrival_string,"ARRIVAL":estimated_arrival}
                                    
                arrived_vehicles=pd.DataFrame(arrived_vehicles)
                arrived_vehicles=arrived_vehicles.rename_axis('TRUCK NO')
                arrived_vehicles=arrived_vehicles.T
                arrived_vehicles=arrived_vehicles.sort_values(by="ARRIVAL")
                today_arrived_vehicles=pd.DataFrame(today_arrived_vehicles)
                today_arrived_vehicles=today_arrived_vehicles.rename_axis('TRUCK NO')
                enroute_vehicles=pd.DataFrame(enroute_vehicles)
                enroute_vehicles=enroute_vehicles.rename_axis('TRUCK NO')
                st.dataframe(enroute_vehicles.T)                      
                for i in enroute_vehicles:
                    st.write(f"Truck No : {i} is Enroute to {enroute_vehicles[i]['DESTINATION']} at {enroute_vehicles[i]['ETA']}")
            with daily3:
                select = st.radio(
                                "Select Today's Arrived Vehicles or All Delivered Vehicles",
                                ["TODAY'S ARRIVALS", "ALL ARRIVALS"])
                if select=="TODAY'S ARRIVALS":
                    st.table(today_arrived_vehicles.T)
                if select=="ALL ARRIVALS":
                    
                    st.table(arrived_vehicles.drop(columns=['ARRIVAL']))
        
        with inv2:
            
            def convert_df(df):
                # IMPORTANT: Cache the conversion to prevent computation on every rerun
                return df.to_csv().encode('utf-8')
            try:
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
                                ["DAILY", "ACCUMULATIVE", "FIND BY DATE"])
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
                else:
                    st.dataframe(suzano_report)
                    csv=convert_df(suzano_report)
                    file_name=f'OLYMPIA_ALL_SHIPMENTS to {datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%m-%d,%Y")}.csv'
                
                
                
               
                
            
                st.download_button(
                    label="DOWNLOAD REPORT AS CSV",
                    data=csv,
                    file_name=file_name,
                    mime='text/csv')
            except:
                st.write("NO REPORTS RECORDED")
            

        with inv3:
            edi_files=list_files_in_subfolder(target_bucket, rf"EDIS/")
            requested_edi_file=st.selectbox("SELECT EDI",edi_files[1:])
            try:
                requested_edi=gcp_download(target_bucket, rf"EDIS/{requested_edi_file}")
                st.text_area("EDI",requested_edi,height=400)
                st.download_button(
                    label="DOWNLOAD EDI",
                    data=requested_edi,
                    file_name=f'{requested_edi_file}',
                    mime='text/csv')

            except:
                st.write("NO EDI FILES IN DIRECTORY")
            

            
        with inv4:
            combined=gcp_csv_to_df(target_bucket,rf"combined.csv")
            combined["Batch"]=combined["Batch"].astype(str)
            
            inv_bill_of_ladings=gcp_download(target_bucket,rf"terminal_bill_of_ladings.json")
            inv_bill_of_ladings=pd.read_json(inv_bill_of_ladings).T
            ro=gcp_download(target_bucket,rf"release_orders/RELEASE_ORDERS.json")
            raw_ro = json.loads(ro)
            bol_mapping=gcp_download(target_bucket,rf"bol_mapping.json")
            bol_mapping = json.loads(bol_mapping)
            
            maintenance=False
                            
            if maintenance:
                st.title("CURRENTLY UNDER MAINTENANCE, CHECK BACK LATER")

                           
            else:
                inv4tab1,inv4tab2,inv4tab3=st.tabs(["DAILY SHIPMENT REPORT","INVENTORY","UNREGISTERED LOTS FOUND"])
                with inv4tab1:
                    
                    amount_dict={"KIRKENES-2304":9200,"JUVENTAS-2308":10000,"LYSEFJORD-2308":10000,"LAGUNA-3142":250}
                    inv_vessel=st.selectbox("Select Vessel",["KIRKENES-2304","JUVENTAS-2308","LYSEFJORD-2308","LAGUNA-3142"])
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
                    
                        
                with inv4tab2:
                    

                    #raw_ro = json.loads(ro)
                    grouped_df = inv_bill_of_ladings.groupby('ocean_bill_of_lading')['release_order'].agg(set)
                    bols=grouped_df.T.to_dict()
                    #st.write(bol_mapping)
                    
                    
                    
                    
                    bols_allocated={}
                    for rel in raw_ro:
                        for sale in raw_ro[rel]:
                            member=raw_ro[rel][sale]['ocean_bill_of_lading']
                            if member not in bols_allocated:
                                bols_allocated[member]={}
                                bols_allocated[member]["RO"]=rel
                                bols_allocated[member]["Total"]=raw_ro[rel][sale]['total']
                                bols_allocated[member]["Remaining"]=raw_ro[rel][sale]['remaining']
                            else:
                                bols_allocated[member]["RO"]=rel
                                bols_allocated[member]["Total"]+=raw_ro[rel][sale]['total']
                                bols_allocated[member]["Remaining"]+=raw_ro[rel][sale]['remaining']
                    
                    #raw_ro = json.loads(ro)
                    grouped_df = inv_bill_of_ladings.groupby('ocean_bill_of_lading')['release_order'].agg(set)
                    bols=grouped_df.T.to_dict()
                    
                    
                    
                    
                    
                    grouped_df = inv_bill_of_ladings.groupby(['release_order','ocean_bill_of_lading','destination'])[['quantity']].agg(sum)
                    info=grouped_df.T.to_dict()
                    info_=info.copy()
                    for bol in bols: #### for each bill of lading
                        for rel_ord in bols[bol]:##   (for each release order on that bill of lading)
                            found_keys = [key for key in info.keys() if rel_ord in key]
                            for key in found_keys:
                                #print(key)
                                qt=info[key]['quantity']
                                info_.update({key:{'wrap':bol_mapping[bol]['grade'],'total':sum([raw_ro[rel_ord][sales]['total'] for sales in raw_ro[rel_ord]]) if rel_ord in ro else 0,
                                                  'shipped':qt,'remaining':sum([raw_ro[rel_ord][sales]['remaining'] for sales in raw_ro[rel_ord]])}})
                    new=pd.DataFrame(info_).T
                    new=new.reset_index()
                    new.groupby('level_1')['remaining'].sum()
                    
                    temp1=new.groupby("level_1")[["total","shipped","remaining"]].sum()
                    temp2=combined.groupby("Ocean B/L")[["Bales","Shipped","Remaining"]].sum()/8
                    temp=temp2.copy()
                    temp["Shipped"]=temp.index.map(lambda x: temp1.loc[x,"shipped"] if x in temp1.index else 0)
                    temp.columns=["Total","Shipped","Remaining"]
                    temp.columns=["Total","Shipped","Remaining"]
                    
                    temp.insert(2,"Damaged",[1,0,5,2,2,0,0,0])
                    temp["Remaining"]=temp.Total-temp.Shipped-temp.Damaged
                    
                    temp=temp.astype(int)
                    
                    temp.insert(1,"Allocated to ROs",[bols_allocated[i]["Total"] for i in temp.index])
                    temp.insert(3,"Remaining on ROs",[bols_allocated[i]["Remaining"] for i in temp.index])
                    temp["Remaining After ROs"]=temp["Total"] -temp["Allocated to ROs"]-temp["Damaged"]
                    temp.loc["TOTAL"]=temp.sum(axis=0)
                    
                    
                    tempo=temp*2

                    #inv_col1,inv_col2=st.columns([2,2])
                   # with inv_col1:
                    st.subheader("By Ocean BOL,UNITS")
                    st.dataframe(temp)
                    #with inv_col2:
                    st.subheader("By Ocean BOL,TONS")
                    st.dataframe(tempo)               
                with inv4tab3:
                    alien_units=json.loads(gcp_download(target_bucket,rf"alien_units.json"))
                    alien_vessel=st.selectbox("SELECT VESSEL",["KIRKENES-2304","JUVENTAS-2308","LAGUNA-3142"])
                    alien_list=pd.DataFrame(alien_units[alien_vessel]).T
                    alien_list.reset_index(inplace=True)
                    alien_list.index=alien_list.index+1
                    st.markdown(f"**{len(alien_list)} units that are not on the shipping file found on {alien_vessel}**")
                    st.dataframe(alien_list)
                    
                  
        with inv5:
            inv_bill_of_ladings=gcp_download(target_bucket,rf"terminal_bill_of_ladings.json")
            inv_bill_of_ladings=pd.read_json(inv_bill_of_ladings).T
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
                csv_weekly=convert_df(resampled_quantity)
                st.download_button(
                label="DOWNLOAD WEEKLY REPORT AS CSV",
                data=csv_weekly,
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


        with inv6:
            inv_bill_of_ladings=gcp_download(target_bucket,rf"terminal_bill_of_ladings.json")
            inv_bill_of_ladings=pd.read_json(inv_bill_of_ladings).T
            ro=gcp_download(target_bucket,rf"release_orders/RELEASE_ORDERS.json")
            raw_ro = json.loads(ro)
            grouped_df = inv_bill_of_ladings.groupby(['release_order','sales_order','destination'])[['quantity']].agg(sum)
            info=grouped_df.T.to_dict()
            for rel_ord in raw_ro:
                for sales in raw_ro[rel_ord]:
                    try:
                        found_key = next((key for key in info.keys() if rel_ord in key and sales in key), None)
                        qt=info[found_key]['quantity']
                    except:
                        qt=0
                    info[rel_ord,sales,raw_ro[rel_ord][sales]['destination']]={'total':raw_ro[rel_ord][sales]['total'],
                                            'shipped':qt,'remaining':raw_ro[rel_ord][sales]['remaining']}
                                        
            new=pd.DataFrame(info).T
            new=new.reset_index()
            #new.groupby('level_1')['remaining'].sum()
            new.columns=["Release Order #","Sales Order #","Destination","Total","Shipped","Remaining"]
            new.index=[i+1 for i in new.index]
            #new.columns=["Release Order #","Sales Order #","Destination","Total","Shipped","Remaining"]
            new.index=[i+1 for i in new.index]
            new.loc["Total"]=new[["Total","Shipped","Remaining"]].sum()
            release_orders = [str(key[0]) for key in info.keys()]
            release_orders=[str(i) for i in release_orders]
            release_orders = pd.Categorical(release_orders)
            
            total_quantities = [item['total'] for item in info.values()]
            shipped_quantities = [item['shipped'] for item in info.values()]
            remaining_quantities = [item['remaining'] for item in info.values()]
            destinations = [key[2] for key in info.keys()]
            # Calculate the percentage of shipped quantities
            #percentage_shipped = [shipped / total * 100 for shipped, total in zip(shipped_quantities, total_quantities)]
            
            # Create a Plotly bar chart
            fig = go.Figure()
            
            # Add bars for total quantities
            fig.add_trace(go.Bar(x=release_orders, y=total_quantities, name='Total', marker_color='lightgray'))
            
            # Add filled bars for shipped quantities
            fig.add_trace(go.Bar(x=release_orders, y=shipped_quantities, name='Shipped', marker_color='blue', opacity=0.7))
            
            # Add remaining quantities as separate scatter points
            #fig.add_trace(go.Scatter(x=release_orders, y=remaining_quantities, mode='markers', name='Remaining', marker=dict(color='red', size=10)))
            
            remaining_data = [remaining if remaining > 0 else None for remaining in remaining_quantities]
            fig.add_trace(go.Scatter(x=release_orders, y=remaining_data, mode='markers', name='Remaining', marker=dict(color='red', size=10)))
            
            # Add destinations as annotations
            annotations = [dict(x=release_order, y=total_quantity, text=destination, showarrow=True, arrowhead=4, ax=0, ay=-30) for release_order, total_quantity, destination in zip(release_orders, total_quantities, destinations)]
            #fig.update_layout(annotations=annotations)
            
            # Update layout
            fig.update_layout(title='Shipment Status',
                              xaxis_title='Release Orders',
                              yaxis_title='Quantities',
                              barmode='overlay',
                              width=1300,
                              height=700,
                              xaxis=dict(tickangle=-90, type='category'))
            #relcol1,relcol2=st.columns([5,5])
            #with relcol1:
                #st.dataframe(new)
            #with relcol2:
                #st.plotly_chart(fig)
            st.dataframe(new)
            st.plotly_chart(fig)
            temp_dict={}
            for rel_ord in raw_ro:
                
                
                for sales in raw_ro[rel_ord]:
                    temp_dict[rel_ord,sales]={}
                    dest=raw_ro[rel_ord][sales]['destination']
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


elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')




    
 
