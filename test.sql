# Load delivery data and filter for latest date
delivery_df = source_spread.sheet_to_df(sheet='배송', index=None)
latest_date = delivery_df['기록 날짜'].max()
delivery_df = delivery_df[delivery_df['기록 날짜'] == latest_date]

# Load order data and filter for latest date
order_df = source_spread.sheet_to_df(sheet='주문', index=None)
latest_order_date = order_df['기록 날짜'].max()
order_df = order_df[order_df['기록 날짜'] == latest_order_date]

# Create base_data by merging delivery and order
base_data = pd.merge(delivery_df, order_df, 
                    on='주문 key', how='left', 
                    suffixes=('', '_order'))

# Group by delivery fields to aggregate order quantities
base_data = base_data.groupby([
    '배송 주소', '배송 key', '주문 key', '주문 id', '고객 key', 
    '옵션 key', '수취자 이름', '수취자 휴대폰', '수취자 전화번호',
    '선착불 여부', '배송 메시지', '플랫폼', '출고 날짜'
]).agg({
    '주문 수량': 'sum'
}).reset_index()

base_data['해당 배송 회차'] = '1'

# Load and filter customer data
customer_df = source_spread.sheet_to_df(sheet='고객', index=None)
customer_data = pd.merge(base_data, customer_df,
                        on='고객 key', how='left')

# Load and filter SKU related data
option_sku_df = source_spread.sheet_to_df(sheet='옵션 스큐 연결', index=None)  # Fixed sheet name

sku_df = source_spread.sheet_to_df(sheet='스큐', index=None)

# Merge with option_sku and sku data
sku_data = pd.merge(customer_data, option_sku_df,
                   on='옵션 key', how='left')
sku_data = pd.merge(sku_data, sku_df,
                   on='SKU key', how='left')

# Calculate SKU quantities based on order quantity
sku_data['SKU 수량'] = sku_data['SKU 수량'].fillna(0).astype(int) * sku_data['주문 수량'].fillna(0).astype(int)

# Group by all fields except SKU to aggregate SKU names and quantities
sku_data = sku_data.groupby([
    '배송 key', '주문 key', '고객 key', '수취자 이름', '고객 이름',
    '배송 주소', '수취자 휴대폰', '수취자 전화번호', '고객 휴대폰',
    '주문 수량', '선착불 여부', '배송 메시지', '주문 id', '플랫폼',
    '출고 날짜', '해당 배송 회차'
]).agg({
    'SKU 이름': lambda x: '\n'.join([str(i) for i in x if pd.notna(i) and str(i).strip()]),
    'SKU 수량': lambda x: '\n'.join([str(i) for i in x if pd.notna(i) and str(i).strip()])
}).reset_index()

# Select final columns in desired order
result_df = sku_data[[
    '배송 key', '주문 key', '고객 key', '수취자 이름', '고객 이름',
    '배송 주소', '수취자 휴대폰', '수취자 전화번호', '고객 휴대폰',
    '주문 수량', '선착불 여부', 'SKU 이름', 'SKU 수량', '배송 메시지',
    '주문 id', '플랫폼', '출고 날짜', '해당 배송 회차'
]]

-- with base_data as (
-- select
--     b.배송 주소,
--     b.배송 key,
--     o.주문 key,
--     o.주문 id,
--     o.고객 key,
--     b.옵션 key,
--     b.수취자 이름,
--     b.수취자 휴대폰,
--     b.수취자 전화번호,
--     b.선착불 여부,
--     b.배송 메시지,
--     '1' as 해당 배송 회차,
--     b.플랫폼,
--     b.출고 날짜,
--     sum(o.주문 수량) as 주문 수량
-- from 원본데이터.배송 as b
-- left join 원본데이터.주문  as o
--   on o.주문 key = b.주문 key
-- group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14
-- ),
-- customer_data as (
-- select 
--     b.*,
--     c.고객 이름,
--     c.고객 휴대폰
-- from base_data as b
-- left join 원본데이터.고객 as c
--   on b.고객 key = c.고객 key -- Fixed typo: 고개 -> 고객

-- ),
-- sku_data as (
-- select 
--     c.*,
--     array_agg(s.SKU 이름) as SKU 이름,
--     array_agg(cast(os.SKU 수량 as varchar)) as SKU 수량 -- Added cast to varchar for array_agg
-- from customer_data as c
-- left join 원본데이터.옵션_스큐_연결 as os -- Fixed table name to match Python code
--   on os.옵션 key = c.옵션 key -- Fixed IN operator to = since 옵션 key is single value
-- left join 원본데이터.스큐 as s
--   on s.SKU key = os.SKU key
-- group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17  
-- )
-- select 
--     배송 key,
--     주문 key,
--     고객 key,
--     수취자 이름,
--     고객 이름,
--     배송 주소,
--     수취자 휴대폰,
--     수취자 전화번호,
--     고객 휴대폰,
--     주문 수량,
--     선착불 여부,
--     SKU 이름,
--     SKU 수량,
--     배송 메시지,
--     주문 id,
--     플랫폼,
--     출고 날짜,
--     해당 배송 회차
-- from sku_data
