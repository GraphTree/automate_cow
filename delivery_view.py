import streamlit as st
import pandas as pd
from gspread_pandas import Spread, Client
from google.oauth2 import service_account
from common_processor import update_worksheet, load_the_spreadsheet
import re

def load_and_process_data():
    # Load credentials and connect to Google Sheets
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = service_account.Credentials.from_service_account_info(
                    st.secrets["gcp_service_account"], scopes = scope)
    client = Client(scope=scope, creds=credentials)
    
    # Connect to source and destination spreadsheets
    source_spread = Spread("원본 데이터", client=client)
    source_sh = client.open("원본 데이터")
    
    dest_spread = Spread("데이터 종합", client=client) 
    dest_sh = client.open("데이터 종합")

    # Load delivery data and filter for latest date
    source_delivery_df = source_spread.sheet_to_df(sheet='배송', index=None)
    latest_date = source_delivery_df['기록 날짜'].max()
    latest_delivery_df = source_delivery_df[source_delivery_df['기록 날짜'] == latest_date]

    # Load order data and filter for latest date
    source_order_df = source_spread.sheet_to_df(sheet='주문', index=None)
    latest_order_date = source_order_df['기록 날짜'].max()
    latest_order_df = source_order_df[source_order_df['기록 날짜'] == latest_order_date]

    # Create base_data by merging delivery and order
    merged_delivery_order_df = pd.merge(latest_delivery_df, latest_order_df, 
                        on='주문 key', how='left', 
                        suffixes=('', '_order'))

    # Group by delivery fields to aggregate order quantities
    grouped_delivery_df = merged_delivery_order_df.groupby([
        '배송 주소', '배송 key', '주문 key', '주문 id', '고객 key', 
        '옵션 key', '수취자 이름', '수취자 휴대폰', '수취자 전화번호',
        '선착불 여부', '배송 메시지', '출고 날짜'
    ]).agg({
        '주문 수량': lambda x: x.astype(int).sum()
    }).reset_index()

    grouped_delivery_df['해당 배송 회차'] = '1'

    st.write("base_data DataFrame:", grouped_delivery_df)

    # Load and filter customer data
    source_customer_df = source_spread.sheet_to_df(sheet='고객', index=None)
    merged_customer_delivery_df = pd.merge(grouped_delivery_df, source_customer_df,
                            on='고객 key', how='left')

    # Load and filter SKU related data
    source_option_sku_df = source_spread.sheet_to_df(sheet='옵션 스큐 연결', index=None)
    source_sku_df = source_spread.sheet_to_df(sheet='스큐', index=None)

    # Merge with option_sku and sku data
    merged_option_df = pd.merge(merged_customer_delivery_df, source_option_sku_df,
                       on='옵션 key', how='left')
    merged_sku_df = pd.merge(merged_option_df, source_sku_df,
                       on='SKU key', how='left')

    # Calculate SKU quantities based on order quantity
    merged_sku_df['SKU 수량'] = merged_sku_df['SKU 수량'].fillna(0).astype(int) * merged_sku_df['주문 수량'].fillna(0).astype(int)

    # Group by delivery address and SKU info to combine orders going to same address
    grouped_by_address_df = merged_sku_df.groupby(['배송 주소', 'SKU 이름']).agg({
        '배송 key': lambda x: '\n'.join(x.unique()),
        '주문 key': lambda x: '\n'.join(x.unique()), 
        '주문 id': lambda x: '\n'.join(x.unique()),
        '고객 key': 'first',
        '고객 이름': 'first',
        '고객 휴대폰': 'first',
        '수취자 이름': 'max',
        '수취자 휴대폰': 'max', 
        '수취자 전화번호': 'max',
        '선착불 여부': 'max',
        '배송 메시지': 'max',
        '플랫폼': 'max',
        '출고 날짜': 'max',
        '해당 배송 회차': 'max',
        'SKU 수량': 'sum'
    }).reset_index()

    # Sort by address and SKU quantity descending
    sorted_by_address_df = grouped_by_address_df.sort_values(['배송 주소', 'SKU 수량'], ascending=[True, False])

    # Group by all fields except SKU to aggregate SKU names and quantities
    grouped_by_fields_df = sorted_by_address_df.groupby([
        '배송 key', '주문 key', '고객 key', '수취자 이름', '고객 이름',
        '배송 주소', '수취자 휴대폰', '수취자 전화번호', '고객 휴대폰',
        '선착불 여부', '배송 메시지', '주문 id', '플랫폼',
        '출고 날짜', '해당 배송 회차'
    ]).agg({
        'SKU 이름': lambda x: '\n'.join([str(i) for i in x if pd.notna(i) and str(i).strip()]),
        'SKU 수량': lambda x: '\n'.join([str(i) for i in x if pd.notna(i) and str(i).strip()])
    }).reset_index()

    st.write("sku data DataFrame:", grouped_by_fields_df)

    # Select final columns in desired order
    ordered_delivery_df = grouped_by_fields_df[[
        '배송 key', '주문 key', '고객 key', '수취자 이름', '고객 이름',
        '배송 주소', '수취자 휴대폰', '수취자 전화번호', '고객 휴대폰',
        '선착불 여부', 'SKU 이름', 'SKU 수량', '배송 메시지',
        '주문 id', '플랫폼', '출고 날짜', '해당 배송 회차'
    ]]

    # Create sort code (first letter of each product name)
    def get_sort_code(product_list):
        # Get first letter of each product in the list
        if not product_list or not isinstance(product_list, str):
            return ''
        
        # Split into separate products
        products = product_list.split('\n')
        
        # Get first letter of each product
        first_letters = []
        for product in products:
            clean_product = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', product)
            if clean_product.strip():
                first_letters.append(clean_product[0])
                
        # Combine all first letters
        return ''.join(first_letters) if first_letters else ''

    # Add sort code column
    ordered_delivery_df['정렬'] = ordered_delivery_df['SKU 이름'].apply(get_sort_code)
    # Replace all NaN values with empty string for all columns
    final_delivery_df = ordered_delivery_df.fillna('').replace('nan', '')

    st.write("result_df DataFrame:", final_delivery_df)

    # Update destination spreadsheet by appending after last row
    try:
        dest_delivery_df = load_the_spreadsheet('배송', dest_sh)
        update_worksheet(dest_delivery_df, final_delivery_df, "배송", "배송 운영 데이터 업데이트 완료 (4/4)", dest_sh, dest_spread)
    except Exception as e:
        st.error(f"Error updating destination sheet: {str(e)}")
