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
target_bucket="olym_suzano"
utc_difference=8


admin_tab1,admin_tab2,admin_tab3,admin_tab4=st.tabs(["RELEASE ORDERS","BILL OF LADINGS","EDI'S","STORAGE"])
with admin_tab4:
    maintenance=False
    if not maintenance:
        def calculate_balance(start_tons, daily_rate, storage_rate):
            balances={}
            tons_remaining = start_tons
            accumulated=0
            day=1
            while tons_remaining>daily_rate:
                #print(day)
                balances[day]={"Remaining":tons_remaining,"Charge":0,"Accumulated":0}
                if day % 7 < 5:  # Consider only weekdays
                    tons_remaining-=daily_rate
                    #print(tons_remaining)
                    
                    balances[day]={"Remaining":tons_remaining,"Charge":0,"Accumulated":0}
        
                    # If storage free days are over, start applying storage charges
                elif day % 7 in ([5,6]):
                    balances[day]={"Remaining":tons_remaining,"Charge":0,"Accumulated":accumulated}
                if day >free_days_till:
                    charge = round(tons_remaining*storage_rate,2)  # You can adjust the storage charge after the free days
                    accumulated+=charge
                    accumulated=round(accumulated,2)
                    balances[day]={"Remaining":tons_remaining,"Charge":charge,"Accumulated":accumulated}
                
                day+=1
            return balances
            
        here1,here2,here3=st.columns([2,5,3])
        
        with here1:
            with st.container(border=True):
                initial_tons =st.number_input("START TONNAGE", min_value=1000, help=None, on_change=None,step=50, disabled=False, label_visibility="visible",key="fas2aedseq")
                daily_rate=st.slider("DAILY SHIPMENT TONNAGE",min_value=248, max_value=544, step=10,key="fdee2a")
                storage_rate = st.number_input("STORAGE RATE DAILY ($)",value=0.15, help="dsds", on_change=None, disabled=False, label_visibility="visible",key="fdee2dsdseq")
                free_days_till = st.selectbox("FREE DAYS",[15,30,45,60])
        
        with here3:
            with st.container(border=True):    
                balances = calculate_balance(initial_tons, daily_rate, storage_rate)
                d=pd.DataFrame(balances).T
                start_date = pd.to_datetime('today').date()
                end_date = start_date + pd.DateOffset(days=120)  # Adjust as needed
                date_range = pd.date_range(start=start_date, end=end_date, freq='D')
                
                d.columns=["Remaining Tonnage","Daily Charge","Accumulated Charge"]
                d.rename_axis("Days",inplace=True)
                total=round(d.loc[len(d),'Accumulated Charge'],1)
                st.dataframe(d)

        with here2:
            with st.container(border=True):     
                st.write(f"######  Cargo: {initial_tons} - Loadout Rate/Day: {daily_rate} Tons - Free Days : {free_days_till}" )
                st.write(f"##### TOTAL CHARGES:  ${total}" )
                st.write(f"##### DURATION OF LOADOUT:  {len(d)} Days")
                st.write(f"##### MONTHLY REVENUE: ${round(total/len(d)*30,1)} ")
                fig = px.bar(d, x=d.index, y="Accumulated Charge", title="Accumulated Charges Over Days")

                # Add a horizontal line for the monthly average charge
                average_charge = round(total/len(d)*30,1)
                fig.add_shape(
                    dict(
                        type="line",
                        x0=d.index.min(),
                        x1=d.index.max(),
                        y0=average_charge,
                        y1=average_charge,
                        line=dict(color="red", dash="dash"),
                    )
                )
                
                # Add annotation with the average charge value
                fig.add_annotation(
                    x=d.index.max()//3,
                    y=average_charge,
                    text=f'Monthly Average Income: <b><i>${average_charge:.2f}</b></i> ',
                    showarrow=True,
                    arrowhead=4,
                    ax=-50,
                    ay=-30,
                    font=dict(size=16),
                    bgcolor='rgba(255, 255, 255, 0.6)',
                )
                
                # Set layout options
                fig.update_layout(
                    xaxis_title="Days",
                    yaxis_title="Accumulated Charge",
                    sliders=[
                        {
                            "steps": [
                                {"args": [[{"type": "scatter", "x": d.index, "y": d["Accumulated Charge"]}], "layout"], "label": "All", "method": "animate"},
                            ],
                        }
                    ],
                )
                st.plotly_chart(fig)
        
