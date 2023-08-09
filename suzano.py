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

from google.cloud import storage
import os
import io
from io import StringIO


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



pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.options.mode.chained_assignment = None  # default='warn'

st.set_page_config(layout="wide")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "client_secrets.json"

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
def store_release_order_data(vessel,release_order_number,sales_order_item,batch,ocean_bill_of_lading,dryness,quantity,tonnage,transport_type,carrier_code):
       
    # Create a dictionary to store the release order data
    release_order_data = { vessel: {
       
        "release_order_number":{
        "sales_order_item": {
        "batch": bill_of_lading,
        "ocean_bill_of_lading": ocean_bill_of_lading,
        "dryness":dryness,
        "transport_type": transport_type,
        "carrier_code": carrier_code,
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

def edit_release_order_data(file,vessel,release_order_number,sales_order_item,batch,ocean_bill_of_lading,dryness,quantity,tonnage,transport_type,carrier_code):
       
    # Edit the loaded current dictionary.
    if sales_order_item not in file[vessel][release_order_number]:
        file[vessel][release_order_number][sales_order_item]={}
    file[vessel][release_order_number][sales_order_item]["batch"]= batch
    file[vessel][release_order_number][sales_order_item]["ocean_bill_of_lading"]= ocean_bill_of_lading
    file[vessel][release_order_number][sales_order_item]["dryness"]= dryness
    file[vessel][release_order_number][sales_order_item]["transport_type"]= transport_type
    file[vessel][release_order_number][sales_order_item]["carrier_code"]= carrier_code
    file[vessel][release_order_number][sales_order_item]["quantity"]= quantity
    file[vessel][release_order_number][sales_order_item]["tonnage"]= tonnage
    file[vessel][release_order_number][sales_order_item]["shipped"]= 0
    file[vessel][release_order_number][sales_order_item]["remaining"]= quantity
    
    
       

    # Convert the dictionary to JSON format
    json_data = json.dumps(file)
    return json_data

def generate_bill_of_lading():
    pass

user="AFSIN"
    
#if user :
#colu1,colu2=st.columns([1,8])
select=st.sidebar.radio("SELECT FUNCTION",
    ('ADMIN', 'LOADOUT', 'INVENTORY'))

    #tab1,tab2,tab3,tab4= st.tabs(["UPLOAD SHIPMENT FILE","ENTER LOADOUT DATA","INVENTORY","CAPTURE"])
    

    
if select=="ADMIN" :
    admin_tab1,admin_tab2=st.tabs(["SHIPMENT FILES","RELEASE ORDERS"])
    with admin_tab1:
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
                          [str(i)[20:28] for i in temp[7]])),columns=["Lot","Lot Qty","B/L"])
                df["Lot Qty"]=[int(int(i)/2) for i in df["Lot Qty"]]
                df["Wrap"]=[i[:3] for i in temp[1]]
                df["Vessel"]=[i[-12:] for i in temp[7]]
                df["DryWeight"]=[int(i) for i in temp[8]]
                df["ADMT"]=[int(i)/0.9/100000 for i in temp[8]]
                new_list=[]
                lotq=[]
                bl=[]
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
                        bl.append(str(df.loc[i,"B/L"]))
                        wrap.append(df.loc[i,"Wrap"])
                        vessel.append(df.loc[i,"Vessel"])
                        DryWeight.append(df.loc[i,"DryWeight"])
                        ADMT.append(df.loc[i,"ADMT"])
                new_df=pd.DataFrame(list(zip(new_list,lotq,bl,wrap,vessel,DryWeight,ADMT)),columns=df.columns.to_list())
                new_df["Location"]="OLYM"
                new_df["Warehouse_In"]="8/24/2023"
                new_df["Warehouse_Out"]=""
                new_df["Vehicle_Id"]=""
                new_df["Release_Order_Number"]=""
                new_df["Carrier_Code"]=""
                new_df["BL"]=""
                bls=new_df["B/L"].value_counts()
                wraps=[new_df[new_df["B/L"]==k]["Wrap"].unique()[0] for k in bls.keys()]
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
                    st.write(requested_shipping_file[["Lot","Lot Qty","B/L","Wrap","Ocean B/L","DryWeight","ADMT","Location","Warehouse_In","Warehouse_Out","Vehicle_Id","Release_Order_Number","Carrier_Code","BL"]])
    with admin_tab2:
        
        #st.markdown("RELEASE ORDERS") 
        
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
            sales_order_item=st.text_input("Sales Order Item")
            ocean_bill_of_lading=st.selectbox("Ocean Bill Of Lading",batch_mapping.keys())
            batch=st.text_input("Batch No",batch_mapping[ocean_bill_of_lading]["batch"],disabled=True)
            dryness=st.text_input("Dryness",batch_mapping[ocean_bill_of_lading]["dryness"],disabled=True)
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
                    temp=edit_release_order_data(to_edit,vessel,release_order_number,sales_order_item,batch,ocean_bill_of_lading,dryness,quantity,tonnage,transport_type,carrier_code)
                    st.write(f"ADDED sales order item {sales_order_item} to release order {release_order_number}!")
                else:
                    
                    temp=store_release_order_data(vessel,release_order_number,sales_order_item,batch,ocean_bill_of_lading,dryness,quantity,tonnage,transport_type,carrier_code)
                    #st.write(temp)
                storage_client = storage.Client()
                bucket = storage_client.bucket("olym_suzano")
                blob = bucket.blob(rf"release_orders/{vessel}/{release_order_number}.json")
                blob.upload_from_string(temp)
                st.write(f"Recorded Release Order - {release_order_number} for Item No: {sales_order_item}")
                
        with release_order_tab2:
            vessel=st.selectbox("SELECT VESSEL",["KIRKENES-2304"],key="other")
            files_in_folder = [i.replace(".json","") for i in list_files_in_subfolder("olym_suzano", rf"release_orders/KIRKENES-2304/")]
            requested_file=st.selectbox("ACTIVE RELEASE ORDERS",files_in_folder)
            
            nofile=0
            try:
                data=gcp_download("olym_suzano",rf"release_orders/{vessel}/{requested_file}.json")
                release_order_json = json.loads(data)
                target=release_order_json[vessel][requested_file]
                number_of_sales_orders=len(target)
                rel_col1,rel_col2,rel_col3=st.columns([2,2,2])
            except:
                nofile=1
                
            

                         
            if nofile!=1:         
                            
                targets=[i for i in target]
                with rel_col1:
                    
                    st.markdown(f"**:blue[Release Order Number] : {requested_file}**")
                    st.markdown(f"**:blue[Sales Order Item] : {targets[0]}**")
                    st.write(f"        Total Quantity-Tonnage : {target[targets[0]]['quantity']} Bales - {target[targets[0]]['tonnage']} Metric Tons")
                    st.write(f"        Ocean Bill Of Lading : {target[targets[0]]['ocean_bill_of_lading']}")
                    st.write(f"        Batch : {target[targets[0]]['batch']}")
                    st.write(f"        Bales Shipped : {target[targets[0]]['shipped']} Bales - {2*target[targets[0]]['shipped']} Metric Tons")
                    st.write(f"        Bales Remaining : {target[targets[0]]['remaining']} Bales - {2*target[targets[0]]['remaining']} Metric Tons")
                    
                with rel_col2:
                    try:
                    
                        st.markdown(f"**:blue[Release Order Number] : {requested_file}**")
                        st.markdown(f"**:blue[Sales Order Item] : {targets[1]}**")
                        st.write(f"        Total Quantity-Tonnage : {target[targets[1]]['quantity']} Bales - {target[targets[1]]['tonnage']} Metric Tons")                        
                        st.write(f"        Ocean Bill Of Lading : {target[targets[1]]['ocean_bill_of_lading']}")
                        st.write(f"        Batch : {target[targets[1]]['batch']}")
                        st.write(f"        Bales Shipped : {target[targets[1]]['shipped']} Bales - {2*target[targets[1]]['shipped']} Metric Tons")
                        st.write(f"        Bales Remaining : {target[targets[1]]['remaining']} Bales - {2*target[targets[1]]['remaining']} Metric Tons")
                        
                            
                    except:
                        pass
    
                with rel_col3:
                    try:
                    
                        st.markdown(f"**:blue[Release Order Number] : {requested_file}**")
                        st.markdown(f"**:blue[Sales Order Item] : {targets[2]}**")
                        st.write(f"        Total Quantity-Tonnage : {target[targets[2]]['quantity']} Bales - {target[targets[2]]['tonnage']} Metric Tons")
                        st.write(f"        Ocean Bill Of Lading : {target[targets[1]]['ocean_bill_of_lading']}")
                        st.write(f"        Batch : {target[targets[2]]['batch']}")
                        st.write(f"        Bales Shipped : {target[targets[2]]['shipped']} Bales - {2*target[targets[2]]['shipped']} Metric Tons")
                        st.write(f"        Bales Remaining : {target[targets[2]]['remaining']} Bales - {2*target[targets[2]]['remaining']} Metric Tons")
                        
                        
                    except:
                        pass
    
                hangisi=st.selectbox("SELECT SALES ORDER ITEM TO DISPATCH",([i for i in target]))
                dol1,dol2,dol3=st.columns([2,2,8])
                with dol1:
                                                                  
                    if st.button("DISPATCH TO WAREHOUSE",key="lala"):
                        dispatched={"vessel":vessel,"date":datetime.datetime.strftime(datetime.datetime.today()-datetime.timedelta(hours=7),"%b-%d-%Y"),
                                        "time":datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=7),"%H:%M:%S"),
                                            "release_order":requested_file,"sales_order":hangisi,"ocean_bill_of_lading":ocean_bill_of_lading,"batch":batch}
                        json_data = json.dumps(dispatched)
                        storage_client = storage.Client()
                        bucket = storage_client.bucket("olym_suzano")
                        blob = bucket.blob(rf"dispatched.json")
                        blob.upload_from_string(json_data)
                with dol2:
                    
                    if st.button("DELETE ITEM",key="lalag"):
                        data_d=gcp_download("olym_suzano",rf"release_orders/{vessel}/{release_order_number}.json")
                        to_edit_d=json.loads(data_d)
                        to_edit_d[hangisi]={}
                        st.write(to_edit)
                        
                        #json_data = json.dumps(dispatched)
                       # storage_client = storage.Client()
                      #  bucket = storage_client.bucket("olym_suzano")
                      #  blob = bucket.blob(rf"dispatched.json")
                      #  blob.upload_from_string(json_data)

            else:
                st.write("NO RELEASE ORDERS IN DATABASE")

   

