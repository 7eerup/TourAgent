import requests

# === 1. 변수 선언 ===
url = 'https://maps.apigw.ntruss.com/map-geocode/v2/geocode'
query = '강서한강공원'

# 실제 자신의 API KEY/ID로 바꿔주세요!
API_KEY_ID = 'sc1hult6y6'
API_KEY = 'nyKElo9KG8ibZg0wdidElwg0PEywoqrrozrb2etx'

params = {'query': query}
headers = {
    'x-ncp-apigw-api-key-id': API_KEY_ID,
    'x-ncp-apigw-api-key': API_KEY,
    'Accept': 'application/json',
    # 필요시 Web 서비스 URL로 Referer 추가 (주석 해제해서 시도)
    # 'Referer': 'http://116.125.140.113',
}

# === 2. 요청 정보 사전 출력 ===
print('---[요청 정보]---')
print('URL:', url)
print('params:', params)
print('headers:', headers)
print('-----------------')

# === 3. 요청 실행 ===
try:
    response = requests.get(url, params=params, headers=headers)
except Exception as e:
    print('❌ [예외 발생] :', e)
    exit(1)

print('\n---[응답]---')
print('Status Code:', response.status_code)
print('응답 헤더:', response.headers)
print('Raw Response:', response.text)
print('-------------')

# === 4. JSON 파싱/에러 메시지 상세 출력 ===
try:
    resp_json = response.json()
    print('\n---[JSON Response]---')
    print(resp_json)
    print('---------------------')
except Exception as e:
    print('❌ [JSON 파싱 실패]:', e)
    exit(1)

# === 5. 401 에러 등 상세 원인 자동분석 ===
if response.status_code == 401:
    print('\n❗[401 Unauthorized] - 네이버 클라우드 콘솔에서 다음을 점검하세요:')
    print(' - API Key/ID 값 정확한지')
    print(' - 프로젝트에 지도-Geocode API 구독 상태인지')
    print(' - 호출 허용 IP/Referer에 이 서버가 등록되어 있는지')
    print(' - Web 서비스 URL만 등록된 경우, Referer 헤더도 추가 시도')
    print(' - 필요시 API 키 재발급 후 교체')
    print(' - 여전히 안 되면 콘솔 전체 설정 화면 캡처로 전문가/고객센터 문의')

elif response.status_code != 200:
    print(f'\n❗[{response.status_code} 에러] - 응답 내용 참고하여 콘솔 설정 또는 파라미터/헤더 값 확인 필요')
else:
    # 정상 응답 데이터 표시 (예시)
    addresses = resp_json.get('addresses', [])
    if addresses:
        print('주소 좌표 결과:')
        for addr in addresses:
            print(f" - {addr.get('roadAddress', '')}: {addr.get('x')}, {addr.get('y')}")
    else:
        print('❗[정상응답]지만, 좌표 결과 없음! 쿼리 파라미터/주소명을 확인하세요.')
