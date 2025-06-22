import datetime
from langchain_core.prompts import PromptTemplate

# 현재 시점(YYYY-MM-DD HH:MM:SS) 저장
now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# # Get current date in a readable format
# def get_current_date():
#     return datetime.now().strftime("%B %d, %Y")


# 3) 테이블 스키마 설명 문자열 준비
# ---------------------------------------------------------------
# (1) 관광정보 테이블 스키마 (수정해야 함!!)
tourinfo_table_info = """
Table name: TourInfo

Columns:
- tourinfo_id      (INT)           NOT NULL  : 관광정보 고유 ID
- title            (VARCHAR(200))  NOT NULL  : 콘텐츠 제목
- content_type_id  (VARCHAR(20))   NOT NULL  : 콘텐츠 유형  
                                         (12: 관광지, 14: 문화시설, 15: 축제공연행사, 25: 여행코스,  
                                          28: 레포츠, 32: 숙박, 38: 쇼핑, 39: 음식점)
- address          (VARCHAR(255))  NULL      : 도로명 주소 (기본값: '')
- lDongRegnCd      (VARCHAR(20))   NOT NULL  : 법정동 시도 코드 (e.g. 서울특별시)
- lDongSignguCd    (VARCHAR(20))   NOT NULL  : 법정동 시군구 코드 (e.g. 종로구, 용산구)
- phone_number     (VARCHAR(200))  NULL      : 전화번호 (하이픈/숫자만 허용, 기본값: '')
- map_x            (FLOAT)         NOT NULL  : WGS84 경도 좌표
- map_y            (FLOAT)         NOT NULL  : WGS84 위도 좌표
- category_one     (VARCHAR(50))   NOT NULL  : 카테고리 코드1  
                                           (자연, 인문, 레포츠, 쇼핑, 음식, 숙박, 추천코스)
- category_two     (VARCHAR(50))   NOT NULL  : 카테고리 코드2  
                                           (자연관광지, 역사관광지, 레포츠소개, 음식점, 숙박시설 등)
- category_three   (VARCHAR(50))   NOT NULL  : 카테고리 코드3  
                                           (국립공원, 고궁, 박물관, 캠핑코스, 스키/보드 등)
- content_id       (INT)           NOT NULL  : 원본 콘텐츠 ID (uk)

Constraints:
- PRIMARY KEY (`tourinfo_id`)
- UNIQUE KEY (`content_id`)
"""


