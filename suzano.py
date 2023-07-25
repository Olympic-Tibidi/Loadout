import streamlit as st
import streamlit.components.v1 as components
import cv2
import numpy as np


from camera_input_live import camera_input_live
import pandas as pd
import datetime
from requests import get
from collections import defaultdict
import json
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt
#from pyzbar.pyzbar import decode
import pickle



pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.options.mode.chained_assignment = None  # default='warn'

st. set_page_config(layout="wide")
path=r"c:\Users\AfsinY\Desktop\SUZANO_"




def process_frame(frame):
    global qr_code_found, data

    # Convert the frame to grayscale
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Decode the QR codes in the frame
    qr_codes =decode(gray_frame)

    # Iterate through the detected QR codes
    for qr_code in qr_codes:
        # Extract the data and barcode type from the QR code
        data = qr_code.data.decode('utf-8')
        barcode_type = qr_code.type

        # Print the results
        #print(f"Data: {data}")
        #print(f"Barcode Type: {barcode_type}")

        # Draw a rectangle around the QR code
        x, y, w, h = qr_code.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Set the flag to indicate a QR code is found
        qr_code_found = True
        break
        
    # Display the frame with the QR codes and rectangles
    cv2.imshow('QR Code Reader', frame)
def read_barcodes(frame):
    barcodes = pyzbar.decode(frame)
    for barcode in barcodes:
        x, y , w, h = barcode.rect
        #1
        barcode_info = barcode.data.decode('utf-8')
        cv2.rectangle(frame, (x, y),(x+w, y+h), (0, 255, 0), 2)
        
        #2
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, barcode_info, (x + 6, y - 6), font, 2.0, (255, 255, 255), 1)
        #3
        with open("barcode_result.txt", mode ='w') as file:
            file.write("Recognized Barcode:" + barcode_info)
    return frame   

Inventory=pd.ExcelFile("Inventory.xlsx")
Inventory=Inventory.parse()
tab1,tab2,tab3= st.tabs(["ENTER DATA","INVENTORY","CAPTURE"])


if 'captured_units' not in st.session_state:
    st.session_state.captured_units =[]
    
    
    
with tab1:
    col1, col2,col3,col4,col5= st.columns([2,2,2,2,2])
    with col1:
    

        file_date=st.date_input("File Date",datetime.datetime.today(),key="file_dates")
        if file_date not in st.session_state:
            st.session_state.file_date=file_date
        file_time = st.time_input('FileTime', datetime.datetime.now())
        terminal_code=st.text_input("Terminal Code","OLYM")
        release_order_number=st.text_input("Release Order Number (FROM SUZANO)")
        
        if release_order_number not in st.session_state:
            st.session_state.release_order_number=release_order_number
        delivery_date=st.date_input("Delivery Date",datetime.datetime.today(),key="delivery_date")
    with col2:
        transport_sequential_number=st.selectbox("Transport Sequential",["TRUCK","RAIL"])
        transport_type=st.selectbox("Transport Type",["TRUCK","RAIL"])
        vehicle_id=st.text_input("Vehicle ID")
        quantity=st.number_input("Quantity In Tons", min_value=1, max_value=24, value=20, step=1,  key=None, help=None, on_change=None, disabled=False, label_visibility="visible")
        frame_placeholder = st.empty()
    with col3: 
        carrier_code=st.text_input("Carrier Code")
        bill_of_lading=st.text_input("Bill of Lading")
        eta_date=st.date_input("ETA Date (For Trucks same as delivery date)",delivery_date,key="eta_date")
        sales_order_item=st.text_input("Sales Order Item (Material Code)")
    with col4:
        loads = []
        for i in range(10):
            try:
                value = st.text_input(f"Unit No : {i + 1}", value=st.session_state.captured_units[i])
            except IndexError:
                value = st.text_input(f"Unit No : {i + 1}")

            loads.append(value)

            # JavaScript to move to the next textbox when 8 digits are scanned
            st.script(
                f"""
                const textBox{i} = document.querySelector('input[data-bk="{i}"]');
                if (textBox{i}) {{
                    textBox{i}.addEventListener("input", (event) => {{
                        if (event.data && event.data.length === 1) {{
                            if (event.inputType === "insertText") {{
                                textBox{i}.value = textBox{i}.value.replace(/[^0-9]/g, ''); // Remove non-numeric characters
                                if (textBox{i}.value.length === 8) {{
                                    const nextTextBox = document.querySelector('input[data-bk="{i + 1}"]');
                                    if (nextTextBox) {{
                                        nextTextBox.focus();
                                    }}
                                }}
                            }}
                        }}
                    }});
                }}
                """
            )

    # ... Your existing code ...

