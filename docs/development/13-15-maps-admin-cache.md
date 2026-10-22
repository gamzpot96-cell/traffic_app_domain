# 개발 이력 보존 문서

> 이 문서는 2026-10-22 README 간소화 과정에서 옮긴 **당시 설계·검증 기록**입니다. 현재 동작 및 정책은 저장소 최상위 README와 소스코드를 우선 확인하세요.

## 13. D01 카카오맵 JavaScript SDK 전환 설계 (2026-10-19)

> **사용자 의사:** 현재 OpenLayers + CARTO Voyager 배경은 선명해졌지만 국내 지도 정보의 상세함과 한글 레이블이 부족하여 **카카오맵으로 전환 선택**. 사용자는 **기존 기능을 보존하는 상세 설계 및 필요한 설정을 먼저 제시**하도록 요청. 따라서 **이 커밋은 설계 문서만 변경**하며 JavaScript/Python/DB·환경설정 값을 변경하지 않음. 설계 확인 후 별도 코드 구현 승인·로컬 구성 확인을 거쳐 착수.

### 13.1 도입 목표·정확한 범위

- 목표: 서울 도로명·장소명을 한글로 확인하기 쉬운 카카오맵 웹 SDK에 교통 상태별 경로선을 표시하고 기존 D01 지도 페이지의 정보를 유지.
- 지도 **표시 기술**만 OpenLayers 6.9.0의 OSM/CARTO 타일 + vector overlay에서 `kakao.maps.Map`, `kakao.maps.Polyline`, `kakao.maps.Marker`로 교체.
- **유지할 서버 기능:** `GET /api/route?origin=...&destination=...` (Kakao Local 장소 검색 → Kakao Mobility 자동차 경로 → 기존 `summarize_route` 반환). 서버의 장소 찾기·자동차 길찾기·교통 상태 분석·뉴스 생성·F16/F17/F22 데이터 API 변경 없음.
- **유지할 F23 기능:** `/map?article_id=8&route_index=0` URL, 기존 `GET /api/news/history/{article_id}`, 선택 기사·경로 번호 유효성 검증, 저장 거리/예상 시간/정체·지체 비율·KST, 출발/도착 자동 입력, 뉴스 복귀, **사용자 버튼 클릭 전 실시간 경로 재조회 금지**, 과거 경로 선형 생성 금지.
- **지도 색상:** traffic_state 1 원활 `#16a34a`, 2 서행 `#eab308`, 3 정체 `#dc2626`, 그 외 미확인 `#64748b`; 기존 범례 유지. Kakao 지도 기본 배경의 색은 실제 교통 상태라는 의미로 사용하지 않음.
- 새 DB 테이블/컬럼/RLS·데이터 쓰기/정기 수집 없음. 새 AI·지도 데이터·가상 사고 수치 없음.

### 13.2 공식 API와 2026 정책 확인

- 공식 카카오맵 이해하기 https://developers.kakao.com/docs/ko/kakaomap/common : Map Web SDK에는 **JavaScript 키** 사용, 기존 REST API 키를 SDK에 전달하면 안 됨.
- 공식 지도 Web API 가이드 https://apis.map.kakao.com/web/guide/ 및 레퍼런스 https://apis.map.kakao.com/web/documentation/ : JavaScript SDK 지도·마커·Polyline·LatLngBounds 지원, 로딩에 SDK JavaScript 키 필요.
- 앱 개발자 콘솔 https://developers.kakao.com/console/app : **[앱] → [플랫폼 키] → [JavaScript 키] → [JavaScript SDK 도메인]** (예전 '사이트 도메인'과 혼동 금지). 로컬 `http://127.0.0.1:8000`, 필요시 `http://localhost:8000` 등록하고 Vercel 배포 도메인은 별도 추가. URL 등록 규칙은 해당 대시보드 현재 허용 형식 확인. 카카오맵 서비스는 **[카카오맵] → [사용 설정] → [ON]** 상태 요구.
- **2026-07-21 무료 쿼터 정책 변경:** 개발자 계정 기준 **첫 번째로 카카오맵 API를 활성화한 앱**에만 무료 쿼터 제공. 두 번째 활성화 앱 또는 무료 범위 초과 사용은 비즈월렛/유료 API 설정 필요할 수 있음. 신규 비용 유발 설정은 사용자 확인·승인 전 수행하지 않음. 앱 대시보드의 무료 쿼터 적용 뱃지·쿼터·이용 약관 확인 필수.
- 현재 CARTO 지도 키는 별개. 카카오 REST 키·Supabase 관리자 키·환경비밀을 SDK 응답에 넣지 않음.

### 13.3 키·환경변수·보안 설계

- 신규 로컬 `traffic-api/.env`(Git 제외) 항목 제안: `KAKAO_MAP_JS_KEY=<카카오 JavaScript 키>`. 실제 키를 GitHub/README/채팅에 공유하지 않고 등록 여부만 확인.
- 카카오 **JavaScript 키는 브라우저 SDK에서 요구되어 요청 URL/개발자 도구에 보이는 플랫폼 키**이므로 서버 비밀 키처럼 절대 숨길 수 있다는 설명을 금지; 카카오 콘솔 JavaScript SDK 도메인 제한·앱 정책 적용 필수.
- 제안 `GET /api/map/sdk-config` (신규 읽기 전용) 또는 기존 `/api/map/basemap-config`의 호환 확장: `provider=kakao`와 **JavaScript 키만** 반환. 설정 미완료/키 없음이면 오해를 부르지 않도록 안내 후 기존 OpenLayers/CARTO/OSM 지도 사용. 다른 키 반환 금지, no-store 캐시 고려.
- **초기 이행 기간 기존 카카오맵 옵션/기존 지도 복구 기능 유지**. 최종 전환·복구 검증 및 관리자 승인 후 선택적으로 CARTO 코드와 `CARTO_BASEMAP_KEY` 제거를 별도 커밋에서 수행.

### 13.4 좌표·경로 변환과 프런트 구현 계약

- 현행 Kakao Mobility 응답 `data.roads[].vertexes`의 `[longitude, latitude, longitude, latitude, ...]` → `new kakao.maps.LatLng(latitude, longitude)`로 순서를 바꿔 다수 Polyline의 path 생성. 위경도 값 범위/유한성 및 꼭짓점이 2개 미만인 구간은 기존과 동일하게 그리지 않음.
- OpenLayers `routeSource.clear()`의 기능을 `displayedPolylines`, `displayedMarkers` 관리 배열에 저장한 Kakao 오버레이 각각 `setMap(null)`로 재현; 연속 검색 시 선형/마커가 누적되지 않도록 검사.
- 각 도로 구간의 기존 상태 색을 `new kakao.maps.Polyline({map, path, strokeWeight:5, strokeColor:..., strokeOpacity:...})`에 적용. 미확인 구간도 회색으로 명시.
- 출발 마커는 파랑, 도착 마커는 어두운 색을 유지하는 **Kakao MarkerImage/CustomOverlay 또는 접근 가능한 HTML 범례** 사용을 우선 검토. 기본 `kakao.maps.Marker`만 사용하면 기존 파랑/검정의 시각 구분이 달라질 수 있으므로 테스트에서 구분성 요구.
- 전체 오버레이의 좌표를 `new kakao.maps.LatLngBounds()`에 포함하고 `map.setBounds(bounds, padding...)`로 경로 영역 맞춤. 좌표가 없으면 기본 중심 서울 시청 인근(37.5665, 126.9780), 과도한 확대 방지·초기 화면을 실제 Chrome에서 검증.
- 카카오 JavaScript SDK 초기화 실패(키/도메인/쿼터/네트워크) 시 오류가 화면에 글자로 나타나야 하며, 기존 OpenLayers 지도 복구는 **별도 엔진 로딩 경로로 재초기화**해야 함. 단순 `tileSource` 스위치처럼 취급 금지.
- 기존 `mapRouteForm`, `origin`, `destination`, `mapRouteSubmit`, `result`, `savedArticlePanel`, `mapArticleStatus`, `backToSavedArticle`, `map`, `mapBasemapStatus` ID와 현재 D01 헤더·카드·반응형 CSS 유지.
- HTML 삽입 대신 `textContent`로 실측·기사 문자열 출력, 기사 ID와 route_index 검증 유지. 타일/SDK 안내는 지도 데이터의 관측 시각으로 오인되지 않게 구분.

### 13.5 사용자 화면/처리 순서

~~~text
[서울 교통 경로 지도 | 홈으로 돌아가기]
[과거 기사 저장 카드 (article_id 및 route_index가 유효한 경우에만 표시)]
  기사 #8 · 교통정보 조회 완료(KST) · 저장된 거리/예상 시간/정체 비율
  [뉴스 기사로 돌아가기]   ※ 저장된 요약이며 과거 도로 경로선은 저장되지 않음
[현재 경로 검색 카드]
  [출발지] [목적지] [현재 경로 새로 조회]
  [조회 전/진행/성공/오류 텍스트]
  [회색 미확인 · 녹색 원활 · 노랑 서행 · 빨강 정체]
[카카오맵 한글 배경]
  수동 조회 전: 카카오 기본 지도만 표시(과거 경로선을 임의로 그리지 않음)
  수동 조회 후: 현재 경로 폴리라인·출발/도착 마커·경로 구간 상태색
~~~

- PC 1280px/850px, 모바일 390px/320px에서 지도 높이·입력·확대 컨트롤·범례 겹침 점검.
- SDK 실패 시 사용자에게 '지도 표시를 불러오지 못했습니다. 키/도메인/쿼터를 확인하세요.' 안내와 재시도 또는 기존 지도 표시를 제공; 경로 조회 API 오류는 기존대로 텍스트 처리.

### 13.6 코드·API·DB 변경 계획과 검증

| 파일 | 구현 승인 후 변경 |
|---|---|
| `traffic-api/static/map.html` | OpenLayers 지도를 Kakao Map SDK 중심으로 전환, marker/polyline/bounds 구현, UI 유지, 복구 경로 |
| `traffic-api/app/main.py` | 새 읽기 전용 `GET /api/map/sdk-config` 제안, 공개용 JS 키만 전달, 기존 `/api/map/basemap-config` 호환 유지 |
| `traffic-api/tests/test_news_map_link.py` | F23 기사→지도, 버튼 이전 미조회, 저장 요약·오류 메시지 회귀 검사 |
| 신규 `tests/test_kakao_map.py` | 키/도메인 미설정 안내, 좌표 순서, 구간별 색/마커, 새 조회 후 정리, bounds, SDK 오류와 fallback 정적/모의 테스트 |
| `README.md` | 배포/환경 설정/실제 테스트 값/인증 및 정책/데이터 무변경 기록 |

- 기존 unittest **46개 전체**가 최근 사용자 환경에서 성공했음. SDK 교체 시 OpenLayers 엔진 문자열을 검사하는 `test_basemap_config.py` 및 `test_news_map_link.py` 등은 **기능동등성에 맞게 정정·보강**, 실제 동작 보존 검사 없이 삭제/무력화 금지.
- 검증 순서: ① 앱·JS 키·SDK 도메인/카카오맵 ON·비용/쿼터 확인 → ② 로컬 지도 첫 렌더링 및 한글 지명/선명도 확인 → ③ 새 경로 검색/상태색/마커/범위, 연속 검색 중복 방지 → ④ F23 기사 #8 첫 경로 자동 입력·40.4분 과거 값 유지·버튼 수동 후 최신 경로 표시 → ⑤ 잘못된 기사·경로 번호/404/외부 API 실패 → ⑥ 320/390/850/1280px/키보드 및 확대 → ⑦ 기존 + 신규 unittest 전체/DB 읽기 전용 건수 확인 → ⑧ README 증거 기록.
- **DB 영향 0**: `traffic_information` 레거시 30,538행 및 뉴스·스냅샷 저장 데이터, Supabase RLS/스키마 불변. 지도 업그레이드만으로 새 기사/경로를 DB에 쓰지 않음.
- 기존 `main` 브랜치는 수정하지 않고 `kakao`만 사용.

### 13.7 착수 전 승인 체크

- [ ] 기존 Kakao Developers 앱 중 지도 SDK를 사용할 앱 확정, 카카오맵 기능 ON 및 무료 적용 앱·쿼터/비용 확인
- [ ] JavaScript 플랫폼 키를 확보하고 SDK 허용 도메인 `127.0.0.1:8000` 등 등록(값은 공유하지 않음)
- [ ] 사용자에게 OpenLayers→카카오맵 화면 엔진 교체 및 임시 구 지도 복구 범위 최종 승인 확인
- [ ] 키 없는 환경과 SDK/쿼터 오류에 대한 사용자 안내, 기존 기사·지도 기능 보존 테스트 방법 승인
- [ ] 코드 적용 전후 DB 저장 건수와 기존 46개 테스트 및 신규 회귀 완료 확인

**현재 상태:** 카카오맵으로 **전환할 방향은 선택**, 본 13장 상세 계획/SDK 필수 설정을 사용자에게 제시했고 **설계 승인 및 키/도메인 준비 확인 이전이므로 코드·DB 변경 없음**.

### 13.8 D01 카카오맵 SDK 최초 구현 및 로컬 검증 대기 (2026-10-19)