# (2) 날씨 예보 테이블 스키마 (수정해야 함!!)
weather_table_info = """
Table name: Weather

Columns:
- weather_id   (INT)       NOT NULL : 날씨정보 고유 ID
- BASE_DATE    (DATE)      NOT NULL : 기준 날짜 (yyyy-MM-dd)
- BASE_TIME    (TIME)      NOT NULL : 기준 시각 (HH:mm:ss)
- FCST_DATE    (DATE)      NOT NULL : 예측 날짜 (yyyy-MM-dd)
- FCST_TIME    (TIME)      NOT NULL : 예측 시각 (HH:mm:ss)
- nx           (INT)       NOT NULL : 기상청 격자 경도 인덱스
- ny           (INT)       NOT NULL : 기상청 격자 위도 인덱스
- AREA_NM      (VARCHAR(100)) NOT NULL : 지역명
- map_x        (FLOAT)     NOT NULL : GPS X좌표 (WGS84 경도)
- map_y        (FLOAT)     NOT NULL : GPS Y좌표 (WGS84 위도)
- PCP          (FLOAT)     NOT NULL : 1시간 강수량 (mm)  
                                     - ‘강수없음’→0, ‘1mm 미만’→0.5  
                                     - 값 ≥900 또는 ≤-900 → 결측 처리  
- POP          (INT)       NOT NULL : 강수확률 (%)  
                                     - 값 ≥900 또는 ≤-900 → 결측 처리  
- PTY          (INT)       NOT NULL : 강수 형태 코드  
                                     (0: 없음, 1: 비, 2: 비/눈, 3: 눈, 4: 소나기)  
- REH          (INT)       NOT NULL : 습도 (%)  
                                     - 값 ≥900 또는 ≤-900 → 결측 처리  
- SNO          (FLOAT)     NOT NULL : 1시간 적설량 (cm)  
                                     - ‘적설없음’→0  
                                     - 값 ≥900 또는 ≤-900 → 결측 처리  
- SKY          (INT)       NOT NULL : 하늘 상태 코드  
                                     (1: 맑음, 3: 구름많음, 4: 흐림)  
- TMP          (FLOAT)     NOT NULL : 1시간 기온 (℃)  
                                     - 값 ≥900 또는 ≤-900 → 결측 처리  
- TMN          (FLOAT)     NOT NULL : 일 최저기온 (℃)  
                                     - 하루 1회 제공, 나머지 시간대는 -999 → 결측 처리  
- TMX          (FLOAT)     NOT NULL : 일 최고기온 (℃)  
                                     - 하루 1회 제공, 나머지 시간대는 -999 → 결측 처리  
- WSD          (TINYINT)   NOT NULL : 풍속 범주  
                                     (0: 약함(0≤WSD<4), 1: 약간강함(4≤WSD<9),  
                                      2: 강함(9≤WSD<14), 3: 매우강함(WSD≥14))

Constraints:
- PRIMARY KEY (`accommodation_id`)
- 모든 컬럼 NOT NULL 처리하여, 결측치는 지정된 값(-999 또는 ≥900 기준)으로 인코딩
"""

# (3) 숙박업체 테이블 스키마 (수정해야 함!!)
accommodation_table_info = """
Table name: Accommodation

Columns:
- accommodation_id         (INT)            NOT NULL  : 숙박업체 고유 ID
- store_name               (VARCHAR(100))   NOT NULL  : 가게명 (최대 100자)
- grade                    (VARCHAR(50))    NOT NULL  : 성급 또는 브랜드 모델 등
- address                  (VARCHAR(255))   NOT NULL  : 도로명 주소 (최대 255자)
- phone_number             (VARCHAR(20))    NULL      : 전화번호 (하이픈·숫자만 허용, DEFAULT '')
- rating                   (FLOAT)          NOT NULL  : 별점 (결측치는 -999로 인코딩, DEFAULT -999)
- visitor_review_count     (INT)            NOT NULL  : 방문자 리뷰 수 (결측치는 -999로 인코딩, DEFAULT -999)
- blog_review_count        (INT)            NOT NULL  : 블로그 리뷰 수 (결측치는 -999로 인코딩, DEFAULT -999)
- reservation_site         (VARCHAR(255))   NULL      : 예약 사이트 URL 또는 플랫폼 (DEFAULT '')
- map_x                    (FLOAT)          NOT NULL  : WGS84 경도 좌표 (결측치는 -999, DEFAULT -999)
- map_y                    (FLOAT)          NOT NULL  : WGS84 위도 좌표 (결측치는 -999, DEFAULT -999)

Constraints:
- PRIMARY KEY (`accommodation_id`)
"""

