import streamlit as st
import pandas as pd
from gspread_pandas import Spread, Client
from google.oauth2 import service_account
from common_processor import update_worksheet, load_the_spreadsheet
import re

def get_latest_data(spread, sheet_name, date_col='기록 날짜'):
    """Load data from sheet and filter for latest date"""
    df = spread.sheet_to_df(sheet=sheet_name, index=None)
    latest_date = df[date_col].max()
    return df[df[date_col] == latest_date]

def merge_and_group_delivery_data(delivery_df, order_df):
    """Merge delivery and order data and group by delivery fields"""
    # Merge delivery and order data
    merged_df = pd.merge(delivery_df, order_df,
                        on='주문 key', how='left',
                        suffixes=('', '_order'))

    # Group by delivery fields
    grouped_df = merged_df.groupby([
        '배송 주소', '배송 key', '주문 key', '주문 id', '고객 key',
        '옵션 key', '수취자 이름', '수취자 휴대폰', '수취자 전화번호', 
        '선착불 여부', '배송 메시지', '출고 날짜'
    ]).agg({
        '주문 수량': lambda x: x.astype(int).sum()
    }).reset_index()

    grouped_df['해당 배송 회차'] = '1'
    return grouped_df

def process_sku_data(df, option_sku_df, sku_df):
    """Process and merge SKU related data"""
    # Merge with option_sku and sku data
    merged_df = pd.merge(df, option_sku_df, on='옵션 key', how='left')
    merged_df = pd.merge(merged_df, sku_df, on='SKU key', how='left')

    # Calculate SKU quantities
    merged_df['SKU 수량'] = merged_df['SKU 수량'].fillna(0).astype(int) * merged_df['주문 수량'].fillna(0).astype(int)
    return merged_df

def group_by_address(df):
    """Group data by delivery address"""
    grouped_df = df.groupby(['배송 주소', 'SKU 이름']).agg({
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

    return grouped_df.sort_values(['배송 주소', 'SKU 이름'], ascending=[True, False])

def get_sort_code(product_list):
    """Create sort code from first letter of each product name"""
    if not product_list or not isinstance(product_list, str):
        return ''
    
    products = product_list.split('\n')
    first_letters = []
    for product in products:
        clean_product = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', product)
        if clean_product.strip():
            first_letters.append(clean_product[0])
            
    return ''.join(first_letters) if first_letters else ''

def load_and_process_data():
    # Set up Google Sheets connection
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = service_account.Credentials.from_service_account_info(
                    st.secrets["gcp_service_account"], scopes = scope)
    client = Client(scope=scope, creds=credentials)
    
    # Connect to spreadsheets
    source_spread = Spread("원본 데이터", client=client)
    source_sh = client.open("원본 데이터")
    dest_spread = Spread("데이터 종합", client=client)
    dest_sh = client.open("데이터 종합")

    # Get latest data
    latest_delivery_df = get_latest_data(source_spread, '배송')
    latest_order_df = get_latest_data(source_spread, '주문')
    
    # Process delivery data
    grouped_delivery_df = merge_and_group_delivery_data(latest_delivery_df, latest_order_df)
    st.write("base_data DataFrame:", grouped_delivery_df)

    # Load and merge customer data
    source_customer_df = source_spread.sheet_to_df(sheet='고객', index=None)
    merged_customer_df = pd.merge(grouped_delivery_df, source_customer_df, 
                                on='고객 key', how='left')

    # Load and process SKU data
    source_option_sku_df = source_spread.sheet_to_df(sheet='옵션 스큐 연결', index=None)
    source_sku_df = source_spread.sheet_to_df(sheet='스큐', index=None)
    merged_sku_df = process_sku_data(merged_customer_df, source_option_sku_df, source_sku_df)

    # Group by address
    grouped_by_address_df = group_by_address(merged_sku_df)

    # Final grouping and column selection
    final_columns = [
        '배송 key', '주문 key', '고객 key', '수취자 이름', '고객 이름',
        '배송 주소', '수취자 휴대폰', '수취자 전화번호', '고객 휴대폰',
        '선착불 여부', '배송 메시지', '주문 id', '플랫폼',
        '출고 날짜', '해당 배송 회차'
    ]

    grouped_by_fields_df = grouped_by_address_df.groupby(final_columns).agg({
        'SKU 이름': lambda x: '\n'.join([str(i) for i in x if pd.notna(i) and str(i).strip()]),
        'SKU 수량': lambda x: '\n'.join([str(i) for i in x if pd.notna(i) and str(i).strip()])
    }).reset_index()

    st.write("sku data DataFrame:", grouped_by_fields_df)

    # Prepare final delivery DataFrame
    final_columns = final_columns + ['SKU 이름', 'SKU 수량']
    ordered_delivery_df = grouped_by_fields_df[final_columns]
    ordered_delivery_df['정렬'] = ordered_delivery_df['SKU 이름'].apply(get_sort_code)
    final_delivery_df = ordered_delivery_df.fillna('').replace('nan', '')
    # Reorder columns to match final_columns list and drop the 'sort' column that was temporarily used
    final_delivery_df = final_delivery_df[final_columns]

    st.write("result_df DataFrame:", final_delivery_df)

    # Update destination spreadsheet
    try:
        dest_delivery_df = load_the_spreadsheet('배송', dest_sh)
        update_worksheet(dest_delivery_df, final_delivery_df, "배송", 
                        "배송 운영 데이터 업데이트 완료 (4/4)", dest_sh, dest_spread)
    except Exception as e:
        st.error(f"Error updating destination sheet: {str(e)}")
