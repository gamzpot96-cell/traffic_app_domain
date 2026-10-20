"""서버 전용 OpenAI 교통 뉴스 초안 생성. 카카오 분석 결과만 근거로 사용."""
import json
import os

import httpx


class NewsGenerationError(Exception):
    pass


async def create_ai_news_briefing(analysis_results):
    """AI가 제목·리드·본문을 작성하되 사실표 및 범위 안내는 서버가 관리."""
    if len(analysis_results) != 3:
        raise NewsGenerationError("세 경로의 분석 결과가 모두 필요합니다.")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key.startswith("your_"):
        raise NewsGenerationError("OpenAI API 키가 설정되지 않았습니다.")

    facts = []
    for route in analysis_results:
        distance = route.get("distance_m")
        congested = route.get("congested_distance_m")
        count = route.get("congested_count")
        total_count = route.get("total_road_count")
        if (not isinstance(distance, int) or isinstance(distance, bool) or distance <= 0
                or not isinstance(congested, int) or isinstance(congested, bool)
                or not 0 <= congested <= distance
                or not isinstance(count, int) or not isinstance(total_count, int)
                or not 0 <= count <= total_count
                or not isinstance(route.get("duration_seconds"), int)
                or route["duration_seconds"] < 0):
            raise NewsGenerationError("기사 생성에 필요한 경로 수치가 올바르지 않습니다.")
        facts.append({
            "start": route["start"],
            "end": route["end"],
            "distance_m": distance,
            "duration_seconds": route["duration_seconds"],
            "total_road_count": total_count,
            "congested_count": count,
            "congested_distance_m": congested,
            "congestion_ratio_percent": round(congested / distance * 100, 1),
        })

    scope = ("카카오 자동차 길찾기 API의 조회된 3개 자동차 경로에 한정된 분석입니다. "
             "서울 전체 도로 상황을 대표하지 않으며, 정체·지체 거리 비율만으로 "
             "전체 교통 혼잡도를 판단할 수 없습니다.")
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": (
                "당신은 신중한 한국어 데이터 저널리스트입니다. JSON 객체의 title, lead, body만 작성하세요. "
                "주어진 Fact Sheet만 사용하세요. 거리·시간·건수·비율은 주어진 수치 그대로 사용하고 "
                "새로운 숫자, 추정 원인, 사고, 관측 시각, 인용, 인터뷰, 외부 통계, 현장 상황을 만들지 마세요. "
                "이동 시간은 API 예상값이라고 명시하세요. 세 경로만 비교하고 서울 전역으로 일반화하지 마세요. "
                "제목은 짧고 과장하지 않으며, 본문은 객관적인 2~3문단의 기사 문체로 작성하세요."
            )},
            {"role": "user", "content": "Fact Sheet (Kakao Mobility 기반 계산 결과):\n"
                                  + json.dumps(facts, ensure_ascii=False)}
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": "Bearer " + api_key,
                         "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
        message = result["choices"][0]["message"]
        if message.get("refusal"):
            raise NewsGenerationError("AI가 기사 작성을 거절했습니다.")
        article = json.loads(message["content"])
        if not isinstance(article, dict):
            raise ValueError("not an object")
        fields = {}
        for key, limit in (("title", 200), ("lead", 700), ("body", 4000)):
            value = article.get(key)
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise ValueError("invalid " + key)
            fields[key] = value.strip()
        fields["scope_notice"] = scope
        return fields
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise NewsGenerationError("OpenAI 기사 생성에 실패했습니다. 설정이나 응답을 확인하세요.") from exc
