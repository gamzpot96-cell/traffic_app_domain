
def create_traffic_briefing(route_data):
    """자동차 경로 데이터를 바탕으로 교통 브리핑을 생성합니다."""

    # 1. 출발지와 목적지
    origin_name = route_data["origin"]["name"]
    destination_name = route_data["destination"]["name"]

    # 2. 전체 이동 거리와 예상 시간
    distance_m = route_data.get("total_distance_m")
    duration_seconds = route_data.get("total_duration_seconds")

    roads = route_data.get("roads", [])

    # 3. 기본 브리핑 문장
    briefing_sentences = []

    briefing_sentences.append(
        f"{origin_name}에서 {destination_name}까지의 "
        "자동차 이동 경로 교통 상황입니다."
    )

    if distance_m is not None and duration_seconds is not None:
        distance_km = round(distance_m / 1000, 1)
        duration_minutes = round(duration_seconds / 60, 1)

        briefing_sentences.append(
            f"전체 이동 거리는 약 {distance_km}km이며, "
            f"예상 소요 시간은 약 {duration_minutes}분입니다."
        )

    # 4. 정체 또는 지체 구간 추출
    congested_roads = []

    for road in roads:
        traffic_state = road.get("traffic_state")
        traffic_speed = road.get("traffic_speed_kmh")

        if traffic_state in [1, 2] and traffic_speed is not None:
            congested_roads.append(road)

    # 5. 정체 및 지체 구간 분석
    if congested_roads:
        briefing_sentences.append(
            f"조회된 도로 구간 가운데 "
            f"{len(congested_roads)}개 구간에서 "
            "정체 또는 지체 상태가 확인됐습니다."
        )

        # 통행속도가 낮은 구간부터 정렬
        congested_roads.sort(
            key=lambda road: road["traffic_speed_kmh"]
        )

        # 가장 느린 구간
        slowest_road = congested_roads[0]

        road_name = slowest_road["name"]
        speed = slowest_road["traffic_speed_kmh"]

        briefing_sentences.append(
            f"이 가운데 {road_name} 구간의 "
            f"통행속도는 시속 {speed:g}km로 나타났습니다."
        )

    else:
        briefing_sentences.append(
            "조회된 경로에서 정체 또는 지체로 "
            "분류된 구간은 확인되지 않았습니다."
        )

    # 6. 분석 범위 안내
    briefing_sentences.append(
        "이번 브리핑은 조회한 자동차 경로에 한정되며, "
        "서울 전체 도로의 교통 상황을 의미하지는 않습니다."
    )

    # 7. 문장을 하나로 합치기
    briefing_text = " ".join(briefing_sentences)

    return {
        "title": f"{origin_name} → {destination_name} 교통 브리핑",
        "content": briefing_text,
        "congested_road_count": len(congested_roads),
        "total_road_count": len(roads)
    }
