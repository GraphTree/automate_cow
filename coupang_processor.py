import streamlit as st
import pandas as pd
import traceback
from common_processor import load_the_spreadsheet, update_worksheet



def process_coupang_customer(df, sh, spread):
    """Process coupang customer data and update customer worksheet"""
    if df is None:
        st.error("Please upload a file first")
        return
        
    try:
        customer_data = pd.DataFrame({
            '고객 key': df['구매자전화번호'] + '_쿠팡',
            '고객 id': '',
            '고객 이름': df['구매자'],
            '고객 휴대폰': df['구매자전화번호'],
            '고객 전화번호': '',
            '플랫폼': '쿠팡',
            '기록날짜': pd.to_datetime('now').strftime('%Y%m%d %H:%M:%S')
        })
        
        # Get the customer worksheet with first row as column names
        existing_df = load_the_spreadsheet('고객', sh)
        
        new_customer_data = customer_data[~(
            (customer_data['고객 휴대폰'].isin(existing_df['고객 휴대폰'])) & 
            (customer_data['플랫폼'] == '쿠팡')
        )]
        new_customer_data = new_customer_data.sort_values('고객 이름')
        
        update_worksheet(existing_df, new_customer_data, '고객', 
                        f'{len(new_customer_data)} new customer records added successfully', sh, spread)
            
    except Exception as e:
        st.error(f"Error processing customer data: {str(e)}")
        st.error(f"Full error traceback:\n{traceback.format_exc()}")

def process_coupang_order(df, sh, spread):
    """Process coupang order data and update order worksheet"""
    if df is None:
        st.error("Please upload a file first")
        return
        
    try:
        df = df.sort_values('주문번호')
        
        # Get option data and customer data with proper column names
        option_df = load_the_spreadsheet('옵션', sh)
        customer_df = load_the_spreadsheet('고객', sh)
        existing_orders = load_the_spreadsheet('주문', sh)
        product_df = load_the_spreadsheet('상품', sh)
        
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

        # Get discount amount from product table
        # Create a mapping dictionary that maps product IDs to their discount amounts
        # This will be used to look up the discount amount for each order based on the product ID
        discount_mapping = dict(zip(product_df['상품 id'], product_df['할인액']))
        
        # Map option keys and customer keys
        option_keys = df.apply(
            lambda x: option_mapping.get((x['노출상품ID'], x['등록옵션명']), ''),
            axis=1
        )
        
        customer_keys = df.apply(
            lambda x: customer_mapping.get((x['구매자전화번호'], '쿠팡'), ''),
            axis=1
        )

        # Calculate platform fee (11.66%)
        platform_fee = df['결제액'] * 0.1166
        
        # Create order data DataFrame with mapped columns
        order_data = pd.DataFrame({
            '주문 key': df['주문번호'] + '_쿠팡',
            '옵션 key': option_keys,
            '고객 key': customer_keys,
            '주문 id': df['주문번호'],
            '주문 날짜': df['주문일'],
            '결제 날짜': df['주문일'],
            '판매금액': df['결제액'],
            '할인금액': df['노출상품ID'].map(discount_mapping),
            '플랫폼 비용': platform_fee,
            '정산금액': df['결제액'] - df['노출상품ID'].map(discount_mapping) - platform_fee,
            '배송비': df['배송비'],
            '주문 수량': df['구매수(수량)'],
            '사은품': '',
            '주문 총 무게': '',
            '주문 상태': '',
            '플랫폼': '쿠팡',
            '기록날짜': pd.to_datetime('now').strftime('%Y%m%d %H:%M:%S')
        })
        
        update_worksheet(existing_orders, order_data, '주문', 
                        'Order data updated successfully', sh, spread)
            
    except Exception as e:
        st.error(f"Error processing order data: {str(e)}")
        st.error(f"Full error traceback:\n{traceback.format_exc()}")

def process_coupang_delivery(df, sh, spread):
    """Process delivery data from coupang excel and update the delivery worksheet"""
    if df is None:
        st.error("Please upload a file first")
        return
        
    try:
        # Get existing delivery data
        existing_deliveries = load_the_spreadsheet('배송', sh)
        
        # Create delivery data DataFrame with one row per order
        delivery_data = pd.DataFrame({
            '배송 key': df['주문번호'].apply(lambda x: f"배송_{x}_쿠팡"),
            '주문 key': df['주문번호'].apply(lambda x: f"{x}_쿠팡"),
            '배송 주소': df['수취인 주소'],
            '배송 우편번호': df['우편번호'],
            '배송 메시지': df['배송메세지'],
            '배송 날짜': df['출고일(발송일)'],
            '해당 배송회차': '',
            '방문수령 여부': '',
            '방문수령 날짜': '',
            '수취자 휴대폰': df['수취인전화번호'],
            '수취자 전화번호': '', 
            '수취자 이름': df['수취인이름'],
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