- **승인 확인:** 사용자 기존 Kakao Developers 앱의 카카오맵 사용 설정 ON, JavaScript SDK 허용 도메인 등록 완료, 로컬 `traffic-api/.env`에 `KAKAO_MAP_JS_KEY` 설정 완료. README 13장 설계 및 기존 기능 보존·`kakao` 브랜치만 수정·DB 무변경 구현을 명시적으로 승인함.
- **실제 변경:** `static/map.html`의 표시 엔진 OpenLayers→Kakao Maps JavaScript SDK 전환. `GET /api/map/sdk-config`(키 없으면 `{provider:'unconfigured'}`, 있으면 `{provider:'kakao',javascript_key:...}`, `Cache-Control:no-store`)를 `app/main.py`에 추가. 기존 REST API 키/DB 연결 키는 노출하지 않음. 지도 SDK는 브라우저용 키이므로 공개 가능한 키이며 콘솔 허용 도메인 제한 필요.
- **프런트:** `kakao.maps.Map`, `Polyline` 도로별 상태색 `#16a34a/#eab308/#dc2626/#64748b`, `Marker` 출발/도착 라벨 및 색 구분, `LatLngBounds` 전체 경로 맞춤. 좌표 `vertexes`가 [경도, 위도]이면 `LatLng(위도, 경도)` 순서로 정확히 변환. 직전 Polyline/Marker를 `setMap(null)`로 지우고 다음 현재 경로를 표시함.
- **기존 F23 보존:** `/map?article_id=8&route_index=0` 기사 ID/경로 번호 검증, `/api/news/history/{id}` 불러오기, 과거 저장 거리·소요시간·정체 비율 및 KST, 기존 폼 자동 입력, **버튼 클릭 전 현재 API 미호출** 및 사용자 수동 `/api/route` 제출 후 실제 현재 경로 표시. 기존 ID/내비게이션/디자인 유지, Supabase 쓰기/스키마 변경 없음.
- **복구:** 최초 변경 직전 `static/map.html`의 실제 사본을 `static/legacy-map.html`로 보존. 새 지도에서 키 없음/SDK 로딩 실패/초기화 실패 시 사용자에게 오류 문구와 `/static/legacy-map.html` 링크(기존 article_id/route_index query 보존)를 제공. 해당 복구 페이지에서 구 OpenLayers+OSM/CARTO 모드 그대로 사용. 새 SDK 로드 완료 전에 사용자가 조회 버튼을 누르면 대기 메시지와 복구 링크를 표시. **기존 CARTO 설정 API 및 .env 키는 변경하지 않음**.
- **테스트 코드:** 기존 `test_basemap_config.py` 네 번째 테스트는 보존된 legacy 지도 대상으로 전환, `test_navigation.py`의 OpenLayers 구조 검사는 새로운 `drawCurrentRoute` 검사로 변경(기능 검사는 유지). 신규 `tests/test_kakao_map.py`에 **6개 테스트** 추가: 설정 없음/정상/잘못된 키, 카카오맵 렌더링·마커·Polyline·확대·복구 HTML, F23 과거 기사/수동 현재 조회, 기존 지도 복구 페이지. 이전 전체 46개와 합해 **52개 테스트 예상**.
- **별도 문법 검사:** GitHub의 현재 `static/map.html` inline JavaScript를 V8 함수 파서로 검사해 **syntax PASS** 확인. 실제 브라우저 SDK 로딩과 52개 Python unittest는 아직 실행되지 않았으므로 성공이라고 단정하지 않음.
- **로컬 검증 명령:** `cd C:\\workspace\\traffic_app_domain\\traffic-api` → `git pull origin kakao` → `.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_*.py" -v` → FastAPI 재시작 → `/map?article_id=8&route_index=0`에서 카카오맵 한글 라벨/기사 과거값·현재 수동 조회 색 선·마커 확인. 문제가 있으면 브라우저 개발자 도구 Console 오류(키 문자열 제거)를 확인.
- **검증 상태:** 저장소 `kakao` 코드와 문서 반영 완료, 전체 테스트·브라우저 렌더링 **사용자 실행 대기**. D01 관리자 페이지 디자인은 그 다음 단계.

### 13.9 카카오맵 전환 Windows 전체 자동 테스트 52개 통과 (2026-10-19)

- 사용자 로컬 Windows PowerShell에서 `.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_*.py" -v` 실행한 결과: **Ran 52 tests in 0.265s / OK**, 실패·오류 0개.
- 카카오맵 SDK 신규 6개 테스트 모두 통과: `KAKAO_MAP_JS_KEY` 없는 경우/잘못된 경우/정상 키, Kakao SDK·Polyline·Marker·LatLngBounds·기존 지도 복구 구조, F23 기사 요약과 현재 경로 수동 조회, `/static/legacy-map.html` 접근.
- 기존 CARTO/OSM 복구 4개, 공통 내비게이션 및 D01 구조 10개, 뉴스 초안 서명 4개, F23 6개, F16 7개, F22 8개, F17 7개 역시 모두 `ok`.
- `CARTO 지도 키 형식...`은 잘못된 키를 입력한 테스트의 예상 경고; `RuntimeError: test DB error`, `private DB detail`, `secret DB`는 예외가 이용자에게 노출되지 않는지 확인하는 모의 DB 실패의 예상 기록. `StarletteDeprecationWarning`은 비치명적.
- **판정:** API 단위/HTML 구조 자동 회귀 통과. 실제 브라우저 카카오 지도 SDK 로딩, 한국어 지명·선명도, 마커/실제 경로 폴리라인 렌더링, 기사 #8 과거 수치/실시간 수치의 분리 및 기존 지도 복구 클릭은 여전히 실화면 확인 필요.
- **다음 단계:** FastAPI 재시작, `http://127.0.0.1:8000/map?article_id=8&route_index=0`에 접속하여 지도 배경과 기사 요약의 초기 상태 캡처. 정상 확인 후 `현재 경로 새로 조회` 버튼을 눌러 실제 구간 색상·마커·예상 소요시간 표시 확인. SDK 실패 시 `기존 OpenLayers 지도로 열기` 제공 여부 확인.
- `kakao` 브랜치 **README 문서만 갱신**. DB/스키마/앱 코드 변경 없음.

### 13.10 카카오맵 빈 화면 원인과 JavaScript 구문 오류 복구 (2026-10-19)

- 사용자 첨부 map.html과 GitHub kakao 브랜치에서 동일한 JS 구문 손상 확인: 기존 227행의 F23 함수 선언 및 const query 누락, 309행의 잘못 삽입된 중복 submit 이벤트 등록.
- 이 구문 오류로 inline JavaScript 전체가 실행되지 않아 카카오맵 초기화·기사 기록 로딩이 모두 중단되고 화면에 지도 로딩 문구만 남음. VS Code의 붉은 4개 오류 표시도 같은 문제의 증상.
- static/map.html의 async function loadSavedArticleRouteFromUrl() 선언과 const query = new URLSearchParams(...) 복원, 훼손된 중복 이벤트 등록 제거. 교통 상태별 경로·마커·F23 기사 링크·카카오 REST API·기존 지도 복구 링크 유지.
- tests/test_kakao_map.py에 함수 선언 및 submit 이벤트 1개, 손상 문자열 부재 검사 1개 신규 추가. 기존 52개 + 신규 1개 = 총 53개 예상.
- 사용자 첨부 map.html에 동일 수정 적용한 inline JS를 Node.js node --check로 검사한 결과 문법 오류 없음. GitHub 저장 파일에서도 두 손상 패턴 제거 여부 확인. 실제 브라우저 실행 및 전체 Python 테스트는 사용자 재검증 전.
- 다음: git pull origin kakao → 전체 53개 unittest 실행 → 서버 재시작 → Ctrl+F5로 /map?article_id=8&route_index=0에서 한글 카카오맵과 과거 기사 요약 확인. 실패하면 F12 Console의 첫 빨간 오류만 공유하고 키/SDK URL은 숨길 것.
- DB/스키마/REST 키 변경 없음. kakao 브랜치만 수정.

### 13.11 Windows CRLF 줄바꿈으로 인한 회귀 테스트 오탐 수정 (2026-10-19)

- 사용자 Windows 전체 unittest 실행 로그: **Ran 53 tests in 0.309s / FAILED (failures=1)**. 실패는 새 `test_map_script_function_boundaries_are_intact` 하나이며 나머지 **52개 ok**.
- 원인: `map.html`의 정상적인 함수 선언 다음 줄바꿈이 Windows CRLF(`\r\n`)인데, 회귀 테스트의 `assertIn`은 Unix LF(`\n`) 문자열만 기대하여 불일치. 첨부 로그에는 실제 `async function loadSavedArticleRouteFromUrl() {`와 `const query = ...` 및 단일 폼 이벤트 등록이 존재. 이 로그만으로 SDK 실동작을 검증한 것은 아니지만 테스트 오류는 줄바꿈 차이로 확인됨.
- **수정:** `traffic-api/tests/test_kakao_map.py`의 해당 검사에서 응답 원문을 `source.replace("\r\n", "\n")`로 정규화해 CRLF/LF 양쪽을 수용. 그 밖의 손상 탐지, 단일 이벤트 등록 검사 그대로 유지.
- **변경 범위:** `kakao` 브랜치 테스트 파일 및 최상위 README만 수정, `map.html`, Kakao REST API, Supabase DB 및 스키마 변경 없음.
- **확인 대기:** Windows `git pull origin kakao` 후 전체 53개 테스트 재실행. 기대값 `Ran 53 tests ... OK`; 실제 통과 여부는 사용자 로그로 확정. 이후 Chrome 카카오맵 한글 기본 지도·기사 #8 요약·수동 교통 경로선 확인.

### 13.12 Windows 카카오맵 수정 후 전체 53개 테스트 통과 (2026-10-19)

- 사용자가 로컬 PowerShell에서 전체 unittest를 재실행한 결과: **Ran 53 tests in 0.229s / OK**, failures=0, errors=0.
- 지난 실행에서 실패했던 `test_map_script_function_boundaries_are_intact`가 Windows CRLF 정규화 수정 뒤 **ok**로 통과했음을 확인. 신규 카카오맵 지도 구성 및 OpenLayers 복구, F23 뉴스→지도 연결, F16 검색, F17 기록 그래프, F22 CSV 다운로드, D01 디자인 등 나머지 회귀도 모두 `ok`.
- `StarletteDeprecationWarning`은 비치명적. `CARTO 지도 키 형식...`은 잘못된 키 검사 중 예상 경고, `test DB error` / `private DB detail` / `secret DB`는 의도적 모의 DB 실패이며 관련 테스트 모두 통과.
- **판정:** 전체 53개 자동 테스트 통과. 실제 Chrome에서 Kakao Maps SDK 로딩·한글 지도·기사 #8 저장 요약 표시 및 현재 경로 수동 조회 후 Polyline/마커 렌더링은 아직 별도 화면 검증 필요.
- **다음 확인:** Uvicorn 재시작 → `http://127.0.0.1:8000/map?article_id=8&route_index=0` 접속 → `Ctrl+F5` → 기사 과거 정보와 카카오맵 배경이 함께 나오는 초기 화면 캡처. 정상인 경우 버튼 클릭 후 현재 경로선·상태 색상 캡처. 실패 시 F12 Console 오류 메시지를 API 키 노출 없이 공유.
- README 기록만 갱신. 앱 코드·DB·키·스키마 변경 없음, `kakao` 브랜치만 수정.

### 13.13 카카오맵 HTML 종료 태그 누락 수정 (2026-10-19)

- 사용자 Chrome 초기 화면에서 계속 `카카오맵을 불러오는 중입니다.`만 출력되고 배경 지도/기사 #8의 저장 경로 카드가 나타나지 않음. 직전 53개 unittest는 모두 통과했으나 브라우저 실행은 실패.
- `kakao` 브랜치의 실제 `traffic-api/static/map.html` 파일을 직접 검사한 결과 **inline `<script>`가 닫히지 않았고 파일 끝의 `</script>`, `</body>`, `</html>`이 통째로 누락**되어 있었음. 앞선 파일 수정 당시 잘못된 문자열 위치 기반 조합으로 문서 꼬리 부분이 잘린 것이 원인. HTML 파서가 JavaScript를 정상 실행하지 못해 SDK 초기화와 F23 기사 조회가 중단된 현상과 일치. 이전 문법 검사는 빈 문자열을 추출하여 통과한 것이었으므로 유효한 전체 본문 문법 검사로 인정할 수 없음.
- **수정:** `map.html` 끝에 `</script>`, `</body>`, `</html>` 복원. JS inline 본문 11,722자를 추출해 V8 JavaScript 구문 분석 `new Function(script)` 검증 **PASS**. 현재 `<script` 여는 태그 2개(외부 navigation JS + 인라인 JS), 닫는 `</script>` 2개, 본문/HTML 닫는 태그 정상 확인.
- **재발 방지:** `tests/test_kakao_map.py`에 `test_map_html_closes_inline_script_and_document` 추가, script 열기/닫기 개수, 문서 끝 `</html>`, 인라인 JS 안에 SDK 초기화와 기사 로더 호출 포함 검사. 기존 53개에 1개 추가돼 전체 **54개 예상**. 실제 로컬 전체 테스트와 Chrome 재검증은 아직 완료 전.
- **다음:** `git pull origin kakao` → `.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_*.py" -v` (54개 `OK` 확인) → 서버 재시작 및 `Ctrl+F5`로 `/map?article_id=8&route_index=0` 확인. 카카오맵 로딩 또는 기사 카드가 여전히 실패하면 Chrome F12 Console의 첫 오류 문구를 키/SDK URL 없이 확인.
- 기존 REST API 경로, 기사 저장, 지도 Polyline/마커, OpenLayers 복구 파일, Supabase DB/스키마·API 키는 변경하지 않음. 오직 `kakao` 브랜치의 HTML, 테스트, 문서 수정.

### 13.13 빈 지도 원인: HTML 종료 태그 복원 및 회귀 검사 추가 (2026-10-19)

- 사용자 브라우저에서 `/map?article_id=8&route_index=0` 페이지가 계속 `카카오맵을 불러오는 중입니다.`에 머물고 과거 기사 #8 정보도 로딩되지 않는 것을 확인. 53개 Python 문자열 기반 자동 테스트는 통과했지만 지도 실화면은 실패.
- GitHub `kakao`의 `traffic-api/static/map.html` 실제 파일 끝에 `</script>`, `</body>`, `</html>` 종료 태그가 모두 빠져 있음을 확인. HTML 파서가 스크립트 끝을 인식하지 못해 지도 초기화와 F23 기사 연결이 실행되지 않는 현상을 설명함.
- `map.html` 맨 끝에 세 종료 태그를 복원함(커밋 `d7134d5`). 복원된 전체 inline JavaScript를 분리하여 V8 JavaScript 문법 파서로 확인: **PASS**, script 시작/끝 태그 각각 2개(외부 공통 메뉴 script 1개 + 지도 inline 1개).
- 사용자 재적용 요청에 따라 `tests/test_kakao_map.py`에 **`test_map_html_tags_close_correctly`** 추가. `<script>` 시작/끝 수 일치 및 정확한 `</script>`, `</body>`, `</html>` 문서 끝을 CRLF/LF 모두에서 검사하여 동일 장애 재발을 방지. 기존 53개 + 신규 1개 = **54개 자동 테스트 예상**. 사용자 로컬 실행 전에는 통과 단정하지 않음.
- `kakao` 브랜치만 수정. 앱 데이터/스키마, REST API 키, Supabase, 기존 교통 경로선/마커/F23 기능 변경 없음.
- 다음 검증: `git pull origin kakao` → 전체 54개 unittest → FastAPI 재시작 후 `Ctrl+F5` → 카카오맵 한글 도로명과 기사 #8 저장 정보 표시 여부 캡처. 문제 재현 시 Chrome F12 Console 첫 에러만 키/SDK 전체 URL 가리고 공유.

### 13.13 카카오맵 HTML 복구 이후 전체 Windows 테스트 55개 통과 (2026-10-19)

- 사용자 PowerShell에서 `python -m unittest discover -s tests -p "test_*.py" -v` 전체 실행 확인: **Ran 55 tests in 0.272s / OK**, 실패/오류 0개.
- 추가된 `test_map_html_closes_inline_script_and_document`, `test_map_html_tags_close_correctly` 등 HTML 종료 태그 검증과 `test_map_script_function_boundaries_are_intact`가 모두 `ok`. 기존 카카오맵 SDK 설정, 레거시 OpenLayers 복구, F23 뉴스→지도 연결, F16 뉴스 검색, F17 교통 기록 차트, F22 CSV 다운로드, D01 공통 UI 관련 테스트도 모두 통과.
- 중간 로그의 `test DB error`, `private DB detail`, `secret DB`는 모의 DB 오류 처리 검사의 예상 출력이며 `StarletteDeprecationWarning`은 비치명적. `CARTO 지도 키 형식...` 역시 유효하지 않은 키에 대한 예상 검사 메시지.
- **검증 범위:** Windows 자동 회귀 55개 전부 통과. Chrome에서 카카오맵 SDK가 실제로 로드되어 한글 지도 타일이 렌더링되는지, 기사 #8 저장 요약 및 버튼 수동 재조회 후 교통 색상 선·마커가 보이는지는 여전히 브라우저 실확인 필요.
- **다음 순서:** 실행 중인 FastAPI를 재시작하고 `http://127.0.0.1:8000/map?article_id=8&route_index=0`에서 Ctrl+F5 → 지도 및 기사 저장 정보가 나타나는지 확인. 지도 로딩 실패 시 Console 첫 오류(키 비공개) 확인. 이후 현재 경로 새로 조회 버튼 테스트.
- README 기록만 갱신. `kakao` 브랜치 유지, DB/스키마/키/앱 코드 수정 없음.

