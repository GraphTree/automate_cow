import streamlit as st
import pandas as pd
import traceback

# def worksheet_names():
#     """Get names of all worksheets in the spreadsheet"""
#     sheet_names = []   
#     for sheet in worksheet_list:
#         sheet_names.append(sheet.title)  
#     return sheet_names

def load_the_spreadsheet(spreadsheetname):
    """Load a worksheet and convert it to a pandas DataFrame"""
    worksheet = sh.worksheet(spreadsheetname)
    values = worksheet.get_all_values()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

def update_the_spreadsheet(spreadsheetname,dataframe):
    """Add new data to the spreadsheet"""
    # Find the last row with data
    worksheet = sh.worksheet(spreadsheetname)
    values = worksheet.get_all_values()
    last_row = len(values)
    
    # Add new data after the last row
    col = ['Compound CID','Time_stamp']
    spread.df_to_sheet(dataframe[col], sheet=spreadsheetname, index=False, start=(last_row+1,1))
    st.sidebar.info('Updated to GoogleSheet')

def process_auction_customer(df):
    """Process auction customer data and update customer worksheet"""
    if df is None:
        st.error("Please upload a file first")
        return
        
    try:
        customer_data = pd.DataFrame({
            '고객 Key': df.apply(lambda x: f"고객_{x['구매자명']}_{pd.to_datetime('now').strftime('%Y%m%d %H:%M:%S')}", axis=1),
            '고객 Id': df['구매자아이디'],
            '고객 이름': df['구매자명'],
            '고객 휴대폰': df['구매자 휴대폰'],
            '고객 전화번호': df['구매자 전화번호'],
            '플랫폼': '옥션'
        })
        
        # Get the customer worksheet with first row as column names
        existing_df = load_the_spreadsheet('고객')
        
        new_customer_data = customer_data[~customer_data['고객 휴대폰'].isin(existing_df['고객 휴대폰'])]
        new_customer_data = new_customer_data.sort_values('구매자명')
        
        if not new_customer_data.empty:
            spread.df_to_sheet(
                new_customer_data,
                sheet='고객',
                index=False,
                start=(len(existing_df)+2, 1),
                headers=False,
                replace=False
            )
            st.sidebar.success(f'{len(new_customer_data)} new customer records added successfully')
        else:
            st.sidebar.info('No new customer records to add')
            
    except Exception as e:
        st.error(f"Error processing customer data: {str(e)}")
        st.error(f"Full error traceback:\n{traceback.format_exc()}")

def process_auction_order(df):
    """Process auction order data and update order worksheet"""
    if df is None:
        st.error("Please upload a file first")
        return
        
    try:
        df['total_discount'] = df['판매자쿠폰할인'] + df['구매쿠폰적용금액'] + df['우수회원할인']
        df = df.sort_values('주문번호')
        
        # Get option data and customer data with proper column names
        option_df = load_the_spreadsheet('옵션')
        customer_df = load_the_spreadsheet('고객')
        existing_orders = load_the_spreadsheet('주문')
        
        # Create a mapping dictionary for options
        option_mapping = dict(zip(
            zip(option_df['상품 id'], option_df['옵션 이름']),
            option_df['옵션 key']
        ))
        
        # Create a mapping dictionary for customers
        customer_mapping = dict(zip(
            customer_df['고객 휴대폰'],
            customer_df['고객 Key']
        ))
        
        # Map option keys and customer keys
        option_keys = df.apply(
            lambda x: option_mapping.get((x['상품번호'], x['옵션']), ''),
            axis=1
        )
        
        customer_keys = df['구매자 휴대폰'].map(customer_mapping)
        
        # Create order data DataFrame with mapped columns
        order_data = pd.DataFrame({
            '주문 key': df.apply(lambda x: f"주문_{x['주문번호']}_{pd.to_datetime('now').strftime('%Y%m%d %H:%M:%S')}", axis=1),
            '옵션 key': option_keys,
            '고객 key': customer_keys,
            '주문 id': df['주문번호'],
            '주문 날짜': df['결제일'],
            '판매금액': df['판매금액'],
            '할인금액': df['total_discount'],
            '정산금액': df['정산예정금액'],
            '배송비': df['배송비 금액'],
            '주문 수량': df['수량'],
            '사은품': '',
            '주문 총 무게': '',
            '주문 상태': '',
            '플랫폼': '옥션'
        })
        
        # Update the order worksheet
        if not order_data.empty:
            spread.df_to_sheet(
                order_data,
                sheet='주문',
                index=False,
                headers=False,
                start=(len(existing_orders)+2, 1),
                replace=False
            )
            st.sidebar.success('Order data updated successfully')
        else:
            st.sidebar.info('No order data to update')
            
    except Exception as e:
        st.error(f"Error processing order data: {str(e)}")
        st.error(f"Full error traceback:\n{traceback.format_exc()}")

def process_auction_delivery(df):
    """Process delivery data from auction excel and update the delivery worksheet"""
    try:
        # Get existing delivery data to determine next row
        existing_deliveries = load_the_spreadsheet('배송')
        
        # Group by address and aggregate other columns
        grouped_df = df.groupby('주소').agg({
            '주문번호': lambda x: list(x),  # Keep all order numbers
            '우편번호': 'first',
            '수령인 휴대폰': 'first', 
            '수령인 전화번호': 'first',
            '수령인명': 'first',
            '배송시 요구사항': 'first'
        }).reset_index()

        grouped_df['배송_key'] = grouped_df.apply(lambda x: f"배송_{pd.to_datetime('now').strftime('%Y%m%d %H:%M:%S')}", axis=1)
        grouped_df = grouped_df.sort_values('주소')
        
        # Create delivery data DataFrame with mapped columns
        delivery_data = pd.DataFrame({
            '배송 key': grouped_df['배송_key'],
            '주문 key': grouped_df['주문번호'].apply(lambda x: [f"주문_{num}_{pd.to_datetime('now').strftime('%Y%m%d %H:%M:%S')}" for num in x]),
            '배송 주소': grouped_df['주소'],
            '배송 우편번호': grouped_df['우편번호'],
            '배송 메시지': grouped_df['배송시 요구사항'],
            '배송 날짜': '',
            '해당 배송회차': '',
            '방문수령 여부': '',
            '방문수령 날짜': '',
            '수취자 휴대폰': grouped_df['수령인 휴대폰'],
            '수취자 전화번호': grouped_df['수령인 전화번호'],
            '수취자 이름': grouped_df['수령인명'],
            '선착불 여부': '',
            '선착불 금액': '',
            '택배운임 여부': ''
        })

        # Update the delivery worksheet
        if not delivery_data.empty:
            spread.df_to_sheet(
                delivery_data,
                sheet='배송',
                index=False,
                headers=False,
                start=(len(existing_deliveries)+2, 1),
                replace=False
            )
            st.sidebar.success('Delivery data updated successfully')
        else:
            st.sidebar.info('No delivery data to update')
            
    except Exception as e:
        st.error(f"Error processing delivery data: {str(e)}")
        st.error(f"Full error traceback:\n{traceback.format_exc()}")
