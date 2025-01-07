import streamlit as st
import pandas as pd
import traceback
from common_processor import load_the_spreadsheet, update_worksheet, get_delivery_date, safe_convert, clean_string

def _clean_and_filter_df(df):
    """Clean input dataframe and filter out empty order numbers"""
    if df is None:
        st.error("Please upload a file first")
        return None
        
    # Clean input data
    df = df.astype(str).apply(lambda x: x.str.strip())
    
    # Filter out rows with empty 주문아이디
    return df[df['주문아이디'] != '']

def _handle_error(e, process_name):
    """Standardized error handling"""
    st.error(f"Error processing {process_name} data: {str(e)}")
    st.error(f"Full error traceback:\n{traceback.format_exc()}")

def process_always_customer(df, sh, spread):
    """Process always customer data and update customer worksheet"""
    try:
        df = _clean_and_filter_df(df)
        if df is None:
            return
            
        # Remove duplicates based on phone number
        df = df.drop_duplicates(subset=['수령인 연락처'])
        
        customer_data = pd.DataFrame({
            '고객 key': df['수령인 연락처'] + '_올웨이즈',
            '고객 id': '',
            '고객 이름': df['수령인'],
            '고객 휴대폰': df['수령인 연락처'],
            '고객 전화번호': '',
            '플랫폼': '올웨이즈',
            '기록날짜': pd.to_datetime('now').strftime('%Y-%m-%d %H:%M:%S')
        })
        
        existing_df = load_the_spreadsheet('고객', sh)
        existing_always = existing_df[existing_df['플랫폼'] == '올웨이즈']
        
        # Filter out existing customers
        new_customer_data = customer_data[~customer_data['고객 휴대폰'].isin(existing_always['고객 휴대폰'])]
        new_customer_data = new_customer_data.sort_values('고객 이름')
        
        update_worksheet(existing_df, new_customer_data, '고객', 
                        f'{len(new_customer_data)} 명의 고객 데이터 업데이트 완료 (1/4)', sh, spread)
            
    except Exception as e:
        _handle_error(e, "customer")

def process_always_order(df, sh, spread):
    """Process always order data and update order worksheet"""
    st.write("Initial DataFrame:", df)
    
    try:
        df = _clean_and_filter_df(df)
        if df is None:
            return
            
        # Calculate total discount and sort
        df['total_discount'] = safe_convert(df['올웨이즈 부담 쿠폰할인금']) + safe_convert(df['판매자 부담 쿠폰할인금'])
        df = df.sort_values('주문아이디')
        
        # Load reference data
        option_df = load_the_spreadsheet('옵션', sh).astype(str).apply(lambda x: x.str.strip())
        customer_df = load_the_spreadsheet('고객', sh).astype(str).apply(lambda x: x.str.strip())
        existing_orders = load_the_spreadsheet('주문', sh)
        
        # Prepare option mapping data
        df_for_option = df[['주문아이디', '상품아이디', '옵션']].copy()
        df_for_option.columns = ['주문아이디', '상품 id', '옵션 이름']
        df_for_option['옵션 이름'] = df_for_option['옵션 이름'].replace('nan', '').fillna('')
        df_for_option['옵션 id'] = df_for_option['상품 id'] + '_' + df_for_option['옵션 이름']
        
        # Prepare customer mapping data
        df_for_customer = df[['주문아이디', '수령인 연락처']].copy()
        df_for_customer['플랫폼'] = '올웨이즈'
        df_for_customer.columns = ['주문아이디', '고객 휴대폰', '플랫폼']
        
        # Get mapped keys through joins
        option_merged = pd.merge(
            df_for_option,
            option_df[['옵션 id', '옵션 key']],
            on='옵션 id',
            how='left'
        )
        st.write("Option Merged DataFrame:", option_merged)

        customer_merged = pd.merge(
            df_for_customer,
            customer_df[['고객 휴대폰', '플랫폼', '고객 key']],
            on=['고객 휴대폰', '플랫폼'],
            how='left'
        )
        st.write("Customer Merged DataFrame:", customer_merged)
        
        # Create final order data
        order_data = pd.DataFrame({
            '주문 key': df['주문아이디'].fillna('').astype(str) + '_올웨이즈',
            '옵션 key': option_merged['옵션 key'],
            '고객 key': customer_merged['고객 key'],
            '주문 id': df['주문아이디'],
            '주문 날짜': df['주문 시점'],
            '결제 날짜': df['주문 시점'],
            '판매금액': df['상품가격'],
            '할인금액': df['total_discount'],
            '플랫폼 비용': str(0),
            '정산금액': df['정산대상금액(수수료 제외)'],
            '배송비': df['배송비'],
            '주문 수량': df['수량'],
            '사은품': '',
            '주문 총 무게': '',
            '주문 상태': '',
            '플랫폼': '올웨이즈',
            '기록날짜': pd.to_datetime('now').strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Clean up final data
        order_data = order_data[order_data['주문 key'].notna() & (order_data['주문 key'] != '')].fillna('')
        st.write("final order DataFrame:", order_data)

        update_worksheet(existing_orders, order_data, '주문', 
                        '주문 데이터 업데이트 완료 (2/4)', sh, spread)
            
    except Exception as e:
        _handle_error(e, "order")

def process_always_delivery(df, sh, spread):
    """Process delivery data from always excel and update the delivery worksheet"""
    try:
        df = _clean_and_filter_df(df)
        if df is None:
            return
            
        existing_deliveries = load_the_spreadsheet('배송', sh)
        
        delivery_data = pd.DataFrame({
            '배송 key': df['주문아이디'].fillna('').astype(str).apply(lambda x: f"배송_{x}_올웨이즈"),
            '주문 key': df['주문아이디'].fillna('').astype(str).apply(lambda x: f"{x}_올웨이즈"),
            '배송 주소': df['주소'].fillna('').astype(str),
            '배송 우편번호': df['우편번호'].fillna('').astype(str),
            '배송 메시지': df['공동현관 비밀번호'].fillna('').astype(str),
            '출고 날짜': get_delivery_date(),
            '해당 배송회차': '1',
            '방문수령 여부': df['수령 방법'].fillna('').astype(str),
            '방문수령 날짜': '',
            '수취자 휴대폰': df['수령인 연락처'].fillna('').astype(str),
            '수취자 전화번호': '',
            '수취자 이름': df['수령인'].fillna('').astype(str),
            '선착불 여부': '',
            '선착불 금액': '',
            '기록날짜': pd.to_datetime('now').strftime('%Y-%m-%d %H:%M:%S')
        })

        update_worksheet(existing_deliveries, delivery_data, '배송',
                        '배송 데이터 업데이트 완료 (3/4)', sh, spread)
    except Exception as e:
        _handle_error(e, "delivery")