### 13.14 카카오맵 HTML 복구 후 Chrome 초기 화면 실검증 (2026-10-19)

- 사용자 Chrome 스크린샷에서 `/map?article_id=8&route_index=0`의 카카오맵 한글 지도 타일(서울특별시청, 중구, 종로구, 용산구, 강남구 등) 및 지도 확대/축소 컨트롤이 정상 렌더링됨. 이전의 빈 화면·무한 '불러오는 중' 문제가 해소됨.
- 지도 위 안내가 **`카카오맵 지도 표시 중 · 한국어 지명과 도로명`**으로 변경됨. 기사 #8 관련 상단 카드의 '뉴스 기사로 돌아가기' 링크가 보이고, 출발지 `서울역`, 목적지 `잠실역 2호선`이 자동 입력됨. 결과 메시지는 **`과거 저장 경로를 확인했습니다. 현재 경로를 보려면 조회 버튼을 누르세요.`**로 나타나 F23 저장 기사 정보 로딩이 확인됨.
- 수동 현재 경로 조회 전 경로선이 없는 상태는 F23 설계와 일치. 과거 저장값을 현재 경로로 자동 그림으로 재현하지 않음.
- **현재 판정:** HTML 종료 태그 복구 후 카카오 SDK 지도 렌더링과 F23 기사→지도 초기 연결 브라우저 실검증 성공. **실제 현재 자동차 경로 조회, 도로 구간별 Polyline 색과 마커, 예상 시간 표시는 아직 검증 전**.
- **다음 확인:** 이 화면에서 `현재 경로 새로 조회` 클릭 후 색상별 경로선/출발·도착 마커/현재 예상 소요시간이 보이는지 스크린샷 확인. 과거 기사 저장 요약은 그대로 유지돼야 함. 오류 시 Console 내용에서 API 키·SDK URL은 제거하여 공유.
- 앱 코드/DB/스키마/키는 변경하지 않고 `kakao` 브랜치 README 기록만 추가.

### 13.15 카카오맵 현재 경로 실사용 성공 및 새 채팅 인계 (2026-10-19)

- 사용자가 Chrome `/map?article_id=8&route_index=0`에서 **현재 경로 새로 조회**를 클릭한 최종 스크린샷을 제공. **서울역 → 잠실역 2호선**, 현재 예상 **55.2분**, 카카오맵 한글 지명·도로 상세도·출발/도착 마커·도로 교통 상태별 빨간색/녹색/회색 경로선·경로 자동 범위 맞춤이 정상 표시된 것을 확인. 55.2분은 이번 조회 시점의 값이며 저장 기사 #8 과거 예상 40.4분과 달라도 정상. 다른 시점에는 다르게 조회될 수 있음.
- **판정:** D01 카카오맵 지도 엔진 전환의 브라우저 초기 화면 검증뿐 아니라 실제 현재 자동차 경로 선 표시까지 사용자 실확인 **통과**. 지도 앱 코드/DB/스키마 수정 없음. 자동 테스트 최신 확인은 README 13.13의 **Ran 55 tests in 0.272s / OK**.
- **다음 개발 순서:** D01 관리자 `/admin` 화면 디자인 개선. 기존 통합 D01 설계는 README 12장; 구체 관리자 화면 설계를 루트 README에 별도 기술·승인받은 뒤, 인증·초안 생성/미리보기/확인 후 저장/로그아웃 등 기존 JS/API 기능 보존하며 구현. DB를 테스트 목적으로 변경하거나 임의 저장하지 않음.
- 사용자는 현재 대화 최대 길이 경고 때문에 새 채팅으로 이동하기를 원하며, 이전 대화 링크만으로 맥락이 충분히 전달되지 않았음을 보고. 이를 해결하기 위해 **kakao 브랜치 루트 `PROJECT_HANDOFF.md`** 생성: 작업 규칙, 파일·명령, 기존 기능, 최신 검증, 남은 D01 관리자 작업, 새 채팅 첫 메시지 템플릿을 보존. **새 채팅에서 이 파일과 루트 README를 먼저 읽도록 지시**, 가능하면 동일 ChatGPT 프로젝트 내에서 새 대화를 시작할 것.
- 단, 과거 모든 메시지·첨부·미공개 로그까지 완전 자동 이관되는 기능은 아니며, 인계 문서가 작업 맥락의 지속 가능한 대체 기록임.


---

## 14. D01 관리자 화면 전용 개선 설계 — 승인 대기 (2026-10-19)

> **상태: 설계 문서만 기록 / 사용자 별도 승인 전 코드 구현 금지.** 작업 대상 브랜치는 `kakao`만. 본 절은 실제 `traffic-api/static/admin.html`, `app/main.py`, `app/admin_auth.py`, 공통 디자인 CSS와 12~13장, `PROJECT_HANDOFF.md`를 읽은 뒤 작성했다. 로그인·초안 생성·기사 저장을 실제 실행하거나 DB에 쓰지 않았다. 기존 55개 테스트 통과 및 지도 Chrome 합격은 13장에 기록된 **이전 검증**으로, 본 문서 작업에서 재실행한 것이 아니다.

### 14.1 현행 구현과 개선 목표

- 현행 `/admin`은 로그인 시 `.login-container` 최대 420px, 로그인 후 `body.admin-active .login-container` 최대 900px. 로그인 폼·인증 후 패널·초안 작업이 하나의 컨테이너에 있으며 로그인 전에는 `adminPanel`이 CSS `display:none`으로 가려져 있다.
- 공통 `design-system.css`, `navigation.css`, `navigation.js`가 이미 로드된다. 상단 메뉴 hover 순간만 강조하고 키보드 `:focus-visible` 표시를 유지해야 한다.
- 현재 JS는 `POST /api/admin/login` → `GET /api/admin/me`의 관리자 인증 성공 후에만 `loginForm`을 숨기고 `adminPanel`을 표시한다. 관리자 토큰은 브라우저 JS 메모리 변수 `adminAccessToken`에만 둔다.
- 생성 버튼은 `POST /api/admin/news/generate`로 세 경로를 조회하고 서버 서명 `draft_token`과 초안을 받는다. `draftPreview`의 기사 제목/본문/경로별 표를 표시한 뒤에만 저장 버튼을 활성화한다. 저장 버튼을 실제 클릭하면 `POST /api/admin/news/save`가 호출된다. 로그아웃 시 토큰·초안 표시·저장 버튼 상태를 초기화한다.
- **목표:** 로그인 전에는 신뢰성 있는 관리자 인증 안내, 로그인 후에는 ‘① 초안 생성 → ② 내용 검토 → ③ 명시적 저장’ 작업 단계를 한눈에 보이게 배치. 디자인 개선이지 권한/저장 절차의 재설계가 아니다.

### 14.2 화면 변경 상세(구현 제안)

**A. 로그인 전 /admin — 네이비 히어로 + 로그인 카드**

1. 공통 네이비 상단 메뉴 아래에 가로 최대 1120px의 관리자 소개 영역을 둔다. 왼쪽은 네이비 `#13243b` 배경의 ‘서울 교통 뉴스 · 관리자 작업실’ 제목, 인증이 필요한 기능과 ‘초안 검토 전 자동 저장되지 않음’ 안내; 오른쪽은 흰색 로그인 카드다. 화면 너비 850px 이하에서는 상하 1열로 쌓는다.
2. 카드에는 ‘관리자 로그인’ 제목, 이메일·비밀번호 레이블/입력칸, 파란색 로그인 버튼, `loginMessage` 상태/오류 메시지를 둔다. 비밀번호 값 표시나 토큰·관리자 UID 화면 노출은 금지한다.
3. 인증 전 `adminPanel`은 숨김을 유지한다. **CSS 스타일만으로 인증을 대신하지 않는다.** 레이아웃용 외부 래퍼를 추가하더라도 기존 `loginForm`의 표시 상태 변경이 레이아웃과 충돌하지 않게 로그인/인증완료 전환을 함께 검증한다.

**B. 인증 후 /admin — 관리자 작업실**

1. 기존 `body.admin-active` 상태에서 중앙 최대 1120px 작업실을 사용한다. 상단은 ‘관리자 작업실’ 제목/인증 확인 안내와 회색 보조 ‘로그아웃’ 버튼을 배치한다. 로그아웃은 항상 접근할 수 있어야 한다.
2. 작업 안내를 번호가 있는 3단계 카드 또는 단계 표시줄로 나타낸다: `1. 새 교통 뉴스 생성`, `2. 미리보기와 경로별 자료 확인`, `3. 확인한 뉴스 저장`. 단계는 사용 흐름 설명이며 별도 API나 자동 진행 기능은 추가하지 않는다.
3. 초안 생성 버튼(`generateDraftButton`)과 상태 영역(`draftStatus`)은 작업실 상단에 배치한다. 불러오는 중·조회 실패·초안 만료/새 생성 안내를 텍스트로 전달하고 기존 JS의 버튼 disabled 처리와 상태 변경을 유지한다.
4. 기사 미리보기(`draftPreview`)는 흰색 카드로 구분하고 제목(`draftTitle`), KST 조회시각(`draftRetrievedAt`), 리드(`draftLead`), 본문(`draftBody`), 분석 범위/한계(`draftNotice`), 경로별 데이터 표(`draftRoutes`) 순서로 보여 준다. 미리보기 전에는 `hidden` 유지, 가상 데이터를 실제 기사처럼 채우지 않는다.
5. 저장 구역은 미리보기 아래에 두어 ‘기사와 경로별 값을 검토한 뒤 저장’이라는 경고성 안내, `saveDraftButton` 및 `savedArticleLink`를 포함한다. **새 초안 생성만으로 저장하지 않고 저장 API는 기존 저장 버튼 클릭에만 묶는다.** 저장 성공/중복/실패 메시지와 저장 후 비활성화 상태를 보존한다.
6. 표는 좁은 화면에서 `.table-scroll` 가로 스크롤을 유지한다. 단위(km, 분, %)와 결측값 문구를 그대로 보존한다.

**C. 색상·반응형·접근성**

- 기존 CSS 변수 우선 사용: 네이비 `#13243b`, 블루 `#2463eb`, 청록 `#087e8b`, 배경 `#f3f6fa`, 카드 흰색, 회색 설명 텍스트. 교통 원활/정체 색과 관리자 단계 색은 의미를 혼동하지 않는다.
- 데스크톱(예: 1280px)은 소개+로그인 2열 / 관리자 작업실의 읽기 폭과 작업 구역을 분리. 850px 이하에서는 로그인 소개·카드를 1열; 600px 이하에서는 카드 내부 여백을 줄이고 작업 버튼을 세로로 쌓는다. 320px/390px/768px/1280px 확인.
- 입력 레이블, 상태 메시지의 `role=status`, 오류를 읽을 수 있는 명도 대비, 키보드 Tab 순서 및 `:focus-visible` 유지. 애니메이션은 필수 아님. 상단 공통 메뉴·모바일 토글·hover/포커스 기존 규칙 변경 금지.
- 화면 배치는 아직 사용자의 Chrome 스크린샷으로 검증되지 않았다. **이 절은 텍스트 설계이지 실제 렌더링 결과가 아니다.**

### 14.3 기존 기능·보안 계약 (절대 보존)

- 기존 DOM ID 유지: `loginForm`, `adminEmail`, `adminPassword`, `loginButton`, `loginMessage`, `adminPanel`, `logoutButton`, `generateDraftButton`, `saveDraftButton`, `draftStatus`, `draftPreview`, `draftTitle`, `draftRetrievedAt`, `draftLead`, `draftBody`, `draftNotice`, `draftRoutes`, `savedArticleLink`, `sharedNavigation`.
- 보존할 JS 상태 및 이벤트: `adminAccessToken`, `pendingDraftToken`; 로그인 submit, 로그아웃 click, 생성 click, 저장 click; 권한 확인 전 패널 비표시, 실패 시 비밀번호 삭제 및 저장 비활성화, 로그아웃 시 초기화, 저장 성공 후 중복 클릭 방지.
- 보존할 서버 계약: `POST /api/admin/login`, `GET /api/admin/me`, `POST /api/admin/news/generate`, `POST /api/admin/news/save`, `require_admin`, Supabase Auth 사용자 검증/관리자 UID 비교, 서버 서명 초안 유효기간 및 동일 초안 저장 보호.
- **불변 범위:** `main` 브랜치, Python API 서버 동작, REST·JS 키/환경변수·관리자 비밀번호, Supabase RLS/테이블/스키마/기존 데이터, `traffic_information` 약 30,538행, `traffic_news_articles`, `traffic_route_snapshots`, 기존 지도 및 뉴스 기능. 로그인·기사 저장을 자동 실행하는 테스트 추가 금지.
- 실제 소스에서 확인한 `admin.html`에는 `loginForm.style.display`와 `adminPanel.style.display` 전환이 있다. HTML 래퍼를 나누는 경우 **로그인 성공 직후 빈 카드/남은 히어로 영역이 보이지 않도록** CSS/JS 표시 계약을 작은 변경 단위로 검증한다.

### 14.4 구현 예정 파일 및 작업 단위 (승인 후에만)

1. **기본 수정 후보:** `traffic-api/static/admin.html`의 로그인 전/인증 후 HTML 섹션 구조와 해당 문서에 한정한 CSS. 기존 JS의 인증·생성·저장 처리 본문은 원칙적으로 건드리지 않는다. 레이아웃 전환에 꼭 필요한 최소 UI 표시 코드만 별도 점검 후 반영한다.
2. **테스트 추가 후보:** `traffic-api/tests/test_admin_design.py` — 보존 ID, 관리자 패널 숨김, API 호출·기존 이벤트 시그니처, 종료 HTML 태그 및 JS 본문 누락·중복 이벤트 방지, 공통 디자인/반응형 CSS 계약. 기존 `test_news_drafts.py` 등 회귀 테스트 유지.
3. **변경 금지:** `traffic-api/app/main.py`, `app/admin_auth.py`, DB 관련 파일, 기존 공유 메뉴 JS/CSS, `.env`, Supabase 데이터. 새 라이브러리·새 API·새 DB 테이블 없음.
4. **결과 기록:** 구현·테스트·사용자 실화면 승인 결과는 반드시 **루트 `README.md`의 다음 절**에 단계별로 남기고 `kakao` 커밋을 안내한다.

### 14.5 승인 후 검증 순서 (한 번에 하나씩)

