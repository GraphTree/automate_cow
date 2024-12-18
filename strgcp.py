import streamlit as st  # Streamlit for creating web apps
import pandas as pd
from gspread_pandas import Spread, Client
from google.oauth2 import service_account
from datetime import datetime  # For timestamps
import ssl
import traceback
import auction_processor as auction_p  # Renamed to avoid namespace conflict
import eleven_processor as ep
import naver_processor as naver_p  # Renamed to avoid namespace conflict 
import coupang_processor as cp
import always_processor as always_p  # Renamed to avoid namespace conflict
from common_processor import read_naver_excel
from delivery_view import load_and_process_data
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

# Platform selection dropdown
platform = st.selectbox(
    "Select Platform",
    ["11번가", "네이버/스토어", "쿠팡", "올웨이즈", "옥션/지마켓"]
)

# File uploader
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"], key="file_uploader")

# Process the uploaded file
if uploaded_file is not None:
    try:        
        
        if platform == "11번가":
            df = pd.read_excel(uploaded_file, header=1)
            ep.process_eleven_customer(df, sh, spread)
            ep.process_eleven_order(df, sh, spread)
            ep.process_eleven_delivery(df, sh, spread)
            st.session_state.processing_complete = True
            
        elif platform == "네이버/스토어":
            df = read_naver_excel()
            naver_p.process_naver_customer(df, sh, spread)
            naver_p.process_naver_order(df, sh, spread)
            naver_p.process_naver_delivery(df, sh, spread)
            st.session_state.processing_complete = True
            
        elif platform == "쿠팡":
            df = pd.read_excel(uploaded_file)
            cp.process_coupang_customer(df, sh, spread)
            cp.process_coupang_order(df, sh, spread) 
            cp.process_coupang_delivery(df, sh, spread)
            st.session_state.processing_complete = True
            
        elif platform == "올웨이즈":
            df = pd.read_excel(uploaded_file)
            always_p.process_always_customer(df, sh, spread)
            always_p.process_always_order(df, sh, spread)
            always_p.process_always_delivery(df, sh, spread)
            st.session_state.processing_complete = True
            
        elif platform == "옥션/지마켓":
            df = pd.read_excel(uploaded_file)
            auction_p.process_auction_customer(df, sh, spread)
            auction_p.process_auction_order(df, sh, spread)
            auction_p.process_auction_delivery(df, sh, spread)
            st.session_state.processing_complete = True
            
        if st.session_state.processing_complete:
            load_and_process_data()
            st.success("Processing complete! Please upload another file if needed.")
            # Reset the processing flag
            st.session_state.processing_complete = False

    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        st.error(f"Full error traceback:\n{traceback.format_exc()}")
        st.session_state.processing_complete = False
else:
    st.info("Please upload an Excel file to process")
