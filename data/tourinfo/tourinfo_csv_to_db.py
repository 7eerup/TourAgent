import pandas as pd
from sqlalchemy import create_engine

# # 1. CSV 파일 경로
# csv_file = '/경로/파일이름.csv'

# # 2. MariaDB 연결 정보
# user = 'dbuser'
# password = 'dbpassword'
# host = 'localhost'
# port = 3306
# db = 'testdb'
# table_name = 'my_table'

# # 3. CSV 읽기
# df = pd.read_csv(csv_file)

# # 4. DB 엔진 만들기
# engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4')

# # 5. 테이블에 데이터 넣기
# df.to_sql(table_name, con=engine, if_exists='append', index=False)

# print('CSV -> MariaDB 업로드 완료!')

# ==============

# 1.tourInfo
csv_file = './TourInfo.csv'

# 2. MariaDB 연결 정보
user = 'aitomic123'
password = 'aitomic463'
host = 'localhost'
port = 3306
db = 'aitomic123_db'
table_name = 'api_tourinfo'

# 3. CSV 읽기
df = pd.read_csv(csv_file)

# 널 허용 컬럼 처리 (빈 문자열/공백 → NaN)
nullable_columns = [
    'address', 'phone_number', 
    'category_one', 'category_two', 'category_three'
]
for col in nullable_columns:
    df[col] = df[col].replace('', pd.NA)


# 타입 맞추기
df['title'] = df['title'].astype(str)
df['content_type_id'] = df['content_type_id'].astype(str)
df['address'] = df['address'].astype('string')  # nullable 컬럼은 string dtype으로
df['lDongRegnCd'] = df['lDongRegnCd'].astype(str)
df['lDongSignguCd'] = df['lDongSignguCd'].astype(str)
df['phone_number'] = df['phone_number'].astype('string')  # 이 부분 중요
df['map_x'] = df['map_x'].astype(float)
df['map_y'] = df['map_y'].astype(float)
df['category_one'] = df['category_one'].astype('string')
df['category_two'] = df['category_two'].astype('string')
df['category_three'] = df['category_three'].astype('string')
df['content_id'] = df['content_id'].astype(int)


# 오토인크리먼트 컬럼 제거
if 'tourinfo_id' in df.columns:
    df = df.drop('tourinfo_id', axis=1)

# 4. DB 엔진 만들기
engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4')

# 5. 테이블에 데이터 넣기
df.to_sql(table_name, con=engine, if_exists='append', index=False)

print('CSV -> MariaDB 업로드 완료!')