1. Git 브랜치 및 변경 파일 확인: `git branch --show-current`, `git status --short`; `kakao` 및 의도한 관리자 UI/테스트 파일만 수정 확인.
2. Windows PowerShell: `cd C:\workspace\traffic_app_domain\traffic-api` → `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v`. 기존 **55개 회귀 + 신규 관리자 테스트** 모두 통과해야 하며 구체 개수/시간은 실행 결과로만 기록.
3. 같은 위치에서 `.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload` 실행; 사용자가 Chrome `http://127.0.0.1:8000/admin`에서 Ctrl+F5 후 **로그인 전 디자인/폼/관리자 작업실 비표시** 스크린샷 제공.
4. 실제 비밀번호는 채팅에 공유하지 않고 로컬 Chrome에서만 입력: 관리자 로그인 성공 후 `/api/admin/me` 검증, 작업실 표시·로그아웃 위치 스크린샷 확인. 잘못된 인증 시 작업실 노출이 없어야 함.
5. 사용자 동의하에 **초안 생성까지만** 수행하고 미리보기 제목/본문/KST/경로표·상태/저장 버튼 표시 및 모바일·키보드 사용성 검증. **'확인한 뉴스 저장' 클릭은 실행하지 않음**. 미리보기 호출이 외부 Kakao API 비용/쿼터를 소비할 수 있으므로 사용자 선택 후 실시.
6. 로그아웃 시 작업실 비표시·토큰/초안 초기화·로그인 폼 재표시 확인. Chrome Console 오류 여부 확인 시 키/토큰 등 민감값 제거.
7. 저장 API의 권한 보호·서명·중복 방지는 **기존 모의 테스트로만** 회귀 검증. 실제 DB 데이터나 카운트를 바꾸는 저장 테스트 금지. 읽기 전용 카운트 확인이 가능할 때만 보존 확인.
8. 각 검증 결과/미검증 항목/스크린샷 판정·커밋 SHA를 루트 README에 추가 기록하고 다음 단계 진행 여부를 사용자에게 묻는다.

### 14.6 승인 요청

- **이번 변경:** 루트 README에 D01 관리자 화면 변경 설계와 검증 계획을 기록하는 것까지.
- **승인 전 절대 하지 않을 작업:** 관리자 HTML/CSS/JS 수정, Python/API/테스트 코드 변경, 실제 관리자 로그인 시도, 기사 초안 생성/저장 호출, DB 수정, `.env` 수정, `main` 브랜치 변경.
- **다음 결정:** 사용자에게 본 설계의 로그인 전 2열 구성, 인증 후 3단계 작업실, 모바일 배치와 검증 범위 승인을 받은 뒤 별도 구현 착수.


### 14.7 D01 관리자 UI 승인 후 구현 반영 및 검증 대기 (2026-10-19)

- **사용자 승인:** README 14장 D01 관리자 화면 상세 설계를 승인하고 `kakao` 브랜치에서 UI 구현 및 테스트 추가를 요청함. 인증·DB·기존 저장 절차 변경은 승인하지 않음.
- **구현 파일:** `traffic-api/static/admin.html` 한 파일의 HTML/CSS만 교체. 로그인 전 네이비 소개 영역 + 흰색 로그인 카드(데스크톱 2열, 850px 이하 1열), 로그인 후 3단계 관리자 작업실(① 생성 ② 미리보기 ③ 직접 저장), 모바일 600px 이하 작업 버튼 세로 배치, 경로별 표 가로 스크롤 및 공통 D01 토큰 활용.
- **중요 구조:** 로그인 폼을 `.admin-login-layout` 내부에, 관리자 작업실은 별도 `#adminPanel` 내부에 배치. `body.admin-active .admin-login-layout { display: none; }`으로 인증 성공 시 로그인 카드·소개 영역 모두 숨기고 기존 JS의 `adminPanel.style.display = "block"` 전환을 유지. `.admin-panel { display: none; }`으로 미인증 관리자 작업실 초기 노출 방지.
- **기능 보존:** 기존 인라인 관리자 JS **내용 변경 없음**, 19개 중요 DOM ID 각각 하나씩 존재 확인, 관리자 REST API/서명 초안·미리보기/저장 이벤트, 로그인 후 권한 재검증·로그아웃 초기화 및 저장 버튼 초기 비활성화 유지. 실제 외부 API 호출/기사 저장/DB 변경 없음.
- **테스트 추가:** `traffic-api/tests/test_admin_design.py`에 4개 테스트 작성: 필수 DOM ID 고유성, 로그인/작업실/반응형 CSS 구조, 인증/저장 API 이벤트 계약, 문서 닫힘/스크립트 개수/이벤트 중복 검사. 외부 네트워크·DB 접근 없는 정적 구조 테스트임.
- **이 대화에서 실행한 점검:** GitHub 파일을 다시 읽어 JS 구문을 V8 파서로 검사 **PASS**; 19개 ID 고유성 **PASS**; `<script>`와 `</script>` 각각 2개; 최종 `</html>` 존재; 신규 테스트 함수 정의 4개 존재. 이는 **전체 Python unittest 실행이나 실제 브라우저 렌더링 검증과 다름**.
- **Windows 전체 테스트 미실행:** 사용자 로컬 `.venv` 및 운영 중인 서버·실제 Chrome 화면에는 이 연결로 접근하지 않았음. 이전 55개 통과 기록을 변경 후 테스트 결과로 대체하지 않음. 신규 4개 추가로 **59개 예상**이며 실제 숫자/통과 여부는 사용자의 실행 출력으로 확정.
- **반영 커밋:** 관리자 UI `4d785a1`, 신규 테스트 `b55f921` (둘 다 `kakao`). 그 외 API/DB/환경 파일 변경 없음. 최종 설계/결과 기록 커밋은 별도 안내.
- **다음 사용자 검증 (한 번에 하나):** Windows PowerShell에서 `cd C:\workspace\traffic_app_domain\traffic-api` → `git pull origin kakao` → `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v` 순서. 테스트 결과를 확인한 뒤 `/admin` 로그인 전 Chrome 화면부터 검증. 관리자 계정이나 비밀번호·토큰을 채팅으로 전달하지 말 것.
- **잔여 확인:** 사용자 Chrome에서 로그인 전 레이아웃, 관리자 인증 후 작업실, 저장 없이 미리보기·로그아웃, 모바일 320/390/768/1280px 및 Tab 포커스/Console 상태. **기사 저장 버튼은 테스트 목적으로 클릭하지 않음.** 새 초안 생성은 Kakao API 호출 가능성이 있어 사용자 선택 후 진행. 문제 발견 시 승인된 범위 내 최소 수정 및 README 검증 기록 추가.

### 14.8 D01 관리자 화면 Windows 전체 59개 자동 테스트 통과 (2026-10-19)

- 사용자가 `kakao` 브랜치에서 `git pull origin kakao` 완료한 뒤 Windows PowerShell `C:\workspace\traffic_app_domain\traffic-api`에서 `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v` 실행 결과를 제출함.
- **실제 결과: `Ran 59 tests in 0.340s / OK`**, 실패 0, 오류 0. 신규 `test_admin_design.py` 4개(HTML·script 종료, 로그인/작업실 배치, 비밀번호/기사 저장 계약, DOM ID 고유성) 모두 `ok`; 기존 55개 회귀 검사도 `ok`.
- `RuntimeError: test DB error`, `private DB detail`, `secret DB` 추적은 기존 오류 응답 비노출 mock 테스트에서 의도적으로 출력됐으며 각 테스트가 `ok`로 끝남. `StarletteDeprecationWarning`은 비치명적 라이브러리 경고로 이번 실패를 뜻하지 않음.
- **검증 범위 구분:** 자동 테스트 합격은 Chrome의 실제 배치·인터랙션 확인을 대체하지 않음. 미인증 로그인 화면, 로그인 후 작업실, 반응형·Tab 포커스·Console 및 안전한 로그아웃은 사용자 브라우저 검증 대기. 기사 저장 호출·DB 데이터 변경 없음.
- **다음 단계:** 서버 시작 후 `http://127.0.0.1:8000/admin`에서 로그인 전 화면을 Chrome으로 확인하고 스크린샷 검토. 계정·비밀번호·토큰은 공유하지 않음. `main` 브랜치, 관리자 API 및 DB 변경 없이 `kakao` 루트 README에 테스트 결과만 기록.

### 14.9 D01 관리자 로그인 전 Chrome 실화면 검증 (2026-10-19)

- 사용자가 로컬 Chrome `http://127.0.0.1:8000/admin`의 로그인 전 전체 화면 스크린샷을 제공함. **이미지를 직접 확인**한 결과 공통 상단 네이비 메뉴, 왼쪽 네이비 소개 영역, 오른쪽 흰 로그인 카드, 이메일/비밀번호 입력란 및 파란 로그인 버튼이 보임. '초안을 생성해도 자동 저장되지 않는다'는 안내가 표시됨.
- 데스크톱 2열 배치와 여백/정렬이 승인된 README 14.2 설계에 부합하며, 스크린샷 범위에서 요소 잘림·겹침 없음. 미인증 상태에서 관리자 작업실은 보이지 않음. **로그인 전 데스크톱 시각 검증 합격**.
- 스크린샷만으로 버튼 기능, 실제 관리자 인증, 서버 권한 보호, 모바일 반응형, 키보드 접근성, Console 오류 및 저장 기능을 검증했다고 주장하지 않음. 이전 사용자 Windows 전체 59개 자동 테스트 OK 기록은 14.8 참고.
- **다음 확인:** 사용자가 본인 로컬 Chrome에서만 관리자 계정으로 로그인하고, 인증 후 관리자 작업실 전체 화면 스크린샷 제공. 비밀번호·토큰·개인 이메일 공유 금지. 아직 초안 생성·기사 저장 버튼은 누르지 않음. DB/API/HTML/JS 변경 없음.

### 14.10 D01 관리자 로그인 후 Chrome 작업실 화면 검증 (2026-10-19)

- 사용자가 로컬 Chrome `/admin`에서 관리자 로그인 후 전체 작업실 스크린샷을 제공함. **실제 이미지에서 확인된 범위:** 공통 네이비 내비게이션, 네이비 관리자 헤더의 '관리자 작업실' 및 '관리자 권한 확인 완료' 안내, 오른쪽 로그아웃 버튼, ① 새 교통 뉴스 생성 ② 내용과 수치 검토 ③ 확인한 뉴스 저장 단계 카드, 아래의 독립적인 초안 생성·미리보기·검토 후 저장 구역이 모두 화면에 배치됨.
- 아직 초안이 없는 상태에서 `아직 생성된 기사가 없습니다.` 문구가 표시되며 미리보기 기사 세부내용은 표시되지 않음. `확인한 뉴스 저장` 버튼은 회색 비활성화 상태로 보임. 화면 범위에서 카드의 겹침/잘림은 관찰되지 않음. **데스크톱 인증 후 관리자 작업실 시각 검증 합격**.
- 로그인 후 작업실이 보이는 것으로 로그인 흐름의 화면 전환은 확인되지만 **스크린샷만으로 서버 인증 처리 내부, 버튼 이벤트, 오류 응답, 모바일/키보드 접근성, Console 및 실제 DB 저장은 검증되지 않음**. Windows 전체 59개 자동 테스트 통과는 14.8 참조.
- 사용자 지시대로 실제 기사 저장 및 DB 변경을 수행하지 않았으며 `kakao` 루트 README만 기록. 다음에는 사용자 의사 확인 후, Kakao 호출이 가능한 **'새 교통 뉴스 생성'만** 실행해 미리보기 데이터·상태/버튼 전환을 확인하고, 저장 버튼은 클릭하지 않음.

### 14.11 D01 입력창 주황색 포커스 외곽선 제거 설계 — 코드 수정 승인 대기 (2026-10-19)

- **사용자 요구:** 지도 출발지 등 텍스트 입력창을 클릭했을 때 나타나는 두꺼운 주황색 테두리가 싫음. 색상을 파란색으로 바꾸는 것도 원치 않으며 **입력창의 외곽선을 아예 없애고 기존 기본 테두리를 유지**하기 원함. 이번 `ok`는 **설계를 README에 기록하는 절차**에 대한 동의로 해석하며 CSS 코드 변경은 별도 확인 후 수행.
- **실제 원인 확인:** `traffic-api/static/design-system.css`의 `:where(button, input, select, textarea, a):focus-visible` 규칙이 `outline: 3px solid #f59e0b; outline-offset: 3px`을 적용함. 텍스트 입력칸은 마우스로 클릭해도 Chrome의 `:focus-visible` 조건에 해당할 수 있음. CSS 포커스 스타일과 한글 IME의 자음 조합 문제는 별개이며 입력기 설정 변경은 본 코드 작업에 포함하지 않음.
- **제안 변경 파일:** `traffic-api/static/design-system.css` 하나. 해당 공통 선택자에서 **`input, textarea, select`만 제외하고** `:where(button, a):focus-visible` 규칙으로 제한하여 텍스트 입력 및 선택 컨트롤의 D01 주황색 외곽선을 없앤다. `outline:none` 같은 전역 강제 제거, 새 파란 테두리, DOM/JavaScript 수정은 하지 않는다. 기존 입력란 기본 border는 각 페이지 CSS가 지정한 값을 유지한다.
- **유지:** 상단 메뉴 `.site-nav`의 키보드 포커스 표시와 버튼/링크의 포커스 표시, 다른 페이지 색상/호버 동작, 관리자 로그인·뉴스 생성·저장, Kakao SDK/REST, DB 및 `.env`. 일부 개별 페이지의 별도 CSS나 브라우저 자체 기본 포커스 스타일이 남을 수 있으므로 **모든 강조가 사라질 것이라고 미리 단정하지 않음**.
- **접근성 주의:** 입력란은 마우스 포커스와 키보드 포커스 모두에서 공통 주황색 외곽선이 사라질 수 있으며, 기존 테두리만으로 키보드 사용자가 현재 위치를 충분히 구분하기 어려울 수 있음. 요청에 따라 외곽선을 없애되 키보드 접근성 손실을 실제 Tab 검증에서 명확히 알리고, 추가 대체 표시가 필요하면 **별도 설계·승인**을 받는다. 순수 CSS `:focus-visible`만으로 텍스트 입력의 마우스 클릭/키보드 이동을 항상 정확하게 구분한다고 주장하지 않는다.
- **승인 후 테스트 계획:** (1) `kakao` 브랜치 확인, (2) 공통 CSS의 선택자·다른 버튼/링크/메뉴 포커스 보존에 대한 정적 회귀검사 추가 또는 기존 테스트 확대, (3) 사용자 Windows PowerShell 전체 `unittest discover -s tests -p "test_*.py" -v` 재실행 (직전 59개 합격 기록을 새 결과로 간주하지 않음), (4) Chrome `/map` 출발지·목적지 입력창 마우스 클릭에서 주황색 외곽선 소멸 확인, (5) Tab 이동 시 입력창과 버튼의 초점 식별 가능 여부, `/admin` 로그인 입력창, 모바일 레이아웃, Console 확인, (6) 결과를 루트 README에 추가 기록.
- **금지:** `main` 브랜치 변경, API/DB/스키마/인증/저장 절차 및 환경 키 수정, 기사 자동 생성·저장, 불필요한 전체 CSS 재작성.

