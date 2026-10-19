# 교통정보_도메인 프로젝트 — 새 채팅 인계 문서

> 기준: 2026-10-19, 작업 브랜치 **kakao**. **새 대화에서 이 파일을 먼저 읽고 최상위 README.md의 상세 설계·테스트 기록을 함께 확인할 것.** 오래된 진행 기록보다 본 문서의 최신 상태를 우선하되, 충돌 시 실제 kakao 브랜치 코드·사용자 최신 메시지를 확인.

## 1. 이 프로젝트에서 반드시 지킬 작업 원칙

1. 저장소: https://github.com/gamzpot96-cell/traffic_app_domain, **kakao 브랜치만 작업. main 브랜치 수정 금지**.
2. 정본은 저장소 **루트 README.md**. traffic-api/README.md가 아님. 모든 기능/디자인/DB 변경은 **구체적 설계를 먼저 루트 README.md에 작성해 사용자의 승인을 받은 뒤 코드 변경**. 각 사용자 테스트·브라우저 실확인 결과를 루트 README에 기록하고 해당 커밋을 안내.
3. DB 구조·기존 데이터는 사용자 별도 승인 없이는 변경하지 않는다. 특히 레거시 traffic_information 약 **30,538건** 보존. 뉴스·경로 스냅샷의 기존 데이터도 삭제/초기화/이관 금지. 설명용 가짜 실시간 측정값이나 임의 뉴스·수치 생성 금지.
4. 사용자 초보 개발자 수준에 맞게 설명하고 VS Code/PowerShell에서 실행할 **정확한 명령과 한 번에 하나씩의 브라우저 검증 단계** 안내. JavaScript 변수/함수명 명확하고 이해하기 쉬운 코드, 필요한 부분만 주석. 급한 대량 변경보다 기능 보존과 회귀검사 우선.
5. **비밀키는 채팅/README/커밋에 게시하지 않는다**. FastAPI REST 키·Supabase 비밀키와 브라우저 JavaScript 플랫폼 키를 구분한다. .env는 Git 제외. 인증·관리자 저장 권한 유지. 사용자 승인 없이 실제 기사 저장이나 외부 비용 설정 변경 금지.
6. 이 프로젝트의 실제 요구는 '서울에서 선택한 자동차 경로의 Kakao 교통 정보와 뉴스 브리핑'이지 '서울 전체 실시간 ITS 도로망'이 아니다. 자동 정기 수집/전체 도로 범위/LLM 기능을 새로 있다고 주장하거나 구현하지 않는다.
7. 소스·화면 변경 후 자동 테스트를 실행하고 사용자 Chrome 스크린샷으로 실제 UI를 확인. 문자열 검증만으로 브라우저 동작이 확인됐다고 말하지 말 것. 특히 과거 map.html 수정 때 함수 선언 유실/이벤트 중복/</script></body></html> 누락 오류가 있었으므로 **완전한 HTML 태그 및 실제 JS 본문 구문**을 검증할 것.

## 2. 로컬 실행과 서비스 구성

- Windows VS Code, 로컬 저장소 C:\workspace\traffic_app_domain.
- FastAPI 실행 위치: C:\workspace\traffic_app_domain\traffic-api.
- 가상환경 파이썬: .\.venv\Scripts\python.exe
- 코드 동기화: cd C:\workspace\traffic_app_domain\traffic-api, git pull origin kakao.
- 서버: .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload.
- 전체 테스트: .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v.
- 웹 페이지: / (홈), /news (교통뉴스와 저장기사·기록 차트·CSV), /map (카카오맵 경로), /admin (관리자 뉴스 생성/미리보기/저장).
- 기술: FastAPI, Python, HTML/CSS/Vanilla JS, 카카오 REST(Local/Mobility) 자동차 길찾기, 카카오맵 JavaScript SDK, Supabase PostgreSQL/Auth, D01 공통 디자인 CSS/메뉴, 배포 환경 관련 정보는 README 참조.
- REST API 키: 서버에만 사용, **그대로 유지**. 카카오맵 SDK는 별도 KAKAO_MAP_JS_KEY 및 개발자 콘솔에 등록된 http://127.0.0.1:8000 허용 도메인; 사용 설정 ON이라고 사용자 확인. CARTO_BASEMAP_KEY는 구 OpenLayers 지도 선택적 고해상도 타일용으로 여전히 설정돼 있을 수 있음.
- 지도 복구 페이지: /static/legacy-map.html, 기존 OpenLayers/OSM+CARTO 구현을 그대로 보존. /api/map/basemap-config는 구 지도용; /api/map/sdk-config는 카카오맵 브라우저용 JavaScript 키 설정 API. SDK 키는 브라우저에 노출되는 용도이고 서버 비밀키로 오인하지 않는다.

