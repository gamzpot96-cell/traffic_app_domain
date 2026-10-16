
import os
import requests
import xml.etree.ElementTree as ET

from dotenv import load_dotenv

# 환경변수 불러오기
load_dotenv()

api_key = os.getenv("SEOUL_API_KEY")

# 테스트할 도로 구간
link_id = "1220003800"

if not api_key:
    raise ValueError("SEOUL_API_KEY가 설정되지 않았습니다.")


# 서울시 API 데이터를 조회하는 함수
def get_api_data(service_name, road_link_id):

    api_url = (
        f"http://openapi.seoul.go.kr:8088/"
        f"{api_key}/xml/{service_name}/1/5/{road_link_id}"
    )

    response = requests.get(api_url, timeout=20)
    response.raise_for_status()

    root = ET.fromstring(response.content)

    result_code = root.findtext("RESULT/CODE")

    if result_code != "INFO-000":
        raise ValueError(
            f"{service_name} API 오류: {result_code}"
        )

    # 첫 번째 도로 구간 데이터 반환
    return root.find("row")


try:
    # 1. 교통속도 데이터 가져오기
    traffic_row = get_api_data(
        "TrafficInfo",
        link_id
    )

    # 2. 도로 구간 상세정보 가져오기
    link_row = get_api_data(
        "LinkInfo",
        link_id
    )

    if traffic_row is None or link_row is None:
        print("조회된 도로 정보가 없습니다.")

    else:
        # 두 응답의 구간 ID가 일치하는지 확인
        traffic_link_id = traffic_row.findtext("link_id")
        detail_link_id = link_row.findtext("link_id")

        if traffic_link_id != detail_link_id:
            raise ValueError("도로 구간 ID가 일치하지 않습니다.")

        # 3. 교통정보를 하나의 딕셔너리로 정리
        traffic_information = {
            "link_id": traffic_link_id,
            "road_name": link_row.findtext("road_name"),
            "start_node": link_row.findtext("st_node_nm"),
            "end_node": link_row.findtext("ed_node_nm"),
            "distance_m": int(link_row.findtext("map_dist")),
            "speed_kmh": float(traffic_row.findtext("prcs_spd")),
            "travel_time_seconds": int(
                traffic_row.findtext("prcs_trv_time")
            )
        }

        # 4. 결과 출력
        print("\n===== 서울시 도로교통 통합정보 =====")

        print("도로명:", traffic_information["road_name"])
        print("시작 지점:", traffic_information["start_node"])
        print("종료 지점:", traffic_information["end_node"])

        print(
            "도로 거리:",
            traffic_information["distance_m"],
            "m"
        )

        print(
            "통행속도:",
            traffic_information["speed_kmh"],
            "km/h"
        )

        travel_minutes = (
            traffic_information["travel_time_seconds"] / 60
        )

        print("통행시간:", travel_minutes, "분")

        print("\nPython 딕셔너리:")
        print(traffic_information)

except requests.exceptions.RequestException as error:
    print("API 요청 오류:", error.__class__.__name__)

except ET.ParseError as error:
    print("XML 분석 오류:", error)

except (ValueError, TypeError) as error:
    print("데이터 처리 오류:", error)