### 14.12 D01 입력창 주황색 포커스 외곽선 제거 코드 반영 (2026-10-19)

- **승인:** 사용자가 14.11 설계를 확인한 뒤 CSS 수정·커밋·푸시를 명시적으로 요청함. 작업 브랜치는 **`kakao`**.
- **실제 수정:** `traffic-api/static/design-system.css`의 공통 포커스 선택자 `:where(button, input, select, textarea, a):focus-visible`을 `:where(button, a):focus-visible`로 제한. 입력·선택 컨트롤에서 공통 주황색 아웃라인을 제외하고, 버튼/링크의 기존 주황색 포커스 규칙은 유지. 새 파란색 테두리나 `outline:none` 강제 규칙은 추가하지 않음. 일부 입력창에는 브라우저 기본 아웃라인 등이 남을 수 있으므로 실제 Chrome 확인 필요.
- **테스트 추가:** `traffic-api/tests/test_navigation.py`에 `test_d01_form_fields_do_not_receive_orange_outline`을 추가하여 공통 포커스 선택자와 공유 메뉴 키보드 포커스 규칙 보존을 검증. 전체 테스트는 기존 59개에서 **60개 예상**이나, 사용자 Windows 환경에서 아직 실행하지 않았으므로 통과를 단정하지 않음.
- **GitHub 커밋:** CSS `1069602`, 테스트 `fad7864`. GitHub `kakao`에서 두 파일을 다시 읽어 수정된 선택자와 신규 테스트 함수가 있음을 확인함. 서버 코드/관리자 인증/뉴스 저장/DB/`.env`/`main` 브랜치 변경 없음.
- **다음 사용자 검증:** `git pull origin kakao` → `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v` (실제 결과 확인) → Chrome `/map`에서 출발지 입력창 클릭 후 주황색 외곽선 유무 확인 → 필요시 Tab/관리자 입력 화면 확인. 실제 웹 UI와 키보드 접근성 판정은 사용자 캡처 후 README에 기록.

### 14.13 D01 입력창 포커스 변경 Windows 전체 60개 자동 테스트 통과 (2026-10-19)

- 사용자가 Windows PowerShell `C:\workspace\traffic_app_domain\traffic-api`에서 `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v` 실행 로그를 제출함.
- **실제 실행 결과: `Ran 60 tests in 0.258s`, `OK`**. CSS 포커스 관련 신규 `test_d01_form_fields_do_not_receive_orange_outline`도 `ok`이며, 실패·오류 0개. 기존 관리자, 지도, 뉴스, 검색, CSV 내보내기, 히스토리 회귀 테스트 통과.
- 로그의 `RuntimeError: test DB error`, `private DB detail`, `secret DB`는 의도적인 예외 처리 테스트에서 출력되며 최종 결과는 모두 `ok`. `StarletteDeprecationWarning`은 비치명적 의존성 경고.
- **검증 한계:** 이 테스트는 CSS 선택자 및 서버·정적 응답 회귀를 확인할 뿐, Chrome의 실제 입력창 포커스 테두리 상태나 Tab 키보드 접근성을 검증하지 않음. 실제 Chrome `/map` 출발지·목적지 입력창 클릭 및 `/admin` 입력창, Tab 이동 시 초점 식별 가능성 확인 대기.
- 이 단계에서 기사 생성·저장, DB 변경, 관리자 설정 수정 없음.

### 14.14 D01 Chrome 검증: 기본 검은 포커스 외곽선 잔존 — 보완 설계 (2026-10-19)

- **사용자 Chrome 실제 화면:** `/map` 목적지 '용산역' 입력창에 포커스가 있는 상태에서 검은색 테두리가 보임. 출발지 '중각역' 입력창은 기존 연회색 테두리. 주황색 D01 3px 외곽선은 사라졌지만 요구한 '포커스 때 추가 외곽선 없음'은 미달. 실제 화면 검증은 **미통과**.
- **진단:** `static/design-system.css`에서 공통 `input`의 `:focus-visible` 규칙을 제외했으나 브라우저 기본 `outline`이 적용될 수 있음. `static/map.html`에는 기존 `input { border:1px solid #cbd5e1; ... }`, `.map-controls input { ... }`이 있으며, 현재 공통 CSS에는 폼 컨트롤의 기본 `outline`을 명시적으로 제거한 규칙이 없음.
- **사용자 승인 대기 보완안:** `static/design-system.css`에서 `:where(input, textarea, select):focus { outline: none; }` 추가로 폼 컨트롤의 포커스 시 브라우저 기본 외곽선을 제거. 기존 페이지에서 지정한 `border`는 유지. 버튼/링크의 기존 `:focus-visible` 강조와 내비게이션 포커스 강조는 손대지 않음. 전역 폼 포커스 표시가 사라지는 키보드 접근성 단점이 있으므로 별도 피드백 필요하면 별도 설계·승인.
- **예정 검증:** 관련 테스트를 수정해 `outline: none` 범위가 폼 컨트롤로 한정됨을 확인, 전체 Windows 단위 테스트 실행, Chrome `/map` 출발지/목적지 마우스 포커스/Tab 포커스 및 `/admin` 입력창 확인. **스크린샷 검증 성공 전에는 해결 완료로 간주하지 않음.**
- **현 단계:** README 기록만 추가. CSS, 테스트, 인증, DB, Kakao API, 저장 기능은 변경하지 않음. `main` 제외, `kakao` 브랜치만 사용.

### 14.15 D01 검은 기본 포커스 외곽선 보완 반영 (2026-10-19)

- **사용자 지시:** 이전에 승인된 입력창 포커스 외곽선 제거 작업의 후속 수정은 별도 승인 질문 없이 자동으로 커밋·푸시하도록 요청. 기존 범위(입력창 테두리 및 회귀 검증)에 한정하며 새 기능·DB·인증 변경은 포함하지 않음.
- **실제 보완:** `traffic-api/static/design-system.css`에 `:where(input, textarea, select):focus { outline: none; }` 추가. Chrome에서 보였던 기본 검은 포커스 외곽선을 폼 컨트롤에 한정해 없앰. 별도 `border` 색상 변경 없음; `:where(button, a):focus-visible`과 공통 내비게이션 접근성 규칙은 유지.
- **회귀 테스트 보강:** `traffic-api/tests/test_navigation.py`의 `test_d01_form_fields_do_not_receive_orange_outline`에 폼 컨트롤 한정 `outline: none` 규칙과 버튼 포커스 규칙 보존 검증을 추가. 기존 테스트 개수는 **60개 예상**이며 로컬 Windows 전체 테스트 실행 전이라 합격 여부 미확인.
- **GitHub kakao 반영:** CSS `3904f44`, 테스트 `97b419a`; 루트 README에 반영 이력 기록. `main`, API, DB, 관리자 인증, 뉴스 생성·저장은 변경하지 않음.
- **검증 대기:** Windows에서 `git pull origin kakao`, 전체 60개 자동 테스트, Chrome 강력 새로고침 후 `/map` 입력창 클릭 시 검은/주황 외곽선이 모두 없는지 스크린샷 확인. Tab 이동 시 입력창 시각적 포커스 구분이 사라지는 접근성 단점이 있어 별도 디자인 검토 필요. 실제 Chrome 검증 전 완료 판정 금지.

### 14.16 D01 Chrome 지도 입력창 포커스 시각 검증 (2026-10-19)

- **실제 사용자 Chrome 캡처:** `http://127.0.0.1:8000/map`, 출발지 '혜화역', 목적지 '영등포역'의 텍스트 입력칸과 예상 55.1분, 카카오맵 경로·출발/도착 마커 확인. 목적지 입력란 안에 텍스트 커서가 있으며 **기존 주황색 3px 및 검은 브라우저 기본 포커스 외곽선이 모두 보이지 않음**. 입력창 고유의 연한 회색 border는 유지.
- **판정:** 지도 화면에서 목적지 입력창 마우스 포커스 외곽선 제거에 대한 **사용자 Chrome 캡처 시각 검증 합격**. 첫 보완 후 검은 테두리가 남았던 14.14 문제에 대해 14.15 CSS 추가 적용된 화면은 요구한 상태로 보임.
- **한계:** 단일 화면 이미지이므로 Tab 키 이동 시 키보드 초점 식별, 관리자 로그인 입력창, 모바일, DevTools Console, 다른 브라우저 및 모든 입력 컨트롤의 표시를 입증하지 않음. 텍스트 입력란에 시각적 키보드 포커스 안내가 약해지는 접근성 단점은 여전히 존재.
- 이 기록은 README 검증 문서만 변경하며 CSS·JS·API·DB·저장 기능과 `main` 브랜치는 수정하지 않음. 기존 Windows 60개 테스트 `OK`는 14.13 결과로, 14.15 보완 이후 재실행 결과로 혼동하지 않음.

### 14.17 D01 관리자 새 교통 뉴스 생성 Chrome 미리보기 검증 (2026-10-19)

- **사용자 실제 Chrome `/admin` 캡처:** 관리자 로그인 후 '새 교통 뉴스 생성' 실행 결과, 세 경로 수치·기사 제목·본문·조회 시각·경로별 분석표가 화면에 표시됨. 저장은 실행하지 않음.
- **기사 제목:** '서울 주요 3개 경로 중 광화문~강남역 2호선, 정체·지체 거리 비율 가장 높아'. 조회 완료 시각은 **2026-10-19 오후 5:43:37 (KST)**로 표시됨.
- **표시 수치:** 서울역→잠실역 2호선 17.82km, 67.8분, 정체·지체 51.1%; 광화문→강남역 2호선 12.75km, 48.7분, 79.0%; 여의도역 5호선→잠실역 2호선 19.25km, 58.0분, 31.4%. 화면의 제목과 표에서 가장 높은 비율(79.0%)이 서로 일치.
- **저장 상태:** '확인한 뉴스 저장' 버튼이 파란색 활성 상태로 보이나 클릭하지 않음. Supabase 실제 기사 저장, 행 생성, 영속화 등은 검증하지 않았으며 기존 DB 변경 없음.
- **판정:** 실제 Chrome에서 관리자 새 교통 뉴스 **초안 생성·미리보기 표시 시각 검증 합격**. 단일 화면으로 Kakao 원본 API 데이터와 정확성, 토큰·내부 저장 계약, Console, 모바일, DB 저장 성공을 판정하지 않음.
- **후속:** 저장을 포함한 검증은 사용자 별도 명시적 승인 이후 진행. 보안 정보·환경 키 불필요. `kakao` 브랜치 README 문서만 수정.

### 14.18 D01 관리자 기사 #11 저장 및 API 재조회 검증 (2026-10-19)

- **사용자 Chrome 관리자 화면:** 새 기사 초안에 대한 '확인한 뉴스 저장' 클릭 후 '저장 완료! 기사 #11' 메시지 표시. 저장 버튼이 회색 비활성 상태로 변하고 '저장된 기사 확인 (기사 #11)' 링크가 표시됨.
- **사용자가 링크를 클릭한 실제 JSON 조회 결과:** `id=11`, 제목 '서울 주요 3개 경로 중 서울역~잠실역 2호선, 정체·지체 거리 비율 가장 높아', 리드/본문/`scope_notice` 존재, `analyzed_route_count=3`, `routes` 3개, `retrieved_at=2026-10-19T08:52:37.321666+00:00`, `created_at=2026-10-19T08:52:38.663072+00:00`. 관리자 화면과 재조회 JSON에서 제목 및 핵심 데이터가 일치.
- **경로 데이터:** 서울역→잠실역 2호선 18139m, 4092초, 정체·지체 6941m/28개 도로 구간 중 11개, 38.27%; 광화문→강남역 2호선 13099m, 2547초, 4338m/14개 중 6개, 33.12%; 여의도역 5호선→잠실역 2호선 19249m, 3592초, 6046m/27개 중 6개, 31.41%. 사용자 화면의 반올림 값 18.14km/68.2분/38.3%, 13.10km/42.5분/33.1%, 19.25km/59.9분/31.4%와 일치함.
- **판정:** 관리자 초안 생성 → 검토 → 저장 완료 메시지 → 기사 ID 11을 이용한 재조회 JSON 반환까지 **실제 사용자 검증 성공**. 기존 기사 삭제·수정 없음. DB 내부 레코드 직접 조회, 일반 뉴스 목록의 UI 표시, 카카오 원본 API 대조, 중복 저장 재시도, 모바일/Console은 확인하지 않았으므로 별도 항목.
- **다음 확인:** 사용자 브라우저에서 `http://127.0.0.1:8000/news` 접속하여 저장된 기사 #11이 뉴스 페이지 목록/검색에서 보이고 선택 시 제목·본문이 표시되는지 확인. 비밀키나 계정 정보는 공유하지 않음.
- **변경 범위:** 위 실제 검증 내용을 `kakao` 루트 README에만 기록. 애플리케이션 코드, DB 스키마, 관리자 인증 및 `main` 브랜치 변경 없음.

### 14.19 D01 저장 기사 #11 일반 뉴스 화면 Chrome 검증 (2026-10-19)

- **사용자 Chrome 실제 캡처:** `http://127.0.0.1:8000/news` 화면에서 저장된 교통 뉴스 목록의 맨 위에 **기사 #11**이 표시되고 같은 기사 제목이 하단 상세 기사 영역에도 표시됨. 기사 제목 '서울 주요 3개 경로 중 서울역~잠실역 2호선, 정체·지체 거리 비율 가장 높아'.
- **기사 상세 검증:** 본문과 범위 한정 문구, 조회 시각, 3개 경로 요약 및 막대 그래프 표시. 서울역→잠실역 38.3%, 광화문→강남역 33.1%, 여의도역→잠실역 31.4%가 이전 저장 기사 #11 API 재조회 값과 화면 반올림 범위에서 일치. 화면에 3개 경로별 '지도에서 확인' 버튼 존재.
- **판정:** D01 **관리자 뉴스 생성 → 검토 → 저장 → JSON API 재조회 → 일반 사용자 뉴스 페이지 목록/상세 표시**까지 실제 사용자 캡처/반환값으로 검증 완료. 관리자 저장 성공 및 API 상세는 14.18 참고.
- **검증 한계:** 지도 확인 버튼 실제 클릭과 저장 경로 이동, CSV 다운로드 실행, 검색 필터 조작, 모바일 반응형, Tab 접근성 및 개발자도구 Console은 아직 확인되지 않음. 화면에 버튼이 보이는 사실을 클릭 동작 성공으로 간주하지 않음.
- **작업 범위:** Chrome 확인 결과를 `kakao` 루트 README에 기록; 앱 코드/인증/API/DB/.env/main 변경 및 추가 저장 없음.

### 14.20 기사 #11 저장 경로 지도 연결 Chrome 검증 (2026-10-19)

