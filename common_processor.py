import streamlit as st
import pandas as pd
import re
import io
import msoffcrypto


def load_the_spreadsheet(spreadsheetname, sh):
    """Load a worksheet and convert it to a pandas DataFrame"""
    worksheet = sh.worksheet(spreadsheetname)
    values = worksheet.get_all_values()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

def update_worksheet(existing_df, data, sheet_name, success_msg, sh, spread):
    """Common function to update worksheet with new data"""
    if not data.empty:
        spread.df_to_sheet(
            data,
            sheet=sheet_name,
            index=False,
            headers=False, 
            start=(len(existing_df)+2, 1),
            replace=False
        )
        st.sidebar.success(success_msg)
    else:
        st.sidebar.info(f'No {sheet_name} data to update')

    
def get_delivery_date():
    """
    Returns delivery date based on current time in YYYY-MM-DD format:
    - If current time is after 6pm, returns next day at midnight
    - If current time is before 6pm, returns current day at midnight
    """
    current_time = pd.to_datetime('now')
    midnight = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if current_time.hour >= 18:
        return (midnight + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        return midnight.strftime('%Y-%m-%d')



def safe_convert(value):
    if isinstance(value, str):
        return int(value.replace(',', '')) if value else 0
    return value if isinstance(value, (int, float)) else 0

def clean_string(value):
    """
    Clean string by:
    - Removing leading/trailing spaces
    - Removing special characters
    - Converting to lowercase
    - Normalizing whitespace
    - Removing emojis and other unicode characters
    Returns empty string if input is not a string.
    """
    if not isinstance(value, str):
        return ''
    

    
    # Convert to lowercase and strip whitespace
    value = value.lower().strip()
    
    # Normalize whitespace (replace multiple spaces with single space)
    value = ' '.join(value.split())
    
    # Remove emojis and other unicode characters
    value = value.encode('ascii', 'ignore').decode('ascii')
    
    # Remove special characters but keep spaces between words
    value = re.sub(r'[^a-z0-9가-힣\s]', '', value)
    
    # Final strip to remove any remaining whitespace
    return value.strip()



def read_naver_excel(excel_file, password="1212", sheet_name="발주발송관리", header=1):
    """
    Read and decrypt a password-protected Naver Excel file
    
    Args:
        excel_file: Excel file object from file upload
        password (str): Password to decrypt the file
        sheet_name (str): Name of sheet to read
        header (int): Row number to use as column headers (0-indexed)
        
    Returns:
        pandas.DataFrame: Decrypted Excel data as DataFrame
    """
    decrypted_workbook = io.BytesIO()
    office_file = msoffcrypto.OfficeFile(excel_file)
    office_file.load_key(password=password)
    office_file.decrypt(decrypted_workbook)

    return pd.read_excel(decrypted_workbook, sheet_name=sheet_name, header=header)

def get_eleven_input():
    """Get input configuration for 11st platform processing"""
    return {
        # Customer processing config
        'platform_name': '11st',
        'platform_id': '11st',
        'phone_col': '휴대폰번호',
        'id_col': '구매자ID', 
        'name_col': '구매자',
        'tel_col': '전화번호',

        # Order processing config
        'order_id_col': '주문번호',
        'discount_cols': ['판매자기본할인금액', '판매자 추가할인금액'],
        'order_cols': {
            '주문 id': '주문번호',
            '주문 날짜': '주문일시',
            '결제 날짜': '결제일시',
            '판매금액': '주문금액',
            '플랫폼 비용': '서비스이용료',
            '정산금액': '정산예정금액',
            '배송비': '배송비',
            '주문 수량': '수량',
            '사은품': '',
            '주문 총 무게': '',
            '주문 상태': ''
        },
        'option_mapping': {
            'product_id': '상품번호',
            'option_name': '옵션'
        },
        'customer_mapping': {
            'phone': '휴대폰번호'
        },

        # Delivery processing config
        'delivery_cols': {
            '배송 주소': '주소',
            '배송 우편번호': '우편번호',
            '배송 메시지': '배송메시지',
            '수취자 휴대폰': '휴대폰번호',
            '수취자 전화번호': '전화번호',
            '수취자 이름': '수취인'
        }
    }