# (4) 식당 테이블 스키마 (수정해야 함!!)
restaurant_table_info = """
Table name: Restaurant

Columns:
- restaurant_id         (INT)            NOT NULL  : 업체 고유 ID  
- store_name            (VARCHAR(100))   NOT NULL  : 가게명 (최대 100자)  
- category              (VARCHAR(20))    NOT NULL  : 업종 분류  
                                              (한식, 카페·디저트, 일식·횟집, 양식·퓨전,  
                                               중식·아시안, 패스트푸드, 바·펍, 분식·길거리식, 기타)  
- description           (VARCHAR(50))    NULL      : 가게 설명 (최대 50자, DEFAULT ‘’)  
- address               (VARCHAR(255))   NOT NULL  : 도로명 주소 (최대 255자)  
- phone_number          (VARCHAR(20))    NULL      : 전화번호 (하이픈·숫자만 허용, DEFAULT ‘’)  
- rating                (FLOAT)          NULL      : 별점 (소수, DEFAULT -999)  
- visitor_review_count  (INT)            NULL      : 방문자 리뷰 수 (DEFAULT -999)  
- blog_review_count     (INT)            NULL      : 블로그 리뷰 수 (DEFAULT -999)  
- monday_biz_hours      (VARCHAR(20))    NULL      : 월 영업시간 (HH:mm-HH:mm 형태, DEFAULT ‘’)  
- monday_break_time     (VARCHAR(20))    NULL      : 월 휴식시간 (DEFAULT ‘’)  
- monday_last_order     (VARCHAR(20))    NULL      : 월 라스트오더 (DEFAULT ‘’)  
- tuesday_biz_hours     (VARCHAR(20))    NULL      : 화 영업시간 (DEFAULT ‘’)  
- tuesday_break_time    (VARCHAR(20))    NULL      : 화 휴식시간 (DEFAULT ‘’)  
- tuesday_last_order    (VARCHAR(20))    NULL      : 화 라스트오더 (DEFAULT ‘’)  
- wednesday_biz_hours   (VARCHAR(20))    NULL      : 수 영업시간 (DEFAULT ‘’)  
- wednesday_break_time  (VARCHAR(20))    NULL      : 수 휴식시간 (DEFAULT ‘’)  
- wednesday_last_order  (VARCHAR(20))    NULL      : 수 라스트오더 (DEFAULT ‘’)  
- thursday_biz_hours    (VARCHAR(20))    NULL      : 목 영업시간 (DEFAULT ‘’)  
- thursday_break_time   (VARCHAR(20))    NULL      : 목 휴식시간 (DEFAULT ‘’)  
- thursday_last_order   (VARCHAR(20))    NULL      : 목 라스트오더 (DEFAULT ‘’)  
- friday_biz_hours      (VARCHAR(20))    NULL      : 금 영업시간 (DEFAULT ‘’)  
- friday_break_time     (VARCHAR(20))    NULL      : 금 휴식시간 (DEFAULT ‘’)  
- friday_last_order     (VARCHAR(20))    NULL      : 금 라스트오더 (DEFAULT ‘’)  
- saturday_biz_hours    (VARCHAR(20))    NULL      : 토 영업시간 (DEFAULT ‘’)  
- saturday_break_time   (VARCHAR(20))    NULL      : 토 휴식시간 (DEFAULT ‘’)  
- saturday_last_order   (VARCHAR(20))    NULL      : 토 라스트오더 (DEFAULT ‘’)  
- sunday_biz_hours      (VARCHAR(20))    NULL      : 일 영업시간 (DEFAULT ‘’)  
- sunday_break_time     (VARCHAR(20))    NULL      : 일 휴식시간 (DEFAULT ‘’)  
- sunday_last_order     (VARCHAR(20))    NULL      : 일 라스트오더 (DEFAULT ‘’)  
- map_x                 (FLOAT)          NOT NULL  : WGS84 경도 좌표 (DEFAULT -999)  
- map_y                 (FLOAT)          NOT NULL  : WGS84 위도 좌표 (DEFAULT -999)  

Constraints:
- PRIMARY KEY (`restaurant_id`)
"""