- **사용자 Chrome 실제 캡처:** `/map?article_id=11&route_index=0` 접속 결과 화면에 '기사 #11의 저장된 경로' 패널, 기사 조회 시각 `2026. 10. 19. 오후 5:52:37 (KST)`, 서울역→잠실역 2호선, 저장 거리 18.1km·예상 68.2분·정체·지체 비율 38.3%가 표시됨. 지도 입력값도 출발 서울역·도착 잠실역 2호선으로 설정됨. 카카오맵 배경 지도 로드 확인.
- **검증 판정:** 일반 뉴스 화면 '지도에서 확인'을 통해 기사 #11의 첫 번째 저장된 경로 요약과 지도 페이지를 연결하는 기능 **실제 Chrome 검증 합격**. 저장 상세 JSON의 18139m/4092초/38.27%와 반올림 값이 일치.
- **기능 경계:** 지도는 저장 당시의 통계와 위치 입력을 재표시하며 저장된 상세 도로 좌표를 복원하지 않음. 화면에서도 '과거 저장 경로를 확인했습니다. 현재 경로를 보려면 조회 버튼을 누르세요.' 안내가 보임. 현재 길찾기 버튼은 아직 클릭하지 않았으며 **현재 경로의 지도 선형·Kakao API 호출 결과는 이 캡처로 검증하지 않음**.
- **남은 검증:** 선택적 '현재 경로 새로 조회' 클릭 결과의 도로 선형 및 저장 수치와 현재 수치의 구분, 나머지 2개 경로 링크, 모바일/Tab/Console. 사용자 승인 없이 추가 기사 생성·DB 변경 없음.
- **변경 범위:** 검증 결과를 `kakao` 루트 README에만 기록; 앱 코드, DB 스키마, API 키, 관리자 인증, `main`은 변경하지 않음.

### 14.21 기사 #11 현재 경로 재조회 Chrome 검증 및 지도 타일 표시 문제 (2026-10-19)

- **사용자 Chrome 실제 캡처:** 기사 #11 첫 경로 `/map?article_id=11&route_index=0`에서 '현재 경로 새로 조회' 실행 후 서울역→잠실역 2호선 현재 예상 **66.1분** 표시. 저장 당시 68.2분 요약 패널은 그대로 유지되어 양쪽 시점 정보가 구분됨. 현재 예상 시간은 저장 당시보다 **2.1분 짧음**.
- **경로 시각 검증:** 출발·도착 마커 및 도로를 따른 빨강·초록·회색 경로 선형이 표시됨. 색상별 구간 표시 기능의 결과는 보이나 외부 카카오 원본 응답과 개별 도로 속성을 독립 검증하지는 않음.
- **새로 발견한 표시 문제:** 스크린샷에서 지도 왼쪽 일부만 기초 지도 이미지가 나타나고 대부분의 영역은 베이지색 배경 위 `kakaomap` 워터마크 형태로 보임. **지도 배경 타일의 불완전한 표시/로딩 가능성**. 카카오 API 인증 문제·네트워크 오류·일시적 타일 로딩 지연 가운데 원인은 아직 특정하지 않음.
- **판정:** 기사 #11의 저장 당시 정보와 새로 조회한 현재 경로 정보 분리, 현재 경로 선형 표시 **Chrome 캡처 검증 합격**. 지도 배경 타일 전체 로딩은 **미통과/추가 확인 필요**. 저장 기사 #11 및 다른 DB 데이터를 변경하지 않음.
- **후속 진단 제안:** Chrome에서 몇 초 대기 후 같은 지도 확인 및 DevTools Network/Console에 타일 네트워크 오류가 있는지 확인. 지속 재현 시 기존 Kakao 지도 SDK/타일 처리 및 크기 재조정 로직을 코드 읽기 중심으로 조사하고, 범위를 넘는 구현 변경 전 README 설계 및 사용자 확인. `kakao` 브랜치만 사용.

### 14.22 기사 #11 지도 배경 타일 재확인 정상 (2026-10-19)

- 사용자 추가 Chrome 캡처에서 `/map?article_id=11&route_index=0`의 **카카오맵 배경 타일이 화면 전체에 정상 표시**됨. 이전 14.21의 대부분 베이지색 빈 타일 문제는 이번 화면에서 재현되지 않음. 당시 원인이 일시적 로딩 지연·캐시·네트워크 상태 중 무엇인지는 확인하지 못함.
- 저장 기사 #11의 서울역→잠실역 2호선 **68.2분** 요약은 유지되고, 새로 조회된 경로의 예상 **65.4분**이 별도 표시되어 2.8분 차이가 보임. 출발·도착 마커, 도로를 따른 빨강·초록·회색 경로 선형 표시 확인.
- **판정:** 이번 Chrome 화면 범위에서 지도 배경 타일 및 새 경로 선형 **시각 검증 합격**. 14.21의 타일 문제는 현재 재현되지 않지만 원인 미확정이므로 반복 시 네트워크 상태/DevTools Console 점검. 외부 Kakao API 원본·모든 네트워크 응답·모바일 및 Tab 키 기능은 이 캡처로 확인하지 않음.
- 변경 범위는 `kakao` 루트 README 검증 기록만. 기존 기사 #11 및 DB, API, JS, CSS, `main` 브랜치 변경 없음.

### 14.23 기사 #11 저장 경로 3개 지도 연결 완료 (2026-10-19)

- 사용자 Chrome 캡처 2장으로 **두 번째 경로** `/map?article_id=11&route_index=1`의 광화문→강남역 2호선, 저장 거리 13.1km, 예상 42.5분, 정체·지체 비율 33.1%와 출발/도착 입력 자동 설정을 확인. 기사 #11 표제와 저장 시각 표시, 카카오맵 배경 표시 확인.
- **세 번째 경로** `/map?article_id=11&route_index=2`의 여의도역 5호선→잠실역 2호선, 저장 거리 19.2km, 예상 59.9분, 정체·지체 비율 31.4%와 출발/도착 입력 자동 설정을 확인. 기사 #11 안내·저장 시각·카카오맵 배경 표시 확인.
- 두 화면 모두 '과거 저장 경로를 확인했습니다. 현재 경로를 보려면 조회 버튼을 누르세요.' 안내가 있음. 기사 당시의 저장 요약을 표시하는 기능이며 현재 경로 API를 자동으로 호출하지 않음.
- **판정:** 앞서 14.20에서 검증한 첫 번째 경로(서울역→잠실역 2호선)와 이번 두 경로를 합쳐 **기사 #11의 3개 저장 경로 링크 및 요약 정보 전달 Chrome 화면 검증 완료**. 사용자 캡처로 확인 가능한 표시 범위만 합격으로 판정.
- **제외 범위:** 두 번째·세 번째 경로의 현재 길찾기 버튼 클릭, 상세 도로 선형, 모바일/키보드 Tab/Console 검증은 포함하지 않음. 코드/DB/관리자 인증/API 키/`main` 변경 없음; `kakao` 루트 README 기록만 변경.

### 14.24 D01 뉴스 모바일 390px Chrome 배치 검증 및 빈 목록 관찰 (2026-10-19)

- **사용자 실제 Chrome 디바이스 모드 390px `/news` 캡처:** 내비게이션 '메뉴 열기' 전환, 네이비 뉴스 소개 카드, 날짜·시간별 교통 변화 검색 폼, 저장된 교통 뉴스 검색·초기화, CSV 다운로드 폼, 주요 경로 교통 현황 카드 및 기사 상세 영역이 한 열로 배치됨. 캡처 범위에서 명백한 가로 넘침·요소 겹침은 관찰되지 않음.
- **주의할 상태:** 캡처에서 저장 뉴스 목록은 `0 / 0 페이지`이고 '검색 버튼을 눌러 저장된 기사를 확인하세요'가 표시됨. 우측 요약값은 대시(-), 기사 상세에는 '아직 생성된 뉴스가 없습니다', '교통정보 조회 전입니다.'가 표시됨. **조회 전의 초기 상태일 수 있으므로 DB 기사 삭제나 모바일 고장으로 단정하지 않음.** 이전 데스크톱에서 기사 #11 목록/상세 성공(14.19)을 별도로 확인함.
- **판정:** **390px 반응형 배치 시각 검증 합격(정적 배치 기준)**. 모바일에서 검색 실행 후 기사 목록/상세 로드, 햄버거 메뉴 클릭/접근성, Console, 다른 너비 320/768px는 아직 검증하지 않음.
- **다음 사용자 확인:** 모바일 모드를 유지한 상태에서 저장된 교통 뉴스 영역의 '검색' 버튼을 눌러 목록에 기사 #11이 나오는지 확인. 불러오지 못할 때만 Console/Network 에러 확인. 저장/DB/앱 코드 변경 없이 `kakao` README 문서만 기록.

### 14.25 D01 모바일 390px 저장 뉴스 검색 결과 표시 검증 (2026-10-19)

- 사용자 Chrome 모바일 디바이스 모드 `/news` 390px 전체 캡처에서 저장된 교통 뉴스 검색 버튼 실행 후 여러 기사 카드가 세로로 표시됨. 첫 번째 카드의 제목은 기사 #11 '서울 주요 3개 경로 중 서울역~잠실역 2호선, 정체·지체 거리 비율 가장 높아'로 이전 저장 결과와 일치하며 각 카드에 '더 보기' 버튼이 표시됨.
- 저장 기사 목록이 비어 있던 14.24 화면과 달리 검색 수행 뒤 정상적으로 조회 결과가 표시됨. 따라서 이전 0건 표시는 조회 전 초기 상태였을 가능성이 높고, 모바일 DB 조회 실패로 판정할 근거가 없음.
- 캡처에서 카드, 필터, CSV 다운로드, 요약 카드가 단일 열로 표시되며 눈에 띄는 가로 넘침이나 겹침은 관찰되지 않음.
- **판정:** 모바일 390px **저장 뉴스 검색 및 기사 #11 목록 노출 Chrome 시각 검증 합격**. 하단 기사 상세 영역은 '아직 생성된 뉴스가 없습니다' 상태로 보이며, 기사 #11 '더 보기'를 누른 이후 상세 본문 및 요약 그래프 갱신은 아직 확인하지 않음. Console, 모바일 메뉴 실제 상호작용, Tab 포커스는 미검증.
- DB·기사 저장·API 코드·CSS/JS·`main`은 변경하지 않았으며 `kakao` README 문서에 검증 결과만 기록.

### 14.26 D01 모바일 390px 기사 #11 상세 검증 (2026-10-19)

- 사용자 Chrome 모바일 390px `/news` 전체 화면 캡처에서 저장된 뉴스 기사 #11의 '더 보기' 선택 후 상세 정보가 나타나는 상태를 확인함.
- **실제 표시:** 주요 경로 교통 현황 3개 경로, 최고 정체·지체 비율 38.3%, 해당 구간 11개, 경로별 비율 막대 그래프(38.3%/33.1%/31.4%), '기사에서 분석한 경로' 3개 및 각 '지도에서 확인' 버튼, 기사 #11 제목·본문·조회 시점·범위 한정 안내가 표시됨.
- **판정:** 모바일 390px에서 검색 결과 목록 → 기사 #11 상세 선택 → 경로 요약·본문·지도 연결 버튼 **Chrome 시각 검증 합격**. 캡처 범위에서 뚜렷한 가로 넘침·요소 겹침은 없음.
- **검증 한계:** 버튼이 보인다는 사실만으로 모바일 경로 버튼 클릭, 햄버거 메뉴 상호작용, 320/768px 화면, Tab 포커스, Console 무오류를 확인했다고 주장하지 않음. 지도 링크 3개 데스크톱 검증은 14.20/14.23 별도 기록.
- `kakao` 브랜치 루트 README에만 검증 기록 추가. 앱 소스, Supabase DB, 관리자 인증 및 `main` 변경 없음.

### 14.27 D01 모바일 390px 내비게이션 메뉴 펼침 Chrome 검증 (2026-10-19)

- 사용자 Chrome 모바일 390px `/news` 실제 스크린샷에서 상단 모바일 내비게이션 확장 상태를 확인. 닫힘 상태의 '메뉴 열기' 버튼이 열린 상태에서 **'메뉴 닫기'**로 전환되었고, '교통 현황', '분석·통계', '교통 뉴스', '서비스 안내', '관리자' 항목이 세로 목록으로 펼쳐짐.
- 펼친 내비게이션 아래 뉴스 소개 카드 및 검색·통계·기사 화면이 흐름에 따라 아래로 배치됨. 캡처 범위에서 뚜렷한 겹침이나 가로 넘침 없음. 검색 실행 전이라 목록/상세가 빈 상태인 것은 메뉴 테스트의 실패로 보지 않음.
- **판정:** 390px 모바일 내비게이션 **메뉴 펼침 및 버튼 라벨 전환 시각 검증 합격**. 실제 하위 메뉴 펼침/링크 이동, 닫기 클릭 결과, Tab·Esc 키보드 접근성 및 Console 상태는 별도 확인 필요.
- 사용자 승인 범위의 검증 기록만 `kakao` 루트 README에 추가. 코드·API·DB 및 `main` 변경 없음.

### 14.28 D01 모바일 교통 뉴스 하위 메뉴 펼침·이동 확인 (2026-10-19)

- 사용자 Chrome 390px 스크린샷에서 모바일 상단 메뉴를 펼친 뒤 '교통 뉴스' 하위 메뉴가 흰색 카드로 확장되는 것을 확인. '최신 교통 뉴스', '저장된 기사 아카이브', '기사 검색·기간 필터', '기사 공유·읽기 모드'(준비 중) 항목이 표시됨.
- 사용자는 **하위 메뉴를 눌렀을 때 실제 페이지 이동도 확인했다**고 명시적으로 보고함. 이동한 모든 목적지의 URL·상세 화면을 별도 캡처로 확인한 것은 아니므로 사용자 확인과 스크린샷 직접 확인을 구분해 기록.
- **판정:** 모바일 교통 뉴스 하위 메뉴 펼침은 사용자 Chrome 화면으로 검증, 하위 메뉴 클릭 시 이동은 사용자 직접 확인으로 기능 검증 완료. 메뉴와 본문이 명백하게 겹치거나 가로로 넘치는 문제는 제공 이미지에서 관찰되지 않음.
- 미검증: 키보드 Tab/Enter/Escape, Console 오류, 320px/768px 화면, 각 하위 메뉴 링크의 전수 개별 확인. 기존 UI나 DB 변경 없이 `kakao` 루트 README 검증 기록만 추가.

### 14.29 D01 상단 메뉴 키보드 Tab·Enter·Esc 사용자 검증 (2026-10-19)

- 사용자가 Chrome 데스크톱 뉴스 화면에서 키보드 점검 결과를 직접 보고함: **Tab 이동 시 노란색 키보드 포커스가 보이고 Enter와 Esc 조작도 작동**함.
- **판정:** 상단 내비게이션의 키보드 포커스 시각 표시와 Enter/ESC 기본 동작 **사용자 직접 검증 합격**. 이전 공통 CSS 수정에서 입력 컨트롤의 기본 포커스 외곽선을 없앴지만 버튼/링크의 포커스 강조는 유지됨.
- **검증 범위 한계:** 별도 화면/녹화로 모든 메뉴, 링크를 전수 확인한 것은 아님. 입력창 자체의 Tab 포커스 시각 식별, 다른 해상도(320/768px), DevTools Console 무오류는 아직 별도 미검증. CSS 변경으로 입력창 Tab 포커스 테두리도 없어지는 접근성 단점은 계속 존재.
- **변경 범위:** 사용자 제공 결과만 `kakao` 루트 README에 기록함. 코드, DB, 환경설정, 관리자 인증, `main` 변경 없음.

