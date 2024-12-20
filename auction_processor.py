import streamlit as st
import pandas as pd
import traceback
from common_processor import load_the_spreadsheet, update_worksheet, get_delivery_date, safe_convert



def process_auction_customer(df, sh, spread):
    """Process auction customer data and update customer worksheet"""
    if df is None:
        st.error("Please upload a file first")
        return
        
    try:
        # Clean input data
        df = df.astype(str).apply(lambda x: x.str.strip())
        
        customer_data = pd.DataFrame({
            '고객 key': df['구매자 휴대폰'] + '_옥션',
            '고객 id': df['구매자아이디'],
            '고객 이름': df['구매자명'],
            '고객 휴대폰': df['구매자 휴대폰'],
            '고객 전화번호': df['구매자 전화번호'],
            '플랫폼': '옥션',
            '기록날짜': pd.to_datetime('now').strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Get the customer worksheet with first row as column names
        existing_df = load_the_spreadsheet('고객', sh)  # Added missing sh parameter
        
        # Get existing 11st customers
        existing_auction = existing_df[existing_df['플랫폼'] == '옥션']
        
        # Filter out customers whose phone numbers already exist
        new_customer_data = customer_data[~customer_data['고객 휴대폰'].isin(existing_auction['고객 휴대폰'])]
        new_customer_data = new_customer_data.sort_values('고객 이름')
        
        update_worksheet(existing_df, new_customer_data, '고객', 
                        f'{len(new_customer_data)} 명의 고객 데이터 업데이트 완료 (1/4)', sh, spread)
            
    except Exception as e:
        st.error(f"Error processing customer data: {str(e)}")
        st.error(f"Full error traceback:\n{traceback.format_exc()}")

def process_auction_order(df, sh, spread):
    """Process auction order data and update order worksheet"""
    if df is None:
        st.error("Please upload a file first")
        return
        
    try:
        # Clean input data
        df = df.astype(str).apply(lambda x: x.str.strip())

        df['total_discount'] = safe_convert(df['판매자쿠폰할인']) + safe_convert(df['구매쿠폰적용금액']) + safe_convert(df['우수회원할인'])
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
            lambda x: option_mapping.get((x['상품번호'], x['옵션']), ''),
            axis=1
        )
        
        customer_keys = df.apply(
            lambda x: customer_mapping.get((x['구매자 휴대폰'], '옥션'), ''),
            axis=1
        )
        
        # Create order data DataFrame with mapped columns
        order_data = pd.DataFrame({
            '주문 key': df['주문번호'].astype(str) + '_옥션',
            '옵션 key': option_keys,
            '고객 key': customer_keys,
            '주문 id': df['주문번호'],
            '주문 날짜': df['주문일자(결제확인전)'],
            '결제 날짜': df['결제일'],
            '판매금액': df['판매금액'],
            '할인금액': df['total_discount'],
            '플랫폼 비용': df['서비스이용료'],
            '정산금액': df['정산예정금액'],
            '배송비': df['배송비 금액'],
            '주문 수량': df['수량'],
            '사은품': df['사은품'],
            '주문 총 무게': '',
            '주문 상태': '',
            '플랫폼': '옥션',
            '기록날짜': pd.to_datetime('now').strftime('%Y-%m-%d %H:%M:%S')
        })
        
        update_worksheet(existing_orders, order_data, '주문', 
                        '주문 데이터 업데이트 완료 (2/4)', sh, spread)
            
    except Exception as e:
        st.error(f"Error processing order data: {str(e)}")
        st.error(f"Full error traceback:\n{traceback.format_exc()}")

def process_auction_delivery(df, sh, spread):
    """Process delivery data from auction excel and update the delivery worksheet"""
    if df is None:  # Added null check for consistency
        st.error("Please upload a file first")
        return
        
    try:
        # Clean input data
        df = df.astype(str).apply(lambda x: x.str.strip())
        
        # Get existing delivery data
        existing_deliveries = load_the_spreadsheet('배송', sh)
        
        # Create delivery data DataFrame with one row per order
        delivery_data = pd.DataFrame({
            '배송 key': df['주문번호'].astype(str).apply(lambda x: f"배송_{x}_옥션"),
            '주문 key': df['주문번호'].astype(str).apply(lambda x: f"{x}_옥션"),
            '배송 주소': df['주소'],
            '배송 우편번호': df['우편번호'],
            '배송 메시지': df['배송시 요구사항'],
            '출고 날짜': get_delivery_date(),
            '해당 배송회차': '1',
            '방문수령 여부': '',
            '방문수령 날짜': '',
            '수취자 휴대폰': df['수령인 휴대폰'],
            '수취자 전화번호': df['수령인 전화번호'], 
            '수취자 이름': df['수령인명'],
            '선착불 여부': '',
            '선착불 금액': '',
            '기록날짜': pd.to_datetime('now').strftime('%Y-%m-%d %H:%M:%S')
        })

        update_worksheet(existing_deliveries, delivery_data, '배송',
                        '배송 데이터 업데이트 완료 (3/4)', sh, spread)
    except Exception as e:
        st.error(f"Error processing delivery data: {str(e)}")
        st.error(f"Full error traceback:\n{traceback.format_exc()}")