with admin_tab2:
    bill_data=gcp_download(target_bucket,rf"terminal_bill_of_ladings.json")
    admin_bill_of_ladings=json.loads(bill_data)
    admin_bill_of_ladings=pd.DataFrame.from_dict(admin_bill_of_ladings).T[1:]
    
    def convert_df(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')
    use=True
    if use:
        now=datetime.datetime.now()-datetime.timedelta(hours=utc_difference)
        
        daily_admin_bill_of_ladings=admin_bill_of_ladings.copy()
        
        daily_admin_bill_of_ladings["Date"]=[datetime.datetime.strptime(i,"%Y-%m-%d %H:%M:%S").date() for i in admin_bill_of_ladings["issued"]]
        daily_admin_bill_of_ladings_=daily_admin_bill_of_ladings[daily_admin_bill_of_ladings["Date"]==now.date()]
        choose = st.radio(
                        "Select Today's Bill of Ladings or choose by Date or choose ALL",
                        ["DAILY", "ACCUMULATIVE", "FIND BY DATE"],key="wewas")
        if choose=="DAILY":
            st.dataframe(daily_admin_bill_of_ladings_)
            csv=convert_df(daily_admin_bill_of_ladings_)
            file_name=f'OLYMPIA_DAILY_BILL_OF_LADINGS-{datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%m-%d,%Y")}.csv'
        elif choose=="FIND BY DATE":
            required_date=st.date_input("CHOOSE DATE",key="dssar")
            filtered_daily_admin_bill_of_ladings=daily_admin_bill_of_ladings[daily_admin_bill_of_ladings["Date"]==required_date]
            
            st.dataframe(filtered_daily_admin_bill_of_ladings)
            csv=convert_df(filtered_daily_admin_bill_of_ladings)
            file_name=f'OLYMPIA_BILL_OF_LADINGS_FOR-{datetime.datetime.strftime(required_date,"%m-%d,%Y")}.csv'
        else:
            st.dataframe(admin_bill_of_ladings)
            csv=convert_df(admin_bill_of_ladings)
            file_name=f'OLYMPIA_ALL_BILL_OF_LADINGS to {datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(hours=utc_difference),"%m-%d,%Y")}.csv'

        st.download_button(
            label="DOWNLOAD BILL OF LADINGS",
            data=csv,
            file_name=file_name,
            mime='text/csv')
with admin_tab3:
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
                                                                     

                


              
with admin_tab1:
    carrier_list_=gcp_download(target_bucket,rf"carrier.json")
    carrier_list=json.loads(carrier_list_)
    junk=gcp_download(target_bucket,rf"junk_release.json")
    junk=json.loads(junk)
    mill_shipments=gcp_download(target_bucket,rf"mill_shipments.json")
    mill_shipments=json.loads(mill_shipments)
    mill_df=pd.DataFrame.from_dict(mill_shipments).T
    mill_df["Terminal Code"]=mill_df["Terminal Code"].astype(str)
    mill_df["New Product"]=mill_df["New Product"].astype(str)
    try:
        release_order_database=gcp_download(target_bucket,rf"release_orders/RELEASE_ORDERS.json")
        release_order_database=json.loads(release_order_database)
    except:
        release_order_database={}
    
  
    release_order_tab1,release_order_tab2,release_order_tab3=st.tabs(["CREATE RELEASE ORDER","RELEASE ORDER DATABASE","RELEASE ORDER STATUS"])
    with release_order_tab3:
        maintenance=False
        if not maintenance:
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
            new.index=[i for i in new.index]
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
                              xaxis=dict(tickangle=-90, type='category'))
            relcol1,relcol2=st.columns([5,5])
            #with relcol1:
            st.dataframe(new)
            #with relcol2:
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
            
    with release_order_tab1:   ###CREATE RELEASE ORDER
        #vessel=st.selectbox("SELECT VESSEL",["KIRKENES-2304","JUVENTAS-2308"])  ###-###
       
        add=st.checkbox("CHECK TO ADD TO EXISTING RELEASE ORDER",disabled=False)
        edit=st.checkbox("CHECK TO EDIT EXISTING RELEASE ORDER")
        batch_mapping=gcp_download(target_bucket,rf"batch_mapping.json")
        batch_mapping=json.loads(batch_mapping)
        if edit:
            
            release_order_number=st.selectbox("SELECT RELEASE ORDER",([i for i in [i.replace(".json","") for i in list_files_in_subfolder(target_bucket, rf"release_orders/ORDERS/")[1:]] if i not in junk]))
            to_edit=gcp_download(target_bucket,rf"release_orders/ORDERS/{release_order_number}.json")
            to_edit=json.loads(to_edit)
            po_number_edit=st.text_input("PO No",to_edit[release_order_number]["po_number"],disabled=False)
            destination_edit=st.text_input("Destination",to_edit[release_order_number]["destination"],disabled=False)
            sales_order_item_edit=st.selectbox("Sales Order Item",list(to_edit[release_order_number].keys())[2:],disabled=False)
            vessel_edit=vessel=st.selectbox("SELECT VESSEL",["KIRKENES-2304","JUVENTAS-2308","LAGUNA-3142","LYSEFJORD-2308"],key="poFpoa")
            ocean_bill_of_lading_edit=st.selectbox("Ocean Bill Of Lading",batch_mapping[vessel_edit].keys(),key="trdfeerw") 
            wrap_edit=st.text_input("Grade",to_edit[release_order_number][sales_order_item_edit]["grade"],disabled=False)
            batch_edit=st.text_input("Batch No",to_edit[release_order_number][sales_order_item_edit]["batch"],disabled=False)
            dryness_edit=st.text_input("Dryness",to_edit[release_order_number][sales_order_item_edit]["dryness"],disabled=False)
            admt_edit=st.text_input("ADMT PER UNIT",round(float(batch_mapping[vessel_edit][ocean_bill_of_lading_edit]["dryness"])/90,6),disabled=False)
            unitized_edit=st.selectbox("UNITIZED/DE-UNITIZED",["UNITIZED","DE-UNITIZED"],disabled=False)
            quantity_edit=st.number_input("Quantity of Units", 0, disabled=False, label_visibility="visible")
            tonnage_edit=2*quantity_edit
            shipped_edit=st.number_input("Shipped # of Units",to_edit[release_order_number][sales_order_item_edit]["shipped"],disabled=True)
            remaining_edit=st.number_input("Remaining # of Units",
                                           quantity_edit-to_edit[release_order_number][sales_order_item_edit]["shipped"],disabled=True)
            carrier_code_edit=st.selectbox("Carrier Code",[f"{key}-{item}" for key,item in carrier_list.items()],key="dsfdssa")          
            
        elif add:
            release_order_number=st.selectbox("SELECT RELEASE ORDER",([i for i in [i.replace(".json","") for i in list_files_in_subfolder(target_bucket, rf"release_orders/ORDERS/")][1:] if i not in junk]))
            to_add=gcp_download(target_bucket,rf"release_orders/ORDERS/{release_order_number}.json")
            to_add=json.loads(to_add)
            po_number_add=st.text_input("PO No",to_add[release_order_number]["po_number"],disabled=False)
            destination_add=st.text_input("Destination",to_add[release_order_number]["destination"],disabled=False)
            sales_order_item_add=st.text_input("Sales Order Item",disabled=False)
            vessel_add=vessel=st.selectbox("SELECT VESSEL",["KIRKENES-2304","JUVENTAS-2308","LAGUNA-3142","LYSEFJORD-2308"],key="popoa")
            ocean_bill_of_lading_add=st.selectbox("Ocean Bill Of Lading",batch_mapping[vessel_add].keys(),key="treerw")  
            wrap_add=st.text_input("Grade",batch_mapping[vessel_add][ocean_bill_of_lading_add]["grade"],disabled=True) 
            batch_add=st.text_input("Batch No",batch_mapping[vessel_add][ocean_bill_of_lading_add]["batch"],disabled=False)
            dryness_add=st.text_input("Dryness",batch_mapping[vessel_add][ocean_bill_of_lading_add]["dryness"],disabled=False)
            admt_add=st.text_input("ADMT PER UNIT",round(float(batch_mapping[vessel_add][ocean_bill_of_lading_add]["dryness"])/90,6),disabled=False)
            unitized_add=st.selectbox("UNITIZED/DE-UNITIZED",["UNITIZED","DE-UNITIZED"],disabled=False)
            quantity_add=st.number_input("Quantity of Units", 0, disabled=False, label_visibility="visible")
            tonnage_add=2*quantity_add
            shipped_add=0
            remaining_add=st.number_input("Remaining # of Units", quantity_add,disabled=True)
            transport_type_add=st.radio("Select Transport Type",("TRUCK","RAIL"))
            carrier_code_add=st.selectbox("Carrier Code",[f"{key}-{item}" for key,item in carrier_list.items()])            
        else:  ### If creating new release order
            
            release_order_number=st.text_input("Release Order Number")
            po_number=st.text_input("PO No")
            destination_list=list(set([f"{i}-{j}" for i,j in zip(mill_df["Group"].tolist(),mill_df["Final Destination"].tolist())]))
            #st.write(destination_list)
            destination=st.selectbox("SELECT DESTINATION",destination_list)
            sales_order_item=st.text_input("Sales Order Item")  
            vessel=st.selectbox("SELECT VESSEL",["KIRKENES-2304","JUVENTAS-2308","LAGUNA-3142","LYSEFJORD-2308"],key="tre")
            ocean_bill_of_lading=st.selectbox("Ocean Bill Of Lading",batch_mapping[vessel].keys())   #######
            wrap=st.text_input("Grade",batch_mapping[vessel][ocean_bill_of_lading]["grade"],disabled=True)   ##### batch mapping injection
            batch=st.text_input("Batch No",batch_mapping[vessel][ocean_bill_of_lading]["batch"],disabled=True)   #####
            dryness=st.text_input("Dryness",batch_mapping[vessel][ocean_bill_of_lading]["dryness"],disabled=True)   #####
            admt=st.text_input("ADMT PER UNIT",round(float(batch_mapping[vessel][ocean_bill_of_lading]["dryness"])/90,6),disabled=True)  #####
            unitized=st.selectbox("UNITIZED/DE-UNITIZED",["UNITIZED","DE-UNITIZED"],disabled=False)
            quantity=st.number_input("Quantity of Units", min_value=1, max_value=5000, value=1, step=1,  key=None, help=None, on_change=None, disabled=False, label_visibility="visible")
            tonnage=2*quantity
            #queue=st.number_input("Place in Queue", min_value=1, max_value=20, value=1, step=1,  key=None, help=None, on_change=None, disabled=False, label_visibility="visible")
            transport_type=st.radio("Select Transport Type",("TRUCK","RAIL"))
            carrier_code=st.selectbox("Carrier Code",[f"{key}-{item}" for key,item in carrier_list.items()])            
        

        create_release_order=st.button("SUBMIT")
        if create_release_order:
            
            if add: 
                data=gcp_download(target_bucket,rf"release_orders/ORDERS/{release_order_number}.json")
                to_edit=json.loads(data)
                temp=add_release_order_data(to_add,release_order_number,destination_add,po_number_add,sales_order_item_add,vessel_add,batch_add,ocean_bill_of_lading_add,wrap_add,dryness_add,unitized_add,quantity_add,tonnage_add,transport_type_add,carrier_code_add)
                storage_client = storage.Client()
                bucket = storage_client.bucket(target_bucket)
                blob = bucket.blob(rf"release_orders/ORDERS/{release_order_number}.json")
                blob.upload_from_string(temp)
                st.success(f"ADDED sales order item {sales_order_item_add} to release order {release_order_number}!")
            elif edit:
                data=gcp_download(target_bucket,rf"release_orders/ORDERS/{release_order_number}.json")
                to_edit=json.loads(data)
                temp=edit_release_order_data(to_edit,sales_order_item_edit,quantity_edit,tonnage_edit,shipped_edit,remaining_edit,carrier_code_edit)
                storage_client = storage.Client()
                bucket = storage_client.bucket(target_bucket)
                blob = bucket.blob(rf"release_orders/ORDERS/{release_order_number}.json")
                blob.upload_from_string(temp)
                st.success(f"Edited release order {release_order_number} successfully!")
                
            else:
                
                temp=store_release_order_data(release_order_number,destination,po_number,sales_order_item,vessel,batch,ocean_bill_of_lading,wrap,dryness,unitized,quantity,tonnage,transport_type,carrier_code)
                storage_client = storage.Client()
                bucket = storage_client.bucket(target_bucket)
                blob = bucket.blob(rf"release_orders/ORDERS/{release_order_number}.json")
                blob.upload_from_string(temp)
                st.success(f"Created release order {release_order_number} successfully!")
            
            try:
                junk=gcp_download(target_bucket,rf"release_orders/{vessel}/junk_release.json")
            except:
                junk=gcp_download(target_bucket,rf"junk_release.json")
            junk=json.loads(junk)
            try:
                del junk[release_order_number]
                jason_data=json.dumps(junk)
                storage_client = storage.Client()
                bucket = storage_client.bucket(target_bucket)
                blob = bucket.blob(rf"junk_release.json")
                blob.upload_from_string(jason_data)
            except:
                pass
            

            

            if edit:
                release_order_database[release_order_number][sales_order_item_edit]={"destination":destination_edit,"vessel":vessel_edit,"total":quantity_edit,"remaining":remaining_edit}
            elif add:
                if sales_order_item_add not in release_order_database[release_order_number]:
                    release_order_database[release_order_number][sales_order_item_add]={}
                    release_order_database[release_order_number][sales_order_item_add]={"destination":destination_add,"vessel":vessel_add,"total":quantity_add,"remaining":quantity_add}
            else:
                release_order_database[release_order_number]={}
                release_order_database[release_order_number][sales_order_item]={}
                
                release_order_database[release_order_number][sales_order_item]={"destination":destination,"vessel":vessel,"total":quantity,"remaining":quantity}
                st.write(f"Updated Release Order Database")
            
            release_orders_json=json.dumps(release_order_database)
            storage_client = storage.Client()
            bucket = storage_client.bucket(target_bucket)
            blob = bucket.blob(rf"release_orders/RELEASE_ORDERS.json")
            blob.upload_from_string(release_orders_json)
            
    with release_order_tab2:  ##   RELEASE ORDER DATABASE ##
        
        #vessel=st.selectbox("SELECT VESSEL",["KIRKENES-2304","JUVENTAS-2308"],key="other")
        rls_tab1,rls_tab2,rls_tab3=st.tabs(["ACTIVE RELEASE ORDERS","COMPLETED RELEASE ORDERS","ENTER MF NUMBERS"])
        data=gcp_download(target_bucket,rf"release_orders/RELEASE_ORDERS.json")  #################
        try:
            release_order_database=json.loads(data)
        except: 
            release_order_dictionary={}
        
        with rls_tab1:
            
            completed_release_orders=[]   #### Check if any of them are completed.
         
            
            for key in release_order_database:
                not_yet=0
                for sales in release_order_database[key]:
                    if release_order_database[key][sales]["remaining"]>0:
                        not_yet=1
                    else:
                        pass
                if not_yet==0:
                    completed_release_orders.append(key)
        
            files_in_folder_ = [i.replace(".json","") for i in list_files_in_subfolder(target_bucket, rf"release_orders/ORDERS/")]   ### REMOVE json extension from name
            
            junk=gcp_download(target_bucket,rf"junk_release.json")
            junk=json.loads(junk)
            files_in_folder=[i for i in files_in_folder_ if i not in completed_release_orders]        ###  CHECK IF COMPLETED
            files_in_folder=[i for i in files_in_folder if i not in junk.keys()]        ###  CHECK IF COMPLETED
            
            ###       Make Release order destinaiton map for dropdown menu
            
            release_order_dest_map={} 
            for i in release_order_database:
                for sales in release_order_database[i]:
                    release_order_dest_map[i]=release_order_database[i][sales]["destination"]
            destinations_of_release_orders=[f"{i} to {release_order_dest_map[i]}" for i in files_in_folder if i!=""]

            ###       Dropdown menu
            nofile=0
            requested_file_=st.selectbox("ACTIVE RELEASE ORDERS",destinations_of_release_orders)
            requested_file=requested_file_.split(" ")[0]
     
            
           
            data=gcp_download(target_bucket,rf"release_orders/ORDERS/{requested_file}.json")
            release_order_json = json.loads(data)
                
                
            target=release_order_json[requested_file]
            destination=target['destination']
            po_number=target["po_number"]
            if len(target.keys())==0:
                nofile=1
               
            number_of_sales_orders=len([i for i in target if i not in ["destination","po_number"]])   ##### WRONG CAUSE THERE IS NOW DESTINATION KEYS
        
            
            
            rel_col1,rel_col2,rel_col3,rel_col4=st.columns([2,2,2,2])
            #### DISPATCHED CLEANUP  #######
            
            try:
                dispatched=gcp_download(target_bucket,rf"dispatched.json")
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
                bucket = storage_client.bucket(target_bucket)
                blob = bucket.blob(rf"dispatched.json")
                blob.upload_from_string(json_data)
            except:
                pass
            
                
            
            
            
            ### END CLEAN DISPATCH

            
                                  
            if nofile!=1 :         
                            
                targets=[i for i in target if i not in ["destination","po_number"]] ####doing this cause we set jason path {downloadedfile[releaseorder] as target. i have to use one of the keys (release order number) that is in target list
                sales_orders_completed=[k for k in targets if target[k]['remaining']<=0]
                
                with rel_col1:
                    
                    st.markdown(f"**:blue[Release Order Number] : {requested_file}**")
                    st.markdown(f"**:blue[PO Number] : {target['po_number']}**")
                    if targets[0] in sales_orders_completed:
                        st.markdown(f"**:orange[Sales Order Item : {targets[0]} - COMPLETED]**")
                        target0_done=True
                        
                    else:
                        st.markdown(f"**:blue[Sales Order Item] : {targets[0]}**")
                    st.markdown(f"**:blue[Destination] : {target['destination']}**")
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
                
                hangisi=st.selectbox("**:green[SELECT SALES ORDER ITEM TO DISPATCH]**",([i for i in target if i not in sales_orders_completed and i not in ["destination","po_number"]]))
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
                        bucket = storage_client.bucket(target_bucket)
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
                        bucket = storage_client.bucket(target_bucket)
                        blob = bucket.blob(rf"release_orders/{vessel}/{requested_file}.json")
                        blob.upload_from_string(json_data)
                    if st.button("DELETE RELEASE ORDER ITEM!",key="laladg"):
                        junk=gcp_download(target_bucket,rf"junk_release.json")
                        junk=json.loads(junk)
                       
                        junk[requested_file]=1
                        json_data = json.dumps(junk)
                        storage_client = storage.Client()
                        bucket = storage_client.bucket(target_bucket)
                        blob = bucket.blob(rf"junk_release.json")
                        blob.upload_from_string(json_data)
                               
                with dol2:  
                    if st.button("CLEAR DISPATCH QUEUE!"):
                        dispatch={}
                        json_data = json.dumps(dispatch)
                        storage_client = storage.Client()
                        bucket = storage_client.bucket(target_bucket)
                        blob = bucket.blob(rf"dispatched.json")
                        blob.upload_from_string(json_data)
                        st.markdown(f"**CLEARED ALL DISPATCHES**")   
                with dol3:
                    dispatch=gcp_download(target_bucket,rf"dispatched.json")
                    dispatch=json.loads(dispatch)
                    try:
                        item=st.selectbox("CHOOSE ITEM",dispatch.keys())
                        if st.button("CLEAR DISPATCH ITEM"):                                       
                            del dispatch[item]
                            json_data = json.dumps(dispatch)
                            storage_client = storage.Client()
                            bucket = storage_client.bucket(target_bucket)
                            blob = bucket.blob(rf"dispatched.json")
                            blob.upload_from_string(json_data)
                            st.markdown(f"**CLEARED DISPATCH ITEM {item}**")   
                    except:
                        pass
                st.markdown("**CURRENT DISPATCH QUEUE**")
                try:
                    dispatch=gcp_download(target_bucket,rf"dispatched.json")
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
            data=gcp_download(target_bucket,rf"release_orders/RELEASE_ORDERS.json")
            completed_release_orders=[]
            for key in release_order_database:
                not_yet=0
                for sales in release_order_database[key]:
                    if release_order_database[key][sales]["remaining"]>0:
                        not_yet=1
                    else:
                        pass
                if not_yet==0:
                    completed_release_orders.append(key)
            
            #for completed in completed_release_orders:
                #st.write(completed)
                #data=gcp_download(target_bucket,rf"release_orders/ORDERS/{completed}.json")
                #comp_rel_order=json.loads(data)
            
            completed_release_order_dest_map={}
            for i in release_order_database:
                if i in completed_release_orders:
                    completed_release_order_dest_map[i]=release_order_database[i]["001"]#["destination"]
            if len(pd.DataFrame(completed_release_order_dest_map).T)>=1:
                st.write(pd.DataFrame(completed_release_order_dest_map).T)
                
                #destinations_of_completed_release_orders=[f"{i} to {completed_release_order_dest_map[i]}" for i in completed_release_orders]
                #requested_file_=st.selectbox("COMPLETED RELEASE ORDERS",destinations_of_completed_release_orders,key=16)
                #requested_file=requested_file_.split(" ")[0]
                #nofile=0
        with rls_tab3:
            mf_numbers_=gcp_download(target_bucket,rf"release_orders/mf_numbers.json")
            mf_numbers=json.loads(mf_numbers_)
            goahead=True
            if goahead:
                
                gp_release_orders=[i for i in release_order_database if release_order_database[i]["001"]["destination"] in ["GP-Clatskanie,OR","GP-Halsey,OR"] ]   # and (release_order_database[i]["001"]["remaining"]>0|release_order_database[i]["001"]["remaining"]>0)
                
                destinations_of_release_orders=[f"{i} to {release_order_dest_map[i]}" for i in release_order_database if release_order_database[i]["001"]["destination"] in ["GP-Clatskanie,OR","GP-Halsey,OR"]]
                if len(destinations_of_release_orders)==0:
                    st.warning("NO GP RELEASE ORDERS FOR THIS VESSEL")
                else:
                    
                    release_order_number_mf=st.selectbox("SELECT RELEASE ORDER FOR MF",destinations_of_release_orders,key="tatata")
                    release_order_number_mf=release_order_number_mf.split(" ")[0]
                    input_mf_numbers=st.text_area("**ENTER MF NUMBERS**",height=100,key="juy")
                    if input_mf_numbers is not None:
                        input_mf_numbers = input_mf_numbers.splitlines()
                        input_mf_numbers=[i for i in input_mf_numbers if len(i)==10]####### CAREFUL THIS ASSUMES SAME DIGIT MF EACH TIME
                   
                    if st.button("SUBMIT MF NUMBERS",key="ioeru" ):
                        if release_order_number_mf not in mf_numbers.keys():   
                            mf_numbers[release_order_number_mf]=[]
                        mf_numbers[release_order_number_mf]+=input_mf_numbers
                        mf_numbers[release_order_number_mf]=list(set(mf_numbers[release_order_number_mf]))
                        mf_data=json.dumps(mf_numbers)
                        storage_client = storage.Client()
                        bucket = storage_client.bucket(target_bucket)
                        blob = bucket.blob(rf"release_orders/mf_numbers.json")
                        blob.upload_from_string(mf_data)
                    if st.button("REMOVE MF NUMBERS",key="ioerssu" ):
                        for i in input_mf_numbers:
                            if i in mf_numbers[release_order_number_mf]:
                                mf_numbers[release_order_number_mf].remove(i)
                        mf_data=json.dumps(mf_numbers)
                        storage_client = storage.Client()
                        bucket = storage_client.bucket(target_bucket)
                        blob = bucket.blob(rf"release_orders/mf_numbers.json")
                        blob.upload_from_string(mf_data)
                    st.write(mf_numbers)
            else:
                #st.write("NO RELEASE ORDER FOR THIS VESSEL IN DATABASE")
                pass