### 14.30 D01 교통 뉴스 Chrome Console 오류 점검 (2026-10-19)

- 사용자가 Chrome `http://127.0.0.1:8000/news`에서 개발자도구 Console을 열고 새로고침한 후 **'Console 빨간 오류 없음'**이라고 직접 보고함.
- **판정:** 이 사용자 점검 시점의 `/news` 페이지에서 **Console의 빨간 오류 미발견(사용자 확인)**. 사용자가 메시지로 보고한 결과이며 Console 출력 전체를 별도 캡처·로그로 수령한 것은 아님.
- **종합 진행:** 이전 14.18~14.29에 관리자 기사 생성·저장·재조회, 공개 뉴스 기사 #11, 저장 경로 3개 링크, 390px 모바일 뉴스·내비게이션, 상단 메뉴 Tab/Enter/Esc 확인을 각각 기록함.
- **남은 범위:** `/map`·`/admin` Console, 320px/768px 반응형, 폼 입력칸 Tab 포커스 식별 등은 별도 미검증. 기존 입력 컨트롤 `outline:none`에 따른 키보드 초점 시각 표시 약화는 접근성 과제로 남음.
- **변경:** `kakao` 브랜치 루트 README 검증 기록만 추가하며 앱 코드/DB/API 키/인증/`main`은 변경하지 않음.

### 14.31 D01 관리자 Chrome Console 오류 점검 (2026-10-19)

- 사용자가 Chrome `http://127.0.0.1:8000/admin`에서 개발자 도구 Console 점검 후 **'관리자 Console 빨간 오류 없음'**이라고 직접 보고함.
- **판정:** 사용자 점검 시점의 관리자 페이지에서 Console 빨간 오류 미발견(사용자 확인). Console 전체 출력 캡처나 네트워크 로그를 직접 수령한 것은 아니므로 그 이상은 단정하지 않음.
- 뉴스 페이지 `/news` Console 점검 결과는 14.30에 별도 기록. 관리자 기사 #11 생성·저장·API 재조회와 공개 페이지 노출 검증은 14.18~14.19 참고.
- **잔여 점검:** `/map` Console, 다른 화면 너비(320px/768px), 입력 컨트롤의 Tab 키 포커스 시각 식별 등은 아직 별도 검증하지 않음.
- `kakao` 루트 README만 갱신. 앱 코드·DB·관리자 인증·API 키·`main` 브랜치 변경 없음.

### 14.32 D01 지도 Chrome Console 로딩·경로 조회 검증 (2026-10-19)

- 사용자가 Chrome `http://127.0.0.1:8000/map`에서 페이지를 열고 Console을 확인한 결과 **빨간 오류가 없었으며**, **'경로 표시' 버튼을 누른 이후에도 Console 오류 메시지가 없었다**고 직접 보고함.
- **판정:** 해당 사용자 점검 시점에 `/map` 초기 로딩과 실제 길찾기 버튼 실행 과정의 Console 오류 **미발견(사용자 직접 확인)**. Console 로그 원문·네트워크 요청 전수·별도 테스트 캡처는 받지 않았으므로 해당 범위를 넘어 단정하지 않음.
- 앞선 `/news` Console 확인(14.30)과 `/admin` Console 확인(14.31)을 합쳐 **주요 3개 페이지 Console 빨간 오류 미발견**. 자동 테스트 60개 통과(14.13)는 첫 CSS 보완 전 결과이므로 후속 CSS 변경 이후의 재실행 증거로 오인하지 않음.
- **잔여 점검:** 반응형 320px·768px, 입력창 자체 Tab 초점 식별, 보완 CSS 이후 전체 Windows 자동 테스트 재실행 등. 추가 기사 저장·DB 수정 없음.
- `kakao` 루트 README 검증 결과만 추가. 앱 코드/DB/API 키/관리자 인증/`main` 브랜치 변경 없음.

### 14.33 Windows 최종 자동 테스트 CRLF 줄바꿈 비교 실패 및 테스트 보완 (2026-10-19)

- 사용자 Windows PowerShell `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v` 재실행 로그: **`Ran 60 tests in 0.250s`, `FAILED (failures=1)`**. 실패는 `test_navigation.SharedNavigationTests.test_d01_form_fields_do_not_receive_orange_outline` 하나이며 다른 59개는 통과.
- 원인: 테스트가 `:where(input, textarea, select):focus {\n    outline: none;\n}`처럼 LF 줄바꿈만 포함한 고정 문자열을 검사했으나, 실제 FastAPI 정적 CSS 응답의 줄바꿈은 Windows CRLF(`\r\n`)이었음. 오류 메시지에 **동일 CSS 규칙 자체는 존재**하며 보완 CSS가 작동하지 않은 것과 구분해야 함.
- 승인된 후속 보완: `traffic-api/tests/test_navigation.py`에서 해당 검사에 사용되는 CSS 문자열을 `.replace("\r\n", "\n")`으로 정규화하도록 최소 수정. **CSS 디자인·일반 기능 변경 없음**. 테스트 수정 커밋 `c3eee91`.
- 아직 수정 뒤 Windows 전체 테스트를 재실행하지 않았으므로 **60개 합격이라고 기재하지 않음**. `git pull origin kakao` 후 같은 명령으로 재검증 필요. 의도된 mock 예외 메시지 및 StarletteDeprecationWarning은 본 실패와 무관.
- `kakao` 루트 README만 기록·`main`/DB/API/인증/.env 변경 없음.

### 14.34 Windows CRLF 보완 후 전체 60개 자동 테스트 통과 (2026-10-19)