# Save the captured_units in the session state after updating the loads list
        st.session_state.captured_units = loads
        
        
     
       
    with col5:
        
        load6=st.text_input("Unit No : 06")
        load7=st.text_input("Unit No : 07")
        load8=st.text_input("Unit No : 08")
        load9=st.text_input("Unit No : 09")
        load10=st.text_input("Unit No : 10")
        
    loads=[load1,load2,load3,load4,load5,load6,load7,load8,load9,load10]
    
                      
    a=datetime.datetime.strftime(file_date,"%Y%m%d")
    
    b=file_time.strftime("%H%M%S")
    c=datetime.datetime.strftime(eta_date,"%Y%m%d")
    
    #st.write(f'1HDR:{datetime.datetime.strptime(file_date,"%y%m%d")}')
    def output():
        with open(fr'c:\Users\AfsinY\Desktop\SUZANO_\Suzano_EDI_{a}_{release_order_number}.txt', 'r') as f:
            output_text = f.read()
        return output_text
    def process():
        line1="1HDR:"+a+b+terminal_code
        tsn="01" if transport_sequential_number=="TRUCK" else "02"
        tt="0001" if transport_type=="TRUCK" else "0002"
        line2="2DTD:"+release_order_number+" "*(10-len(release_order_number))+sales_order_item+a+tsn+tt+vehicle_id+" "*(20-len(vehicle_id))+str(quantity*1000)+" "*(16-len(str(quantity*1000)))+"USD"+" "*36+carrier_code+" "*(10-len(carrier_code))+bill_of_lading+" "*(50-len(bill_of_lading))+c
        loadl1="2DEV:"+release_order_number+" "*(10-len(release_order_number))+sales_order_item+a+tsn+load1+" "*(10-len(load1))+"0"*16+str(quantity*100)
        loadl2="2DEV:"+release_order_number+" "*(10-len(release_order_number))+sales_order_item+a+tsn+load2+" "*(10-len(load2))+"0"*16+str(quantity*100)
        loadl3="2DEV:"+release_order_number+" "*(10-len(release_order_number))+sales_order_item+a+tsn+load3+" "*(10-len(load3))+"0"*16+str(quantity*100)
        loadl4="2DEV:"+release_order_number+" "*(10-len(release_order_number))+sales_order_item+a+tsn+load4+" "*(10-len(load4))+"0"*16+str(quantity*100)
        loadl5="2DEV:"+release_order_number+" "*(10-len(release_order_number))+sales_order_item+a+tsn+load5+" "*(10-len(load5))+"0"*16+str(quantity*100)
        loadl6="2DEV:"+release_order_number+" "*(10-len(release_order_number))+sales_order_item+a+tsn+load6+" "*(10-len(load6))+"0"*16+str(quantity*100)
        loadl7="2DEV:"+release_order_number+" "*(10-len(release_order_number))+sales_order_item+a+tsn+load7+" "*(10-len(load7))+"0"*16+str(quantity*100)
        loadl8="2DEV:"+release_order_number+" "*(10-len(release_order_number))+sales_order_item+a+tsn+load8+" "*(10-len(load8))+"0"*16+str(quantity*100)
        loadl9="2DEV:"+release_order_number+" "*(10-len(release_order_number))+sales_order_item+a+tsn+load9+" "*(10-len(load9))+"0"*16+str(quantity*100)
        loadl10="2DEV:"+release_order_number+" "*(10-len(release_order_number))+sales_order_item+a+tsn+load10+" "*(10-len(load10))+"0"*16+str(quantity*100)
        end="9TRL:0013"
        
        for i in loads:
            #st.write(i)
            try:
                
                Inventory.loc[Inventory["Unit_No"]==i,"Terminal"]="ON TRUCK"
                Inventory.loc[Inventory["Unit_No"]==i,"Warehouse_Out"]=datetime.datetime.combine(file_date,file_time)
                Inventory.loc[Inventory["Unit_No"]==i,"Vehicle_Id"]=vehicle_id
                Inventory.loc[Inventory["Unit_No"]==i,"Release_Order_Number"]=release_order_number
                Inventory.loc[Inventory["Unit_No"]==i,"Carrier_Code"]=carrier_code
                Inventory.loc[Inventory["Unit_No"]==i,"BL"]=bill_of_lading
            except:
                st.write("Check Unit Number,Unit Not In Inventory")
            #st.write(vehicle_id)
