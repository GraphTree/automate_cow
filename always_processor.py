import streamlit as st
import pandas as pd
import traceback
from common_processor import load_the_spreadsheet, update_worksheet



def process_always_customer(df, sh, spread):
    """Process always customer data and update customer worksheet"""
    if df is None:
        st.error("Please upload a file first")
        return
        
    try:
        customer_data = pd.DataFrame({
            '고객 key': df['수령인 연락처'] + '_올웨이즈잇',
            '고객 id': '',
            '고객 이름': df['수령인'],
            '고객 휴대폰': df['수령인 연락처'],
            '고객 전화번호': '',
            '플랫폼': '올웨이즈잇',
            '기록날짜': pd.to_datetime('now').strftime('%Y%m%d %H:%M:%S')
        })
        
        # Get the customer worksheet with first row as column names
        existing_df = load_the_spreadsheet('고객', sh)
        
        new_customer_data = customer_data[~(
            (customer_data['고객 휴대폰'].isin(existing_df['고객 휴대폰'])) & 
            (customer_data['플랫폼'] == '올웨이즈잇')
        )]
        new_customer_data = new_customer_data.sort_values('고객 이름')
        
        update_worksheet(existing_df, new_customer_data, '고객', 
                        f'{len(new_customer_data)} new customer records added successfully', sh, spread)
            
    except Exception as e:
        st.error(f"Error processing customer data: {str(e)}")
        st.error(f"Full error traceback:\n{traceback.format_exc()}")

def process_always_order(df, sh, spread):
    """Process always order data and update order worksheet"""
    if df is None:
        st.error("Please upload a file first")
        return
        
    try:
        df['total_discount'] = df['올웨이즈 부담 쿠폰할인금'] + df['판매자 부담 쿠폰할인금']
        df = df.sort_values('주문아이디')
        
        # Get option data and customer data with proper column names
        option_df = load_the_spreadsheet('옵션', sh)
        customer_df = load_the_spreadsheet('고객', sh)
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
            lambda x: option_mapping.get((x['상품아이디'], x['옵션']), ''),
            axis=1
        )
        
        customer_keys = df.apply(
            lambda x: customer_mapping.get((x['수령인 연락처'], '올웨이즈잇'), ''),
            axis=1
        )
        
        # Create order data DataFrame with mapped columns
        order_data = pd.DataFrame({
            '주문 key': df['주문아이디'] + '_올웨이즈잇',
            '옵션 key': option_keys,
            '고객 key': customer_keys,
            '주문 id': df['주문아이디'],
            '주문 날짜': df['주문 시점'],
            '결제 날짜': df['주문 시점'],
            '판매금액': df['상품가격'],
            '할인금액': df['total_discount'],
            '플랫폼 비용': 0,
            '정산금액': df['정산대상금액(수수료 제외)'],
            '배송비': df['배송비'],
            '주문 수량': df['수량'],
            '사은품': '',
            '주문 총 무게': '',
            '주문 상태': '',
            '플랫폼': '올웨이즈잇',
            '기록날짜': pd.to_datetime('now').strftime('%Y%m%d %H:%M:%S')
        })
        
        update_worksheet(existing_orders, order_data, '주문', 
                        'Order data updated successfully', sh, spread)
            
    except Exception as e:
        st.error(f"Error processing order data: {str(e)}")
        st.error(f"Full error traceback:\n{traceback.format_exc()}")

def process_always_delivery(df, sh, spread):
    """Process delivery data from always excel and update the delivery worksheet"""
    if df is None:
        st.error("Please upload a file first")
        return
        
    try:
        # Get existing delivery data
        existing_deliveries = load_the_spreadsheet('배송', sh)
        
        # Create delivery data DataFrame with one row per order
        delivery_data = pd.DataFrame({
            '배송 key': df['주문아이디'].apply(lambda x: f"배송_{x}_올웨이즈잇"),
            '주문 key': df['주문아이디'].apply(lambda x: f"{x}_올웨이즈잇"),
            '배송 주소': df['주소'],
            '배송 우편번호': df['우편번호'],
            '배송 메시지': df['공동현관 비밀번호'],
            '배송 날짜': '',
            '해당 배송회차': '',
            '방문수령 여부': df['수령 방법'],
            '방문수령 날짜': '',
            '수취자 휴대폰': df['수령인 연락처'],
            '수취자 전화번호': '', 
            '수취자 이름': df['수령인'],
            '선착불 여부': '',
            '선착불 금액': '',
            '택배운임 여부': '',
            '기록날짜': pd.to_datetime('now').strftime('%Y%m%d %H:%M:%S')
        })

        update_worksheet(existing_deliveries, delivery_data, '배송',
                        'Delivery data updated successfully', sh, spread)
    except Exception as e:
        st.error(f"Error processing delivery data: {str(e)}")
        st.error(f"Full error traceback:\n{traceback.format_exc()}")