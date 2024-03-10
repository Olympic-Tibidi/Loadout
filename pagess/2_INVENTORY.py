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