- 사용자가 Windows PowerShell `C:\workspace\traffic_app_domain\traffic-api`에서 `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v` 재실행 로그를 제출함.
- **실제 최종 결과: `Ran 60 tests in 0.227s`, `OK`**. 60개 전체 `ok`, 실패·오류 0개. 이전 14.33에서 실패했던 `test_d01_form_fields_do_not_receive_orange_outline`이 이번에는 `ok`로 완료됨.
- `RuntimeError: test DB error`, `private DB detail`, `secret DB`는 예외 처리를 검사하는 mock 테스트의 예상 로그로 해당 테스트들은 `ok`였음. `StarletteDeprecationWarning`은 비치명적 라이브러리 경고.
- **검증 구분:** 위는 사용자 Windows 환경의 실제 자동 테스트 성공 기록. 별도 Chrome 검증(기사 #11 저장/조회/지도 연결, 390px 모바일 화면, Console)은 앞선 14.18~14.32에 기록되어 있으며 자동 테스트만으로 브라우저 조작을 확인했다고 주장하지 않음.
- **잔여 항목:** 모바일 320px·768px 반응형 및 입력 필드 Tab 포커스의 시각적 식별은 아직 미검증. 폼 포커스 `outline:none`에 따른 접근성 문제는 잔존할 수 있음.
- 이 기록은 `kakao` 루트 README만 갱신하며 코드/DB/API/.env/관리자 인증/`main` 브랜치는 변경하지 않음.

### 14.35 D01 뉴스 320px 모바일 반응형 Chrome 시각 검증 (2026-10-19)

- 사용자 Chrome 320px 디바이스 모드 `/news` 전체 페이지 스크린샷을 확인함. 모바일 내비게이션 '메뉴 열기', 뉴스 소개 카드, 날짜·시간별 교통 변화 폼, 저장된 뉴스 검색, CSV 다운로드, 주요 경로 교통 현황 및 기사 상세 기본 상태가 좁은 너비에 맞는 1열로 배치됨.
- 카드 제목·CSV 문구 자동 줄바꿈 확인. 스크린샷 범위에서 명백한 가로 스크롤 유발 요소나 카드·입력창 겹침은 관찰되지 않음.
- 조회 전 상태로 보이는 `0 / 0 페이지` 및 '아직 생성된 뉴스가 없습니다' 문구는 이 캡처만으로 DB 조회 오류로 해석하지 않음. 390px 기사 검색/상세 성공은 14.25~14.26에 별도 검증됨.
- **판정:** 320px **정적 반응형 배치 Chrome 시각 검증 합격**. 320px에서 검색, 기사 상세 클릭, 메뉴 실제 동작, Console 검증은 하지 않았으며 768px은 미검증.
- `kakao` 브랜치 루트 README 기록만 추가하고 코드·DB·인증·API/.env·`main`은 변경하지 않음.

### 14.36 D01 뉴스 768px 태블릿 반응형 Chrome 시각 검증 (2026-10-19)

- 사용자 Chrome 디바이스 모드 768px `/news` 전체 화면 캡처에서 모바일형 '메뉴 열기' 내비게이션, 뉴스 소개 카드, 날짜·시간별 교통 변화, 저장 뉴스 검색, CSV 다운로드, 주요 경로 현황, 기본 기사 상세 영역을 시각 확인.
- 768px에서 날짜·기간 필터와 주요 통계 카드가 여러 열로 배치되며, 카드·입력 컨트롤은 영역 안에 표시됨. 캡처 범위에서 눈에 띄는 가로 넘침·겹침 없음. 320px(14.35)·390px(14.24~14.26)보다 넓은 화면 구성으로 전환된 것이 확인됨.
- **판정:** 768px **정적 반응형 배치 Chrome 시각 검증 합격**. 이 화면은 조회 전 초기 상태이므로 0건 표시를 DB 오류나 실제 데이터 삭제로 해석하지 않음.
- **미검증:** 768px에서 검색·상세 클릭 및 하위 메뉴 이동, 폼 입력칸 Tab 포커스의 시각적 식별 등. 코드/DB/API/.env/인증/`main`은 변경하지 않고 `kakao` 루트 README 문서에만 기록.

### 14.37 D01 뉴스 입력 필드 Tab·Shift+Tab 시각 포커스 확인 (2026-10-19)

- 사용자가 Chrome `/news` 데스크톱 화면에서 입력창 간 키보드 이동을 직접 확인한 결과, **Shift+Tab 시 노란색 테두리가 왼쪽으로 이동**하고 **Tab 시 노란색 테두리가 오른쪽으로 이동**한다고 보고함.
- **판정:** 사용자의 실제 환경에서 입력 필드 간 키보드 이동 및 초점 위치의 시각적 식별 **사용자 직접 검증 합격**. 다만 영상·개발자 도구의 computed style은 받지 않았고, 어느 CSS 선택자가 노란색 테두리를 만들어내는지는 확정하지 않음.
- 기존 공통 CSS `:where(input, textarea, select):focus { outline: none; }`와 사용자 관찰이 어떻게 공존하는지는 페이지별 CSS 또는 브라우저의 실제 적용 스타일을 별도로 확인해야 함. 현재 기능상 불편이 보고되지 않았으므로 디자인/JS를 추측에 따라 수정하지 않음.
- 이 결과로 뉴스 페이지 320/390/768px 정적 반응형, 기사 생성·저장·조회, 저장 경로 지도 연결, 주요 Console 및 Windows 전체 60개 자동 테스트 결과를 종합 가능. 다른 페이지의 폼 Tab 동작·모든 접근성 요소는 전수 검증하지 않음.
- `kakao` 루트 README 검증 기록만 수정; 앱 코드, DB, 인증, 환경설정, `main` 변경 없음.

### 14.38 D01 단계 최종 검증 요약 및 다음 개발 단계 준비 (2026-10-19)

- **D01 단계 판정:** 사용자 Windows와 Chrome에서 확인한 범위에 한하여 관리자 뉴스 생성·검토·저장, 기사 #11의 JSON/API 재조회와 일반 `/news` 목록·본문 표시, 해당 기사의 저장 경로 3개 `/map` 연결이 검증됨. **D01 계획된 핵심 사용자 흐름 검증 완료**. 개별 증거는 14.18~14.23 참조.
- **실제 기사 저장 근거:** 관리자 화면에서 `저장 완료! 기사 #11` 및 저장 링크가 표시되고, 해당 링크가 `id=11`인 기사 JSON(제목/본문/3개 경로/조회·생성 시각)을 반환했음. 별도로 수행하지 않은 DB 내부 전수 검사나 중복 저장 실험을 수행했다고 주장하지 않음.
- **지도 확인:** 기사 #11 저장 당시 첫 경로 68.2분과 새로 조회한 66.1분/65.4분이 별도로 표시됐으며, 색상별 현재 도로 선형·출발/도착 마커가 관찰됨. 일시적으로 불완전했던 Kakao 배경 타일은 후속 화면에서 정상 표시됨. 타일 문제의 근본 원인은 미확정.
- **반응형·조작:** `/news` 320px·390px·768px 정적 배치(14.24~14.26, 14.35~14.36), 모바일 검색·기사 #11 상세와 모바일 메뉴·교통 뉴스 하위 메뉴(14.25~14.28) 확인. 상단 메뉴 Tab/Enter/Esc 및 뉴스 입력창 Tab/Shift+Tab 포커스 식별 가능 여부는 사용자 직접 확인 결과(14.29, 14.37)로 기록함.
- **Console 및 자동 테스트:** 사용자 Chrome `/news`, `/admin`, `/map` 페이지에서 빨간 Console 오류 미발견(14.30~14.32). 최종 Windows `unittest`는 **`Ran 60 tests in 0.227s`, `OK`**(14.34), 앞선 CRLF 실패를 테스트 정규화로 보완한 뒤 재실행한 증거임.
- **남은 제한 및 비검증:** CSS 입력 컨트롤 포커스 처리의 접근성 전수 평가, 모든 페이지·해상도의 인터랙션/Console, 저장 동시성·재시도 중복 방지의 실DB 검증, Kakao 원본 응답과 독립 비교, 모든 네트워크·타일 로딩 케이스는 별도 미검증. 확인하지 않은 기능을 전면 합격으로 표현하지 않음.
- **프로젝트 상태와 다음 진행:** D01 핵심 흐름은 마무리하되 **전체 교통정보 프로젝트의 완료 선언은 아님**. 다음 기능 작업을 시작할 때 기존 프로젝트 지침대로 실제 파일·브랜치·DB 의존성을 확인하고, 새 범위 설계를 루트 README에 기록한 후 사용자 승인을 받는다. 기존 기사·교통 데이터, 인증·API 키·환경 설정 보존.
- 이 절은 `kakao` 루트 README 문서에 한하여 추가하며 애플리케이션 코드/DB/인증/`main` 브랜치 변경 없음.

## 15. F19-A 동일 자동차 경로 반복 조회 단기 캐시 설계 — 사용자 승인 대기 (2026-10-19)

> **상태: 설계안만 기록.** D01 핵심 사용자 흐름과 Windows 전체 60개 자동 테스트가 완료된 뒤 다음 후보로 P1 API 과호출 완화(F19 일부)를 제안함. 사용자의 명시적 구현 승인 전에는 Python/HTML/JS/DB 변경 금지.

### 15.1 기능정의서 변경 제안

- **F19-A / 방문자 공개 경로 조회:** 같은 출발지·목적지의 `GET /api/route` 요청을 매우 짧은 시간 안에 반복할 때, 서버 메모리에 있는 **정상 완료된 응답**을 재사용하여 카카오 Local 검색 2건+Mobility 경로 조회 1건을 중복 호출하지 않도록 검토.
- 최초 제안 TTL은 **30초**. 만료 뒤에는 새 Kakao API 호출. 일반적인 '새 경로 조회'의 최신성 저하가 있을 수 있으므로 캐시 적용 사실과 **원본 조회 완료 시각/재사용 여부**를 응답 또는 UI에 명확히 표시하는 방법을 먼저 확인. 캐시를 '실시간 업데이트'로 소개하지 않음.
- 서로 다른 출발지·목적지에는 캐시 결과 혼합 금지. 키는 유효성 검사된 출발/목적 문자열을 공백 정규화한 쌍으로 구성하고, 역방향 경로는 다른 키로 취급. 실패·인증 오류·응답 불완전 데이터는 캐시 저장 금지.
- **적용 범위 제한:** 1차는 `GET /api/route`만; 관리자 `POST /api/admin/news/generate` 및 저장, `/api/briefing/news`, 지도 SDK 설정, DB 조회는 캐시 영향 없음. 자동 주기 수집·별도 크론/분산 캐시는 범위 밖.
- **응답 호환성:** 기존 JSON 본문 필드, 좌표·도로 vertexes 및 시간·통계 계약 보존. 캐시 상태를 노출할 경우 클라이언트 호환성이 깨지지 않는 응답 헤더 또는 선택적 메타데이터 사용을 우선 검토. 이미 저장된 뉴스 기사 수치나 시간 정보 절대 수정 금지.

### 15.2 DB 설계 영향

- **DB 테이블·컬럼·인덱스·RLS·기존 데이터 변경 없음.** 서버 프로세스 내 짧은 생명주기의 임시 캐시만 고려.
- 서버 재시작/다중 워커에서 캐시가 공유되지 않으며 API 호출 감소량을 보장할 수 없다는 한계 명시. 메모리 사용 상한과 동시 동일 요청 처리 정책은 구현 전 점검.

### 15.3 화면/API 설계 영향

- 기존 `/`, `/map`, `/news`, `/admin` UI 및 메뉴 구조는 유지. 캐시 도입 시 새로 조회한 값과 재사용된 값, Kakao 원본 조회 시점을 혼동하지 않도록 표시 정책 검토.
- `/map?article_id=11&route_index=0` 등 기사 저장 경로 요약은 기존대로 유지. 저장 당시 정보와 현재 조회 정보는 분리. 현재 경로 조회는 30초 캐시로 같은 경로가 재사용될 수 있으므로 사용자에게 알려야 함.
- 캐시 오작동·만료 및 Kakao 오류일 때 정상 실패 응답/메시지를 유지하고, 빈 결과를 오래 저장하지 않음.

### 15.4 개발환경·변경 파일(승인 후)

- 기존 Windows PowerShell, Python/FastAPI, Kakao REST·Maps JS SDK, PostgreSQL/Supabase, 환경 변수, `kakao` 브랜치만 사용. 신규 DB/외부 캐시 서비스/비밀키 도입 없음.
- **예상 파일:** `traffic-api/app/main.py`의 `/api/route` 경로 및 별도의 작고 독립적인 캐시 모듈(필요 시); `traffic-api/tests/test_*.py` 관련 단위 테스트. 실제 파일 범위는 코드 조사 후 최소화. 프런트 표시 변경이 필요하면 별도 세부안으로 설계 후 확인.

### 15.5 승인 후 검증 순서 및 합격 기준

1. 기존 API 응답 스키마·호출 코드 확인 및 캐시 안전성 검토. 기존 60개 자동 테스트 기준 유지.
2. **동일 경로 연속 요청:** 실제 카카오 API를 호출하지 않는 mock 테스트로 외부 호출 1회·캐시 반환 동일값/표시 식별 확인.
3. **키 분리:** 다른 경로 및 역방향 경로가 각각 별도로 조회되는지 확인.
4. **TTL/장애/메모리:** 만료 후 새 조회, 오류 결과 미캐시, 무제한 메모리 증가 방지, 필요한 경우 동시 요청 안전성 테스트.
5. Windows 전체 `unittest` 실행 결과를 기록하고, 실제 Chrome `/` 및 `/map`에서 현재 경로·저장 경로·표시 시각·콘솔·기존 지도 선형 회귀 확인. 테스트 코드를 브라우저 실검증으로 오인하지 않음.
6. 승인 없는 실제 기사 생성/저장/DB 쓰기 금지. 비밀키·토큰 로그/README/커밋 노출 금지.

### 15.6 검토 및 착수 게이트

- **현재 미승인:** 이 절은 다음 P1 후보의 초기 구현 계획이며, F19 전체(정기 수집/스케줄링/DB 누적/분산 캐시)를 승인하거나 구현한 것으로 보지 않음.
- 사용자가 F19-A의 단기 캐시·30초 재사용 및 데이터 최신성 영향에 동의하는지 확인한 뒤에만 기능 코드 변경·회귀검사 진행.

### 15.7 F19-A 승인 후 서버 단기 캐시 코드·회귀 테스트 반영 (2026-10-19)

- 사용자가 README 15장의 **F19-A / 30초 단기 캐시 설계 구현을 명시 승인**함.
- **실제 변경:** `traffic-api/app/main.py`의 공개 `GET /api/route`에 한정하여 정상 응답의 30초 메모리 캐시(최대 128개)를 적용. 출발/목적의 연속 공백을 정규화한 방향성 있는 문자열 쌍이 키. 만료된 항목을 조회 시 청소하고 상한 초과 시 오래 사용하지 않은 항목부터 삭제. 실패한 Kakao 응답은 캐시하지 않음.
- **동시 요청:** `asyncio.Lock`으로 캐시 조회→Kakao 호출→저장을 직렬화하여 동일 경로 동시 요청에서 중복 조회를 방지. 단일 프로세스의 모든 경로 조회도 직렬화되어 서로 다른 경로 동시 요청에 대기 시간이 늘 수 있음. 다중 워커끼리 캐시를 공유하지 않음.
- **응답 호환성:** JSON 본문의 기존 필드를 그대로 유지하고, 응답 헤더 `X-Route-Cache: MISS|HIT`와 `X-Route-Cache-Age-Seconds`로 캐시 재사용 여부와 초 단위 경과 시간을 전달. **프런트엔드 UI에는 별도 표시하지 않음**. 현재 조회 버튼이 30초 내에는 직전 값을 반환할 수 있으므로 최신 교통 상태 보장이 아님.
- **적용 제외:** 관리자 `/api/admin/news/generate`, 저장 API, 기존 뉴스 생성·통계·DB 조회, 지도 SDK, 과거 기사 #11 저장 데이터는 변경 없음. 신규 DB/환경변수/패키지 없음.
- **추가 회귀 테스트:** `traffic-api/tests/test_route_cache.py`에 Kakao API를 호출하지 않는 mock 기반 테스트 6개 추가: 동일/공백 정규화 경로 HIT, 역방향 및 다른 경로 분리, TTL 만료, 오류 미캐시, 같은 경로 동시 요청 1회, 캐시 128개 상한.
- **커밋:** 공개 API 코드 `6a943d3`, 테스트 `6a5805c`. 본 README에 구현 이력 기록. **사용자 Windows 가상환경에서 아직 테스트를 실행하지 않았으므로 통과 판정 금지**. 이전 60개 + 신규 6개 = 전체 66개 예상.
- **다음 검증:** `git pull origin kakao` → Windows 전체 `unittest` → 브라우저 `/map`에서 동일 경로 반복 호출 시 `X-Route-Cache` 헤더 MISS/HIT(개발자도구 Network) 확인, TTL 30초 이후 MISS, 실제 지도 색상·경로 표시 정상 및 Console 확인. 새 기사 생성·저장·DB 변경 금지.

### 15.8 F19-A Windows 신규 6개 오류 원인과 time 이름 충돌 수정 (2026-10-19)

- **사용자 Windows 실제 실행 결과:** `Ran 66 tests in 0.728s`, `FAILED (errors=6)`. F19-A 신규 `test_route_cache.py`의 6개가 전부 `AttributeError: type object 'datetime.time' has no attribute 'monotonic'` 오류로 중단됨. 기존 60개 테스트는 전부 `ok`.
- **확인한 원인:** `app/main.py`에서 새 `import time` 이후 기존 `from datetime import datetime, date, time, timedelta`의 `time` 클래스가 모듈 이름을 덮어썼음. `time.monotonic()`은 표준 시간 모듈이 아닌 `datetime.time`을 가리켜 실패. 실제 Kakao API/DB 장애가 아니며 신규 캐시 로직의 구현 오류.
- **승인 범위 후속 수정:** `import time as monotonic_clock`로 별칭을 주고, 두 곳의 호출을 `monotonic_clock.monotonic()`으로 변경. 기존 날짜·시간 기능의 `datetime.time` 이름과 충돌하지 않도록 수정. `app/main.py`만 변경, GitHub `kakao` 커밋 `14d42df`.
- **재검증 대기:** 수정 후 사용자 Windows 66개 전체 테스트의 실제 결과를 아직 받지 않았으며 이 단계에서 합격 주장 금지. `git pull origin kakao` 후 `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v`로 재실행.
- 캐시 TTL 30초·128개 상한·공개 `/api/route` 한정 방침 유지. 기존 기사·Supabase DB·관리자 권한·카카오 키·`main` 변경 없음.

### 15.9 F19-A Windows 전체 66개 자동 테스트 재검증 통과 (2026-10-19)

- 사용자가 Windows PowerShell `C:\workspace\traffic_app_domain\traffic-api`에서 `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v` 실행 로그를 제출함.
- **실제 결과: `Ran 66 tests in 0.328s`, `OK`**, 실패 0건/오류 0건. 기존 60개와 F19-A 신규 6개(`test_route_cache.py`: 보관 상한, 동시 동일 경로, 경로 방향 분리, TTL 만료, 오류 결과 미캐시, 경로 키 정규화·재사용) 모두 `ok`.
- 직전 15.8의 `datetime.time`과 `time` 이름 충돌을 `monotonic_clock` 별칭으로 수정한 뒤 Windows에서 검증한 결과로서, 앞선 66개 오류 상태와 구분함.
- `RuntimeError: test DB error`, `private DB detail`, `secret DB`, '카카오 경로 조회 실패 (502): 조회 실패'는 예외 처리 mock 테스트의 예상 출력이며 해당 테스트는 `ok`. `StarletteDeprecationWarning`은 이번 테스트 실패를 뜻하지 않음.
- **검증 한계:** 이 결과는 Python/FastAPI mock 기반 자동 회귀 테스트 성공이다. 사용자 Chrome에서 실제 `/map` 경로 선형과 `/api/route` 응답의 `X-Route-Cache: MISS/HIT` 헤더 및 30초 이후 재조회는 아직 실검증하지 않음. 관리자 기사 생성/저장·DB 변화 없음.
- 다음 사용자 검증: Chrome 개발자도구 Network에서 동일 경로의 첫 호출 MISS, 30초 내 두 번째 호출 HIT, 30초 이후 MISS를 확인하고, 기존 지도 표시 및 Console 오류 유무를 점검. README 기록만 갱신하며 `kakao` 브랜치 외 변경 없음.

### 15.10 F19-A Chrome 지도 실제 요청 MISS 헤더 확인 (2026-10-19)

- 사용자 Chrome `http://127.0.0.1:8000/map` Network → Fetch/XHR의 실제 `/api/route?origin=...&destination=...` 응답 캡처를 확인함.
- **실제 Response Headers:** `Status Code: 200 OK`, `X-Route-Cache: MISS`, `X-Route-Cache-Age-Seconds: 0`. 응답 JSON Content-Type도 표시됨.
- 지도에는 서울역 → 잠실역 2호선, 예상 **59.1분**, 카카오 지도 타일·도로 경로 선형·출발/도착 마커가 표시됨. 수치는 해당 캡처 시점의 조회 결과로 이후 달라질 수 있음.
- **판정:** F19-A 공개 경로의 **캐시 MISS 실브라우저 확인 합격**. 이 한 화면만으로 반복 요청 HIT, 30초 후 재조회 MISS, API 요청 수 감소량을 증명한 것은 아님.
- 다음 확인: 같은 경로를 30초 안에 두 번 조회하여 Network 응답에서 HIT 여부 확인. 브라우저 HTTP 캐시와 서버 F19-A 헤더를 혼동하지 말 것.
- `kakao` 루트 README 검증 기록만 갱신하며 코드/DB/`main` 변경 없음.

### 15.11 F19-A Chrome 동일 경로 재조회 HIT 실검증 (2026-10-19)

- 사용자 Chrome `/map` Network → Fetch/XHR의 동일 서울역→잠실역 경로 재조회 캡처에서 **200 OK**, `X-Route-Cache: HIT`, `X-Route-Cache-Age-Seconds: 6`을 직접 확인함.
- 당시 지도는 Kakao 배경·도로 구간별 선형·출발/도착 마커가 정상 표시됐고 예상 소요시간은 **55.9분**. 이 값은 당시 캡처 결과이며 앞선 `MISS` 화면의 **59.1분**과 달라도 서로 다른 원본 조회 시각이라 오류로 확정하지 않음.
- **판정:** 30초 내 동일 경로의 서버 메모리 캐시 HIT, 응답 헤더 표시, 캐시 반환 후 지도 렌더링 **사용자 실제 Chrome 검증 합격**. 헤더에 표시된 `6`은 캐시 저장 이후 경과 초이며 실시간 도로 센서 관측 시간은 아님.
- 앞선 **15.10 첫 요청 MISS**와 합쳐 MISS→HIT 흐름 확인. 아직 30초 만료 뒤 다시 MISS로 복귀하는 실브라우저 검증은 하지 않음. 신규 자동 TTL 테스트는 15.9에서 통과함.
- `kakao` 브랜치 루트 README만 기록. 앱 코드/DB/인증/.env/`main` 변경 없음.

### 15.12 F19-A Chrome 30초 만료 후 MISS 재조회 검증 (2026-10-19)

- 사용자가 동일 서울역→잠실역 경로를 30초 이상 기다린 뒤 Chrome `/map`에서 재조회한 스크린샷을 제출함. **실제 Network Response Headers: HTTP `200 OK`, `X-Route-Cache: MISS`, `X-Route-Cache-Age-Seconds: 0`** 확인.
- Kakao 지도에 현재 경로선(구간별 빨강·녹색 표시), 출발/도착 마커 및 예상 **56.0분**이 표시됨. 직전 HIT 화면의 55.9분과 수치가 다른 것은 재조회 결과로 설명되나 API 원본 교차 검증까지 했다는 의미는 아님.
- 사용자 Chrome 실검증 이력: **15.10 MISS → 15.11 HIT(6초) → 이번 15.12 TTL 만료 뒤 MISS**. Windows 전체 자동 테스트 66개 `OK`는 15.9에 기록. **F19-A 주요 단일 프로세스 캐시 흐름의 실사용 검증 완료**.
- 한계: 30초 이후 재조회 동작 확인이지 모든 만료 시점의 정밀 경계·다중 워커 캐시 공유·장기 부하/비용 절감률 검증은 아님. DB·기사 #11·관리자 저장 기능은 변경/조작하지 않음.
- `kakao` 루트 README에 검증 내용만 기록하고 코드·DB·인증·환경 변수·`main` 변경 없음.