# (5) 실시간 혼잡도 테이블 스키마 (수정해야 함!!)
congestion_table_info = """
Table name: congestion_data

Columns:
- AREA_NM (VARCHAR): 핫스팟 장소명 (예: 강남 MICE 관광특구)
- AREA_CD (VARCHAR): 핫스팟 코드명 (예: POI001)
- AREA_CONGEST_LVL (VARCHAR): 현재 혼잡도 단계 (여유, 보통, 약간 붐빔, 붐빔)
- AREA_CONGEST_MSG (TEXT): 혼잡도 관련 설명 메시지
- AREA_PPLTN_MIN (INT): 현재 실시간 인구 수 (최소값)
- AREA_PPLTN_MAX (INT): 현재 실시간 인구 수 (최댓값)
- MALE_PPLTN_RATE (FLOAT): 남성 인구 비율 (%)
- FEMALE_PPLTN_RATE (FLOAT): 여성 인구 비율 (%)
- PPLTN_RATE_0 (FLOAT): 0~10세 인구 비율 (%)
- PPLTN_RATE_10 (FLOAT): 10대 인구 비율 (%)
- PPLTN_RATE_20 (FLOAT): 20대 인구 비율 (%)
- PPLTN_RATE_30 (FLOAT): 30대 인구 비율 (%)
- PPLTN_RATE_40 (FLOAT): 40대 인구 비율 (%)
- PPLTN_RATE_50 (FLOAT): 50대 인구 비율 (%)
- PPLTN_RATE_60 (FLOAT): 60대 인구 비율 (%)
- PPLTN_RATE_70 (FLOAT): 70대 이상 인구 비율 (%)
- RESNT_PPLTN_RATE (FLOAT): 상주 인구 비율 (%)
- NON_RESNT_PPLTN_RATE (FLOAT): 비상주 인구 비율 (%)
- REPLACE_YN (CHAR): 대체 데이터 여부 (Y/N)
- PPLTN_TIME (DATETIME): 실시간 인구 데이터 업데이트 시각 (YYYY-MM-DD HH:MM)
- FCST_YN (CHAR): 인구 예측 제공 여부 (Y/N)
- FCST_TIME (DATETIME): 인구 예측 시점 (YYYY-MM-DD HH:MM)
- FCST_CONGEST_LVL (VARCHAR): 예측 혼잡도 단계 (여유, 보통, 약간 붐빔, 붐빔)
- FCST_PPLTN_MIN (INT): 예측 실시간 인구 수 (최소값)
- FCST_PPLTN_MAX (INT): 예측 실시간 인구 수 (최댓값)
"""

# (4) 모든 테이블 설명 결합
combined_table_info = tourinfo_table_info + "\n\n" + weather_table_info + "\n\n" + accommodation_table_info + "\n\n" + restaurant_table_info


# congestion_table_info

## 사용자의 요청을 재작성 (수정해야 함!!)
## +1) 날짜를 얘기안하면, 이상하게 sql query 문을 생성해서, 날짜 얘기안하면, 오늘로 무조건 추가하라고 했음

rewrite_question_prompt = PromptTemplate.from_template(
    """
You are a SQL generation assistant. Rewrite the user's original question into a single, concise English question that is directly usable for SQL query generation.

Instructions:
1. If the user does not specify a date or time, assume the current date and time and format them as follows:
   - Date: YYYY-MM-DD (e.g. 2025-06-14)
   - Time: HH:mm:ss   (e.g. 21:37:05)
2. Clarify any other ambiguity (e.g., table names, units) to make the question SQL-friendly.
3. Do NOT generate SQL—only output the rewritten question.

Context:
Current date (YYYY-MM-DD): {current_date}  
Current time (HH:mm:ss):   {current_time}  
Table Schemas:
{table_info}

Original Question:
{question}

Rewritten Question:
"""
)