## 3. 완성된 기능

- Kakao Local 장소검색→Kakao Mobility 자동차 경로 조회, 도로 구간별 원활/서행/정체/미확인 색, 출발·도착 마커, 거리/시간/경로 교통 분석.
- 사용자 조회한 세 서울 경로 중심: 서울역→잠실역 2호선, 광화문→강남역, 여의도역 5호선→잠실역. 경로별 날짜/시간과 결과는 조회 시점에 따라 바뀜.
- F16: 저장된 뉴스 검색/날짜/페이지네이션. F17: Supabase에 실제 저장된 경로 스냅샷 시간별 그래프. F22: CSV 다운로드(UTF-8 BOM, 검색 조건 적용). F23: 저장 뉴스 기사에서 선택 경로→지도 연동(기사 ID/route_index).
- D01 공통 디자인: 네이비 #13243b, 파랑 #2463eb, 청록 #087e8b, 배경 #f3f6fa, 공통 navigation.css/js + design-system.css. 사용자는 홈·뉴스·지도 화면의 개선을 화면으로 확인했으며 hover 배경은 해당 순간에만 강조, 키보드 포커스 지원.
- F23 특별 보존: /map?article_id=8&route_index=0에서 기사 #8의 당시 저장 요약과 KST, 출발지·목적지 자동 입력. **버튼을 누르기 전 현재 /api/route 자동 호출 안 함**. 기사의 과거 경로 선형 자체는 저장되지 않음. 사용자가 '현재 경로 새로 조회'를 누르면 최신 카카오 길찾기 경로가 지도에 그려지고 과거 저장 요약은 변경하지 않음.

## 4. 가장 최근의 실제 검증 상태 (2026-10-19)

- 과거 CARTO 지도가 선명하지만 서울 지명이 영어 중심이고 상세도가 부족하다는 사용자 피드백으로 Kakao JavaScript SDK로 지도 엔진 교체 승인.
- Kakao Developers에서 지도 사용 ON, SDK 도메인 등록, KAKAO_MAP_JS_KEY 로컬 설정은 사용자 직접 완료.
- 카카오맵 전환 초기에 JS 함수 선언/이벤트 코드 손상과 HTML 종료 태그 누락으로 지도 공백 장애가 있었으나 kakao 브랜치에서 복구, 추가 회귀 테스트 추가. 최신 map.html은 카카오 지도 렌더링 정상(아래).
- 마지막으로 사용자가 직접 전달한 **전체 자동 테스트 결과: Ran 55 tests in 0.272s / OK** (상세 기록 README 13.13; 이후 코드 변경하지 않음). 일부 DB 예외 추적과 StarletteDeprecationWarning은 의도적 모의 테스트/비치명적 경고.
- 사용자 Chrome에서 지도 초기 상태 정상: 한글 지명, 확대 버튼, 기사 #8 카드(저장된 요약), 서울역·잠실역 2호선 입력 확인. 이어 **'현재 경로 새로 조회' 클릭 후 실제 지도 스크린샷에서도 카카오맵 한글 지도 및 실도로별 녹색/빨강/회색 경로선, 출발·도착 마커, 자동 지도 이동·현재 예상 55.2분 표시 확인**. 원래 과거 기사에 저장된 40.4분은 별도 과거 데이터이며 최신 55.2분과 달라도 오류가 아님. 교통 상태 값과 시간은 조회할 때마다 달라질 수 있음.
- **현재 진행 판정:** 카카오맵 전환 D01 지도 페이지의 실사용 경로선 브라우저 테스트 합격. 이 최종 캡처 결과는 아래 README 신규 기록에 추가할 예정. DB 미변경.
- 다음 작업은 **D01 관리자 /admin 화면 디자인 개선**. 아직 디자인 코드 변경 전. 최상위 README의 D01 통합 설계(12장)를 우선 읽고, **현재 admin.html 상세 분석→README에 관리자 화면 전용 구체 설계/검증 계획 기록→사용자 승인→코드 변경→전체 55개+신규 테스트→관리자 로그인 화면·인증된 뉴스 초안 화면 실확인** 순서를 지킬 것.
- 사용자 요청에는 로그인, 저장 등 실제 DB 변경이 포함돼 있지 않으므로 관리자 UI 테스트를 위해 실제 기사를 저장하지 말 것. 로그인에 필요한 이메일/비밀번호도 사용자에게 채팅에 공유하도록 요청하지 말 것.

