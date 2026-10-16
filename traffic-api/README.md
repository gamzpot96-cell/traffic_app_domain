# 서울 도로교통 브리핑 (Kakao 브랜치)

이 브랜치는 **ITS/TOPIS 대신 카카오**의 장소 검색 및 자동차 길찾기를 사용하는 시범 구현입니다.

## 기능
- 출발지/목적지 장소 검색: Kakao Local API
- 자동차 경로 조회: Kakao Mobility Directions API
- 도로별 통행속도/교통상태 코드와 지도 경로 표시: FastAPI + OpenLayers
- 실제 API 키는 서버의 환경변수에서만 사용

> **범위 제한:** 카카오 자동차 길찾기 결과는 선택한 경로에 포함된 도로의 정보입니다. 서울특별시 모든 도로의 실시간 교통정보나 도로 전체의 평균속도를 의미하지 않습니다.

## 로컬 실행
```powershell
cd C:\workspace\traffic_app_domain\traffic-api
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`.env.example`을 참고해 `.env` 파일을 만들고 `KAKAO_REST_API_KEY`를 입력합니다. 카카오모빌리티 자동차 길찾기 API 이용 권한이 필요할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

- 메인 화면: http://127.0.0.1:8000/
- 지도: http://127.0.0.1:8000/map
- API 예: http://127.0.0.1:8000/api/route?origin=서울역&destination=잠실역
- 테스트: `.\.venv\Scripts\python.exe -m pytest -q`

## 배포
Vercel 프로젝트의 **Root Directory는 `traffic-api`**로 지정하고, `KAKAO_REST_API_KEY`를 Environment Variables에 설정합니다. 이 브랜치를 배포할 때만 별도의 Preview 배포를 활용하세요.

## 데이터베이스
이 시범 버전은 데이터베이스 저장을 하지 않습니다. 기존 Supabase 코드는 향후 활용을 위한 참고용으로 남겨두었고, 실행 흐름과는 분리했습니다.
