import streamlit as st
import pandas as pd
import traceback
from common_processor import load_the_spreadsheet, update_worksheet, get_delivery_date, safe_convert



def process_naver_customer(df, sh, spread):
    """Process naver customer data and update customer worksheet"""
    if df is None:
        st.error("Please upload a file first")
        return
        
    try:
        # Clean input data
        df = df.astype(str).apply(lambda x: x.str.strip())
        
        customer_data = pd.DataFrame({
            '고객 key': df['구매자연락처'] + '_네이버',
            '고객 id': df['구매자ID'],
            '고객 이름': df['구매자명'],
            '고객 휴대폰': df['구매자연락처'],
            '고객 전화번호': '',
            '플랫폼': '네이버',
            '기록날짜': pd.to_datetime('now').strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Get the customer worksheet with first row as column names
        existing_df = load_the_spreadsheet('고객', sh)
        
        # Get existing naver customers
        existing_naver = existing_df[existing_df['플랫폼'] == '네이버']
        
        # Filter out customers whose phone numbers already exist
        new_customer_data = customer_data[~customer_data['고객 휴대폰'].isin(existing_naver['고객 휴대폰'])]
        new_customer_data = new_customer_data.sort_values('고객 이름')
        
        update_worksheet(existing_df, new_customer_data, '고객', 
                        f'{len(new_customer_data)} new customer records added successfully', sh, spread)
            
    except Exception as e:
        st.error(f"Error processing customer data: {str(e)}")
        st.error(f"Full error traceback:\n{traceback.format_exc()}")

def process_naver_order(df, sh, spread):
    """Process naver order data and update order worksheet"""
    if df is None:
        st.error("Please upload a file first")
        return
        
    try:
        # Clean input data
        df = df.astype(str).apply(lambda x: x.str.strip())
        
        df['원상품가격'] = safe_convert(df['상품가격']) + safe_convert(df['옵션가격']) * safe_convert(df['수량'])
        df = df.sort_values('주문번호')
        
        # Get option data and customer data with proper column names
        option_df = load_the_spreadsheet('옵션', sh).astype(str).apply(lambda x: x.str.strip())
        customer_df = load_the_spreadsheet('고객', sh).astype(str).apply(lambda x: x.str.strip())
        existing_orders = load_the_spreadsheet('주문', sh)
        
        # Create a mapping dictionary for options
        option_mapping = dict(zip(
            zip(option_df['상품 id'], option_df['옵션 이름']),
            option_df['옵션 key']
        ))
        
        # Create a mapping dictionary for customers
        customer_mapping = dict(zip(
            zip(customer_df['고객 휴대폰'], customer_df['플랫폼']),
            customer_df['고객 key']
        ))
        
        # Map option keys and customer keys
        option_keys = df.apply(
            lambda x: option_mapping.get((x['상품번호'], x['옵션정보']), ''),
            axis=1
        )
        
        customer_keys = df.apply(
            lambda x: customer_mapping.get((x['구매자연락처'], '네이버'), ''),
            axis=1
        )
        
        # Create order data DataFrame with mapped columns
        order_data = pd.DataFrame({
            '주문 key': df['주문번호'].astype(str) + '_네이버',
            '옵션 key': option_keys,
            '고객 key': customer_keys,
            '주문 id': df['주문번호'],
            '주문 날짜': df['주문일시'],
            '결제 날짜': df['결제일'],
            '판매금액': df['원상품가격'],
            '할인금액': option_df['옵션 할인금액'],
            '플랫폼 비용': safe_convert(df['네이버페이 주문관리 수수료']) + safe_convert(df['매출연동 수수료']),
            '정산금액': df['정산예정금액'],
            '배송비': df['배송비 합계'],
            '주문 수량': df['수량'],
            '사은품': df['사은품'],
            '주문 총 무게': '',
            '주문 상태': df['주문상태'],
            '플랫폼': '네이버',
            '기록날짜': pd.to_datetime('now').strftime('%Y-%m-%d %H:%M:%S')
        })
        
        update_worksheet(existing_orders, order_data, '주문', 
                        'Order data updated successfully', sh, spread)
            
    except Exception as e:
        st.error(f"Error processing order data: {str(e)}")
        st.error(f"Full error traceback:\n{traceback.format_exc()}")

def process_naver_delivery(df, sh, spread):
    """Process delivery data from naver excel and update the delivery worksheet"""
    if df is None:
        st.error("Please upload a file first")
        return
        
    try:
        # Clean input data
        df = df.astype(str).apply(lambda x: x.str.strip())
        
        # Get existing delivery data
        existing_deliveries = load_the_spreadsheet('배송', sh)
        
        # Create delivery data DataFrame with one row per order
        delivery_data = pd.DataFrame({
            '배송 key': df['주문번호'].astype(str).apply(lambda x: f"배송_{x}_네이버"),
            '주문 key': df['주문번호'].astype(str).apply(lambda x: f"{x}_네이버"),
            '배송 주소': df['통합배송지'],
            '배송 우편번호': df['우편번호'],
            '배송 메시지': df['배송메세지'],
            '출고 날짜': get_delivery_date(),
            '해당 배송회차': '1',
            '방문수령 여부': df['배송방법'],
            '방문수령 날짜': '',
            '수취자 휴대폰': df['수취인연락처1'],
            '수취자 전화번호': df['수취인연락처2'], 
            '수취자 이름': df['수취인명'],
            '선착불 여부': '',
            '선착불 금액': '',
            '기록날짜': pd.to_datetime('now').strftime('%Y-%m-%d %H:%M:%S')
        })

        update_worksheet(existing_deliveries, delivery_data, '배송',
                        'Delivery data updated successfully', sh, spread)
    except Exception as e:
        st.error(f"Error processing delivery data: {str(e)}")
        st.error(f"Full error traceback:\n{traceback.format_exc()}")