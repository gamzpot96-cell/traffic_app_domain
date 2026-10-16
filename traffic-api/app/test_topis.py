
import os
import requests
import xml.etree.ElementTree as ET

from dotenv import load_dotenv

# .env 파일의 환경변수를 불러옵니다.
load_dotenv()

# 서울시 API 인증키
api_key = os.getenv("SEOUL_API_KEY")

# 공식 문서에 제공된 테스트 도로 구간 ID
link_id = "1220003800"

if not api_key:
    raise ValueError("SEOUL_API_KEY가 설정되지 않았습니다.")

# 서울시 실시간 도로 소통 정보 API
api_url = (
    f"http://openapi.seoul.go.kr:8088/"
    f"{api_key}/xml/TrafficInfo/1/5/{link_id}"
)

try:
    # API 서버에 요청합니다.
    response = requests.get(api_url, timeout=20)

    # HTTP 오류가 있는지 확인합니다.
    response.raise_for_status()

    print("HTTP 상태 코드:", response.status_code)

    # XML 응답을 분석합니다.
    root = ET.fromstring(response.content)

    print("XML 최상위 태그:", root.tag)

    # 응답의 첫 부분만 출력합니다.
    print("\nAPI 응답 내용:")
    print(ET.tostring(root, encoding="unicode")[:2000])

except requests.exceptions.RequestException as error:
    print("API 연결 오류:", error)

except ET.ParseError as error:
    print("XML 분석 오류:", error)