#             try:
#                 Inventory.loc[Inventory["Unit_No"]==i,"Vehicle_Id"]="LALA"#str(vehicle_id)
#                 st.write(file_date)
#             except:
#                 pass
#             
#             try:
#                 Inventory.loc[Inventory["Unit_No"]==i,"Warehouse_Out"]=file_date+file_time
#             except:
#                 st.write("couldnt find")
#                 pass
#             st.write(Inventory.loc[Inventory["Unit_No"]==i])
#             Inventory.loc[Inventory["Unit_No"]==i,"Terminal"]="TRUCK" 
#             #st.write("hi")
        #st.write(Inventory[Inventory["Unit_No"]==i])
            
        Inventory.to_excel(r"c:\Users\afsiny\Desktop\SUZANO_\Inventory.xlsx", index=False)
        with open(fr'c:\Users\AfsinY\Desktop\SUZANO_\Suzano_EDI_{a}_{release_order_number}.txt', 'w') as f:
            f.write(line1)
            f.write('\n')
            f.write(line2)
            f.write('\n') 
            f.write(loadl1)
            f.write('\n')
            f.write(loadl2)
            f.write('\n')
            f.write(loadl3)
            f.write('\n')
            f.write(loadl4)
            f.write('\n')
            f.write(loadl5)
            f.write('\n')
            f.write(loadl6)
            f.write('\n')
            f.write(loadl7)
            f.write('\n')
            f.write(loadl8)
            f.write('\n')
            f.write(loadl9)
            f.write('\n')
            f.write(loadl10)
            f.write('\n')
            f.write(end)
            
    try:
        down_button=st.download_button(label="Download EDI as TXT",on_click=process,data=output(),file_name=f'Suzano_EDI_{a}_{release_order_number}.txt')
    except:
        pass        
    if st.button('SAVE/DISPLAY EDI'):
        process()
        with open(fr'c:\Users\AfsinY\Desktop\SUZANO_\Suzano_EDI_{a}_{release_order_number}.txt', 'r') as f:
            output_text = f.read()
        st.markdown("**EDI TEXT**")
        st.text_area('', value=output_text, height=600)

        

        
            


        
                
