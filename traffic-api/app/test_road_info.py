
import os
import requests
import xml.etree.ElementTree as ET

from dotenv import load_dotenv

# 환경변수 불러오기
load_dotenv()

api_key = os.getenv("SEOUL_API_KEY")

# 도시고속도로 코드
road_division_code = "02"

if not api_key:
    raise ValueError("SEOUL_API_KEY가 설정되지 않았습니다.")

# 서울시 RoadInfo API 주소
api_url = (
    f"http://openapi.seoul.go.kr:8088/"
    f"{api_key}/xml/RoadInfo/1/100/{road_division_code}"
)

try:
    # API 요청
    response = requests.get(api_url, timeout=20)
    response.raise_for_status()

    # XML 분석
    root = ET.fromstring(response.content)

    result_code = root.findtext("RESULT/CODE")
    result_message = root.findtext("RESULT/MESSAGE")
    total_count = root.findtext("list_total_count")

    print("HTTP 상태 코드:", response.status_code)
    print("API 처리 코드:", result_code)
    print("API 처리 결과:", result_message)
    print("전체 도로 축 개수:", total_count)

    if result_code != "INFO-000":
        raise ValueError("RoadInfo API 조회 실패")

    road_rows = root.findall("row")

    print("\n===== 도시고속도로 목록 =====")

    for road_row in road_rows:
        road_code = road_row.findtext("axis_cd")
        road_name = road_row.findtext("axis_name")

        print(
            "도로 축 코드:", road_code,
            "| 도로명:", road_name
        )

except requests.exceptions.RequestException as error:
    print("API 요청 오류:", error.__class__.__name__)

except ET.ParseError as error:
    print("XML 분석 오류:", error)

except ValueError as error:
    print("데이터 처리 오류:", error)
