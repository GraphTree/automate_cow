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

    # Load delivery data from source and get latest date
    delivery_columns = ['주문 key', '배송 key', '수취자 이름', '배송 주소', 
                       '수취자 휴대폰', '수취자 전화번호', '선착불 여부', '배송 메시지', '기록 날짜', '출고 날짜', '해당 배송회차']
    delivery_df = source_spread.sheet_to_df(sheet='배송', index=None)[delivery_columns]
    latest_date = delivery_df['기록 날짜'].max()
    delivery_df = delivery_df[delivery_df['기록 날짜'] == latest_date]

    # Load order, option and customer data with specific columns
    order_columns = ['주문 key', '고객 key', '옵션 key', '주문 수량', '주문 id', '플랫폼']
    order_df = source_spread.sheet_to_df(sheet='주문', index=None)[order_columns]
    
    option_columns = ['옵션 key', '상품 이름', '옵션 이름']
    option_df = source_spread.sheet_to_df(sheet='옵션', index=None)[option_columns]
    
    customer_columns = ['고객 key', '고객 이름', '고객 휴대폰']
    customer_df = source_spread.sheet_to_df(sheet='고객', index=None)[customer_columns]

    # Merge delivery and order data
    merge_columns_delivery_order = ['주문 key']
    merged_df = pd.merge(delivery_df, order_df, 
                        on=merge_columns_delivery_order, how='left')

    # Merge with customer data
    merge_columns_customer = ['고객 key']
    merged_df = pd.merge(merged_df, customer_df, 
                        on=merge_columns_customer, how='left')
    
    # Merge with option data to get product names
    merge_columns_option = ['옵션 key']
    merged_df = pd.merge(merged_df, option_df, 
                        on=merge_columns_option, how='left')
    
    # Create combined product name
    merged_df['상품옵션명'] = merged_df['상품 이름'] + ' |' + merged_df['옵션 이름']

    # Group by delivery key and aggregate
    grouped = merged_df.groupby('배송 key').agg({
        '주문 key': 'first',
        '고객 key': 'first',
        '수취자 이름': 'first',
        '고객 이름': 'first',
        '배송 주소': 'first',
        '수취자 휴대폰': 'first',
        '수취자 전화번호': 'first',
        '고객 휴대폰': 'first',
        '주문 수량': 'sum',
        '선착불 여부': 'first',
        '상품옵션명': lambda x: '\n'.join(sorted(list(x))),
        '배송 메시지': 'first',
        '주문 id': 'first',
        '플랫폼': 'first',
        '출고 날짜': 'first',
        '해당 배송회차': 'first'
    }).reset_index()

    # Create sort code (first letter of each product name)
    def get_sort_code(product_list):
        # Get first letters, sort them, remove duplicates and join
        # First split by newline since products are separated by \n
        products = product_list.split(' ')
        # Then remove special characters from each product and get first letter
        first_letters = []
        for product in products:
            # Remove special characters
            clean_product = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', product)
            if clean_product.strip():
                first_letters.append(clean_product[0])
        return ''.join(first_letters)

    # Add sort code column
    grouped['정렬'] = grouped['상품옵션명'].apply(get_sort_code)

    # Maintain exact order of result table columns
    result_columns = [
        '배송 key', '주문 key', '고객 key', '수취자 이름', '고객 이름', '배송 주소', 
        '수취자 휴대폰', '수취자 전화번호', '고객 휴대폰', '주문 수량', '선착불 여부', 
        '상품옵션명', '배송 메시지', '주문 id', '플랫폼', '정렬', '출고 날짜', '해당 배송회차'
    ]
    
    final_df = grouped.reindex(columns=result_columns)

    # Update destination spreadsheet by appending after last row
    try:
        existing_df = load_the_spreadsheet('배송', dest_sh)
        update_worksheet(existing_df, final_df, "배송", "배송 운영 데이터 업데이트 완료 (4/4)", dest_sh, dest_spread)
    except Exception as e:
        st.error(f"Error updating destination sheet: {str(e)}")
