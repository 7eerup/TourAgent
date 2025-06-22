"""메인 실행 파일"""

import pandas as pd
from geo_processor import load_and_process_location_data, match_coordinates
from weather_api import WeatherAPI
from sqlalchemy import create_engine

from dotenv import load_dotenv
import os

# .env 파일에서 GOOGLE API 키를 불러와 환경변수에 설정
load_dotenv()

def main():
    """메인 실행 함수"""
    
    print("=== 서울시 주요 관광지 기상 데이터 수집 시작 ===")
    
    # 1. 지리 데이터 로드 및 처리
    print("\n1. 지리 데이터 로드 중...")
    merged_df, seoul_region_gdf = load_and_process_location_data()
    
    # 2. 좌표 매칭
    print("\n2. 기상청 격자 좌표 매칭 중...")
    location_data = match_coordinates(merged_df, seoul_region_gdf)
    
    # 3. 기상 데이터 수집
    print("\n3. 기상 데이터 수집 중...")
    weather_api = WeatherAPI()
    all_dfs = weather_api.collect_all_weather_data(location_data)

    # DB 엔진 설정 (환경에 맞게 수정)
    HOST = os.getenv("DB_HOST")
    PORT = os.getenv("DB_PORT")
    USERNAME = os.getenv("DB_USER")
    PASSWORD = os.getenv("DB_PASSWORD")
    DB_SCHEMA = os.getenv("DB_NAME")
    WEATHER_TABLE_NAME = os.getenv("WEATHER_TABLE_NAME")

    engine = create_engine(
        f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DB_SCHEMA}"
    )
    
    # 4. 결과 저장
    if all_dfs:
        weather_all = pd.concat(all_dfs, ignore_index=True)

        # data를 wide한 구조로 변경
        weather_df_wide = weather_all.pivot_table(
            index=['baseDate', 'baseTime', 'fcstDate', 'fcstTime', 'nx', 'ny', 'AREA_NM', 'map_x', 'map_y'],
            columns='category',
            values='fcstValue',
            aggfunc='first'
        ).reset_index()    

        ## 데이터 전처리 ##
        # 1. UUU(풍속(동서성분)), VVV(풍속(남북성분)), WAV(파고), VEC(풍향) 제거
        # 2. TMN(일 최저기온), TMX(일 최고기온) 은 하루에 한 번만 제공되므로, 나머지는 NaN 나옴 -> 결측치 -999로 집어 넣음
        # 2-1. => 나중에 프롬프트에서 꼭 llm에게 알려줘야 함
        weather_df_wide = weather_df_wide.drop(columns=['UUU', 'VVV', 'WAV', 'VEC']).fillna(-999)

        # 3. 풍속 (m/s)
        # 풍속은 숫자로 봐도 어떤지 감이 잘 안오기 때문에, 숫자로 인코딩하고, llm에게 프롬프트로 어떤 인코딩인지 알려줘야 함
        # labels의 값은 아래와 같음
        # '0' -> '약함'
        # '1' -> '약간강함'
        # '2' -> '강함'
        # '3' -> '매우강함'
        bins = [0, 4, 9, 14, float('inf')]
        labels = ['0', '1', '2', '3']


        weather_df_wide.WSD = weather_df_wide.WSD.apply(lambda x: float(x)) # str -> float으로 변환
        weather_df_wide.WSD = pd.cut(weather_df_wide.WSD,
                                    bins=bins,
                                    labels=labels,
                                    right=False,
                                    include_lowest=True
                                    )

        # 4. 1시간 강수량 (mm단위), 1시간 신적설 (cm단위)
        # '강수없음', '적설없음' 문자를 '0'으로 할당함
        weather_df_wide.PCP = weather_df_wide.PCP.replace({'강수없음': '0'})
        weather_df_wide.SNO = weather_df_wide.SNO.replace({'적설없음': '0'})

        # 5. 시간 단위가 0시이면 0000으로 되어야 하는데, 0으로 되어 있고, 1시이면, 0100으로 되어야 하는데, 100으로 되어 있음
        weather_df_wide.fcstTime = weather_df_wide.fcstTime.apply(lambda x: str(x).zfill(4))
        weather_df_wide.baseTime = weather_df_wide.baseTime.apply(lambda x: str(x).zfill(4))
        
        # %Y-%m-%d %H:%M:%S

        ## 0은 0000으로 100은 0100으로 변경해주기 위해 zfill 사용
        # weather_df_wide.baseTime = weather_df_wide.baseTime.apply(lambda x: str(x).zfill(4))
        # weather_df_wide.fcstTime = weather_df_wide.fcstTime.apply(lambda x: str(x).zfill(4))

        # Date가 아닌 string 타입으로 되어 있어서 변경해줌
        ## Date는 yyyy:MM:dd 형식으로 저장
        weather_df_wide.baseDate = weather_df_wide.baseDate.apply(lambda x: str(x)[:4] + '-' + str(x)[4:6] + '-' + str(x)[6:8])
        weather_df_wide.baseDate = pd.to_datetime(weather_df_wide.baseDate, format='%Y-%m-%d')

        ## Time은 HH:mm:ss 형식으로 저장
        weather_df_wide.baseTime = weather_df_wide.baseTime.apply(lambda x: str(x)[:2] + ':' + str(x)[2:])
        weather_df_wide.baseTime = pd.to_datetime(weather_df_wide.baseTime, format='%H:%M')
        weather_df_wide.baseTime = weather_df_wide.baseTime.dt.strftime("%H:%M:%S")

        weather_df_wide.fcstDate = weather_df_wide.fcstDate.apply(lambda x: str(x)[:4] + '-' + str(x)[4:6] + '-' + str(x)[6:8])
        weather_df_wide.fcstDate = pd.to_datetime(weather_df_wide.fcstDate, format='%Y-%m-%d')

        weather_df_wide.fcstTime = weather_df_wide.fcstTime.apply(lambda x: str(x)[:2] + ':' + str(x)[2:])
        weather_df_wide.fcstTime = pd.to_datetime(weather_df_wide.fcstTime, format='%H:%M')
        weather_df_wide.fcstTime = weather_df_wide.fcstTime.dt.strftime("%H:%M:%S")
        
        ## PCP가 1.0mm 미만이면, 0.5로 대체함
        weather_df_wide.PCP = weather_df_wide.PCP.apply(lambda x: str(x).replace("1mm 미만", "0.5")).apply(lambda x: str(x).replace('mm', '')).astype('float')

        mapping = {'baseDate': 'BASE_DATE',
                'baseTime': 'BASE_TIME',
                'fcstDate': 'FCST_DATE',
                'fcstTime': 'FCST_TIME'}

        weather_df_wide.rename(mapping, axis=1, inplace=True)

        weather_df_wide.to_sql(
            name=WEATHER_TABLE_NAME,
            con=engine,
            if_exists='append', # 기존 테이블은 유지하고, 새 레코드만 추가
            index=False,
            chunksize=1000
        )
        weather_df_wide.to_csv('./preprocessed_weather.csv', index=False, encoding='utf-8-sig')
        print(f"\n=== DB에 {weather_df_wide.shape[0]}행이 추가되었습니다 ===")
    else:
        print("\n=== 수집된 데이터가 없습니다 ===")

if __name__ == "__main__":
    main()