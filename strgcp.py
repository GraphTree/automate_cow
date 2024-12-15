import streamlit as st  # Streamlit for creating web apps
import pandas as pd
from gspread_pandas import Spread,Client
from google.oauth2 import service_account
from datetime import datetime  # For timestamps
import ssl
import traceback
import auction_processor as auction_p  # Renamed to avoid namespace conflict
import eleven_processor as ep
import naver_processor as naver_p  # Renamed to avoid namespace conflict 
import coupang_processor as cp
import always_processor as always_p  # Renamed to avoid namespace conflict
ssl._create_default_https_context = ssl._create_unverified_context

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes = scope)

client = Client(scope=scope, creds=credentials)
spreadsheetname = "원본 데이터"  # Name of our Google Sheet
spread = Spread(spreadsheetname, client=client)
sh = client.open(spreadsheetname)
worksheet_list = sh.worksheets()

# Initialize session state for tracking processing status if not already present
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

# File uploader
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"], key="file_uploader")

# Process the uploaded file
if uploaded_file is not None:
    try:
        filename = uploaded_file.name.lower()
        
        if '11번가' in filename:
            df = pd.read_excel(uploaded_file, header=1)
            ep.process_eleven_customer(df, sh, spread)
            ep.process_eleven_order(df, sh, spread)
            ep.process_eleven_delivery(df, sh, spread)
            st.session_state.processing_complete = True
        else:
            df = pd.read_excel(uploaded_file)
            
            if '스토어' in filename:
                naver_p.process_naver_customer(df, sh, spread)
                naver_p.process_naver_order(df, sh, spread)
                naver_p.process_naver_delivery(df, sh, spread)
                st.session_state.processing_complete = True
            elif '쿠팡' in filename:
                cp.process_coupang_customer(df, sh, spread)
                cp.process_coupang_order(df, sh, spread) 
                cp.process_coupang_delivery(df, sh, spread)
                st.session_state.processing_complete = True
            elif '올웨이즈' in filename:
                always_p.process_always_customer(df, sh, spread)
                always_p.process_always_order(df, sh, spread)
                always_p.process_always_delivery(df, sh, spread)
                st.session_state.processing_complete = True
            elif '옥션' in filename:
                auction_p.process_auction_customer(df, sh, spread)
                auction_p.process_auction_order(df, sh, spread)
                auction_p.process_auction_delivery(df, sh, spread)
                st.session_state.processing_complete = True
            else:
                st.error("Unable to determine platform from filename. Please check the file name.")
                
        if st.session_state.processing_complete:
            st.success("Processing complete! Please upload another file if needed.")
            # Reset the processing flag
            st.session_state.processing_complete = False

    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        st.error(f"Full error traceback:\n{traceback.format_exc()}")
        st.session_state.processing_complete = False
else:
    st.info("Please upload an Excel file to process")
