import pandas as pd
import numpy as np
from sqlalchemy import create_engine

# 1. 파일 경로와 DB 정보
csv_file = './Accommodation.csv'   # 경로 및 파일명은 실제 파일에 맞게!
user = 'aitomic123'
password = 'aitomic463'
host = 'localhost'
port = 3306
db = 'aitomic123_db'
table_name = 'api_accommodation'

# 2. CSV 불러오기
df = pd.read_csv(csv_file)

# 3. 컬럼 타입 및 null 처리
df['store_name'] = df['store_name'].astype(str)
df['grade'] = df['grade'].astype(str)
df['address'] = df['address'].astype(str)
df['phone_number'] = df['phone_number'].apply(lambda x: str(x)[:20] if pd.notnull(x) and str(x).lower() not in ['nan', 'none', ''] else None)

df['rating'] = df['rating'].astype(float)
df['visitor_review_count'] = df['visitor_review_count'].astype(int)
df['blog_review_count'] = df['blog_review_count'].astype(int)

df['reservation_site'] = df['reservation_site'].apply(lambda x: str(x)[:255] if pd.notnull(x) and str(x).lower() not in ['nan', 'none', ''] else None)

# 널 허용(Null=True)인 좌표는 float, null 입력 허용
for col in ['map_x', 'map_y']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 오토 인크리먼트 컬럼 제거(혹시라도 있으면)
if 'accommodation_id' in df.columns:
    df = df.drop('accommodation_id', axis=1)

# 4. MariaDB 연결 엔진 생성
engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4')

# 5. 데이터 업로드
df.to_sql(table_name, con=engine, if_exists='append', index=False)

print('CSV → MariaDB 업로드 완료!')
