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

labor_issue=False
secondary=True

if secondary:
    pma_rates=gcp_download(target_bucket,rf"pma_dues.json")
    pma_rates=json.loads(pma_rates)
    assessment_rates=gcp_download(target_bucket,rf"occ_codes2023.json")
    assessment_rates=json.loads(assessment_rates)
    lab_tab1,lab_tab2,lab_tab3,lab_tab4=st.tabs(["LABOR TEMPLATE", "JOBS","RATES","LOOKUP"])

    with lab_tab4:
        itsreadytab4=True
        if itsreadytab4:
            
            def dfs_sum(dictionary, key):
                total_sum = 0
            
                for k, v in dictionary.items():
                    if k == key:
                        total_sum += v
                    elif isinstance(v, dict):
                        total_sum += dfs_sum(v, key)
            
                return total_sum
            mt_jobs_=gcp_download(target_bucket,rf"mt_jobs.json")
            mt_jobs=json.loads(mt_jobs_)
            c1,c2,c3=st.columns([2,2,6])
            with c1:
                with st.container(border=True):
                    by_year=st.selectbox("SELECT YEAR",mt_jobs.keys())
                    by_job=st.selectbox("SELECT JOB",mt_jobs[by_year].keys())
                    by_date=st.selectbox("SELECT DATE",mt_jobs[by_year][by_job]["RECORDS"].keys())
                    by_shift=st.selectbox("SELECT SHIFT",mt_jobs[by_year][by_job]["RECORDS"][by_date].keys())
                    
            with c2:
                info=mt_jobs[by_year][by_job]["INFO"]
                st.dataframe(info)
            with c3:
                with st.container(border=True):
                    
                    d1,d2,d3=st.columns([4,4,2])
                    with d1:
                        by_choice=st.radio("SELECT INVOICE",["LABOR","EQUIPMENT","MAINTENANCE"])
                    with d2:
                        by_location=st.radio("SELECT INVOICE",["DOCK","WAREHOUSE","LINES"])
                with st.container(border=True):
                    e1,e2,e3=st.columns([4,4,2])
                    with e1:
                        st.write(f"TOTAL {by_location}-{by_choice} COST for this SHIFT :  ${round(dfs_sum(mt_jobs[by_year][by_job]['RECORDS'][by_date][by_shift][by_choice][by_location],'TOTAL COST'),2)}")
                        st.write(f"TOTAL {by_location}-{by_choice} MARKUP for this SHIFT :  ${round(dfs_sum(mt_jobs[by_year][by_job]['RECORDS'][by_date][by_shift][by_choice][by_location],'Mark UP'),2)}")
                        if by_choice=="LABOR":
                            st.write(f"TOTAL {by_location}-{by_choice} INVOICE for this SHIFT :  ${round(dfs_sum(mt_jobs[by_year][by_job]['RECORDS'][by_date][by_shift][by_choice][by_location],'INVOICE'),2)}")
                        else:
                            st.write(f"TOTAL {by_location}-{by_choice} INVOICE for this SHIFT :  ${round(dfs_sum(mt_jobs[by_year][by_job]['RECORDS'][by_date][by_shift][by_choice][by_location],f'{by_choice} INVOICE'),2)}")
                    with e2:
                        st.write(f"TOTAL {by_location}-{by_choice} COST for this JOB :  ${round(sum([sum([dfs_sum(mt_jobs[by_year][by_job]['RECORDS'][date][shift][by_choice][by_location],'TOTAL COST') for shift in mt_jobs[by_year][by_job]['RECORDS'][date]]) for date in mt_jobs[by_year][by_job]['RECORDS']]),2) }")
                        st.write(f"TOTAL {by_location}-{by_choice} MARKUP for this JOB :  ${round(sum([sum([dfs_sum(mt_jobs[by_year][by_job]['RECORDS'][date][shift][by_choice][by_location],'Mark UP') for shift in mt_jobs[by_year][by_job]['RECORDS'][date]]) for date in mt_jobs[by_year][by_job]['RECORDS']]),2) }")
                        if by_choice=="LABOR":
                            st.write(f"TOTAL {by_location}-{by_choice} INVOICE for this JOB :  ${round(sum([sum([dfs_sum(mt_jobs[by_year][by_job]['RECORDS'][date][shift][by_choice][by_location],'INVOICE') for shift in mt_jobs[by_year][by_job]['RECORDS'][date]]) for date in mt_jobs[by_year][by_job]['RECORDS']]),2) }")
                        else:
                            st.write(f"TOTAL {by_location}-{by_choice} INVOICE for this JOB :  ${round(sum([sum([dfs_sum(mt_jobs[by_year][by_job]['RECORDS'][date][shift][by_choice][by_location],f'{by_choice} INVOICE') for shift in mt_jobs[by_year][by_job]['RECORDS'][date]]) for date in mt_jobs[by_year][by_job]['RECORDS']]),2) }")
                #st.write(mt_jobs[by_year][by_job]["RECORDS"][by_date][by_shift][by_choice][by_location])
            a=pd.DataFrame(mt_jobs[by_year][by_job]["RECORDS"][by_date][by_shift][by_choice][by_location]).T
            if by_choice=="LABOR":
                try:
                    a.loc["TOTAL FOR SHIFT"]=a[["Quantity","Hours","OT","Hour Cost","OT Cost","Total Wage","Benefits","PMA Assessments","TOTAL COST","SIU","Mark UP","INVOICE"]].sum()
                except:
                    pass
            else:
                try:
                    a.loc["TOTAL FOR SHIFT"]=a[[ "Quantity","Hours","TOTAL COST","Mark UP",f"{by_choice} INVOICE"]].sum()
                except:
                    pass
            st.write(a)
                
               
            
    with lab_tab3:
        with st.container(border=True):
            
            tinker,tailor=st.columns([5,5])
            with tinker:
                select_year=st.selectbox("SELECT ILWU PERIOD",["JUL 2023","JUL 2022","JUL 2021"],key="ot1221")
            with tailor:
                select_pmayear=st.selectbox("SELECT PMA PERIOD",["JUL 2023","JUL 2022","JUL 2021"],key="ot12w21")
        
        year=select_year.split(' ')[1]
        month=select_year.split(' ')[0]
        pma_year=select_pmayear.split(' ')[1]
        pma_rates_=pd.DataFrame(pma_rates).T
        occ_codes=pd.DataFrame(assessment_rates).T
        occ_codes=occ_codes.rename_axis('Occ_Code')
        shortened_occ_codes=occ_codes.loc[["0036","0037","0055","0092","0101","0103","0115","0129","0213","0215"]]
        shortened_occ_codes=shortened_occ_codes.reset_index().set_index(["DESCRIPTION","Occ_Code"],drop=True)
        occ_codes=occ_codes.reset_index().set_index(["DESCRIPTION","Occ_Code"],drop=True)
        rates=st.checkbox("SELECT TO DISPLAY RATE TABLE FOR THE YEAR",key="iueis")
        if rates:
            
            lan1,lan2=st.columns([2,2])
            with lan1:
                st.write(occ_codes)
            with lan2:
                st.write(pma_rates[pma_year])
    with lab_tab2:
        lab_col1,lab_col2,lab_col3=st.columns([2,2,2])
        with lab_col1:
            with st.container(border=True):
                
                job_vessel=st.text_input("VESSEL",disabled=False)
                vessel_length=st.number_input("VESSEL LENGTH",step=1,disabled=False)
                job_number=st.text_input("MT JOB NO",disabled=False)
                shipper=st.text_input("SHIPPER",disabled=False)
                cargo=st.text_input("CARGO",disabled=False)
                agent=st.selectbox("AGENT",["TALON","ACGI","NORTON LILLY"],disabled=False)
                stevedore=st.selectbox("STEVEDORE",["SSA","JONES"],disabled=False)
                
                alongside_date=st.date_input("ALONGSIDE DATE",disabled=False,key="arr")
                alongside_date=datetime.datetime.strftime(alongside_date,"%Y-%m-%d")
                
                alongside_time=st.time_input("ALONGSIDE TIME",disabled=False,key="arrt")
                alongside_time=alongside_time.strftime("%H:%M")
                
                departure_date=st.date_input("DEPARTURE DATE",disabled=False,key="dep")
                departure_date=datetime.datetime.strftime(departure_date,"%Y-%m-%d")
               
                departure_time=st.time_input("DEPARTURE TIME",disabled=False,key="dept")
                departure_time=departure_time.strftime("%H:%M")
                
                
            if st.button("RECORD JOB"):
                year="2023"
                mt_jobs_=gcp_download(target_bucket,rf"mt_jobs.json")
                mt_jobs=json.loads(mt_jobs_)
                if year not in mt_jobs:
                    mt_jobs[year]={}
                if job_number not in mt_jobs[year]:
                    mt_jobs[year][job_number]={"INFO":{},"RECORDS":{}}
                mt_jobs[year][job_number]["INFO"]={"Vessel":job_vessel,"Vessel Length":vessel_length,"Cargo":cargo,
                                    "Shipper":shipper,"Agent":agent,"Stevedore":stevedore,"Alongside Date":alongside_date,
                                    "Alongside Time":alongside_time,"Departure Date":departure_date,"Departure Time":departure_time}
                mt_jobs=json.dumps(mt_jobs)
                storage_client = storage.Client()
                bucket = storage_client.bucket(target_bucket)
                blob = bucket.blob(rf"mt_jobs.json")
                blob.upload_from_string(mt_jobs)
                st.success(f"RECORDED JOB NO {job_number} ! ")
    with lab_tab1:
        equipment_tariff={"CRANE":850,"FORKLIFT":65,"TRACTOR":65,"KOMATSU":160,"GENIE MANLIFT":50,"Z135 MANLIFT":95}
        foreman=False
        with st.container(border=True):
            
            tinker,tailor=st.columns([5,5])
            with tinker:
                select_year=st.selectbox("SELECT ILWU PERIOD",["JUL 2023","JUL 2022","JUL 2021"])
            with tailor:
                select_pmayear=st.selectbox("SELECT PMA PERIOD",["JUL 2023","JUL 2022","JUL 2021"])
        
        year=select_year.split(' ')[1]
        month=select_year.split(' ')[0]
        pma_year=select_pmayear.split(' ')[1]
        pma_rates_=pd.DataFrame(pma_rates).T
        occ_codes=pd.DataFrame(assessment_rates).T
        occ_codes=occ_codes.rename_axis('Occ_Code')
        shortened_occ_codes=occ_codes.loc[["0036","0037","0055","0092","0101","0103","0115","0129","0213","0215"]]
        shortened_occ_codes=shortened_occ_codes.reset_index().set_index(["DESCRIPTION","Occ_Code"],drop=True)
        occ_codes=occ_codes.reset_index().set_index(["DESCRIPTION","Occ_Code"],drop=True)
        
        
        
        if "scores" not in st.session_state:
            st.session_state.scores = pd.DataFrame(
                {"Code": [], "Shift":[],"Quantity": [], "Hours": [], "OT": [],"Hour Cost":[],"OT Cost":[],"Total Wage":[],"Benefits":[],"PMA Assessments":[],"SIU":[],"TOTAL COST":[],"Mark UP":[],"INVOICE":[]})
        if "eq_scores" not in st.session_state:
            st.session_state.eq_scores = pd.DataFrame(
                {"Equipment": [], "Quantity":[],"Hours": [], "TOTAL COST":[],"Mark UP":[],"EQUIPMENT INVOICE":[]})
        if "maint_scores" not in st.session_state:
            st.session_state.maint_scores = pd.DataFrame(
                {"Quantity":[2],"Hours": [8], "TOTAL COST":[1272],"Mark UP":[381.6],"MAINTENANCE INVOICE":[1653.6]})
        if "maint" not in st.session_state:
            st.session_state.maint=False
        
        ref={"DAY":["1ST","1OT"],"NIGHT":["2ST","2OT"],"WEEKEND":["2OT","2OT"],"HOOT":["3ST","3OT"]}
        
        def equip_scores():
            equipment=st.session_state.equipment
            equipment_qty=st.session_state.eqqty
            equipment_hrs=st.session_state.eqhrs
            equipment_cost=equipment_qty*equipment_hrs*equipment_tariff[equipment]
            equipment_markup=equipment_cost*st.session_state.markup/100
            eq_score=pd.DataFrame({ "Equipment": [equipment],
                    "Quantity": [equipment_qty],
                    "Hours": [equipment_hrs*equipment_qty],
                    "TOTAL COST":equipment_cost,
                    "Mark UP":[round(equipment_markup,2)],
                    "EQUIPMENT INVOICE":[round(equipment_cost+equipment_markup,2)]})
            st.session_state.eq_scores = pd.concat([st.session_state.eq_scores, eq_score], ignore_index=True)
       
        def new_scores():
            
            if num_code=='0129':
                foreman=True
            else:
                foreman=False
            
            pension=pma_rates[pma_year]["LS_401k"]
            if foreman:
                pension=pma_rates[pma_year]["Foreman_401k"]
                         
            
            qty=st.session_state.qty
            total_hours=st.session_state.hours+st.session_state.ot
            hour_cost=st.session_state.hours*occ_codes.loc[st.session_state.code,ref[st.session_state.shift][0]]
            ot_cost=st.session_state.ot*occ_codes.loc[st.session_state.code,ref[st.session_state.shift][1]]
            wage_cost=hour_cost+ot_cost
            benefits=wage_cost*0.062+wage_cost*0.0145+wage_cost*0.0021792                 #+wage_cost*st.session_state.siu/100
            
            assessments=total_hours*pma_rates[pma_year]["Cargo_Dues"]+total_hours*pma_rates[pma_year]["Electronic_Input"]+total_hours*pma_rates[pma_year]["Benefits"]+total_hours*pension
            total_cost=wage_cost+benefits+assessments
            siu_choice=wage_cost*st.session_state.siu/100
            
            with_siu=total_cost+siu_choice
            markup=with_siu*st.session_state.markup/100   ##+benefits*st.session_state.markup/100+assessments*st.session_state.markup/100
            if foreman:
                markup=with_siu*st.session_state.f_markup/100  ###+benefits*st.session_state.f_markup/100+assessments*st.session_state.f_markup/100
            invoice=total_cost+markup
            
            
            new_score = pd.DataFrame(
                {
                    "Code": [st.session_state.code],
                    "Shift": [st.session_state.shift],
                    "Quantity": [st.session_state.qty],
                    "Hours": [st.session_state.hours*qty],
                    "OT": [st.session_state.ot*qty],
                    "Hour Cost": [hour_cost*qty],
                    "OT Cost": [ot_cost*qty],
                    "Total Wage": [round(wage_cost*qty,2)],
                    "Benefits":[round(benefits*qty,2)],
                    "PMA Assessments":[round(assessments*qty,2)],
                    "TOTAL COST":[round(total_cost*qty,2)],
                    "SIU":[round(siu_choice*qty,2)],
                    "Mark UP":[round(markup*qty,2)],
                    "INVOICE":[round(invoice*qty,2)]
                    
                }
            )
            st.session_state.scores = pd.concat([st.session_state.scores, new_score], ignore_index=True)
            
            
     
        
            
        # Form for adding a new score
        
        with st.form("new_score_form"):
            st.write("##### LABOR")
            form_col1,form_col2,form_col3=st.columns([3,3,4])
            with form_col1:
                
                st.session_state.siu=st.number_input("ENTER SIU (UNEMPLOYMENT) PERCENTAGE",step=1,key="kdsha")
                st.session_state.markup=st.number_input("ENTER MARKUP",step=1,key="wer")
                st.session_state.f_markup=st.number_input("ENTER FOREMAN MARKUP",step=1,key="wfder")
                
            with form_col2:
                st.session_state.shift=st.selectbox("SELECT SHIFT",["DAY","NIGHT","WEEKEND DAY","WEEKEND NIGHT","HOOT"])
                st.session_state.shift_record=st.session_state.shift
                st.session_state.shift="WEEKEND" if st.session_state.shift in ["WEEKEND DAY","WEEKEND NIGHT"] else st.session_state.shift
            
                # Dropdown for selecting Code
                st.session_state.code = st.selectbox(
                    "Occupation Code", options=list(shortened_occ_codes.index)
                )
                # Number input for Quantity
                st.session_state.qty = st.number_input(
                    "Quantity", step=1, value=0, min_value=0
            )
            with form_col3:
                
                # Number input for Hours
                st.session_state.hours = st.number_input(
                    "Hours", step=0.5, value=0.0, min_value=0.0
                )
            
                # Number input for OT
                st.session_state.ot = st.number_input(
                    "OT", step=1, value=0, min_value=0
                )
                
                # Form submit button
                submitted = st.form_submit_button("Submit")
            # If form is submitted, add the new score
        
        if submitted:
            num_code=st.session_state.code[1].strip()
            new_scores()
            st.success("Rank added successfully!")
        
        
        with st.form("equipment_form"):
            st.write("##### EQUIPMENT")
            eqform_col1,eqform_col2,eqform_col3=st.columns([3,3,4])
            with eqform_col1: 
                st.session_state.equipment = st.selectbox(
                    "Equipment", options=["CRANE","FORKLIFT","TRACTOR","KOMATSU","GENIE MANLIFT","Z135 MANLIFT"],key="sds11")
            with eqform_col2:
                # Number input for Equipment Quantity
                st.session_state.eqqty = st.number_input(
                    "Equipment Quantity", key="sds",step=1, value=0, min_value=0)
            with eqform_col3:
                st.session_state.eqhrs = st.number_input(
                    "Equipment Hours",key="sdsss", step=1, value=0, min_value=0)
                eq_submitted = st.form_submit_button("Submit Equipment")
        if eq_submitted:
            equip_scores()
            st.success("Equipment added successfully!")
        
            
        with st.container(border=True):
            
            sub_col1,sub_col2,sub_col3=st.columns([3,3,4])
            with sub_col1:
                pass
            with sub_col2:
                template_check=st.checkbox("LOAD FROM TEMPLATE")
                if template_check:
                    with sub_col3:
                        template_choice_valid=False
                        template_choice=st.selectbox("Select Recorded Template",["Pick From List"]+[i for i in list_files_in_subfolder(target_bucket, rf"labor_templates/")],
                                                      label_visibility="collapsed")
                        if template_choice!="Pick From List":
                            template_choice_valid=True 
                        if template_choice_valid:
                            loaded_template=gcp_csv_to_df(target_bucket,rf"labor_templates/{template_choice}")
                    
                    
           
       
            display=pd.DataFrame(st.session_state.scores)
            display.loc["TOTAL FOR SHIFT"]=display[["Quantity","Hours","OT","Hour Cost","OT Cost","Total Wage","Benefits","PMA Assessments","TOTAL COST","SIU","Mark UP","INVOICE"]].sum()
            display=display[["Code","Shift","Quantity","Hours","OT","Hour Cost","OT Cost","Total Wage","Benefits","PMA Assessments","TOTAL COST","SIU","Mark UP","INVOICE"]]
            display.rename(columns={"SIU":f"%{st.session_state.siu} SIU"},inplace=True)
            eq_display=pd.DataFrame(st.session_state.eq_scores)
            eq_display.loc["TOTAL FOR SHIFT"]=eq_display[[ "Quantity","Hours","TOTAL COST","Mark UP","EQUIPMENT INVOICE"]].sum()
            if template_check and template_choice_valid:
                st.dataframe(loaded_template)
            else:
                st.write("##### LABOR")
                st.dataframe(display)
                part1,part2=st.columns([5,5])
                with part1:
                    st.write("##### EQUIPMENT")
                    st.dataframe(eq_display)
                maint1,maint2,maint3=st.columns([2,2,6])
                st.session_state.maint=False
                with maint1:
                    st.write("##### MAINTENANCE (IF NIGHT/WEEKEND SHIFT)")
                with maint2:
                    maint=st.checkbox("Check to add maint crew")
                if maint:
                    st.session_state.maint=True
                    st.dataframe(st.session_state.maint_scores)
                else:
                    st.session_state.maint=False
                with part2:
                    subpart1,subpart2,subpart3=st.columns([3,3,4])
                    with subpart1:
                        with st.container(border=True):
                            st.write(f"###### COSTS")
                            st.write(f"###### LABOR: {round(display.loc['TOTAL FOR SHIFT','TOTAL COST'],2)}")
                            st.write(f"###### EQUIPMENT: {round(eq_display.loc['TOTAL FOR SHIFT','TOTAL COST'],2)}")
                            if st.session_state.maint:
                                st.write(f"###### MAINTENANCE: {round(st.session_state.maint_scores['TOTAL COST'].values[0],2)}")
                                st.write(f"##### TOTAL: {round(display.loc['TOTAL FOR SHIFT','TOTAL COST']+eq_display.loc['TOTAL FOR SHIFT','TOTAL COST']+st.session_state.maint_scores['TOTAL COST'].values[0],2)}")
                            else:
                                st.write(f"##### TOTAL: {round(display.loc['TOTAL FOR SHIFT','TOTAL COST']+eq_display.loc['TOTAL FOR SHIFT','TOTAL COST'],2)}")

                    with subpart2:
                        with st.container(border=True):
                            st.write(f"###### MARKUPS")
                            st.write(f"###### LABOR: {round(display.loc['TOTAL FOR SHIFT','Mark UP'],2)}")
                            st.write(f"###### EQUIPMENT: {round(eq_display.loc['TOTAL FOR SHIFT','Mark UP'],2)}")
                            if st.session_state.maint:
                                st.write(f"###### MAINTENANCE: {round(st.session_state.maint_scores['Mark UP'].values[0],2)}")
                                st.write(f"##### TOTAL: {round(display.loc['TOTAL FOR SHIFT','Mark UP']+eq_display.loc['TOTAL FOR SHIFT','Mark UP']+st.session_state.maint_scores['Mark UP'].values[0],2)}")
                            else:
                                st.write(f"##### TOTAL: {round(display.loc['TOTAL FOR SHIFT','Mark UP']+eq_display.loc['TOTAL FOR SHIFT','Mark UP'],2)}")

                    with subpart3:
                        with st.container(border=True):
                            st.write(f"###### TOTALS")
                            st.write(f"###### TOTAL LABOR: {round(display.loc['TOTAL FOR SHIFT','INVOICE'],2)}")
                            st.write(f"###### TOTAL EQUIPMENT: {round(eq_display.loc['TOTAL FOR SHIFT','EQUIPMENT INVOICE'],2)}")
                            if st.session_state.maint:
                                st.write(f"###### TOTAL MAINTENANCE: {round(st.session_state.maint_scores['MAINTENANCE INVOICE'].values[0],2)}")
                                st.write(f"##### TOTAL INVOICE: {round(display.loc['TOTAL FOR SHIFT','INVOICE']+eq_display.loc['TOTAL FOR SHIFT','EQUIPMENT INVOICE']+st.session_state.maint_scores['MAINTENANCE INVOICE'].values[0],2)}")
                            else:
                                st.write(f"##### TOTAL INVOICE: {round(display.loc['TOTAL FOR SHIFT','INVOICE']+eq_display.loc['TOTAL FOR SHIFT','EQUIPMENT INVOICE'],2)}")
                                    
                
                    
               
        clear1,clear2,clear3=st.columns([2,2,4])
        with clear1:
            if st.button("CLEAR LABOR TABLE"):
                try:
                    st.session_state.scores = pd.DataFrame(
                    {"Code": [], "Shift":[],"Quantity": [], "Hours": [], "OT": [],"Hour Cost":[],"OT Cost":[],
                     "Total Wage":[],"Benefits":[],"PMA Assessments":[],"SIU":[],"TOTAL COST":[],"Mark UP":[],"INVOICE":[]})
                    st.rerun()
                except:
                    pass
        with clear2:
            if st.button("CLEAR EQUIPMENT TABLE",key="54332dca"):
                try:
                   st.session_state.eq_scores = pd.DataFrame({"Equipment": [], "Quantity":[],"Hours": [], "TOTAL COST":[],"Mark UP":[],"EQUIPMENT INVOICE":[]})
                   st.rerun()
                except:
                    pass
        
        csv=convert_df(display)
        file_name=f'Gang_Cost_Report-{datetime.datetime.strftime(datetime.datetime.now(),"%m-%d,%Y")}.csv'
        down_col1,down_col2,down_col3,down_col4=st.columns([2,2,2,4])
        with down_col1:
            #st.write(" ")
            filename=st.text_input("Name the Template",key="7dr3")
            template=st.button("SAVE AS TEMPLATE",key="srfqw")
            if template:
                temp=display.to_csv(index=False)
                storage_client = storage.Client()
                bucket = storage_client.bucket(target_bucket)
                
                # Upload CSV string to GCS
                blob = bucket.blob(rf"labor_templates/{filename}.csv")
                blob.upload_from_string(temp, content_type="text/csv")
        with down_col2:
            mt_jobs_=gcp_download(target_bucket,rf"mt_jobs.json")
            mt_jobs=json.loads(mt_jobs_)
            #st.write(st.session_state.scores.T.to_dict())
            job_no=st.selectbox("SELECT JOB NO",[i for i in mt_jobs["2023"]])
            year="2023"
            work_type=st.selectbox("SELECT JOB NO",["DOCK","WAREHOUSE","LINES"])
            work_date=st.date_input("Work Date",datetime.datetime.today()-datetime.timedelta(hours=utc_difference),key="work_date")
            record=st.button("RECORD TO JOB",key="srfqwdsd")
            if record:
                
                if year not in mt_jobs:
                    mt_jobs[year]={}
                if job_no not in mt_jobs[year]:
                    mt_jobs[year][job_no]={}
                if "RECORDS" not in mt_jobs[year][job_no]:
                    mt_jobs[year][job_no]["RECORDS"]={}
                if str(work_date) not in mt_jobs[year][job_no]["RECORDS"]:
                    mt_jobs[year][job_no]["RECORDS"][str(work_date)]={}
                if st.session_state.shift_record not in mt_jobs[year][job_no]["RECORDS"][str(work_date)]:
                    mt_jobs[year][job_no]["RECORDS"][str(work_date)][st.session_state.shift_record]={}
                if "LABOR" not in mt_jobs[year][job_no]["RECORDS"][str(work_date)][st.session_state.shift_record]:
                    mt_jobs[year][job_no]["RECORDS"][str(work_date)][st.session_state.shift_record]["LABOR"]={"DOCK":{},"LINES":{},"WAREHOUSE":{}}
                if 'EQUIPMENT' not in mt_jobs[year][job_no]["RECORDS"][str(work_date)][st.session_state.shift_record]:
                    mt_jobs[year][job_no]["RECORDS"][str(work_date)][st.session_state.shift_record]["EQUIPMENT"]={"DOCK":{},"LINES":{},"WAREHOUSE":{}}
                if 'MAINTENANCE' not in mt_jobs[year][job_no]["RECORDS"][str(work_date)][st.session_state.shift_record]:
                    mt_jobs[year][job_no]["RECORDS"][str(work_date)][st.session_state.shift_record]["MAINTENANCE"]={"DOCK":{},"LINES":{},"WAREHOUSE":{}}
                mt_jobs[year][job_no]["RECORDS"][str(work_date)][st.session_state.shift_record]['LABOR'][work_type]=st.session_state.scores.T.to_dict()
                mt_jobs[year][job_no]["RECORDS"][str(work_date)][st.session_state.shift_record]['EQUIPMENT'][work_type]=st.session_state.eq_scores.T.to_dict()
                if st.session_state.maint:
                    mt_jobs[year][job_no]["RECORDS"][str(work_date)][st.session_state.shift_record]['MAINTENANCE'][work_type]=st.session_state.maint_scores.T.to_dict()
                mt_jobs_=json.dumps(mt_jobs)
                storage_client = storage.Client()
                bucket = storage_client.bucket(target_bucket)
                blob = bucket.blob(rf"mt_jobs.json")
                blob.upload_from_string(mt_jobs_)
                st.success(f"RECORDED JOB NO {job_no} ! ")
            
           
            
                                   
        
        index=st.number_input("Enter Index To Delete",step=1,key="1224aa")
        if st.button("DELETE BY INDEX"):
            try:
                st.session_state.scores=st.session_state.scores.drop(index)
                st.session_state.scores.reset_index(drop=True,inplace=True)
            except:
                pass
