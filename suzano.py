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
import yaml
from yaml.loader import SafeLoader

import plotly.graph_objects as go
st.set_page_config(layout="wide")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "client_secrets.json"

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
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_file_name)
    data = blob.download_as_text()
    return data

def gcp_csv_to_df(bucket_name, source_file_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob("Inventory.csv")
    data = blob.download_as_bytes()
    df = pd.read_csv(io.BytesIO(data))
    print(f'Pulled down file from bucket {bucket_name}, file name: {source_file_name}')
    return df
def upload_cs_file(bucket_name, source_file_name, destination_file_name): 
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(destination_file_name)
    blob.upload_from_filename(source_file_name)
    return True
# define function that list files in the bucket
def list_cs_files(bucket_name): 
    storage_client = storage.Client()

    file_list = storage_client.list_blobs(bucket_name)
    file_list = [file.name for file in file_list]

    return file_list
def list_cs_files_f(bucket_name, folder_name):
    storage_client = storage.Client()

    # List all blobs in the bucket
    blobs = storage_client.list_blobs(bucket_name)

    # Filter blobs that are within the specified folder
    folder_files = [blob.name for blob in blobs if blob.name.startswith(folder_name)]

    return folder_files
def list_files_in_folder(bucket_name, folder_name):
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(bucket_name, prefix=folder_name)

    # Extract only the filenames without the folder path
    filenames = [blob.name.split("/")[-1] for blob in blobs if "/" in blob.name]

    return filenames
def list_files_in_subfolder(bucket_name, folder_name):
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(bucket_name, prefix=folder_name, delimiter='/')

    # Extract only the filenames without the folder path
    filenames = [blob.name.split('/')[-1] for blob in blobs]

    return filenames
def store_release_order_data(vessel,release_order_number,destination,sales_order_item,batch,ocean_bill_of_lading,wrap,dryness,unitized,quantity,tonnage,transport_type,carrier_code):
       
    # Create a dictionary to store the release order data
    release_order_data = { vessel: {
        
        release_order_number:{
        'destination':destination,
        sales_order_item: {
        "batch": batch,
        "ocean_bill_of_lading": ocean_bill_of_lading,
        "wrap": wrap,
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
    }
                         

    # Convert the dictionary to JSON format
    json_data = json.dumps(release_order_data)
    return json_data

def edit_release_order_data(file,vessel,release_order_number,destination,sales_order_item,batch,ocean_bill_of_lading,wrap,dryness,unitized,quantity,tonnage,transport_type,carrier_code):
       
    # Edit the loaded current dictionary.
    file[vessel][release_order_number]["destination"]= destination
    if sales_order_item not in file[vessel][release_order_number]:
        file[vessel][release_order_number][sales_order_item]={}
    file[vessel][release_order_number][sales_order_item]["batch"]= batch
    file[vessel][release_order_number][sales_order_item]["ocean_bill_of_lading"]= ocean_bill_of_lading
    file[vessel][release_order_number][sales_order_item]["wrap"]= wrap
    file[vessel][release_order_number][sales_order_item]["dryness"]= dryness
    file[vessel][release_order_number][sales_order_item]["transport_type"]= transport_type
    file[vessel][release_order_number][sales_order_item]["carrier_code"]= carrier_code
    file[vessel][release_order_number][sales_order_item]["unitized"]= unitized
    file[vessel][release_order_number][sales_order_item]["quantity"]= quantity
    file[vessel][release_order_number][sales_order_item]["tonnage"]= tonnage
    file[vessel][release_order_number][sales_order_item]["shipped"]= 0
    file[vessel][release_order_number][sales_order_item]["remaining"]= quantity
    
    
       

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
    line2="2DTD:"+release_order_number+" "*(10-len(release_order_number))+"000"+sales_order_item+a+tsn+tt+vehicle_id+" "*(20-len(vehicle_id))+str(quantity*2000)+" "*(16-len(str(quantity*2000)))+"USD"+" "*36+carrier_code+" "*(10-len(carrier_code))+terminal_bill_of_lading+" "*(50-len(terminal_bill_of_lading))+c
               
    loadls=[]
    if double_load:
        for i in first_textsplit:
            loadls.append("2DEV:"+current_release_order+" "*(10-len(current_release_order))+"000"+current_sales_order+a+tsn+i[:-3]+" "*(10-len(i[:-3]))+"0"*16+str(2000))
        for k in second_textsplit:
            loadls.append("2DEV:"+next_release_order+" "*(10-len(next_release_order))+"000"+next_sales_order+a+tsn+k[:-3]+" "*(10-len(k[:-3]))+"0"*16+str(2000))
    else:
        for k in loads:
            loadls.append("2DEV:"+release_order_number+" "*(10-len(release_order_number))+"000"+sales_order_item+a+tsn+k[:-3]+" "*(10-len(k[:-3]))+"0"*16+str(2000))
        
    if double_load:
        number_of_lines=len(first_textsplit)+len(second_textsplit)+4
    else:
        number_of_lines=len(loads)+3
    end_initial="0"*(4-len(str(number_of_lines)))
    end=f"9TRL:{end_initial}{number_of_lines}"
    Inventory=gcp_csv_to_df("olym_suzano", "Inventory.csv")
    for i in loads:
        #st.write(i)
        try:
              
            Inventory.loc[Inventory["Lot"]==i,"Location"]="ON TRUCK"
            Inventory.loc[Inventory["Lot"]==i,"Warehouse_Out"]=datetime.datetime.combine(file_date,file_time)
            Inventory.loc[Inventory["Lot"]==i,"Vehicle_Id"]=str(vehicle_id)
            Inventory.loc[Inventory["Lot"]==i,"Release_Order_Number"]=str(release_order_number)
            Inventory.loc[Inventory["Lot"]==i,"Carrier_Code"]=str(carrier_code)
            Inventory.loc[Inventory["Lot"]==i,"Terminal Bill Of Lading"]=str(terminal_bill_of_lading)
        except:
            st.write("Check Unit Number,Unit Not In Inventory")
        #st.write(vehicle_id)

        temp=Inventory.to_csv("temp.csv")
        upload_cs_file("olym_suzano", 'temp.csv',"Inventory.csv") 
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
def generate_bill_of_lading(vessel,release_order,sales_order,carrier_id,vehicle,quantity):
    data=gcp_download("olym_suzano",rf"terminal_bill_of_ladings.json")
    bill_of_ladings=json.loads(data)
    list_of_ladings=[]
    try:
        for key in bill_of_ladings:
            list_of_ladings.append(int(key))
        bill_of_lading_number=max(list_of_ladings)+1
    except:
        bill_of_lading_number=115240
    return bill_of_lading_number,bill_of_ladings

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

name, authentication_status, username = authenticator.login('PORT OF OLYMPIA TOS LOGIN', 'main')
if authentication_status:
    authenticator.logout('Logout', 'main')
    if username == 'ayilmaz' or username=='gatehouse':
        st.write(f'Welcome *{name}*')
        select=st.sidebar.radio("SELECT FUNCTION",
            ('ADMIN', 'LOADOUT', 'INVENTORY'))
        
            #tab1,tab2,tab3,tab4= st.tabs(["UPLOAD SHIPMENT FILE","ENTER LOADOUT DATA","INVENTORY","CAPTURE"])
            
        
            
        if select=="ADMIN" :
            admin_tab1,admin_tab2,admin_tab3,admin_tab4,admin_tab5=st.tabs(["RELEASE ORDERS","BILL OF LADINGS","EDI'S","VESSEL SHIPMENT FILES","MILL SHIPMENTS"])
            with admin_tab2:
                bill_data=gcp_download("olym_suzano",rf"terminal_bill_of_ladings.json")
                admin_bill_of_ladings=json.loads(bill_data)
                st.dataframe(pd.DataFrame.from_dict(admin_bill_of_ladings).T[1:])
            with admin_tab3:
                edi_files=list_files_in_subfolder("olym_suzano", rf"EDIS/KIRKENES-2304/")
                requested_edi_file=st.selectbox("SELECT EDI",edi_files[1:])
                try:
                    requested_edi=gcp_download("olym_suzano", rf"EDIS/KIRKENES-2304/{requested_edi_file}")
                    st.text_area("EDI",requested_edi,height=400)
                except:
                    st.write("NO EDI FILES IN DIRECTORY")
                                                                                 
            with admin_tab5:
                mill_shipments=gcp_download("olym_suzano",rf"mill_shipments.json")
                mill_shipments=json.loads(mill_shipments)
                mill_df=pd.DataFrame.from_dict(mill_shipments).T
                mill_df["Terminal Code"]=mill_df["Terminal Code"].astype(str)
                mill_df["New Product"]=mill_df["New Product"].astype(str)
                st.table(mill_df)
            with admin_tab4:
                st.markdown("SHIPMENT FILES")
                shipment_tab1,shipment_tab2=st.tabs(["UPLOAD/PROCESS SHIPMENT FILE","SHIPMENT FILE DATABASE"])
                with shipment_tab1:
                    
                    uploaded_file = st.file_uploader("Choose a file")
                    if uploaded_file is not None:
                        # To read file as bytes:
                        bytes_data = uploaded_file.getvalue()
                        #st.write(bytes_data)
                    
                        # To convert to a string based IO:
                        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                        #st.write(stringio)
                    
                        # To read file as string:
                        string_data = stringio.read()
                        #st.write(string_data)
                    
                        # Can be used wherever a "file-like" object is accepted:
                        temp = pd.read_csv(uploaded_file,header=None)
                        temp=temp[1:-1]
                        gemi=temp[5].unique()[0]
                        voyage=int(temp[6].unique()[0])
                        df=pd.DataFrame(list(zip([i[5:] for i in temp[0]],[str(i)[13:15] for i in temp[7]],
                                  [str(i)[20:28] for i in temp[7]])),columns=["Lot","Lot Qty","Batch"])
                        df["Lot Qty"]=[int(int(i)/2) for i in df["Lot Qty"]]
                        df["Wrap"]=[i[:3] for i in temp[1]]
                        df["Vessel"]=[i[-12:] for i in temp[7]]
                        df["DryWeight"]=[int(i) for i in temp[8]]
                        df["ADMT"]=[int(i)/0.9/100000 for i in temp[8]]
                        new_list=[]
                        lotq=[]
                        batch=[]
                        wrap=[]
                        vessel=[]
                        DryWeight=[]
                        ADMT=[]
                        for i in df.index:
                            #print(df.loc[i,"Lot"])
                            for j in range(1,df.loc[i,"Lot Qty"]+1):
                                #print(f"00{i}")
                                if j<10:
                                    new_list.append(f"{df.loc[i,'Lot']}00{j}")
                                else:
                                    new_list.append(f"{df.loc[i,'Lot']}0{j}")
                                lotq.append(df.loc[i,"Lot Qty"])
                                batch.append(str(df.loc[i,"Batch"]))
                                wrap.append(df.loc[i,"Wrap"])
                                vessel.append(df.loc[i,"Vessel"])
                                DryWeight.append(df.loc[i,"DryWeight"])
                                ADMT.append(df.loc[i,"ADMT"])
                        new_df=pd.DataFrame(list(zip(new_list,lotq,batch,wrap,vessel,DryWeight,ADMT)),columns=df.columns.to_list())
                        new_df["Location"]="OLYM"
                        new_df["Warehouse_In"]="8/24/2023"
                        new_df["Warehouse_Out"]=""
                        new_df["Vehicle_Id"]=""
                        new_df["Release_Order_Number"]=""
                        new_df["Carrier_Code"]=""
                        new_df["BL"]=""
                        bls=new_df["Batch"].value_counts()
                        wraps=[new_df[new_df["Batch"]==k]["Wrap"].unique()[0] for k in bls.keys()]
                        wrap_dict={"ISU":"Unwrapped","ISP":"Wrapped"}
                        col1, col2= st.columns([2,2])
                        with col1:
                            st.markdown(f"**VESSEL = {gemi} - VOYAGE = {voyage}**")
                            st.markdown(f"**TOTAL UNITS = {len(new_df)}**")
                        
                       
                            for i in range(len(bls)):
                                st.markdown(f"**{bls[i]} units of Bill of Lading {bls.keys()[i]} - -{wrap_dict[wraps[i]]}-{wraps[i]}**")
                        with col2:
                            if st.button("RECORD PARSED SHIPMENT TO DATABASE"):
                                #st.write(list_cs_files("olym_suzano"))
                                temp=new_df.to_csv("temp.csv")
                                upload_cs_file("olym_suzano", 'temp.csv',rf"shipping_files/{gemi}-{voyage}-shipping_file.csv") 
                                st.write(f"Uploaded {gemi}-{voyage}-shipping_file.csv to database")
                        st.dataframe(new_df)
                    with shipment_tab2:
                        folder_name = "olym_suzano/shipping_files"  # Replace this with the folder path you want to read
                        files_in_folder = list_files_in_folder("olym_suzano", "shipping_files")
                        requested_file=st.selectbox("SHIPPING FILES IN DATABASE",files_in_folder[1:])
                        if st.button("LOAD SHIPPING FILE"):
                            requested_shipping_file=gcp_csv_to_df("olym_suzano", requested_file)
                            filtered_df=requested_shipping_file[["Lot","Lot Qty","Batch","Wrap","Ocean B/L","DryWeight","ADMT","Location",
                                                                                      "Warehouse_In","Warehouse_Out","Vehicle_Id","Release_Order_Number","Carrier_Code"]]
                            #st.data_editor(filtered_df, use_container_width=True)
                            st.data_editor(filtered_df)
                          
            with admin_tab1:
                
                try:
                    release_order_database=gcp_download("olym_suzano",rf"release_orders/RELEASE_ORDERS.json")
                    release_order_database=json.loads(release_order_database)
                except:
                    release_order_database={}
                
                #st.write(f'CURRENT RELEASE ORDERS : {list_files_in_folder("olym_suzano", "release_orders")[1:]}')
                release_order_tab1,release_order_tab2=st.tabs(["CREATE RELEASE ORDER","RELEASE ORDER DATABASE"])
                with release_order_tab1:
                    vessel=st.selectbox("SELECT VESSEL",["KIRKENES-2304"])
                    edit=st.checkbox("CHECK TO ADD TO EXISTING RELEASE ORDER")
                    batch_mapping=gcp_download("olym_suzano",rf"batch_mapping.json")
                    batch_mapping=json.loads(batch_mapping)
                    if edit:
                        #release_order_number=st.selectbox("SELECT RELEASE ORDER",(list_files_in_folder("olym_suzano", "release_orders/{vessel}")))
                        release_order_number=st.selectbox("SELECT RELEASE ORDER",([i.replace(".json","") for i in list_files_in_subfolder("olym_suzano", rf"release_orders/KIRKENES-2304/")]))
                    else:
                        
                        release_order_number=st.text_input("Release Order Number")
                        
                    destination_list=list(set([f"{i}-{j}" for i,j in zip(mill_df["Group"].tolist(),mill_df["Final Destination"].tolist())]))
                    #st.write(destination_list)
                    destination=st.selectbox("SELECT DESTINATION",destination_list)
                    sales_order_item=st.text_input("Sales Order Item")
                    ocean_bill_of_lading=st.selectbox("Ocean Bill Of Lading",batch_mapping.keys())
                    wrap=st.text_input("Wrap",batch_mapping[ocean_bill_of_lading]["wrap"],disabled=True)
                    batch=st.text_input("Batch No",batch_mapping[ocean_bill_of_lading]["batch"],disabled=True)
                    dryness=st.text_input("Dryness",batch_mapping[ocean_bill_of_lading]["dryness"],disabled=True)
                    admt=st.text_input("ADMT PER UNIT",round(int(batch_mapping[ocean_bill_of_lading]["dryness"])/90,6),disabled=True)
                    unitized=st.selectbox("UNITIZED/DE-UNITIZED",["UNITIZED","DE-UNITIZED"],disabled=False)
                    quantity=st.number_input("Quantity of Units", min_value=1, max_value=800, value=1, step=1,  key=None, help=None, on_change=None, disabled=False, label_visibility="visible")
                    tonnage=2*quantity
                    #queue=st.number_input("Place in Queue", min_value=1, max_value=20, value=1, step=1,  key=None, help=None, on_change=None, disabled=False, label_visibility="visible")
                    transport_type=st.radio("Select Transport Type",("TRUCK","RAIL"))
                    carrier_code=st.text_input("Carrier Code")            
                    
        
                    create_release_order=st.button("SUBMIT")
                    if create_release_order:
                        
                        if edit: 
                            data=gcp_download("olym_suzano",rf"release_orders/{vessel}/{release_order_number}.json")
                            to_edit=json.loads(data)
                            temp=edit_release_order_data(to_edit,vessel,release_order_number,destination,sales_order_item,batch,ocean_bill_of_lading,wrap,dryness,unitized,quantity,tonnage,transport_type,carrier_code)
                            st.write(f"ADDED sales order item {sales_order_item} to release order {release_order_number}!")
                        else:
                            
                            temp=store_release_order_data(vessel,release_order_number,destination,sales_order_item,batch,ocean_bill_of_lading,wrap,dryness,unitized,quantity,tonnage,transport_type,carrier_code)
                            #st.write(temp)
                        try:
                            junk=gcp_download("olym_suzano",rf"release_orders/{vessel}/junk_release.json")
                        except:
                            junk=gcp_download("olym_suzano",rf"junk_release.json")
                        junk=json.loads(junk)
                        try:
                            del junk[release_order_number]
                            jason_data=json.dumps(junk)
                            storage_client = storage.Client()
                            bucket = storage_client.bucket("olym_suzano")
                            blob = bucket.blob(rf"release_orders/{vessel}/junk_release.json")
                            blob.upload_from_string(jason_data)
                        except:
                            pass
                        

                        storage_client = storage.Client()
                        bucket = storage_client.bucket("olym_suzano")
                        blob = bucket.blob(rf"release_orders/{vessel}/{release_order_number}.json")
                        blob.upload_from_string(temp)

                        
                        try:
                            release_order_database[release_order_number][sales_order_item]=temp[vessel][release_order_number]
                            storage_client = storage.Client()
                            bucket = storage_client.bucket("olym_suzano")
                            blob = bucket.blob(rf"release_orders/RELEASE_ORDERS.json")
                            blob.upload_from_string(release_order_database)
                        except:
                            pass
                            #release_order_database[release_order_number]={}
                            #release_order_database[release_order_number][sales_order_item]=temp[vessel][release_order_number]
                        
                        st.write(f"Recorded Release Order - {release_order_number} for Item No: {sales_order_item}")
                        
                with release_order_tab2:
                    
                    vessel=st.selectbox("SELECT VESSEL",["KIRKENES-2304"],key="other")
                    rls_tab1,rls_tab2=st.tabs(["ACTIVE RELEASE ORDERS","COMPLETED RELEASE ORDERS"])
                    completed_release_orders=[]
                    
                    with rls_tab1:
                        
                                    
                        files_in_folder = [i.replace(".json","") for i in list_files_in_subfolder("olym_suzano", rf"release_orders/KIRKENES-2304/")]
                        requested_file=st.selectbox("ACTIVE RELEASE ORDERS",files_in_folder)
                        
                        nofile=0
                        try:
                            data=gcp_download("olym_suzano",rf"release_orders/{vessel}/{requested_file}.json")
                            release_order_json = json.loads(data)
                            
                            target=release_order_json[vessel][requested_file]
                            destination=target['destination']
                            if len(target.keys())==0:
                                nofile=1
                           
                            number_of_sales_orders=len(target)    ##### WRONG CAUSE THERE IS NOW DESTINATION KEYS
                            rel_col1,rel_col2,rel_col3,rel_col4=st.columns([2,2,2,2])
                        except:
                            nofile=1
                        
                        #### DISPATCHED CLEANUP  #######
                        
                        try:
                            dispatched=gcp_download("olym_suzano",rf"dispatched.json")
                            dispatched=json.loads(dispatched)
                            #st.write(dispatched)
                        except:
                            pass
                        to_delete=[]            
                        try:
                            for i in dispatched.keys():
                                if not dispatched[i].keys():
                                    del dispatched[i]
                                
                            for k in to_delete:
                                dispatched.pop(k)
                                #st.write("deleted k")
                           
                            json_data = json.dumps(dispatched)
                            storage_client = storage.Client()
                            bucket = storage_client.bucket("olym_suzano")
                            blob = bucket.blob(rf"dispatched.json")
                            blob.upload_from_string(json_data)
                        except:
                            pass
                        
                            
                        
                        
                        
                        ###CLEAN DISPATCH
        
                        
                                              
                        if nofile!=1 :         
                                        
                            targets=[i for i in target if i !="destination"] ####doing this cause we set jason path {downloadedfile[vessel][releaseorder] as target. i have to use one of the keys (release order number) that is in target list
                            sales_orders_completed=[k for k in targets if target[k]['remaining']<=0]
                            
                            with rel_col1:
                                
                                st.markdown(f"**:blue[Release Order Number] : {requested_file}**")
                                if targets[0] in sales_orders_completed:
                                    st.markdown(f"**:orange[Sales Order Item : {targets[0]} - COMPLETED]**")
                                    target0_done=True
                                    
                                else:
                                    st.markdown(f"**:blue[Sales Order Item] : {targets[0]}**")
                                st.markdown(f"**:blue[Destination : {target['destination']}]**")
                                st.write(f"        Total Quantity-Tonnage : {target[targets[0]]['quantity']} Units - {target[targets[0]]['tonnage']} Metric Tons")
                                st.write(f"        Ocean Bill Of Lading : {target[targets[0]]['ocean_bill_of_lading']}")
                                st.write(f"        Batch : {target[targets[0]]['batch']} WIRES : {target[targets[0]]['unitized']}")
                                st.write(f"        Units Shipped : {target[targets[0]]['shipped']} Units - {2*target[targets[0]]['shipped']} Metric Tons")
                                if 0<target[targets[0]]['remaining']<=10:
                                    st.markdown(f"**:red[Units Remaining : {target[targets[0]]['remaining']} Units - {2*target[targets[0]]['remaining']} Metric Tons]**")
                                elif target[targets[0]]['remaining']<=0:
                                    st.markdown(f":orange[Units Remaining : {target[targets[0]]['remaining']} Units - {2*target[targets[0]]['remaining']} Metric Tons]")                                                                        
                                else:
                                    st.write(f"       Units Remaining : {target[targets[0]]['remaining']} Units - {2*target[targets[0]]['remaining']} Metric Tons")
                            with rel_col2:
                                try:
                                
                                    st.markdown(f"**:blue[Release Order Number] : {requested_file}**")
                                    if targets[1] in sales_orders_completed:
                                        st.markdown(f"**:orange[Sales Order Item : {targets[1]} - COMPLETED]**")                                    
                                    else:
                                        st.markdown(f"**:blue[Sales Order Item] : {targets[1]}**")
                                    st.markdown(f"**:blue[Destination : {target['destination']}]**")
                                    st.write(f"        Total Quantity-Tonnage : {target[targets[1]]['quantity']} Units - {target[targets[1]]['tonnage']} Metric Tons")                        
                                    st.write(f"        Ocean Bill Of Lading : {target[targets[1]]['ocean_bill_of_lading']}")
                                    st.write(f"        Batch : {target[targets[1]]['batch']} WIRES : {target[targets[1]]['unitized']}")
                                    st.write(f"        Units Shipped : {target[targets[1]]['shipped']} Units - {2*target[targets[1]]['shipped']} Metric Tons")
                                    if 0<target[targets[1]]['remaining']<=10:
                                        st.markdown(f"**:red[Units Remaining : {target[targets[1]]['remaining']} Units - {2*target[targets[1]]['remaining']} Metric Tons]**")
                                    elif target[targets[1]]['remaining']<=0:
                                        st.markdown(f":orange[Units Remaining : {target[targets[1]]['remaining']} Units - {2*target[targets[1]]['remaining']} Metric Tons]")
                                    else:
                                        st.write(f"       Units Remaining : {target[targets[1]]['remaining']} Units - {2*target[targets[1]]['remaining']} Metric Tons")
                                        
                                except:
                                    pass
                
                            with rel_col3:
                                try:
                                
                                    st.markdown(f"**:blue[Release Order Number] : {requested_file}**")
                                    if targets[2] in sales_orders_completed:
                                        st.markdown(f"**:orange[Sales Order Item : {targets[2]} - COMPLETED]**")
                                    else:
                                        st.markdown(f"**:blue[Sales Order Item] : {targets[2]}**")
                                    st.markdown(f"**:blue[Destination : {target['destination']}]**")
                                    st.write(f"        Total Quantity-Tonnage : {target[targets[2]]['quantity']} Units - {target[targets[2]]['tonnage']} Metric Tons")
                                    st.write(f"        Ocean Bill Of Lading : {target[targets[2]]['ocean_bill_of_lading']}")
                                    st.write(f"        Batch : {target[targets[2]]['batch']} WIRES : {target[targets[2]]['unitized']}")
                                    st.write(f"        Units Shipped : {target[targets[2]]['shipped']} Units - {2*target[targets[2]]['shipped']} Metric Tons")
                                    if 0<target[targets[2]]['remaining']<=10:
                                        st.markdown(f"**:red[Units Remaining : {target[targets[2]]['remaining']} Units - {2*target[targets[2]]['remaining']} Metric Tons]**")
                                    elif target[targets[2]]['remaining']<=0:
                                        st.markdown(f":orange[Units Remaining : {target[targets[2]]['remaining']} Units - {2*target[targets[2]]['remaining']} Metric Tons]")
                                    else:
                                        st.write(f"       Units Remaining : {target[targets[2]]['remaining']} Units - {2*target[targets[2]]['remaining']} Metric Tons")
                                    
                                    
                                except:
                                    pass
            
                            with rel_col4:
                                try:
                                
                                    st.markdown(f"**:blue[Release Order Number] : {requested_file}**")
                                    if targets[3] in sales_orders_completed:
                                        st.markdown(f"**:orange[Sales Order Item : {targets[3]} - COMPLETED]**")
                                    else:
                                        st.markdown(f"**:blue[Sales Order Item] : {targets[3]}**")
                                    st.markdown(f"**:blue[Destination : {target['destination']}]**")
                                    st.write(f"        Total Quantity-Tonnage : {target[targets[3]]['quantity']} Units - {target[targets[3]]['tonnage']} Metric Tons")
                                    st.write(f"        Ocean Bill Of Lading : {target[targets[3]]['ocean_bill_of_lading']}")
                                    st.write(f"        Batch : {target[targets[3]]['batch']} WIRES : {target[targets[3]]['unitized']}")
                                    st.write(f"        Units Shipped : {target[targets[3]]['shipped']} Units - {2*target[targets[3]]['shipped']} Metric Tons")
                                    if 0<target[targets[3]]['remaining']<=10:
                                        st.markdown(f"**:red[Units Remaining : {target[targets[3]]['remaining']} Units - {2*target[targets[3]]['remaining']} Metric Tons]**")
                                    elif target[targets[3]]['remaining']<=0:
                                        st.markdown(f":orange[Units Remaining : {target[targets[3]]['remaining']} Units - {2*target[targets[3]]['remaining']} Metric Tons]")
                                    else:
                                        st.write(f"       Units Remaining : {target[targets[3]]['remaining']} Units - {2*target[targets[3]]['remaining']} Metric Tons")
                                    
                                    
                                except:
                                    pass
                            
                            # dispatched={"vessel":vessel,"date":datetime.datetime.strftime(datetime.datetime.today()-datetime.timedelta(hours=7),"%b-%d-%Y"),
                                     #               "time":datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=7),"%H:%M:%S"),
                                       #                 "release_order":requested_file,"sales_order":hangisi,"ocean_bill_of_lading":ocean_bill_of_lading,"batch":batch}
                            
                            hangisi=st.selectbox("**:green[SELECT SALES ORDER ITEM TO DISPATCH]**",([i for i in target if i not in sales_orders_completed and i!= "destination"]))
                            dol1,dol2,dol3,dol4=st.columns([2,2,2,2])
                            with dol1:
                               
                                if st.button("DISPATCH TO WAREHOUSE",key="lala"):
                                   
                                    
                                    
                                    dispatch=dispatched.copy()
                                    try:
                                        last=list(dispatch[requested_file].keys())[-1]
                                        #dispatch[requested_file]={}
                                        dispatch[requested_file][hangisi]={"vessel":vessel,"date":datetime.datetime.strftime(datetime.datetime.today()-datetime.timedelta(hours=7),"%b-%d-%Y"),
                                                    "time":datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=7),"%H:%M:%S"),
                                                     "release_order":requested_file,"sales_order":hangisi,"destination":destination,"ocean_bill_of_lading":target[hangisi]["ocean_bill_of_lading"],"batch":target[hangisi]["batch"]}
                                    except:
                                        dispatch[requested_file]={}
                                        dispatch[requested_file][hangisi]={"vessel":vessel,"date":datetime.datetime.strftime(datetime.datetime.today()-datetime.timedelta(hours=7),"%b-%d-%Y"),
                                                    "time":datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=7),"%H:%M:%S"),
                                                     "release_order":requested_file,"sales_order":hangisi,"destination":destination,"ocean_bill_of_lading":target[hangisi]["ocean_bill_of_lading"],"batch":target[hangisi]["batch"]}
            
                                    
                                    json_data = json.dumps(dispatch)
                                    storage_client = storage.Client()
                                    bucket = storage_client.bucket("olym_suzano")
                                    blob = bucket.blob(rf"dispatched.json")
                                    blob.upload_from_string(json_data)
                                    st.markdown(f"**DISPATCHED Release Order Number {requested_file} Item No : {hangisi} to Warehouse**")
                            with dol4:
                                
                                if st.button("DELETE SALES ORDER ITEM",key="lalag"):
                                    
                                    data_d=gcp_download("olym_suzano",rf"release_orders/{vessel}/{requested_file}.json")
                                    to_edit_d=json.loads(data_d)
                                    to_edit_d[vessel][requested_file].pop(hangisi)
                                    #st.write(to_edit_d)
                                    
                                    json_data = json.dumps(to_edit_d)
                                    storage_client = storage.Client()
                                    bucket = storage_client.bucket("olym_suzano")
                                    blob = bucket.blob(rf"release_orders/{vessel}/{requested_file}.json")
                                    blob.upload_from_string(json_data)
                                if st.button("DELETE RELEASE ORDER ITEM!",key="laladg"):
                                    #junk=gcp_download("olym_suzano",rf"release_orders/{vessel}/junk_release.json")
                                    #junk=json.loads(junk)
                                    pass
                                    #st.write(to_edit_d)
                                    #junk[requested_file]=datetime.datetime.strftime(datetime.datetime.today(),"%Y-%m-%d")
                                   #json_data = json.dumps(junk)
                                   # storage_client = storage.Client()
                                   # bucket = storage_client.bucket("olym_suzano")
                                   # blob = bucket.blob(rf"release_orders/{vessel}/junk_release.json")
                                   # blob.upload_from_string(json_data)
                                           
                            with dol2:  
                                if st.button("CLEAR DISPATCH QUEUE!"):
                                    dispatch={}
                                    json_data = json.dumps(dispatch)
                                    storage_client = storage.Client()
                                    bucket = storage_client.bucket("olym_suzano")
                                    blob = bucket.blob(rf"dispatched.json")
                                    blob.upload_from_string(json_data)
                                    st.markdown(f"**CLEARED ALL DISPATCHES**")   
                            with dol3:
                                dispatch=gcp_download("olym_suzano",rf"dispatched.json")
                                dispatch=json.loads(dispatch)
                                try:
                                    item=st.selectbox("CHOOSE ITEM",dispatch.keys())
                                    if st.button("CLEAR DISPATCH ITEM"):                                       
                                        del dispatch[item]
                                        json_data = json.dumps(dispatch)
                                        storage_client = storage.Client()
                                        bucket = storage_client.bucket("olym_suzano")
                                        blob = bucket.blob(rf"dispatched.json")
                                        blob.upload_from_string(json_data)
                                        st.markdown(f"**CLEARED DISPATCH ITEM {item}**")   
                                except:
                                    pass
                            st.markdown("**CURRENT DISPATCH QUEUE**")
                            try:
                                dispatch=gcp_download("olym_suzano",rf"dispatched.json")
                                dispatch=json.loads(dispatch)
                                try:
                                    for dispatched_release in dispatch.keys():
                                        #st.write(dispatched_release)
                                        for sales in dispatch[dispatched_release].keys():
                                            #st.write(sales)
                                            st.markdown(f'**Release Order = {dispatched_release}, Sales Item : {sales}, Destination : {dispatch[dispatched_release][sales]["destination"]} .**')
                                except:
                                    pass
                            except:
                                st.write("NO DISPATCH ITEMS")
                        
                        else:
                            st.write("NO RELEASE ORDERS IN DATABASE")
                    with rls_tab2:
                        pass
                        #sales_orders_completed=[k for k in targets if target[k]['remaining']<=0]
                        
                                
        
                        
        
        ##########  LOAD OUT  ##############
        
        
        
        if select=="LOADOUT" :
        
            
            bill_mapping=gcp_download("olym_suzano","bill_mapping.json")
            bill_mapping=json.loads(bill_mapping)
            no_dispatch=0
            number=None
            if number not in st.session_state:
                st.session_state.number=number
            try:
                dispatched=gcp_download("olym_suzano","dispatched.json")
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
                            menu_destinations[rel_ord]=dispatched[rel_ord][sales]["destination"]
                            break
                        except:
                            pass
                liste=[f"{i} to {menu_destinations[i]}" for i in dispatched.keys()]
                work_order_=st.selectbox("**SELECT RELEASE ORDER/SALES ORDER TO WORK**",liste)
                work_order=work_order_.split(" ")[0]
                order=["001","002","003","004","005","006"]
                
                for i in order:                   ##############HERE we check all the sales orders in dispatched[releaseordernumber] dictionary. it breaks after it finds the first sales order
                    if i in dispatched[work_order].keys():
                        current_release_order=work_order
                        current_sales_order=i
                        vessel=dispatched[work_order][i]["vessel"]
                        destination=dispatched[work_order][i]['destination']
                        break
                    else:
                        pass
                try:
                    next_release_order=dispatched['002']['release_order']    #############################  CHECK HERE ######################## FOR MIXED LOAD
                    next_sales_order=dispatched['002']['sales_order']
                    
                except:
                    
                    pass
                info=gcp_download("olym_suzano",rf"release_orders/{vessel}/{work_order}.json")
                info=json.loads(info)
                
                
                if st.checkbox("CLICK TO LOAD MIXED SKU"):
                    try:
                        next_item=gcp_download("olym_suzano",rf"release_orders/{dispatched['2']['vessel']}/{dispatched['2']['release_order']}.json")
                        double_load=True
                    except:
                        st.markdown("**:red[ONLY ONE ITEM IN QUEUE ! ASK NEXT ITEM TO BE DISPATCHED!]**")
                    
               
                    
                load_col1,load_col2,load_col3=st.columns([4,4,2])
                with load_col1:
                    st.markdown(rf'**:blue[CURRENTLY WORKING] : Release Order-{current_release_order}**')
                    st.markdown(rf'**Destination : {destination} .**')
                    st.markdown(rf'**Sales Order Item-{current_sales_order}**')
                    wrap_dict={"ISU":"UNWRAPPED","ISP":"WRAPPED"}
                    wrap=info[vessel][current_release_order][current_sales_order]["wrap"]
                    st.markdown(f'**Ocean Bill Of Lading : {info[vessel][current_release_order][current_sales_order]["ocean_bill_of_lading"]} - {wrap_dict[wrap]}**')
                    unitized=info[vessel][current_release_order][current_sales_order]["unitized"]
                    st.markdown(rf'**{info[vessel][current_release_order][current_sales_order]["unitized"]}**')
                    st.markdown(rf'**Total Quantity : {info[vessel][current_release_order][current_sales_order]["quantity"]}**')
                    st.markdown(rf'**Shipped : {info[vessel][current_release_order][current_sales_order]["shipped"]}**')
                    remaining=info[vessel][current_release_order][current_sales_order]["remaining"]                #######      DEFINED "REMAINING" HERE FOR CHECKS
                    if remaining<10:
                        st.markdown(rf'**:red[CAUTION : Remaining : {info[vessel][current_release_order][current_sales_order]["remaining"]}]**')
                    st.markdown(rf'**Remaining : {info[vessel][current_release_order][current_sales_order]["remaining"]}**')
                    
                with load_col2:
                    if double_load:
                        
                        try:
                            st.markdown(rf'**NEXT ITEM : Release Order-{next_release_order}**')
                            st.markdown(rf'**Sales Order Item-{next_sales_order}**')
                            st.markdown(f'**Ocean Bill Of Lading : {info[vessel][next_release_order][next_sales_order]["ocean_bill_of_lading"]}**')
                            st.markdown(rf'**Total Quantity : {info[vessel][next_release_order][next_sales_order]["quantity"]}**')
                        except:
                            pass
                      
                col1, col2,col3,col4,col5= st.columns([2,2,2,2,2])
                
              
               
                if info[vessel][current_release_order][current_sales_order]["transport_type"]=="TRUCK":
                    medium="TRUCK"
                else:
                    medium="RAIL"
                
                with col1:
                
                    terminal_code=st.text_input("Terminal Code","OLYM",disabled=True)
                    file_date=st.date_input("File Date",datetime.datetime.today()-datetime.timedelta(hours=7),key="file_dates",disabled=True)
                    if file_date not in st.session_state:
                        st.session_state.file_date=file_date
                    file_time = st.time_input('FileTime', datetime.datetime.now()-datetime.timedelta(hours=7),step=60,disabled=False)
                    delivery_date=st.date_input("Delivery Date",datetime.datetime.today()-datetime.timedelta(hours=7),key="delivery_date",disabled=True)
                    eta_date=st.date_input("ETA Date (For Trucks same as delivery date)",delivery_date,key="eta_date",disabled=True)
                    
                with col2:
                    if double_load:
                        release_order_number=st.text_input("Release Order Number",current_release_order,disabled=True,help="Release Order Number without the Item no")
                        sales_order_item=st.text_input("Sales Order Item (Material Code)",current_sales_order,disabled=True)
                        ocean_bill_of_lading=st.text_input("Ocean Bill Of Lading",info[vessel][current_release_order][current_sales_order]["ocean_bill_of_lading"],disabled=True)
                        current_ocean_bill_of_lading=ocean_bill_of_lading
                        next_ocean_bill_of_lading=info[vessel][next_release_order][next_sales_order]["ocean_bill_of_lading"]
                        batch=st.text_input("Batch",info[vessel][current_release_order][current_sales_order]["batch"],disabled=True)
                        
                        #terminal_bill_of_lading=st.text_input("Terminal Bill of Lading",disabled=False)
                        pass
                    else:
                        release_order_number=st.text_input("Release Order Number",current_release_order,disabled=True,help="Release Order Number without the Item no")
                        sales_order_item=st.text_input("Sales Order Item (Material Code)",current_sales_order,disabled=True)
                        ocean_bill_of_lading=st.text_input("Ocean Bill Of Lading",info[vessel][current_release_order][current_sales_order]["ocean_bill_of_lading"],disabled=True)
                        
                        batch=st.text_input("Batch",info[vessel][current_release_order][current_sales_order]["batch"],disabled=True)
                        #terminal_bill_of_lading=st.text_input("Terminal Bill of Lading",disabled=False)
                   
                        
                    
                with col3: 
                    carrier_code=st.text_input("Carrier Code",info[vessel][current_release_order][current_sales_order]["carrier_code"],disabled=True)
                    transport_sequential_number=st.selectbox("Transport Sequential",["TRUCK","RAIL"],disabled=True)
                    transport_type=st.selectbox("Transport Type",["TRUCK","RAIL"],disabled=True)
                    vehicle_id=st.text_input("**:blue[Vehicle ID]**")
                    foreman_quantity=st.number_input("**:blue[ENTER Quantity of Units]**", min_value=0, max_value=30, value=0, step=1,key=None, help=None, on_change=None, disabled=False, label_visibility="visible")
                
                    
               
                with col4:
                    updated_quantity=0
                    live_quantity=0
                    if updated_quantity not in st.session_state:
                        st.session_state.updated_quantity=updated_quantity
                    def audit_unit(x):
                            if len(x)==11:
                                #st.write(bill_mapping[x[:-3]]["Batch"])
                                #st.write(Inventory_Audit[Inventory_Audit["Lot"]==x]["Location"].iloc[0])
                                if bill_mapping[x[:-3]]["Ocean_bl"]!=ocean_bill_of_lading and bill_mapping[x[:-3]]["Batch"]!=batch:
                                    st.write(f"**:red[WRONG B/L, DO NOT LOAD UNIT {x}]**")
                                    return False
                                
                                if Inventory_Audit[Inventory_Audit["Lot"]==x]["Location"].iloc[0]!="OLYM":
                                    st.write(":red[THIS BELOW UNIT HAS BEEN SHIPPED]")
                                    return False
                                
                                else:
                                    return True
                    def audit_split(release,sales):
                            if len(x)==11:
                                #st.write(bill_mapping[x[:-3]]["Batch"])
                                
                                if bill_mapping[x[:-3]]["Ocean_bl"]!=info[vessel][release][sales]["ocean_bill_of_lading"] and bill_mapping[x[:-3]]["Batch"]!=info[vessel][release][sales]["batch"]:
                                    st.write("**:red[WRONG B/L, DO NOT LOAD BELOW!]**")
                                    return False
                                if Inventory_Audit[Inventory_Audit["Lot"]==x]["Location"].iloc[0]!="OLYM":
                                    st.write(":red[THIS BELOW UNIT HAS BEEN SHIPPED]")
                                    return False
                                else:
                                    return True
                    
                    flip=False 
                    first_load_input=None
                    second_load_input=None
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
                        
        
        
                    
                        load_input=st.text_area("**LOADS**",height=300)#[:-3]
                        if load_input is not None:
                            textsplit = load_input.splitlines()
                            textsplit=[i for i in textsplit if len(i)>8]
                            updated_quantity=len(textsplit)
                            st.session_state.updated_quantity=updated_quantity
                       
                        
                    quantity=st.number_input("**Scanned Quantity of Units**",st.session_state.updated_quantity, key=None, help=None, on_change=None, disabled=True, label_visibility="visible")
                    st.markdown(f"**{quantity*2} TONS - {round(quantity*2*2204.62,1)} Pounds**")
                    #ADMT=st.text_input("ADMT",round(info[vessel][current_release_order][current_sales_order]["dryness"]/90,4)*updated_quantity,disabled=True)
                    admt=round(float(info[vessel][current_release_order][current_sales_order]["dryness"])/90*updated_quantity*2,4)
                    st.markdown(f"**ADMT= {admt} TONS**")
                    
       
                    
                    
                    
                    
                 
                   
                with col5:
                    Inventory_Audit=gcp_csv_to_df("olym_suzano", "Inventory.csv")
                    #st.write(Inventory_Audit)
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
                    
                    else:
                        
                    
                        faults=[]
                        fault_messaging={}
                        if load_input is not None:
                            textsplit = load_input.splitlines()
                            
                                
                            textsplit=[i for i in textsplit if len(i)>8]
                            #st.write(textsplit)
                            seen=set()
                            for i,x in enumerate(textsplit):
                                
                                if audit_unit(x):
                                    if x in seen:
                                        st.text_input(f"Unit No : {i+1}",x)
                                        faults.append(1)
                                        fault_messaging[i+1]="This unit has been scanned TWICE!"
                                    else:
                                        st.text_input(f"Unit No : {i+1}",x)
                                        faults.append(0)
                                else:
                                    st.text_input(f"Unit No : {i+1}",x)
                                    faults.append(1)
                                seen.add(x)
                        loads=[]
                        for k in textsplit:
                            loads.append(k)
                   
                #st.write(faults)                  
                a=datetime.datetime.strftime(file_date,"%Y%m%d")
                a_=datetime.datetime.strftime(file_date,"%Y-%m-%d")
                b=file_time.strftime("%H%M%S")
                b=(datetime.datetime.now()-datetime.timedelta(hours=7)).strftime("%H%M%S")
                b_=(datetime.datetime.now()-datetime.timedelta(hours=7)).strftime("%H:%M:%S")
                c=datetime.datetime.strftime(eta_date,"%Y%m%d")
                
                
                    
                but_col1,but_col2=st.columns([2,2])
                with but_col1:
                    if st.button('SUBMIT EDI'):
                        def gen_bill_of_lading():
                            data=gcp_download("olym_suzano",rf"terminal_bill_of_ladings.json")
                            bill_of_ladings=json.loads(data)
                            list_of_ladings=[]
                            try:
                                for key in bill_of_ladings:
                                    if int(key) % 2 == 0:
                                        list_of_ladings.append(int(key))
                                bill_of_lading_number=max(list_of_ladings)+2
                            except:
                                bill_of_lading_number=115240
                            return bill_of_lading_number,bill_of_ladings
                        #st.write(bill_of_lading_number)
                        
                        edi_name= f'{a}{b}OLYM.txt'
                        if double_load:
                            bill_of_lading_number,bill_of_ladings=gen_bill_of_lading()
                            bill_of_ladings[str(bill_of_lading_number)]={"vessel":vessel,"release_order":release_order_number,"destination":destination,"sales_order":current_sales_order,
                                                                         "ocean_bill_of_lading":ocean_bill_of_lading,"wrap":wrap,"carrier_id":carrier_code,"vehicle":vehicle_id,
                                                                         "quantity":len(first_textsplit),"issued":f"{a_} {b_}","edi_no":edi_name} 
                            bill_of_ladings[str(bill_of_lading_number+1)]={"vessel":vessel,"release_order":release_order_number,"destination":destination,"sales_order":next_sales_order,
                                                                         "ocean_bill_of_lading":ocean_bill_of_lading,"wrap":wrap,"carrier_id":carrier_code,"vehicle":vehicle_id,
                                                                         "quantity":len(first_textsplit),"issued":f"{a_} {b_}","edi_no":edi_name} 
                        else:
                            bill_of_lading_number,bill_of_ladings=gen_bill_of_lading()
                            bill_of_ladings[str(bill_of_lading_number)]={"vessel":vessel,"release_order":release_order_number,"destination":destination,"sales_order":current_sales_order,
                                                                         "ocean_bill_of_lading":ocean_bill_of_lading,"wrap":wrap,"carrier_id":carrier_code,"vehicle":vehicle_id,
                                                                         "quantity":len(textsplit),"issued":f"{a_} {b_}","edi_no":edi_name} 
                            
                     
                        bill_of_ladings=json.dumps(bill_of_ladings)
                        storage_client = storage.Client()
                        bucket = storage_client.bucket("olym_suzano")
                        blob = bucket.blob(rf"terminal_bill_of_ladings.json")
                        blob.upload_from_string(bill_of_ladings)
                        
                        
                        terminal_bill_of_lading=st.text_input("Terminal Bill of Lading",bill_of_lading_number,disabled=True)
                        
                        proceed=False
                        if double_load:
                            if 1 in first_faults or 1 in second_faults:
                                st.markdown(f"**:red[CAN NOT SUBMIT EDI!!] CHECK BELOW UNTIS**")
                                for i in first_faults:
                                    if i==1:
                                        st.markdown(f"**:red[Check Unit Unit{first_faults.index(i)+1}]**")
                                for i in second_faults:
                                    if i==1:
                                        st.markdown(f"**:red[Check Unit Unit{second_faults.index(i)+1}]**")
                            else:
                                proceed=True
                        else:
                            if 1 in faults:
                                proceed=False
                                for i in faults:
                                    if i==1:
                                        st.markdown(f"**:red[Check Unit {faults.index(i)+1}]**")
                            else:
                                proceed=True
                        if fault_messaging.keys():
                            for i in fault_messaging.keys():
                                error=f"**:red[Unitfault_messaging[i]]**"
                        if remaining<0:
                            proceed=False
                            error="**:red[No more Items to ship on this Sales Order]"
                            st.write(error)
                        if not vehicle_id: 
                            proceed=False
                            error="**:red[Please check Vehicle ID]"
                            st.write(error)
                        if len(terminal_bill_of_lading)<6:
                            proceed=False
                            error="**:red[Please check Terminal Bill Of Lading. It should have 6 digits.]"
                            st.write(error)
                        if quantity!=foreman_quantity:
                            proceed=False
                            error=f"**:red[{quantity} loads on this truck. Please check. You planned for {foreman_quantity} loads!]** "
                            st.write(error)
                        if proceed:
                            
                            process()
                            mill_progress=json.loads(gcp_download("olym_suzano",rf"mill_progress.json"))
                            map={8:"SEP 2023",9:"SEP 2023",10:"OCT 2023",11:"NOV 2023",12:"DEC 2023"}
                            mill_progress[destination][map[file_date.month]]["Shipped"]=mill_progress[destination][map[file_date.month]]["Shipped"]+len(textsplit)*2
                            json_data = json.dumps(mill_progress)
                            storage_client = storage.Client()
                            bucket = storage_client.bucket("olym_suzano")
                            blob = bucket.blob(rf"mill_progress.json")
                            blob.upload_from_string(json_data)       
                            if double_load:
                                info[vessel][current_release_order][current_sales_order]["shipped"]=info[vessel][current_release_order][current_sales_order]["shipped"]+len(first_textsplit)
                                info[vessel][current_release_order][current_sales_order]["remaining"]=info[vessel][current_release_order][current_sales_order]["remaining"]-len(first_textsplit)
                                info[vessel][next_release_order][next_sales_order]["shipped"]=info[vessel][next_release_order][next_sales_order]["shipped"]+len(second_textsplit)
                                info[vessel][next_release_order][next_sales_order]["remaining"]=info[vessel][next_release_order][next_sales_order]["remaining"]-len(second_textsplit)
                            else:
                                info[vessel][current_release_order][current_sales_order]["shipped"]=info[vessel][current_release_order][current_sales_order]["shipped"]+len(loads)
                                info[vessel][current_release_order][current_sales_order]["remaining"]=info[vessel][current_release_order][current_sales_order]["remaining"]-len(loads)
                            if info[vessel][current_release_order][current_sales_order]["remaining"]<=0:
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
                                bucket = storage_client.bucket("olym_suzano")
                                blob = bucket.blob(rf"dispatched.json")
                                blob.upload_from_string(json_data)       
                            
                            json_data = json.dumps(info)
                            storage_client = storage.Client()
                            bucket = storage_client.bucket("olym_suzano")
                            blob = bucket.blob(rf"release_orders/{vessel}/{current_release_order}.json")
                            blob.upload_from_string(json_data)
    
    
    
                            
                            with open('placeholder.txt', 'r') as f:
                                output_text = f.read()
                            st.markdown("**SUCCESS! EDI FOR THIS LOAD HAS BEEN SUBMITTED,THANK YOU**")
                            st.markdown("**EDI TEXT**")
                            st.text_area('', value=output_text, height=600)
                            with open('placeholder.txt', 'r') as f:
                                file_content = f.read()
                            newline="\n"
                            filename = f'{a}{b}OLYM'
                            file_name= f'{a}{b}OLYM.txt'
                            st.write(filename)
                            st.write(current_release_order,current_sales_order,destination,ocean_bill_of_lading,terminal_bill_of_lading,wrap)
                            subject = f'Suzano_EDI_{a}_{release_order_number}'
                            body = f"EDI for Below attached.{newline}Release Order Number : {current_release_order} - Sales Order Number:{current_sales_order}{newline}Destination : {destination}Ocean Bill Of Lading : {ocean_bill_of_lading}{newline}Terminal Bill of Lading: {terminal_bill_of_lading} - Wrap : {wrap} {newline}{len(loads)} {unitized} loads were loaded to vehicle : {vehicle_id} with Carried ID : {carrier_code} {newline}Truck loading completed at {a_} {b_}"
                            st.write(body)           
                            sender = "warehouseoly@gmail.com"
                            #recipients = ["alexandras@portolympia.com","conleyb@portolympia.com", "afsiny@portolympia.com"]
                            recipients = ["afsiny@portolympia.com"]
                            password = "xjvxkmzbpotzeuuv"
                    
                              # Replace with the actual file path
                    
                    
                            with open('temp_file.txt', 'w') as f:
                                f.write(file_content)
                    
                            file_path = 'temp_file.txt'  # Use the path of the temporary file
                    
                            send_email_with_attachment(subject, body, sender, recipients, password, file_path,file_name)
                            upload_cs_file("olym_suzano", 'temp_file.txt',rf"EDIS/{vessel}/{file_name}") 
                            
                        else:   ###cancel bill of lading
                            data=gcp_download("olym_suzano",rf"terminal_bill_of_ladings.json")
                            bill_of_ladings=json.loads(data)
                            del bill_of_ladings[str(bill_of_lading_number)]
                            bill_of_ladings=json.dumps(bill_of_ladings)
                            storage_client = storage.Client()
                            bucket = storage_client.bucket("olym_suzano")
                            blob = bucket.blob(rf"terminal_bill_of_ladings.json")
                            blob.upload_from_string(bill_of_ladings)
                with but_col2:
                    if st.button("**CLEAR ENTRIES**"):
                        pass
                            
        
            
                        
            else:
                st.subheader("**Nothing dispatched!**")
                    
            
                    
                        
        
        
                
                        
        if select=="INVENTORY" :
            Inventory=gcp_csv_to_df("olym_suzano", "Inventory.csv")
           
            mill_info=json.loads(gcp_download("olym_suzano",rf"mill_info.json"))
            inv1,inv2,inv3=st.tabs(["DAILY ACTION","MAIN INVENTORY","SUZANO MILL SHIPMENT SCHEDULE/PROGRESS"])
            with inv1:
                data=gcp_download("olym_suzano",rf"terminal_bill_of_ladings.json")
                bill_of_ladings=json.loads(data)
                daily1,daily2,daily3=st.tabs(["TODAY'SHIPMENTS","TRUCKS ENROUTE","TRUCKS AT DESTINATION"])
                with daily1:
                    now=datetime.datetime.now()-datetime.timedelta(hours=7)
                    st.markdown(f"**SHIPPED TODAY ON {datetime.datetime.strftime(now.date(),'%b %d, %Y')}**")     
                    df_bill=pd.DataFrame(bill_of_ladings).T
                    df_bill=df_bill[["vessel","release_order","destination","sales_order","ocean_bill_of_lading","wrap","carrier_id","vehicle","quantity","issued"]]
                    df_bill.columns=["VESSEL","RELEASE ORDER","DESTINATION","SALES ORDER","OCEAN BILL OF LADING","WRAP","CARRIER ID","VEHICLE NO","QUANTITY (UNITS)","ISSUED"]
                    df_bill["Date"]=[None]+[datetime.datetime.strptime(i,"%Y-%m-%d %H:%M:%S").date() for i in df_bill["ISSUED"].values[1:]]
                    
                    df_today=df_bill[df_bill["Date"]==now.date()]
                    df_today.loc["TOTAL","QUANTITY (UNITS)"]=df_today["QUANTITY (UNITS)"].sum()
                       
                    st.dataframe(df_today)

                
                with daily2:
                    enroute_vehicles={}
                    arrived_vehicles={}
                    for i in bill_of_ladings:
                        if i!="115240":
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
                                st.write(f"Truck No : {truck} is Enroute to {destination} with ETA {estimated_arrival_string}")
                                enroute_vehicles[truck]={"DESTINATION":destination,"CARGO":bill_of_ladings[i]["ocean_bill_of_lading"],
                                                 "QUANTITY":f'{2*bill_of_ladings[i]["quantity"]} TONS',"LOADED TIME":f"{ship_date.date()}---{ship_time}","ETA":estimated_arrival_string}
                            else:
                                with daily3:
                                    st.write(f"Truck No : {truck} arrived at {destination} at {estimated_arrival_string}")
                                    arrived_vehicles[truck]={"DESTINATION":destination,"CARGO":bill_of_ladings[i]["ocean_bill_of_lading"],
                                                 "QUANTITY":f'{2*bill_of_ladings[i]["quantity"]} TONS',"LOADED TIME":f"{ship_date.date()}---{ship_time}","ARRIVAL TIME":estimated_arrival_string}
                                    
                    arrived_vehicles=pd.DataFrame(arrived_vehicles)
                    arrived_vehicles=arrived_vehicles.rename_axis('TRUCK NO')               
                    enroute_vehicles=pd.DataFrame(enroute_vehicles)
                    enroute_vehicles=enroute_vehicles.rename_axis('TRUCK NO')
                    st.dataframe(enroute_vehicles.T)                                                    

                with daily3:
                    st.table(arrived_vehicles.T)
                    
            with inv2:
                     
                dab1,dab2=st.tabs(["IN WAREHOUSE","SHIPPED"])
                df=Inventory[Inventory["Location"]=="OLYM"][["Lot","Batch","Ocean B/L","Wrap","DryWeight","ADMT","Location","Warehouse_In"]]
                zf=Inventory[Inventory["Location"]=="ON TRUCK"][["Lot","Batch","Ocean B/L","Wrap","DryWeight","ADMT","Release_Order_Number","Carrier_Code","Terminal B/L",
                                                                 "Vehicle_Id","Warehouse_In","Warehouse_Out"]]
                items=df["Ocean B/L"].unique().tolist()
                
                with dab1:
                    
                    inv_col1,inv_col2,inv_col3=st.columns([2,6,2])
                    with inv_col1:
                        st.markdown(f"**IN WAREHOUSE = {len(df)}**")
                        st.markdown(f"**TOTAL SHIPPED = {len(zf)}**")
                        st.markdown(f"**TOTAL OVERALL = {len(zf)+len(df)}**")
                    with inv_col2:
                        #st.write(items)
                        inhouse=[df[df["Ocean B/L"]==i].shape[0] for i in items]
                        shipped=[zf[zf["Ocean B/L"]==i].shape[0] for i in items]
                        
                        wrap_=[df[df["Ocean B/L"]==i]["Wrap"].unique()[0] for i in items]
                       # st.write(wrap_)
                        tablo=pd.DataFrame({"Ocean B/L":items,"Wrap":wrap_,"In Warehouse":inhouse,"Shipped":shipped},index=[i for i in range(1,len(items)+1)])
                        total_row={"Ocean B/L":"TOTAL","In Warehouse":sum(inhouse),"Shipped":sum(shipped)}
                        tablo = tablo.append(total_row, ignore_index=True)
                        tablo["TOTAL"] = tablo.loc[:, ["In Warehouse", "Shipped"]].sum(axis=1)
             
                        st.dataframe(tablo)
                    if st.checkbox("CLICK TO SEE INVENTORY LIST"):
                        st.table(df)
                with dab2:
                    
                    date_filter=st.checkbox("CLICK FOR DATE FILTER")
                    if "disabled" not in st.session_state:
                        st.session_state.visibility = "visible"
                        st.session_state.disabled = True
                    if date_filter:
                        st.session_state.disabled=False
                        
                    else:
                        st.session_state.disabled=True
                        #min_value=min([i.date() for i in zf["Warehouse_Out"]])
                    filter_date=st.date_input("Choose Warehouse OUT Date",datetime.datetime.today(),min_value=None, max_value=None,disabled=st.session_state.disabled,key="filter_date")
                    
                    
                    #st.write(zf)
                    #zf[["Release_Order_Number","Carrier_Code","Terminal B/L","Vehicle_Id"]]=zf[["Release_Order_Number","Carrier_Code","Terminal B/L","Vehicle_Id"]].astype("int")
                    zf[["Release_Order_Number","Carrier_Code","Terminal B/L","Vehicle_Id"]]=zf[["Release_Order_Number","Carrier_Code","Terminal B/L","Vehicle_Id"]].astype("str")
                    
                    zf["Warehouse_Out"]=[datetime.datetime.strptime(j,"%Y-%m-%d %H:%M:%S") for j in zf["Warehouse_Out"]]
                    filtered_zf=zf.copy()
                    if date_filter:
                        filtered_zf["Warehouse_Out"]=[i.date() for i in filtered_zf["Warehouse_Out"]]
                        
                        filtered_zf=filtered_zf[filtered_zf["Warehouse_Out"]==filter_date]
                        
                    filter_by=st.selectbox("SELECT FILTER",["Wrap","Ocean B/L","Release_Order_Number","Terminal B/L","Carrier_Code","Vehicle_Id"])
                    #st.write(filter_by)
                    choice=st.selectbox(f"Filter By {filter_by}",[f"ALL {filter_by.upper()}"]+[str(i) for i in filtered_zf[filter_by].unique().tolist()])
                    
                    
                    col1,col2=st.columns([2,8])
                    with col1:
                        st.markdown(f"**TOTAL SHIPPED = {len(zf)}**")
                        st.markdown(f"**IN WAREHOUSE = {len(df)}**")
                        st.markdown(f"**TOTAL OVERALL = {len(zf)+len(df)}**")
                    try:
                        filtered_zf=filtered_zf[filtered_zf[filter_by]==choice]
                        filtered_df=filtered_zf[filtered_zf[filter_by]==choice]
                        
                    except:
                        filtered_zf=filtered_zf
                        filtered_df=df.copy()
                        
                        pass
                    with col2:
                        if date_filter:
                            st.markdown(f"**SHIPPED ON THIS DAY = {len(filtered_zf)}**")
                        else:
                            st.markdown(f"**TOTAL SHIPPED = {len(filtered_zf)}**")
                            st.markdown(f"**IN WAREHOUSE = {len(filtered_df)}**")
                            st.markdown(f"**TOTAL OVERALL = {len(filtered_zf)+len(filtered_df)}**")
                        
                        
                    st.table(filtered_zf)
            with inv3:
                mill_progress=json.loads(gcp_download("olym_suzano",rf"mill_progress.json"))
                reformed_dict = {}
                for outerKey, innerDict in mill_progress.items():
                    for innerKey, values in innerDict.items():
                        reformed_dict[(outerKey,innerKey)] = values
                mill_prog_col1,mill_prog_col2=st.columns([2,2])
                with mill_prog_col1:
                    st.dataframe(pd.DataFrame(reformed_dict).T)
                with mill_prog_col2:
                    def cust_business_days(start, end):
                        business_days = pd.date_range(start=start, end=end, freq='B')
                        return business_days
                    daily_needed_rate=68
                    days_passed=len(cust_business_days(datetime.date(2023,8,1),datetime.datetime.today()))
                    days_left=len(cust_business_days(datetime.datetime.today(),datetime.date(2023,9,1)))
                    shipped_so_far=800
                    reference=68*days_passed
                    fig = go.Figure(go.Indicator(
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            value = shipped_so_far,
                            mode = "gauge+number+delta",
                            title = {'text': "Tons Shipped to Lewiston - TARGET 1500 MT"},
                            delta = {'reference': reference},
                            gauge = {'axis': {'range': [None, 1500]},
                                     'steps' : [
                                         {'range': [0, reference], 'color': "lightgray"},
                                      ],
                                     'threshold' : {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 1500}}))

                    st.plotly_chart(fig)





    ########################                                WAREHOUSE                            ####################
    
    elif username == 'warehouse':
        st.write(f'Welcome *{name}*')
        bill_mapping=gcp_download("olym_suzano","bill_mapping.json")
        bill_mapping=json.loads(bill_mapping)
        no_dispatch=0
        number=None
        if number not in st.session_state:
            st.session_state.number=number
        try:
            dispatched=gcp_download("olym_suzano","dispatched.json")
            dispatched=json.loads(dispatched)
        except:
            no_dispatch=1
            pass
       
        
        double_load=False
        
        if len(dispatched.keys())>0 and not no_dispatch:
            #menu_destinations=[f"{i} TO {j}" for i,j in zip[dispatched.keys()
            work_order=st.selectbox("**SELECT RELEASE ORDER/SALES ORDER TO WORK**",dispatched.keys())
            
            order=["001","002","003","004","005","006"]
            
            for i in order:
                if i in dispatched[work_order].keys():
                    current_release_order=work_order
                    current_sales_order=i
                    vessel=dispatched[work_order][i]["vessel"]
                    destination=dispatched[work_order][i]['destination']
                    break
                else:
                    pass
            try:
                next_release_order=dispatched['002']['release_order']
                next_sales_order=dispatched['002']['sales_order']
                
            except:
                
                pass
            info=gcp_download("olym_suzano",rf"release_orders/{vessel}/{work_order}.json")
            info=json.loads(info)
            
            
            if st.checkbox("CLICK TO LOAD MIXED SKU"):
                try:
                    next_item=gcp_download("olym_suzano",rf"release_orders/{dispatched['2']['vessel']}/{dispatched['2']['release_order']}.json")
                    double_load=True
                except:
                    st.markdown("**:red[ONLY ONE ITEM IN QUEUE ! ASK NEXT ITEM TO BE DISPATCHED!]**")
                
        
            load_col1,load_col2,load_col3=st.columns([4,4,2])
            with load_col1:
                st.markdown(rf'**:blue[CURRENTLY WORKING] : Release Order-{current_release_order}**')
                st.markdown(rf'**Destination : {destination} .**')
                st.markdown(rf'**Sales Order Item-{current_sales_order}**')
                wrap_dict={"ISU":"UNWRAPPED","ISP":"WRAPPED"}
                wrap=info[vessel][current_release_order][current_sales_order]["wrap"]
                st.markdown(f'**Ocean Bill Of Lading : {info[vessel][current_release_order][current_sales_order]["ocean_bill_of_lading"]} - {wrap_dict[wrap]}**')
                unitized=info[vessel][current_release_order][current_sales_order]["unitized"]
                st.markdown(rf'**{info[vessel][current_release_order][current_sales_order]["unitized"]}**')
                st.markdown(rf'**Total Quantity : {info[vessel][current_release_order][current_sales_order]["quantity"]}**')
                st.markdown(rf'**Shipped : {info[vessel][current_release_order][current_sales_order]["shipped"]}**')
                remaining=info[vessel][current_release_order][current_sales_order]["remaining"]                #######      DEFINED "REMAINING" HERE FOR CHECKS
                if remaining<10:
                    st.markdown(rf'**:red[CAUTION : Remaining : {info[vessel][current_release_order][current_sales_order]["remaining"]}]**')
                st.markdown(rf'**Remaining : {info[vessel][current_release_order][current_sales_order]["remaining"]}**')
                
            with load_col2:
                if double_load:
                    
                    try:
                        st.markdown(rf'**NEXT ITEM : Release Order-{next_release_order}**')
                        st.markdown(rf'**Sales Order Item-{next_sales_order}**')
                        st.markdown(f'**Ocean Bill Of Lading : {info[vessel][next_release_order][next_sales_order]["ocean_bill_of_lading"]}**')
                        st.markdown(rf'**Total Quantity : {info[vessel][next_release_order][next_sales_order]["quantity"]}**')
                    except:
                        pass
                  
            col1, col2,col3,col4,col5= st.columns([2,2,2,2,2])
            
          
           
            if info[vessel][current_release_order][current_sales_order]["transport_type"]=="TRUCK":
                medium="TRUCK"
            else:
                medium="RAIL"
            
            with col1:
            
                terminal_code=st.text_input("Terminal Code","OLYM",disabled=True)
                file_date=st.date_input("File Date",datetime.datetime.today()-datetime.timedelta(hours=7),key="file_dates",disabled=True)
                if file_date not in st.session_state:
                    st.session_state.file_date=file_date
                file_time = st.time_input('FileTime', datetime.datetime.now()-datetime.timedelta(hours=7),step=60,disabled=False)
                delivery_date=st.date_input("Delivery Date",datetime.datetime.today()-datetime.timedelta(hours=7),key="delivery_date",disabled=True)
                eta_date=st.date_input("ETA Date (For Trucks same as delivery date)",delivery_date,key="eta_date",disabled=True)
                
            with col2:
                if double_load:
                    release_order_number=st.text_input("Release Order Number",current_release_order,disabled=True,help="Release Order Number without the Item no")
                    sales_order_item=st.text_input("Sales Order Item (Material Code)",current_sales_order,disabled=True)
                    ocean_bill_of_lading=st.text_input("Ocean Bill Of Lading",info[vessel][current_release_order][current_sales_order]["ocean_bill_of_lading"],disabled=True)
                    current_ocean_bill_of_lading=ocean_bill_of_lading
                    next_ocean_bill_of_lading=info[vessel][next_release_order][next_sales_order]["ocean_bill_of_lading"]
                    batch=st.text_input("Batch",info[vessel][current_release_order][current_sales_order]["batch"],disabled=True)
                    
                    #terminal_bill_of_lading=st.text_input("Terminal Bill of Lading",disabled=False)
                    pass
                else:
                    release_order_number=st.text_input("Release Order Number",current_release_order,disabled=True,help="Release Order Number without the Item no")
                    sales_order_item=st.text_input("Sales Order Item (Material Code)",current_sales_order,disabled=True)
                    ocean_bill_of_lading=st.text_input("Ocean Bill Of Lading",info[vessel][current_release_order][current_sales_order]["ocean_bill_of_lading"],disabled=True)
                    
                    batch=st.text_input("Batch",info[vessel][current_release_order][current_sales_order]["batch"],disabled=True)
                    #terminal_bill_of_lading=st.text_input("Terminal Bill of Lading",disabled=False)
               
                    
                
            with col3: 
                carrier_code=st.text_input("Carrier Code",info[vessel][current_release_order][current_sales_order]["carrier_code"],disabled=True)
                transport_sequential_number=st.selectbox("Transport Sequential",["TRUCK","RAIL"],disabled=True)
                transport_type=st.selectbox("Transport Type",["TRUCK","RAIL"],disabled=True)
                vehicle_id=st.text_input("**:blue[Vehicle ID]**")
                foreman_quantity=st.number_input("**:blue[ENTER Quantity of Units]**", min_value=0, max_value=30, value=0, step=1,key=None, help=None, on_change=None, disabled=False, label_visibility="visible")
            
                
           
            with col4:
                updated_quantity=0
                live_quantity=0
                if updated_quantity not in st.session_state:
                    st.session_state.updated_quantity=updated_quantity
                def audit_unit(x):
                        if len(x)==11:
                            #st.write(bill_mapping[x[:-3]]["Batch"])
                            #st.write(Inventory_Audit[Inventory_Audit["Lot"]==x]["Location"].iloc[0])
                            if bill_mapping[x[:-3]]["Ocean_bl"]!=ocean_bill_of_lading and bill_mapping[x[:-3]]["Batch"]!=batch:
                                st.write(f"**:red[WRONG B/L, DO NOT LOAD UNIT {x}]**")
                                return False
                            
                            if Inventory_Audit[Inventory_Audit["Lot"]==x]["Location"].iloc[0]!="OLYM":
                                st.write(":red[THIS BELOW UNIT HAS BEEN SHIPPED]")
                                return False
                            
                            else:
                                return True
                def audit_split(release,sales):
                        if len(x)==11:
                            #st.write(bill_mapping[x[:-3]]["Batch"])
                            
                            if bill_mapping[x[:-3]]["Ocean_bl"]!=info[vessel][release][sales]["ocean_bill_of_lading"] and bill_mapping[x[:-3]]["Batch"]!=info[vessel][release][sales]["batch"]:
                                st.write("**:red[WRONG B/L, DO NOT LOAD BELOW!]**")
                                return False
                            if Inventory_Audit[Inventory_Audit["Lot"]==x]["Location"].iloc[0]!="OLYM":
                                st.write(":red[THIS BELOW UNIT HAS BEEN SHIPPED]")
                                return False
                            else:
                                return True
                
                flip=False 
                first_load_input=None
                second_load_input=None
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
                    
    
    
                
                    load_input=st.text_area("**LOADS**",height=300)#[:-3]
                    if load_input is not None:
                        textsplit = load_input.splitlines()
                        textsplit=[i for i in textsplit if len(i)>8]
                        updated_quantity=len(textsplit)
                        st.session_state.updated_quantity=updated_quantity
                   
                    
                quantity=st.number_input("**Scanned Quantity of Units**",st.session_state.updated_quantity, key=None, help=None, on_change=None, disabled=True, label_visibility="visible")
                st.markdown(f"**{quantity*2} TONS - {round(quantity*2*2204.62,1)} Pounds**")
                #ADMT=st.text_input("ADMT",round(info[vessel][current_release_order][current_sales_order]["dryness"]/90,4)*updated_quantity,disabled=True)
                admt=round(float(info[vessel][current_release_order][current_sales_order]["dryness"])/90*updated_quantity*2,4)
                st.markdown(f"**ADMT= {admt} TONS**")
                    
                    
                        
                
                
                
                
             
               
            with col5:
                Inventory_Audit=gcp_csv_to_df("olym_suzano", "Inventory.csv")
                #st.write(Inventory_Audit)
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
                
                else:
                    
                
                    faults=[]
                    fault_messaging={}
                    if load_input is not None:
                        textsplit = load_input.splitlines()
                        
                            
                        textsplit=[i for i in textsplit if len(i)>8]
                        #st.write(textsplit)
                        seen=set()
                        for i,x in enumerate(textsplit):
                            
                            if audit_unit(x):
                                if x in seen:
                                    st.text_input(f"Unit No : {i+1}",x)
                                    faults.append(1)
                                    fault_messaging[i+1]="This unit has been scanned TWICE!"
                                else:
                                    st.text_input(f"Unit No : {i+1}",x)
                                    faults.append(0)
                            else:
                                st.text_input(f"Unit No : {i+1}",x)
                                faults.append(1)
                            seen.add(x)
                    loads=[]
                    for k in textsplit:
                        loads.append(k)
               
            #st.write(faults)                  
            a=datetime.datetime.strftime(file_date,"%Y%m%d")
            a_=datetime.datetime.strftime(file_date,"%Y-%m-%d")
            b=file_time.strftime("%H%M%S")
            b_=file_time.strftime("%H:%M:%S")
            c=datetime.datetime.strftime(eta_date,"%Y%m%d")
            st.write(file_date.month)
            
                
            
            if st.button('SUBMIT EDI'):
                def gen_bill_of_lading():
                    data=gcp_download("olym_suzano",rf"terminal_bill_of_ladings.json")
                    bill_of_ladings=json.loads(data)
                    list_of_ladings=[]
                    try:
                        for key in bill_of_ladings:
                            if int(key) % 2 == 0:
                                list_of_ladings.append(int(key))
                        bill_of_lading_number=max(list_of_ladings)+2
                    except:
                        bill_of_lading_number=115240
                    return bill_of_lading_number,bill_of_ladings
                #st.write(bill_of_lading_number)
                
                
                if double_load:
                    bill_of_lading_number,bill_of_ladings=gen_bill_of_lading()
                    bill_of_ladings[str(bill_of_lading_number)]={"vessel":vessel,"release_order":release_order_number,"destination":destination,"sales_order":current_sales_order,
                                                                 "ocean_bill_of_lading":ocean_bill_of_lading,"wrap":wrap,"carrier_id":carrier_code,"vehicle":vehicle_id,
                                                                 "quantity":len(first_textsplit),"issued":f"{a_} {b_}"} 
                    bill_of_ladings[str(bill_of_lading_number+1)]={"vessel":vessel,"release_order":release_order_number,"destination":destination,"sales_order":next_sales_order,
                                                                 "ocean_bill_of_lading":ocean_bill_of_lading,"wrap":wrap,"carrier_id":carrier_code,"vehicle":vehicle_id,
                                                                 "quantity":len(first_textsplit),"issued":f"{a_} {b_}"} 
                else:
                    bill_of_lading_number,bill_of_ladings=gen_bill_of_lading()
                    bill_of_ladings[str(bill_of_lading_number)]={"vessel":vessel,"release_order":release_order_number,"destination":destination,"sales_order":current_sales_order,
                                                                 "ocean_bill_of_lading":ocean_bill_of_lading,"wrap":wrap,"carrier_id":carrier_code,"vehicle":vehicle_id,
                                                                 "quantity":len(textsplit),"issued":f"{a_} {b_}"} 
                    
             
                bill_of_ladings=json.dumps(bill_of_ladings)
                storage_client = storage.Client()
                bucket = storage_client.bucket("olym_suzano")
                blob = bucket.blob(rf"terminal_bill_of_ladings.json")
                blob.upload_from_string(bill_of_ladings)
                
                
                terminal_bill_of_lading=st.text_input("Terminal Bill of Lading",bill_of_lading_number,disabled=True)
                
                proceed=False
                if double_load:
                    if 1 in first_faults or 1 in second_faults:
                        st.markdown(f"**:red[CAN NOT SUBMIT EDI!!] CHECK BELOW UNTIS**")
                        for i in first_faults:
                            if i==1:
                                st.markdown(f"**:red[Check Unit Unit{first_faults.index(i)+1}]**")
                        for i in second_faults:
                            if i==1:
                                st.markdown(f"**:red[Check Unit Unit{second_faults.index(i)+1}]**")
                    else:
                        proceed=True
                else:
                    if 1 in faults:
                        proceed=False
                        for i in faults:
                            if i==1:
                                st.markdown(f"**:red[Check Unit {faults.index(i)+1}]**")
                    else:
                        proceed=True
                if fault_messaging.keys():
                    for i in fault_messaging.keys():
                        error=f"**:red[Unitfault_messaging[i]]**"
                if remaining<0:
                    proceed=False
                    error="**:red[No more Items to ship on this Sales Order]"
                    st.write(error)
                if not vehicle_id: 
                    proceed=False
                    error="**:red[Please check Vehicle ID]"
                    st.write(error)
                if len(terminal_bill_of_lading)<6:
                    proceed=False
                    error="**:red[Please check Terminal Bill Of Lading. It should have 6 digits.]"
                    st.write(error)
                if quantity!=foreman_quantity:
                    proceed=False
                    error=f"**:red[{quantity} loads on this truck. Please check. You planned for {foreman_quantity} loads!]** "
                    st.write(error)
                if proceed:
                    
                    process()
                    mill_progress=json.loads(gcp_download("olym_suzano",rf"mill_progress.json"))
                    map={8:"SEP 2023",9:"SEP 2023",10:"OCT 2023",11:"NOV 2023",12:"DEC 2023"}
                    mill_progress[destination][map[file_date.month]]["Shipped"]=mill_progress[destination][map[file_date.month]]["Shipped"]+len(textsplit)*2
                    json_data = json.dumps(mill_progress)
                    storage_client = storage.Client()
                    bucket = storage_client.bucket("olym_suzano")
                    blob = bucket.blob(rf"mill_progress.json")
                    blob.upload_from_string(json_data)       
                    if double_load:
                        info[vessel][current_release_order][current_sales_order]["shipped"]=info[vessel][current_release_order][current_sales_order]["shipped"]+len(first_textsplit)
                        info[vessel][current_release_order][current_sales_order]["remaining"]=info[vessel][current_release_order][current_sales_order]["remaining"]-len(first_textsplit)
                        info[vessel][next_release_order][next_sales_order]["shipped"]=info[vessel][next_release_order][next_sales_order]["shipped"]+len(second_textsplit)
                        info[vessel][next_release_order][next_sales_order]["remaining"]=info[vessel][next_release_order][next_sales_order]["remaining"]-len(second_textsplit)
                    else:
                        info[vessel][current_release_order][current_sales_order]["shipped"]=info[vessel][current_release_order][current_sales_order]["shipped"]+len(loads)
                        info[vessel][current_release_order][current_sales_order]["remaining"]=info[vessel][current_release_order][current_sales_order]["remaining"]-len(loads)
                    if info[vessel][current_release_order][current_sales_order]["remaining"]<=0:
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
                        bucket = storage_client.bucket("olym_suzano")
                        blob = bucket.blob(rf"dispatched.json")
                        blob.upload_from_string(json_data)       
                    
                    json_data = json.dumps(info)
                    storage_client = storage.Client()
                    bucket = storage_client.bucket("olym_suzano")
                    blob = bucket.blob(rf"release_orders/{vessel}/{current_release_order}.json")
                    blob.upload_from_string(json_data)



                    
                    with open('placeholder.txt', 'r') as f:
                        output_text = f.read()
                    st.markdown("**SUCCESS! EDI FOR THIS LOAD HAS BEEN SUBMITTED,THANK YOU**")
                    st.markdown("**EDI TEXT**")
                    st.text_area('', value=output_text, height=600)
                    with open('placeholder.txt', 'r') as f:
                        file_content = f.read()
                    newline="\n"
                    filename = f'{a}{b}OLYM'
                    file_name= f'{a}{b}OLYM.txt'
                    st.write(filename)
                    st.write(current_release_order,current_sales_order,destination,ocean_bill_of_lading,terminal_bill_of_lading,wrap)
                    subject = f'Suzano_EDI_{a}_{release_order_number}'
                    body = f"EDI for Below attached.{newline}Release Order Number : {current_release_order} - Sales Order Number:{current_sales_order}{newline}Destination : {destination}Ocean Bill Of Lading : {ocean_bill_of_lading}{newline}Terminal Bill of Lading: {terminal_bill_of_lading} - Wrap : {wrap} {newline}{len(loads)} {unitized} loads were loaded to vehicle : {vehicle_id} with Carried ID : {carrier_code} {newline}Truck loading completed at {a_} {b_}"
                    st.write(body)           
                    sender = "warehouseoly@gmail.com"
                    #recipients = ["alexandras@portolympia.com","conleyb@portolympia.com", "afsiny@portolympia.com"]
                    recipients = ["afsiny@portolympia.com"]
                    password = "xjvxkmzbpotzeuuv"
            
                      # Replace with the actual file path
            
            
                    with open('temp_file.txt', 'w') as f:
                        f.write(file_content)
            
                    file_path = 'temp_file.txt'  # Use the path of the temporary file
            
                    send_email_with_attachment(subject, body, sender, recipients, password, file_path,file_name)
                    upload_cs_file("olym_suzano", 'temp_file.txt',file_name) 
                    
                else:   ###cancel bill of lading
                    data=gcp_download("olym_suzano",rf"terminal_bill_of_ladings.json")
                    bill_of_ladings=json.loads(data)
                    del bill_of_ladings[str(bill_of_lading_number)]
                    bill_of_ladings=json.dumps(bill_of_ladings)
                    storage_client = storage.Client()
                    bucket = storage_client.bucket("olym_suzano")
                    blob = bucket.blob(rf"terminal_bill_of_ladings.json")
                    blob.upload_from_string(bill_of_ladings)
    
        
                    
        else:
            st.subheader("**Nothing dispatched!**")
    elif username == 'olysuzanodash':
        st.write(f'Welcome *{name}*')
        Inventory=gcp_csv_to_df("olym_suzano", "Inventory.csv")
           
        mill_info=json.loads(gcp_download("olym_suzano",rf"mill_info.json"))
        inv1,inv2,inv3=st.tabs(["DAILY ACTION","MAIN INVENTORY","SUZANO MILL SHIPMENT SCHEDULE/PROGRESS"])
        with inv1:
            data=gcp_download("olym_suzano",rf"terminal_bill_of_ladings.json")
            bill_of_ladings=json.loads(data)
            daily1,daily2,daily3=st.tabs(["TODAY'SHIPMENTS","TRUCKS ENROUTE","TRUCKS AT DESTINATION"])
            with daily1:
                          
                df_bill=pd.DataFrame(bill_of_ladings).T
                df_bill=df_bill[["vessel","release_order","destination","sales_order","ocean_bill_of_lading","wrap","carrier_id","vehicle","quantity","issued"]]
                df_bill.columns=["VESSEL","RELEASE ORDER","DESTINATION","SALES ORDER","OCEAN BILL OF LADING","WRAP","CARRIER ID","VEHICLE NO","QUANTITY","ISSUED"]
                st.dataframe(df_bill)
            with daily2:
                
                for i in bill_of_ladings:
                    if i!="115240":
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
                        estimated_arrival_string=datetime.datetime.strftime(estimated_arrival,"%B %d,%Y - %H:%M")
                        now=datetime.datetime.now()-datetime.timedelta(hours=7)
                        if estimated_arrival>now:
                            st.write(f"Truck No : {truck} is Enroute to {destination} with ETA {estimated_arrival_string}")
                        else:
                            with daily3:
                                st.write(f"Truck No : {truck} arrived at {destination} at {estimated_arrival_string}")
                                                                                 

            
        with inv2:
                 
            dab1,dab2=st.tabs(["IN WAREHOUSE","SHIPPED"])
            df=Inventory[Inventory["Location"]=="OLYM"][["Lot","Batch","Ocean B/L","Wrap","DryWeight","ADMT","Location","Warehouse_In"]]
            zf=Inventory[Inventory["Location"]=="ON TRUCK"][["Lot","Batch","Ocean B/L","Wrap","DryWeight","ADMT","Release_Order_Number","Carrier_Code","Terminal B/L",
                                                             "Vehicle_Id","Warehouse_In","Warehouse_Out"]]
            items=df["Ocean B/L"].unique().tolist()
            
            with dab1:
                
                inv_col1,inv_col2,inv_col3=st.columns([2,6,2])
                with inv_col1:
                    st.markdown(f"**IN WAREHOUSE = {len(df)}**")
                    st.markdown(f"**TOTAL SHIPPED = {len(zf)}**")
                    st.markdown(f"**TOTAL OVERALL = {len(zf)+len(df)}**")
                with inv_col2:
                    #st.write(items)
                    inhouse=[df[df["Ocean B/L"]==i].shape[0] for i in items]
                    shipped=[zf[zf["Ocean B/L"]==i].shape[0] for i in items]
                    
                    wrap_=[df[df["Ocean B/L"]==i]["Wrap"].unique()[0] for i in items]
                   # st.write(wrap_)
                    tablo=pd.DataFrame({"Ocean B/L":items,"Wrap":wrap_,"In Warehouse":inhouse,"Shipped":shipped},index=[i for i in range(1,len(items)+1)])
                    total_row={"Ocean B/L":"TOTAL","In Warehouse":sum(inhouse),"Shipped":sum(shipped)}
                    tablo = tablo.append(total_row, ignore_index=True)
                    tablo["TOTAL"] = tablo.loc[:, ["In Warehouse", "Shipped"]].sum(axis=1)
         
                    st.dataframe(tablo)
                if st.checkbox("CLICK TO SEE INVENTORY LIST"):
                    st.table(df)
            with dab2:
                
                date_filter=st.checkbox("CLICK FOR DATE FILTER")
                if "disabled" not in st.session_state:
                    st.session_state.visibility = "visible"
                    st.session_state.disabled = True
                if date_filter:
                    st.session_state.disabled=False
                    
                else:
                    st.session_state.disabled=True
                    #min_value=min([i.date() for i in zf["Warehouse_Out"]])
                filter_date=st.date_input("Choose Warehouse OUT Date",datetime.datetime.today(),min_value=None, max_value=None,disabled=st.session_state.disabled,key="filter_date")
                
                
                #st.write(zf)
                #zf[["Release_Order_Number","Carrier_Code","Terminal B/L","Vehicle_Id"]]=zf[["Release_Order_Number","Carrier_Code","Terminal B/L","Vehicle_Id"]].astype("int")
                zf[["Release_Order_Number","Carrier_Code","Terminal B/L","Vehicle_Id"]]=zf[["Release_Order_Number","Carrier_Code","Terminal B/L","Vehicle_Id"]].astype("str")
                
                zf["Warehouse_Out"]=[datetime.datetime.strptime(j,"%Y-%m-%d %H:%M:%S") for j in zf["Warehouse_Out"]]
                filtered_zf=zf.copy()
                if date_filter:
                    filtered_zf["Warehouse_Out"]=[i.date() for i in filtered_zf["Warehouse_Out"]]
                    
                    filtered_zf=filtered_zf[filtered_zf["Warehouse_Out"]==filter_date]
                    
                filter_by=st.selectbox("SELECT FILTER",["Wrap","Ocean B/L","Release_Order_Number","Terminal B/L","Carrier_Code","Vehicle_Id"])
                #st.write(filter_by)
                choice=st.selectbox(f"Filter By {filter_by}",[f"ALL {filter_by.upper()}"]+[str(i) for i in filtered_zf[filter_by].unique().tolist()])
                
                
                col1,col2=st.columns([2,8])
                with col1:
                    st.markdown(f"**TOTAL SHIPPED = {len(zf)}**")
                    st.markdown(f"**IN WAREHOUSE = {len(df)}**")
                    st.markdown(f"**TOTAL OVERALL = {len(zf)+len(df)}**")
                try:
                    filtered_zf=filtered_zf[filtered_zf[filter_by]==choice]
                    filtered_df=filtered_zf[filtered_zf[filter_by]==choice]
                    
                except:
                    filtered_zf=filtered_zf
                    filtered_df=df.copy()
                    
                    pass
                with col2:
                    if date_filter:
                        st.markdown(f"**SHIPPED ON THIS DAY = {len(filtered_zf)}**")
                    else:
                        st.markdown(f"**TOTAL SHIPPED = {len(filtered_zf)}**")
                        st.markdown(f"**IN WAREHOUSE = {len(filtered_df)}**")
                        st.markdown(f"**TOTAL OVERALL = {len(filtered_zf)+len(filtered_df)}**")
                    
                    
                st.table(filtered_zf)
        with inv3:
            mill_progress=json.loads(gcp_download("olym_suzano",rf"mill_progress.json"))
            reformed_dict = {}
            for outerKey, innerDict in mill_progress.items():
                for innerKey, values in innerDict.items():
                    reformed_dict[(outerKey,innerKey)] = values
            st.dataframe(pd.DataFrame(reformed_dict).T)
elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')




    
 
