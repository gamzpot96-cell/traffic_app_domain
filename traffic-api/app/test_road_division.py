
import os
import requests
import xml.etree.ElementTree as ET

from dotenv import load_dotenv

# 1. 환경변수 불러오기
load_dotenv()

api_key = os.getenv("SEOUL_API_KEY")

if not api_key:
    raise ValueError("SEOUL_API_KEY가 설정되지 않았습니다.")

# 2. 서울시 도로 분류정보 API
service_name = "RoadDivInfo"

api_url = (
    f"http://openapi.seoul.go.kr:8088/"
    f"{api_key}/xml/{service_name}/1/20/"
)

try:
    # 3. 서울시 API 요청
    response = requests.get(api_url, timeout=20)
    response.raise_for_status()

    # 4. XML 변환
    root = ET.fromstring(response.content)

    result_code = root.findtext("RESULT/CODE")
    result_message = root.findtext("RESULT/MESSAGE")
    total_count = root.findtext("list_total_count")

    print("HTTP 상태 코드:", response.status_code)
    print("API 처리 코드:", result_code)
    print("API 처리 결과:", result_message)
    print("전체 데이터 수:", total_count)

    if result_code != "INFO-000":
        raise ValueError("도로 분류정보 조회에 실패했습니다.")

    # 5. 도로 분류별 정보 출력
    road_divisions = root.findall("row")

    for road_division in road_divisions:
        print("\n===== 도로 분류정보 =====")

        for field in road_division:
            print(field.tag, ":", field.text)

except requests.exceptions.RequestException as error:
    print("API 요청 오류:", error.__class__.__name__)

except ET.ParseError as error:
    print("XML 분석 오류:", error)

except ValueError as error:
    print("데이터 처리 오류:", error)