## 5. 관리자 화면 다음 디자인 작업의 필수 보존 요구

- 실제 admin.html 위치: traffic-api/static/admin.html. 지금은 로그인 중심 420px 카드, 인증 후 body.admin-active 등, 기존 D01 공통 CSS와 메뉴 로딩 상태.
- 기존 인증/JS 흐름: loginForm, adminEmail, adminPassword, loginButton, loginMessage, adminPanel, logoutButton, generateDraftButton, saveDraftButton, draftStatus, draftPreview, draftTitle, draftRetrievedAt, draftLead, draftBody, draftNotice, draftRoutes, savedArticleLink. 변경 시 ID 유지.
- Supabase Auth 관리자 인증, /api/admin/login, /api/admin/me, 기사 생성(미리보기)과 **사용자가 확인한 뒤 저장** 단계 및 로그아웃 등 기존 보안/기능/이벤트 보존.
- 디자인 제안: 로그인 전 명확한 네이비 히어로/브랜드·설명+로그인 카드, 인증 후 관리자 작업실(생성/검토/저장 단계)과 뉴스 미리보기 표·상태 텍스트를 같은 색상/반응형으로 다듬는다. 850px/600px 모바일 반응형 및 포커스/상태/오류 읽기 쉬운 UI.
- 관리자 UI 변경 전 브라우저 샘플/구체 설계를 사용자에게 확인받을 것. 기존 인증 엔드포인트를 우회하거나 로그인 여부 없이 adminPanel을 보이게 하면 안 됨.
- 화면 테스트에 오류나 문법 문제 있으면 테스트 통과만 믿지 않고 브라우저 화면/Console을 확인. 변경 뒤 테스트 55개 + 관리자 회귀 테스트 예상.

## 6. 사용자를 위한 새 대화 시작법

1. 반드시 **같은 ChatGPT 프로젝트 '교통정보_도메인'**에서 새 채팅 생성 (프로젝트 외 별도 일반 채팅은 문서/지침 맥락이 덜 연결될 수 있음).
2. 첫 메시지에서 GitHub 연결로 이 파일과 `README.md`의 실제 **kakao 브랜치**를 읽고 진행하라고 구체적으로 지시. 링크만 붙이는 것은 충분치 않음. 필요시 문서를 채팅에 직접 첨부.
3. 새 채팅 첫 요청 예:
   > GitHub 저장소 gamzpot96-cell/traffic_app_domain의 kakao 브랜치에서 PROJECT_HANDOFF.md와 루트 README.md(특히 12~13장)를 먼저 읽어라. 지금까지 55개 자동 테스트와 카카오맵 경로선 실제 브라우저 검증 완료, 기존 REST API/DB 보존. 다음은 D01 관리자 화면 디자인 작업이다. 현재 admin.html과 인증 로직을 검토해 변경 상세 설계를 루트 README에 먼저 기록하고, 승인받기 전에는 코드/DB를 수정하지 마라. 초보자 친화적으로 한 단계씩 진행해라.
4. 새 채팅이 파일을 못 읽으면 해당 채팅에 PROJECT_HANDOFF.md 원문 또는 다운로드 파일을 직접 첨부하거나 GitHub 커넥터 연결을 확인.
5. **정확한 전체 대화 문장, 모든 첨부 스크린샷, 중간 추론, 모든 임시 오류 로그까지 자동·완전하게 이전되는 것은 아님**. 이 인계 문서와 README가 작업에 필요한 지식의 지속 가능한 정본이고 세부 기록은 기존 채팅/소스에 보존됨.