##########  LOAD OUT  ##############




if select=="LOADOUT" :

    bill_mapping=gcp_download("olym_suzano","bill_mapping.json")
    bill_mapping=json.loads(bill_mapping)

    try:
        current=gcp_download("olym_suzano","dispatched.json")
        current=json.loads(current)
    #st.write(current)
        info=gcp_download("olym_suzano",rf"release_orders/{current['vessel']}/{current['release_order']}.json")
        info=json.loads(info)
        #st.write(info)
        st.markdown(rf'**Currently Working : Release Order-{current["release_order"]}  Sales Order Item-{current["sales_order"]}**')
        st.markdown(f'**Ocean Bill Of Lading : {current["ocean_bill_of_lading"]}**')
        st.markdown(rf'**Total Quantity : {info[current["vessel"]][current["release_order"]][current["sales_order"]]["quantity"]}**')
        st.markdown(rf'**Shipped : {info[current["vessel"]][current["release_order"]][current["sales_order"]]["shipped"]}**')
        st.markdown(rf'**Remaining : {info[current["vessel"]][current["release_order"]][current["sales_order"]]["remaining"]}**')
        col1, col2,col3,col4,col5= st.columns([2,2,2,2,2])
        vessel=current["vessel"]
        if info[current["vessel"]][current["release_order"]][current["sales_order"]]["transport_type"]=="TRUCK":
            medium="TRUCK"
        else:
            medium="RAIL"
        
        with col1:
        
            terminal_code=st.text_input("Terminal Code","OLYM",disabled=True)
            file_date=st.date_input("File Date",datetime.datetime.today()-datetime.timedelta(hours=7),key="file_dates",disabled=True)
            if file_date not in st.session_state:
                st.session_state.file_date=file_date
            file_time = st.time_input('FileTime', datetime.datetime.now()-datetime.timedelta(hours=7),disabled=True)
            delivery_date=st.date_input("Delivery Date",datetime.datetime.today()-datetime.timedelta(hours=7),key="delivery_date",disabled=True)
            eta_date=st.date_input("ETA Date (For Trucks same as delivery date)",delivery_date,key="eta_date",disabled=True)
            
        with col2:
            release_order_number=st.text_input("Release Order Number",current["release_order"],disabled=True,help="Release Order Number without the Item no")
            sales_order_item=st.text_input("Sales Order Item (Material Code)",current["sales_order"],disabled=True)
            ocean_bill_of_lading=st.text_input("Ocean Bill Of Lading",current["ocean_bill_of_lading"],disabled=True)
            terminal_bill_of_lading=st.text_input("Terminal Bill of Lading",info[current["vessel"]][current["release_order"]][current["sales_order"]]["bill_of_lading"],disabled=False)
                   
            frame_placeholder = st.empty()
        with col3: 
            carrier_code=st.text_input("Carrier Code",info[current["vessel"]][current["release_order"]][current["sales_order"]]["carrier_code"],disabled=True)
            transport_sequential_number=st.selectbox("Transport Sequential",["TRUCK","RAIL"],disabled=True)
            transport_type=st.selectbox("Transport Type",["TRUCK","RAIL"],disabled=True)
            vehicle_id=st.text_input("**:blue[Vehicle ID]**")
            quantity=st.number_input("**:blue[Quantity in Tons]**", min_value=1, max_value=24, value=20, step=1,  key=None, help=None, on_change=None, disabled=False, label_visibility="visible")
            
        with col4:
              
            
            
            
            load1=st.text_area("Unit No : 01",height=300)#[:-3]
            if load1 is not None:
                textsplit = load1.splitlines()
                #st.write(textsplit)
                for i,x in enumerate(textsplit):
                    #st.write(x)
                    st.text_input(f"Unit No : {i+1}",x)#[:-3]
                    
            def audit_unit(x):
                if len(x)==11:
                    st.write(bill_mapping[x[:-3]])
                    if bill_mapping[x[:-3]]!=ocean_bill_of_lading:
                        st.write("WRONG UNIT, scan another one")
            
                
            
            
            
            
         
           
        with col5:
            if load1 is not None:
                textsplit = load1.splitlines()
                #st.write(textsplit)
                for i,x in enumerate(textsplit):
                    audit_unit(x)
                    st.text_input(f"Unit No : {i+1}",x)#[:-3]
            
        gloads=[load1,load2,load3,load4,load5,load6,load7,load8,load9,load10]
        loads=[]
        for i in gloads:
            if i:
                loads.append(i)
                          
        a=datetime.datetime.strftime(file_date,"%Y%m%d")
        
        b=file_time.strftime("%H%M%S")
        c=datetime.datetime.strftime(eta_date,"%Y%m%d")
        
        #st.write(f'1HDR:{datetime.datetime.strptime(file_date,"%y%m%d")}')
        
            
        def process():
            
            line1="1HDR:"+a+b+terminal_code
            tsn="01" if medium=="TRUCK" else "02"
            
            tt="0001" if medium=="TRUCK" else "0002"
            line2="2DTD:"+release_order_number+" "*(10-len(release_order_number))+"000"+sales_order_item+a+tsn+tt+vehicle_id+" "*(20-len(vehicle_id))+str(quantity*1000)+" "*(16-len(str(quantity*1000)))+"USD"+" "*36+carrier_code+" "*(10-len(carrier_code))+bill_of_lading+" "*(50-len(bill_of_lading))+c
            loadls=[]
            if load1:
                loadl1="2DEV:"+release_order_number+" "*(10-len(release_order_number))+"000"+sales_order_item+a+tsn+load1[:-3]+" "*(10-len(load1[:-3]))+"0"*16+str(quantity*100)
                loadls.append(loadl1)
            if load2:
                loadl2="2DEV:"+release_order_number+" "*(10-len(release_order_number))+"000"+sales_order_item+a+tsn+load2[:-3]+" "*(10-len(load2[:-3]))+"0"*16+str(quantity*100)
                loadls.append(loadl2)
            if load3:
                loadl3="2DEV:"+release_order_number+" "*(10-len(release_order_number))+"000"+sales_order_item+a+tsn+load3[:-3]+" "*(10-len(load3[:-3]))+"0"*16+str(quantity*100)
                loadls.append(loadl3)
            if load4:
                loadl4="2DEV:"+release_order_number+" "*(10-len(release_order_number))+"000"+sales_order_item+a+tsn+load4[:-3]+" "*(10-len(load4[:-3]))+"0"*16+str(quantity*100)
                loadls.append(loadl4)
            if load5:
                loadl5="2DEV:"+release_order_number+" "*(10-len(release_order_number))+"000"+sales_order_item+a+tsn+load5[:-3]+" "*(10-len(load5[:-3]))+"0"*16+str(quantity*100)
                loadls.append(loadl5)
            if load6:
                loadl6="2DEV:"+release_order_number+" "*(10-len(release_order_number))+"000"+sales_order_item+a+tsn+load6[:-3]+" "*(10-len(load6[:-3]))+"0"*16+str(quantity*100)
                loadls.append(loadl6)
            if load7:
                loadl7="2DEV:"+release_order_number+" "*(10-len(release_order_number))+"000"+sales_order_item+a+tsn+load7[:-3]+" "*(10-len(load7[:-3]))+"0"*16+str(quantity*100)
                loadls.append(loadl7)
            if load8:
               loadl8="2DEV:"+release_order_number+" "*(10-len(release_order_number))+"000"+sales_order_item+a+tsn+load8[:-3]+" "*(10-len(load8[:-3]))+"0"*16+str(quantity*100)
               loadls.append(loadl8)
            if load9:
                loadl9="2DEV:"+release_order_number+" "*(10-len(release_order_number))+"000"+sales_order_item+a+tsn+load9[:-3]+" "*(10-len(load9[:-3]))+"0"*16+str(quantity*100)
                loadls.append(loadl9)
            if load10:
                loadl10="2DEV:"+release_order_number+" "*(10-len(release_order_number))+"000"+sales_order_item+a+tsn+load10[:-3]+" "*(10-len(load10[:-3]))+"0"*16+str(quantity*100)
                loadls.append(loadl10)
            number_of_units=len(loadls)+3
            end_initial="0"*(4-len(str(number_of_units)))
            end=f"9TRL:{end_initial}{number_of_units}"
            Inventory=gcp_csv_to_df("olym_suzano", "Inventory.csv")
            for i in loads:
                #st.write(i)
                try:
                      
                    Inventory.loc[Inventory["Lot"]==i,"Location"]="ON TRUCK"
                    Inventory.loc[Inventory["Lot"]==i,"Warehouse_Out"]=datetime.datetime.combine(file_date,file_time)
                    Inventory.loc[Inventory["Lot"]==i,"Vehicle_Id"]=str(vehicle_id)
                    Inventory.loc[Inventory["Lot"]==i,"Release_Order_Number"]=str(release_order_number)
                    Inventory.loc[Inventory["Lot"]==i,"Carrier_Code"]=str(carrier_code)
                    Inventory.loc[Inventory["Lot"]==i,"BL"]=str(bill_of_lading)
                except:
                    st.write("Check Unit Number,Unit Not In Inventory")
                #st.write(vehicle_id)
    
                temp=Inventory.to_csv("temp.csv")
                upload_cs_file("olym_suzano", 'temp.csv',"Inventory.csv") 
            with open(f'placeholder.txt', 'w') as f:
                f.write(line1)
                f.write('\n')
                f.write(line2)
                f.write('\n')
                
                for i in loadls:
                    
                    f.write(i)
                    f.write('\n')
    
                f.write(end)
            
                
        #try:
         #   down_button=st.download_button(label="Download EDI as TXT",on_click=process,data=output(),file_name=f'Suzano_EDI_{a}_{release_order_number}.txt')
       # except:
           # pass 
        if st.button("GENERATE BILL OF LADING"):
            generate_bill_of_lading()
        if st.button('SUBMIT EDI'):
            process()
            info[current["vessel"]][current["release_order"]][current["sales_order"]]["shipped"]=info[current["vessel"]][current["release_order"]][current["sales_order"]]["shipped"]+len(loads)
            info[current["vessel"]][current["release_order"]][current["sales_order"]]["remaining"]=info[current["vessel"]][current["release_order"]][current["sales_order"]]["remaining"]-len(loads)
            json_data = json.dumps(info)
            storage_client = storage.Client()
            bucket = storage_client.bucket("olym_suzano")
            blob = bucket.blob(rf"release_orders/{vessel}/{release_order_number}.json")
            blob.upload_from_string(json_data)
            with open('placeholder.txt', 'r') as f:
                output_text = f.read()
            st.markdown("**EDI TEXT**")
            st.text_area('', value=output_text, height=600)
            with open('placeholder.txt', 'r') as f:
                file_content = f.read()
            newline="\n"
            filename = f'Suzano_EDI_{a}_{release_order_number}'
            file_name= f'Suzano_EDI_{a}_{release_order_number}.txt'
            st.write(filename)
            subject = f'Suzano_EDI_{a}_{release_order_number}'
            body = f"EDI for Release Order Number {release_order_number} is attached.{newline}For Carrier Code:{carrier_code} and Bill of Lading: {bill_of_lading}, {len(loads)} loads were loaded to vehicle {vehicle_id}."
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
    except:
        st.title(f"**:red[NO RELEASE ORDERS DISPATCHED YET!!]**")
        st.title(f"**:red[PLEASE CHECK WITH GATEHOUSE]**")
    
            
    
            
                


        
                