with tab2:
    Inventory=pd.ExcelFile(r"c:\Users\afsiny\Desktop\SUZANO_\Inventory.xlsx")
    Inventory=Inventory.parse()
    dab1,dab2=st.tabs(["IN WAREHOUSE","SHIPPED"])
    df=Inventory[Inventory["Terminal"]=="POLY"][["Unit_No","Terminal","Warehouse_In"]]
    zf=Inventory[Inventory["Terminal"]=="ON TRUCK"][["Unit_No","Release_Order_Number","Carrier_Code","BL",
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
        filter_date=st.date_input("Choose Warehouse OUT Date",datetime.datetime.today(),min_value=min([i.date() for i in zf["Warehouse_Out"]]), max_value=None,disabled=st.session_state.disabled,key="filter_date")
        zf[["Release_Order_Number","Carrier_Code","BL","Vehicle_Id"]]=zf[["Release_Order_Number","Carrier_Code","BL","Vehicle_Id"]].astype("int")
        zf[["Release_Order_Number","Carrier_Code","BL","Vehicle_Id"]]=zf[["Release_Order_Number","Carrier_Code","BL","Vehicle_Id"]].astype("str")
        filtered_zf=zf.copy()
        if date_filter:
            filtered_zf["Warehouse_Out"]=[i.date() for i in filtered_zf["Warehouse_Out"]]
            filtered_zf=filtered_zf[filtered_zf["Warehouse_Out"]==filter_date]
        BL_filter=st.selectbox("Filter By Bill Of Lading",["ALL BILL OF LADINGS"]+[str(int(i)) for i in filtered_zf["BL"].unique().tolist()])
        vehicle_filter=st.selectbox("Filter By Vehicle_Id",["ALL VEHICLES"]+[str(int(i)) for i in filtered_zf["Vehicle_Id"].unique().tolist()])
        carrier_filter=st.selectbox("Filter By Carrier_Id",["ALL CARRIERS"]+[str(int(i)) for i in filtered_zf["Carrier_Code"].unique().tolist()])
        
        col1,col2=st.columns([2,8])
        with col1:
            st.markdown(f"**TOTAL SHIPPED = {len(zf)}**")
            st.markdown(f"**IN WAREHOUSE = {len(df)}**")
            st.markdown(f"**TOTAL OVERALL = {len(zf)+len(df)}**")
        
        
                
        if BL_filter!="ALL BILL OF LADINGS":
            filtered_zf=filtered_zf[filtered_zf["BL"]==BL_filter]
        if carrier_filter!="ALL CARRIERS":
            filtered_zf=filtered_zf[filtered_zf["Carrier_Code"]==carrier_filter]
        if vehicle_filter!="ALL VEHICLES":
            filtered_zf=filtered_zf[filtered_zf["Vehicle_Id"]==vehicle_filter]
        with col2:
            if date_filter:
                st.markdown(f"**SHIPPED ON THIS DAY = {len(filtered_zf)}**")
        st.table(filtered_zf)
with tab3:
    



    image = camera_input_live()

    if image is not None:
        st.image(image)
        bytes_data = image.getvalue()
        cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        detector = cv2.QRCodeDetector()
    
        data, bbox, straight_qrcode = detector.detectAndDecode(cv2_img)
    
        if data:
            st.write("# Found QR code")
            st.write(data)
            with st.expander("Show details"):
                st.write("BBox:", bbox)
                st.write("Straight QR code:", straight_qrcode)
#     st.markdown("**QR Code Reader**")
#     
#     #st.selectbox("SUBMIT FOR LOAD",[f"LOAD-{i}" for i in range(1,11)],key="for_capture")
#     
# 
#     
#     coll1,coll2,coll3=st.columns([2,2,6])
#     with coll2:
#         clear_cache=st.button("CLEAR LOAD LIST")
#         if clear_cache:
#             st.session_state.captured_units=[]
#     with coll1:
#     
#         capture_button=st.button('CAPTURE LOAD')
#         
#         frame_placeholder = st.empty()
#         if capture_button:
#             qr_code_found=False
#             while not qr_code_found:
#                 
#                 capture = cv2.VideoCapture(0)
#                 finds=0
#                 while True:
#                     
# 
#             # Read a frame from the camera
#                     ret, frame = capture.read()
# 
#                     # Check if the frame was successfully captured
#                     if not ret:
#                         break
# 
#                     # Process the frame for QR code detection
#                     process_frame(frame)
#                     frame_placeholder.image(frame, channels="BGR", caption="Camera Feed")
#                     try:
#                         if qr_code_found:
#                             finds+=1
#                     except:
#                         pass
#                        
#                     if finds>50:
#                         #print(f"UNIT NO :{data}")
#                         
#                         break
#                         st.success("CAPTURED")
#                     # Check for the 'q' key press to exit the loop
#                     if cv2.waitKey(1) & 0xFF == ord('q'):
#                         break
# 
#                     # Release the camera and close all windows
#                     capture.release()
#                     cv2.destroyAllWindows()
#                     #st.text_area('', value=data, height=200,key="lala")
#                     #unit_numbers
#                 try:
#                     st.header(f"UNIT NO: {data}")
#                     st.session_state.captured_units.append(data)
#                     
#                 except:
#                     pass
#             st.write(list(set(st.session_state.captured_units)))