# ---------------------------------------------------------------
# 4) SQL 쿼리 생성용 PromptTemplate 정의 (수정해야 함!!)
# ---------------------------------------------------------------
sql_generation_prompt = PromptTemplate.from_template(
    """As of {current_time}, determine which table(s) to query based on the user’s request:

- If it is a weather-related question (예: “내일 서울 날씨”), query the **Weather** table.
  - **Select**: `AREA_NM`, `TMP` (기온), `POP` (강수확률), `PTY` (강수형태), `REH` (습도), `SKY` (하늘상태), 필요 시 `PCP` (강수량), `SNO` (적설량) 등을 포함하세요.
- If it is a general 관광지 추천 question (예: “왕십리 근처 명소 5곳”), query the **TourInfo** table.
- If it is a 식당 추천 question (예: “홍대 맛집 3곳 추천해줘”), query the **Restaurant** table.
- If it is a 숙박 추천 질문 (예: “강남에 위치한 호텔 2곳 알려줘”), query the **Accommodation** table.
- If multiple 도메인(날씨 + 식당/관광지/숙박)을 결합해야 한다면, 공간 좌표(`map_x`, `map_y`)나 지역명(`AREA_NM`)을 이용해 **JOIN** 또는 별도 쿼리로 처리하세요.

1. Think step by step:
   a) Identify the appropriate table(s).
   b) Determine JOIN or WHERE conditions.
   c) Build a syntactically correct, parameterized {dialect} SQLQuery.
2. Error Handling:
   -- If the SQLQuery fails (syntax or missing column), add a brief comment and correct it.
3. Security:
   -- Use parameter placeholders (`%s`, `?`); do not interpolate user input directly.
4. Limit Results:
   -- Unless user specifies, append `LIMIT {top_k}`.

-- [Few-Shot Examples]
-- Example 1:
-- Q: "지금 시간 기준으로 선선한 곳 추천해줘."
-- SQLQuery:
-- "SELECT *
--  FROM Weather
--  WHERE
--    FCST_DATE = DATE_ADD(
--                  CURRENT_DATE(),
--                  INTERVAL CASE
--                    WHEN HOUR(CURRENT_TIME()) = 23
--                         AND MINUTE(CURRENT_TIME()) >= 30
--                    THEN 1 ELSE 0 END DAY
--                )
--    AND FCST_TIME = CONCAT(
--                  LPAD(
--                    CASE
--                      WHEN MINUTE(CURRENT_TIME()) >= 30
--                      THEN (HOUR(CURRENT_TIME()) + 1) % 24
--                      ELSE HOUR(CURRENT_TIME())
--                    END,
--                    2, '0'
--                  ),
--                  ':00:00'
--                )
--  ORDER BY TMP ASC
--  LIMIT 10;"
-- SQLResult: "<Result of the SQLQuery>"
-- Answer: "<Final answer>"

Use EXACT format:

Question: "<Question here>"
SQLQuery: "<SQL query to run>"
SQLResult: "<Result of the SQLQuery>"
Answer: "<Final answer here>"

Tables:
{table_info}

Question: {input}
"""
)

# ---------------------------------------------------------------
# 6) 결과 해석용 PromptTemplate 정의
# ---------------------------------------------------------------
# 쿼리 결과가 빈 리스트여도 “죄송합니다” 없이 유용한 대안을 제안하도록 지시 (수정해야 함!!)

project_context = (
    "You are TourAgent, a recommendation engine for meeting venues in Seoul, "
    "using real-time Weather, TourInfo, Accommodation and Restaurant."
)

answer_prompt = PromptTemplate.from_template(
    """
{project_context}

아래 사용자 Question, SQLQuery, SQLResult 를 참고해 **한국어**로 사용자 친화적인 추천을 작성하세요.

Include:
- 추천 이유 (예: “서늘한 기온”, “지하철 출구 근처”, “지금 붐비지 않음”, "블로그 리뷰가 많음", "사용자 리뷰가 많음", "평점이 높음", "등급이 높음").
- 예상 이동 수단 및 소요 시간.
- 결과가 없을 경우에는 사용자의 질문를 통해 구체화할 수 있도록, 필요한 정보를 다시 물어봐.

원하는 형식:
1. **장소명** (기온: X℃)
   - 종류: (예: 식당, 관광지, 숙소)
   - 이유: …
   - 이동: …, 약 Y분
2. **장소명** (기온: X℃)
   - 종류: (예: 식당, 관광지, 숙소)
   - 이유: …
   - 이동: …, 약 Y분
3. **장소명** (기온: X℃)
   - 종류: (예: 식당, 관광지, 숙소)
   - 이유: …
   - 이동: …, 약 Y분

Question: {question}
SQLQuery: {query}
SQLResult: {result}
Answer:
"""
)
