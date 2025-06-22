import pandas as pd
from sqlalchemy import create_engine

# 1. 파일 경로와 DB 정보
csv_file = './Restaurant.csv'   # CSV 파일 실제 경로로 바꿔주세요!
user = 'aitomic123'
password = 'aitomic463'
host = 'localhost'
port = 3306
db = 'aitomic123_db'
table_name = 'api_restaurant'

# 2. CSV 불러오기
df = pd.read_csv(csv_file)

# 3. 컬럼 타입 맞추기 & 데이터 정제
# - Float/int: NaN 허용, 
# - CharField: 길이 자르기(넘치면 에러), null 허용은 None/np.nan 처리
# - phone_number 등 20자 제한
from numpy import nan

# 문자열 컬럼(길이 제한)
char_fields_20 = [
    'category', 'phone_number', 'monday_biz_hours', 'monday_break_time', 'monday_last_order',
    'tuesday_biz_hours', 'tuesday_break_time', 'tuesday_last_order',
    'wednesday_biz_hours', 'wednesday_break_time', 'wednesday_last_order',
    'thursday_biz_hours', 'thursday_break_time', 'thursday_last_order',
    'friday_biz_hours', 'friday_break_time', 'friday_last_order',
    'saturday_biz_hours', 'saturday_break_time', 'saturday_last_order',
    'sunday_biz_hours', 'sunday_break_time', 'sunday_last_order'
]
char_fields_50 = ['description']
char_fields_100 = ['store_name']
char_fields_255 = ['address']

# 길이 제한 함수
def crop_str(x, maxlen):
    if pd.isna(x) or str(x).lower() in ['nan', 'none', '']:
        return None
    return str(x)[:maxlen]

for col in char_fields_20:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: crop_str(x, 20))
for col in char_fields_50:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: crop_str(x, 50))
for col in char_fields_100:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: crop_str(x, 100))
for col in char_fields_255:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: crop_str(x, 255))

# 숫자형 변환 (null 허용)
num_fields_float = ['rating', 'map_x', 'map_y']
num_fields_int = ['visitor_review_count', 'blog_review_count']

for col in num_fields_float:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
for col in num_fields_int:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')  # null 허용 int

# 오토인크리먼트 PK 컬럼은 제거(혹시 CSV에 있다면)
if 'restaurant_id' in df.columns:
    df = df.drop('restaurant_id', axis=1)

# 4. DB 엔진 생성
engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4')

# 5. 업로드
df.to_sql(table_name, con=engine, if_exists='append', index=False)

print('CSV → MariaDB 업로드 완료!')