if select=="INVENTORY" :
    Inventory=gcp_csv_to_df("olym_suzano", "Inventory.csv")
    
    
    dab1,dab2=st.tabs(["IN WAREHOUSE","SHIPPED"])
    df=Inventory[Inventory["Location"]=="OLYM"][["Lot","Batch","Ocean B/L","DryWeight","ADMT","Location","Warehouse_In"]]
    zf=Inventory[Inventory["Location"]=="ON TRUCK"][["Lot","Batch","Ocean B/L","DryWeight","ADMT","Release_Order_Number","Carrier_Code","BL",
                                                     "Vehicle_Id","Warehouse_In","Warehouse_Out"]]
    with dab1:
        
        st.markdown(f"**IN WAREHOUSE = {len(df)}**")
        st.markdown(f"**TOTAL SHIPPED = {len(zf)}**")
        st.markdown(f"**TOTAL OVERALL = {len(zf)+len(df)}**")
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
        #zf[["Release_Order_Number","Carrier_Code","BL","Vehicle_Id"]]=zf[["Release_Order_Number","Carrier_Code","BL","Vehicle_Id"]].astype("int")
        zf[["Release_Order_Number","Carrier_Code","BL","Vehicle_Id"]]=zf[["Release_Order_Number","Carrier_Code","BL","Vehicle_Id"]].astype("str")
        zf["Warehouse_Out"]=[datetime.datetime.strptime(j,"%Y-%m-%d %H:%M:%S") for j in zf["Warehouse_Out"]]
        filtered_zf=zf.copy()
        if date_filter:
            filtered_zf["Warehouse_Out"]=[i.date() for i in filtered_zf["Warehouse_Out"]]
            
            filtered_zf=filtered_zf[filtered_zf["Warehouse_Out"]==filter_date]
            
        dryweight_filter=st.selectbox("Filter By DryWeight",["ALL DRYWEIGHTS"]+[str(i) for i in filtered_zf["DryWeight"].unique().tolist()])
        BL_filter=st.selectbox("Filter By Bill Of Lading",["ALL BILL OF LADINGS"]+[str(i) for i in filtered_zf["BL"].unique().tolist()])
        vehicle_filter=st.selectbox("Filter By Vehicle_Id",["ALL VEHICLES"]+[str(i) for i in filtered_zf["Vehicle_Id"].unique().tolist()])
        carrier_filter=st.selectbox("Filter By Carrier_Id",["ALL CARRIERS"]+[str(i) for i in filtered_zf["Carrier_Code"].unique().tolist()])
        
        col1,col2=st.columns([2,8])
        with col1:
            st.markdown(f"**TOTAL SHIPPED = {len(zf)}**")
            st.markdown(f"**IN WAREHOUSE = {len(df)}**")
            st.markdown(f"**TOTAL OVERALL = {len(zf)+len(df)}**")
        
        st.write(BL_filter)
        if dryweight_filter!="ALL DRYWEIGHTS":
            
            filtered_zf=filtered_zf[filtered_zf["DryWeight"]==dryweight_filter]       
        if BL_filter!="ALL BILL OF LADINGS":
            #st.write("it happened")
            filtered_zf=filtered_zf[filtered_zf["BL"]==BL_filter]
        if carrier_filter!="ALL CARRIERS":
            #st.write("it happened")
            filtered_zf=filtered_zf[filtered_zf["Carrier_Code"]==carrier_filter]
        if vehicle_filter!="ALL VEHICLES":
            #st.write("it happened")
            filtered_zf=filtered_zf[filtered_zf["Vehicle_Id"]==vehicle_filter]
        with col2:
            if date_filter:
                st.markdown(f"**SHIPPED ON THIS DAY = {len(filtered_zf)}**")
        st.table(filtered_zf)
#with tab4:
#     df=gcp_csv_to_df("olym_suzano", "Inventory.csv")
#    st.write(df)
    

