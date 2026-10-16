
import os
import requests
import xml.etree.ElementTree as ET

from dotenv import load_dotenv

# 1. 환경변수 불러오기
load_dotenv()

api_key = os.getenv("SEOUL_API_KEY")

# 기존 테스트에서 사용한 도로 구간 ID
link_id = "1220003800"

if not api_key:
    raise ValueError("SEOUL_API_KEY가 설정되지 않았습니다.")

# 2. 서울시 도로 구간 상세정보 API 주소
api_url = (
    f"http://openapi.seoul.go.kr:8088/"
    f"{api_key}/xml/LinkInfo/1/5/{link_id}"
)

try:
    # 3. API 요청
    response = requests.get(api_url, timeout=20)
    response.raise_for_status()

    # 4. XML 데이터 분석
    root = ET.fromstring(response.content)

    print("HTTP 상태 코드:", response.status_code)
    print("XML 최상위 태그:", root.tag)

    result_code = root.findtext("RESULT/CODE")
    result_message = root.findtext("RESULT/MESSAGE")

    print("API 처리 코드:", result_code)
    print("API 처리 결과:", result_message)

    if result_code != "INFO-000":
        print("정상적인 데이터 응답이 아닙니다.")

    else:
        # 5. 도로 구간 정보 출력
        traffic_rows = root.findall("row")

        print("조회된 데이터 수:", len(traffic_rows))

        for traffic_row in traffic_rows:
            print("\n===== 도로 구간 상세정보 =====")

            # XML에 포함된 항목을 모두 출력
            for traffic_field in traffic_row:
                print(
                    traffic_field.tag,
                    ":",
                    traffic_field.text
                )

except requests.exceptions.RequestException as error:
    print("API 요청 오류:", error.__class__.__name__)

except ET.ParseError as error:
    print("XML 분석 오류:", error)
