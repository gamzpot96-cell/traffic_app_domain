
import os
import requests
import xml.etree.ElementTree as ET

from dotenv import load_dotenv

# 1. 환경변수 불러오기
load_dotenv()

api_key = os.getenv("SEOUL_API_KEY")
link_id = "1220003800"

if not api_key:
    raise ValueError("SEOUL_API_KEY가 설정되지 않았습니다.")

# 2. API 요청 주소
api_url = (
    f"http://openapi.seoul.go.kr:8088/"
    f"{api_key}/xml/TrafficInfo/1/5/{link_id}"
)

try:
    # 3. API 요청
    response = requests.get(api_url, timeout=20)
    response.raise_for_status()

    # 4. XML 분석
    root = ET.fromstring(response.content)

    result_code = root.findtext("RESULT/CODE")
    result_message = root.findtext("RESULT/MESSAGE")

    print("API 처리 결과:", result_message)

    if result_code != "INFO-000":
        raise ValueError("API 응답 오류: " + str(result_code))

    # 5. 도로 구간 데이터 추출
    traffic_rows = root.findall("row")

    for traffic_row in traffic_rows:
        road_link_id = traffic_row.findtext("link_id")
        speed_text = traffic_row.findtext("prcs_spd")
        travel_time_text = traffic_row.findtext("prcs_trv_time")

        print("\n===== 서울시 도로 교통정보 =====")
        print("도로 구간 ID:", road_link_id)
        print("통행속도:", speed_text, "km/h")
        print("통행시간 원본값:", travel_time_text)

except requests.exceptions.RequestException as error:
    print("API 요청 오류:", error.__class__.__name__)

except ET.ParseError as error:
    print("XML 분석 오류:", error)

except ValueError as error:
    print("데이터 처리 오류:", error)
