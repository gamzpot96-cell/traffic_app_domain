# 개발 이력 보존 문서

> 이 문서는 2026-10-22 README 간소화 과정에서 옮긴 **당시 설계·검증 기록**입니다. 현재 동작 및 정책은 저장소 최상위 README와 소스코드를 우선 확인하세요.

## 19. 인수인계 기준 최신 기능정의서·DB·개발환경 및 F19-B 검증 정리 (2026-10-20)

> **문서 상태:** 2026-10-20 시점 `kakao` 브랜치 코드 및 기존 사용자 실환경 검증 기록을 바탕으로 정리한 **현행 기능·데이터·환경 기준표**. 이전 장의 단계별 설계와 시행착오는 이력으로 보존한다. 이 절은 새 기능이나 DB 변경을 승인/실행하는 문서가 아니다.

### 19.1 개발 기록 관리 원칙 (계속 적용)

1. 모든 개발/문서 커밋 대상은 **`kakao` 브랜치**. `main`은 직접 수정하거나 병합하지 않는다.
2. 새 기능·UI·DB/스키마 변경은 **루트 README에 목적·기능정의·화면/API·데이터 영향·회귀검사·배포 영향 설계부터 기록 → 사용자 승인 → 구현 → Windows 자동 테스트 → 사용자 Chrome 화면 검증 → README 결과 기록 → `kakao` 커밋** 순서로 진행한다. 이미 승인된 범위는 재승인하지 않는다.
3. 루트 README에 **기능정의서, DB 현황/변경 정의, 개발환경 정의**를 유지하고 변동 시마다 갱신한다. 상태는 '설계/승인/구현/자동검증/화면검증/배포'를 구분하며 과거 검증을 새로운 실행 결과로 쓰지 않는다.
4. 기존 Supabase 기록·기사·경로 스냅샷·관리자 인증/REST 키·`.env` 보존. 사용자 별도 승인 없이 데이터 삭제/초기화/스키마 변경/실제 기사 저장/외부 유료 설정 전환 금지. 비밀키·토큰·비밀번호 문서화 금지.
5. **색상과 무관하게 신규 포커스 테두리/외곽선을 추가하지 않는다.** 기존 클릭/키보드 기능과 인증 접근 제어는 유지한다.
6. GitHub 정적 코드 확인, Windows 테스트 로그, Chrome 사용자 스크린샷, 실제 배포 결과는 각각 별도의 근거로 기록한다.

### 19.2 기능정의서 — 현재 구현·검증 범위

| 식별 | 기능 | 현재 근거 기반 정의·제약 | 현재 상태 |
| --- | --- | --- | --- |
| 기본 경로 조회 | Kakao Local 장소 검색과 Kakao Mobility 자동차 길찾기, 도로 구간 상태·소요시간·거리 브리핑 | 선택한 자동차 경로 조회; 서울 전역 도로망 자동 관측 아님 | 기존 구현/브라우저 검증 기록 |
| 지도 및 기사 연동 F23 | Kakao Maps JavaScript SDK, 출발/도착 마커, 상태별 경로선; 저장 기사에서 지도 이동 | 과거 기사의 저장 당시 요약과 버튼을 눌러 조회하는 **현재** 경로를 분리. 과거 경로선 원본은 저장하지 않음 | 기존 구현/브라우저 검증 기록 |
| F16/F17/F22 | 저장 기사 검색·페이지, 실제 저장된 경로 스냅샷 변화 표시, CSV 내려받기 | 실제 Supabase 저장 자료 기반. 제공되지 않은 원인·실시간 수치를 만들지 않음 | 기존 구현/테스트 기록 |
| F18 | 홈·지도 관심 경로 즐겨찾기 | 브라우저 `localStorage`에 출발/도착만 최대 10개 저장·불러오기·개별 삭제. **자동 경로 조회 없음**, 서버/DB 동기화 없음 | 사용자 Chrome 및 Windows 검증 기록 |
| F19-A | 동일 경로 조회의 30초 캐시 | 적용 범위·키 구성·만료의 상세 원칙은 이전 F19-A 설계/구현 절 참조. 서버 메모리 성격과 최신 조회의 차이 구분 | 구현 완료(기존 기록) |
| F19-B | 카카오 API 호출·성공·실패 및 캐시 HIT/MISS 관리자 현황 | `app/api_usage.py` 프로세스 메모리에 **익명 집계**. Local/길찾기 유형, 실패 분류, 측정 시작/최근 실패 시각, 캐시 비율 표시. 자동 새로고침 없이 관리자 버튼으로 조회하며 **공식 카카오 쿼터/과금량이 아님** | Windows 84개 통과·PC/390px 사용자 화면 확인 |
| 관리자 뉴스 | Supabase Auth 권한 확인 후 뉴스 초안 생성→미리보기/검토→명시적 저장 | Bearer 인증과 관리자 UID 검사 유지. 저장 버튼/기존 기사 데이터 보존; 검증 목적으로 저장하지 않음 | 기존 구현/관련 회귀검사 |

**F19-B 검증 종결 기록:** 사용자 Windows PowerShell에서 `Ran 84 tests in 0.617s`, `OK`(실패·오류 0)인 기존 전체 테스트 로그를 제공하였다. Chrome 데스크톱 스크린샷에서는 API 통계 섹션의 **두 열 전체 너비** 및 4개 수치 카드·상세 내용·수동 갱신을 확인하였다. Chrome **390px** 사용자 스크린샷에서는 통계 카드 단일 열과 텍스트 줄바꿈, 주요 컨트롤의 겹침 없음을 확인하였다. 화면 예시 **외부 9 / 성공 9 / 실패 0 / Local 6 / 길찾기 3 / 캐시 HIT·MISS 0·0**은 당시 서버 프로세스 누적치일 뿐 공식 카카오 전체 이용량이 아니다. 이 문서 정리 단계에서 Windows 테스트를 재실행하거나 새 스크린샷을 직접 확인한 것은 아니다. 실제 기사 저장 및 Vercel 운영환경 검증도 이번 판정 범위에서 제외한다.

### 19.3 DB 정의 — 기존 DB 보존을 전제로 한 코드 확인 범위

- **DB 서비스:** Supabase PostgreSQL. 관리자 신원 검증은 별도 **Supabase Auth** 사용(`app/admin_auth.py`에서 전달된 Bearer 토큰 검증 및 허용 관리자 UID 비교).
- **`public.traffic_information`**: 레거시 자료 보존 대상. 인계 문서의 과거 약 30,538건이라는 수치는 **현시점 실 DB 건수 조회가 아님**. 본 절에서 전체 필드·제약조건 확인 안 됨.
- **`public.traffic_news_articles`**: 코드상 `id`, `title`, `lead`, `body`, `scope_notice`, `analyzed_route_count`, `retrieved_at`, `created_at`, `generation_id`를 참조. 기사 보관 및 `generation_id` 중복 저장 방지 처리(`ON CONFLICT`)에 사용.
- **`public.traffic_route_snapshots`**: 코드상 `article_id`, `start_place`, `end_place`, `distance_m`, `duration_seconds`, `total_road_count`, `congested_count`, `congested_distance_m`, `congestion_ratio`, `retrieved_at`를 사용. 기사와 연관된 경로별 당시 기록.
- **저장 관계:** `news_database.py`에서 기사와 연결된 경로 스냅샷을 하나의 DB 연결 컨텍스트로 저장. `article_id` 연결은 코드로 확인되나 **실제 외래키·인덱스·NOT NULL·RLS 및 전체 DDL은 별도 실 DB 메타데이터 검증 필요**. 여기에 적은 열 이름 목록은 **코드 사용 열**이지 검증 완료된 전체 물리 스키마 정의서가 아님.
- **F18 저장소:** 브라우저 `localStorage` 키 `seoul-traffic-favorites-v1`(Supabase 테이블 아님). **F19-A 및 F19-B 서버 메모리 값도 DB 테이블이 아니며 재시작/프로세스별로 지속성이 보장되지 않음.**
- **이번 문서 작업의 DB 변경:** 없음. SQL 실행·마이그레이션·기존 데이터/계정/권한 변경 없음. 향후 DB 변경은 승인된 **변경 전/후 컬럼 정의, 제약조건·관계, 데이터 보존/되돌리기, 검증 SQL 결과**를 본 절에 추가한다.

### 19.4 개발환경 정의 — 저장소 확인 기준

| 항목 | 설정 및 확인 한계 |
| --- | --- |
| 작업 위치 | Windows 11 / VS Code / PowerShell. 프로젝트 `C:\workspace\traffic_app_domain`, API 폴더 `C:\workspace\traffic_app_domain\traffic-api` |
| Python | 로컬 사용자 기준 **Python 3.10.10**; 이 문서 작성 시 실행 버전은 재확인하지 않음. 가상환경 `.venv` 사용 |
| 서버·프런트 | FastAPI + Uvicorn; HTML/CSS/Vanilla JavaScript; Kakao Maps JavaScript SDK와 Kakao Local/Mobility REST |
| 의존성 기준 | `traffic-api/requirements.txt`에 명시된 핀 버전이 저장소 설치 기준. 예: `fastapi==0.142.1`, `uvicorn==0.54.0`, `httpx==0.28.1`, `psycopg[binary]==3.3.6`. 현재 로컬 설치 여부는 미확인 |
| DB·인증 | Supabase PostgreSQL 및 Supabase Auth. 프로젝트 URL은 사용자 제공 `https://lvokohdfixnpfudruguj.supabase.co`; 인증키·DB 비밀번호는 README 기록/노출 금지 |
| 환경변수 | Kakao 서버 REST 키, `KAKAO_MAP_JS_KEY`(브라우저용 플랫폼 키), Supabase 접속·Auth 설정, 선택적 구 지도 `CARTO_BASEMAP_KEY`. 실제 값 및 설정 상태는 보존하며 문서에 복제하지 않음 |
| Vercel | **배포 예정.** 저장소 `traffic-api/vercel.json`에서 지역 `icn1`, Python 함수와 정적 파일 라우팅 선언 확인. 배포 성공·환경변수 적용·빌드 호환성은 **미검증** |
| 로컬 전체 검사 | `cd C:\workspace\traffic_app_domain\traffic-api` 후 `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v` |
| 로컬 웹 실행 | `.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload` |
| Git 동기화 | 사용자 작업 복구 시 작업 트리 상태 확인 후 `kakao`에서만 `git pull origin kakao`. `main`에 쓰기·병합 금지 |

### 19.5 앞으로 README 갱신 시 필수 확인표

새 기능 또는 환경 변화마다 **(1) 기능정의·승인 여부, (2) DB 테이블/스키마/데이터 영향 또는 변경 없음, (3) Python·패키지·환경변수 이름·외부 서비스·배포 설정 변화 또는 변경 없음, (4) 테스트 수치와 수행 환경, (5) 사용자 실화면 검증 상태, (6) `kakao` 커밋 및 배포 상태**를 같은 변경 기록에 덧붙인다. 확인되지 않은 내용은 '미확인/미검증'으로 표시하며 과거 검증 기록을 지우지 않는다.

**이번 변경의 범위:** README 문서화만 수행. 앱 소스·테스트·DB·환경변수·관리자 인증·`main` 변경 없음. 향후 새로운 기능이 정해지면 먼저 이 문서에 구체적 설계를 쓰고 승인을 받는다.

## 20. Vercel 배포 사전 점검 — 승인 전 설계 (2026-10-20)

> **상태: 설계·점검 계획 작성 단계.** 기능·설정·DB·인증 코드를 변경하거나 실제 배포를 시작하지 않았다. 사용자가 배포 점검 및 필요한 수정 범위를 승인한 후 실행한다. 이전에 제거한 별도 과제 내용은 이 README에 포함하지 않는다.

### 20.1 목표와 범위

- 기존 `kakao`의 FastAPI/HTML/CSS/JS·카카오 지도/경로·뉴스/Supabase Auth를 **변경 없이 배포할 수 있는지 우선 점검**한다.
- 실제 배포 전에 Vercel 프로젝트/루트 디렉터리/프레임워크 설정과 환경변수의 **이름·설정 여부**만 확인하고 값·비밀번호·토큰은 기록하지 않는다.
- `traffic-api/vercel.json`의 `icn1`, `@vercel/python` `app/main.py`, `@vercel/static` `static/**` 및 현재 라우팅이 빌드/서비스와 일치하는지 검증한다. 파일 존재만으로 작동을 단정하지 않는다.
- `app/database.py`의 Supabase PostgreSQL Pooler 기본 포트 6543/SSL 사용을 확인했으며, 운영 환경에서의 접속은 별도로 확인한다. 기존 DB/테이블/레코드·인증/권한은 유지한다.
- F19-A 30초 캐시와 F19-B API 통계는 현재 **프로세스 메모리** 사용: Vercel Serverless에서 인스턴스·재시작 사이에 값이 공유·영속된다고 안내하지 않는다. DB에 자동 이전하거나 저장하지 않는다.
- `main`은 배포 점검·개발 과정에서 변경하지 않는다. 최종 완료 시 별도 사전 확인을 거쳐 `kakao` 결과를 `main`에 반영한다.

### 20.2 배포 전 사전 검증 계획

1. 현재 `kakao` HEAD·작업 트리와 프로젝트 구조, Vercel 연결 상태·Root Directory 확인(조회 우선).
2. 패키지 설치 및 Python 런타임/의존성 호환 여부 검사. 현재 `requirements.txt`에 `fastapi==0.142.1`, `uvicorn==0.54.0`, `httpx==0.28.1`, `psycopg[binary]==3.3.6` 기재. Vercel 런타임 버전은 **아직 미확인**.
3. 환경변수는 이름 및 적용 환경만 검수(예: Kakao REST/지도 JS, Supabase PostgreSQL/Auth, ADMIN_USER_ID). **실제 값은 열람·출력·README 삽입하지 않음.**
4. 기능 회귀: 사용자 Windows 전체 `unittest discover` **84개 기존 합격을 기준**으로 코드 변경이 있으면 재실행. Vercel 배포 이후 `/`, `/news`, `/map`, `/admin`, 공개 라우트/권한 보호 API를 실제로 확인한다.
5. 지도 Kakao SDK 배포 도메인 허용 등록, 수동 경로 조회·F23 기사 연동, 뉴스 조회, 비로그인 관리자 접근 차단, 관리자가 수동으로 API 통계 확인하는 흐름을 점검. 운영 데이터 훼손을 피하기 위해 기사 저장 API 실제 호출·임의 행 삽입 금지.
6. 브라우저 데스크톱/390px 캡처는 사용자로부터 확인받아 실제 표시 결과를 기록. **모든 색상의 포커스 테두리 신규 추가 금지**.
7. 오류 발생 시 로그/응답을 확인하고 **최소 범위 수정안을 먼저 README에 기록하고 승인 후 변경**. 수정 후 자동 테스트·화면 점검·README 검증 결과를 `kakao` 커밋.

### 20.3 기능정의서·DB·개발환경 변경 영향

- **기능정의:** 배포 검증만 실시하며 F18/F19-A/F19-B 등 기존 기능 정의 변경 없음.
- **DB:** 기존 `traffic_information`, `traffic_news_articles`, `traffic_route_snapshots` 및 Supabase Auth 유지. DDL/마이그레이션/데이터 삭제·추가 없음.
- **개발환경:** Windows 11 로컬 환경 그대로 유지. Vercel 실제 프로젝트/런타임/환경변수 적용 상태는 미확인. 확인 후 19.4의 확인 범위를 갱신.
- **배포·테스트 상태:** GitHub 설정 파일만 확인. **실제 Vercel 빌드·운영 동작 검사 및 새 Windows 테스트 미실행.**
- **승인 대기:** 이 점검 절차의 진행 승인을 받은 뒤 우선 Vercel 연결/설정 상태를 읽기 전용으로 확인한다. 설정/기능 변경이 필요하면 별도 승인 전까지 변경하지 않는다.


### 20.4 Vercel 연결 계정 읽기 전용 조회 결과 (2026-10-20)

- 사용자가 20장 점검 계획을 승인해 Vercel 연결 계정의 프로젝트 목록과 `journalismstudy` 프로젝트 설정·배포 메타데이터를 **읽기 전용**으로 조회.
- 연결 계정 프로젝트 목록에서 `journalismstudy`(FastAPI), `portfolio-webpage` 두 건을 확인. 이름 검색(`traffic`) 및 저장소 필터(`gamzpot96-cell/traffic_app_domain`) 결과는 모두 **0건**. 이 연결 계정 범위에서는 현재 교통정보 저장소에 연결된 Vercel 프로젝트를 확인하지 못함. 다른 계정/범위의 프로젝트까지 없다고 단정하지 않는다.
- `journalismstudy`의 최근 배포 기록은 `gamzpot96-cell/journalismstudy` 저장소 **`main`** 브랜치를 가리킴. 현재 `gamzpot96-cell/traffic_app_domain`의 **`kakao`** 배포 기록으로 해석하지 않는다. 해당 기존 프로젝트의 설정은 수정하지 않음.
- 따라서 교통정보 프로젝트의 Vercel **Root Directory, Python 런타임, 환경변수 적용 여부, 실제 배포 성공**은 아직 확인되지 않았다. 연결할 새/기존 올바른 프로젝트가 결정되기 전까지 환경변수·프로젝트 설정을 변경하거나 배포하지 않는다.
- 차기 단계 제안: 사용자 확인 후 **교통정보 저장소 전용 Vercel 프로젝트 연결 설계**를 마련한다. 연결 저장소 `traffic_app_domain`, 배포 브랜치 `kakao`, Root Directory `traffic-api` 후보를 검토하되 실제 설정 변경은 별도 승인 후 시행.
- **검증 범위:** Vercel 메타데이터 조회만 수행. 앱 코드·Supabase DB/인증·운영 환경변수·기존 Vercel 프로젝트·`main` 불변. Windows 전체 84개는 앞선 사용자 검증 기록이며 이 단계에서 재실행하지 않았다.


### 20.5 교통정보 전용 Vercel 프로젝트 분리 설계 및 사용자 결정 (2026-10-20)

- **사용자 결정:** 기존 `journalismstudy`에 덮어쓰지 않고 **Vercel 프로젝트 `traffic_app_domain`를 새로 만든다.** `portfolio-webpage` 등 기존 프로젝트는 그대로 유지.
- 대상 소스 저장소: GitHub `gamzpot96-cell/traffic_app_domain`; **현재 개발·배포 대상은 `kakao` 브랜치**. `main`은 프로젝트 종료 후 최종 병합 전까지 변경하거나 개발 단계에서 배포 소스로 사용하지 않는다.
- 프로젝트 설정 제안: 이름 `traffic_app_domain`, FastAPI 프레임워크, 저장소 루트 기준 **Root Directory `traffic-api`**, 서버 함수 지역 `icn1`(기존 `traffic-api/vercel.json` 기준). 루트와 함수 경로/빌드 조합은 실제 첫 배포 단계에서 검증할 것.
- **단계 구분:** 우선 새 Vercel 프로젝트만 생성하여 분리 확인. 잘못된 `main` 자동 배포를 막기 위해 Git 연결과 Production Branch 적용·최초 배포는 이후 Git 연동 방식과 보호 설정을 확인한 뒤 진행. 신규 프로젝트 생성 자체를 배포 성공으로 취급하지 않는다.
- 환경변수/비밀: 새 프로젝트에서 개별 설정해야 하며 기존 `journalismstudy`의 값 복사·출력 금지. Supabase 기존 DB·관리자 인증/기존 기사·스냅샷 및 카카오 REST/지도 키를 변경하지 않는다.
- 확인 계획: 기존 Vercel 2개 프로젝트가 그대로 있는지 확인, 새 프로젝트 이름/ID/Root Directory/프레임워크/지역 확인, Git 브랜치와 배포 상태 확인. 배포 이전에는 실 URL/기능 작동을 주장하지 않는다.
- **기능정의·DB·개발환경 영향:** F18/F19-A/F19-B 기능 수정 없음, DB 스키마 및 데이터 변경 없음. 새로운 Vercel 프로젝트 분리만 개발환경 변경으로 본 절에 기록한다. 포커스 외곽선 모든 색상 추가 금지.


### 20.6 Vercel 신규 프로젝트 생성 권한 오류 (2026-10-20)

- 20.5의 사용자 결정에 따라 `traffic_app_domain` 프로젝트를 별도 생성하려고 Vercel 프로젝트 생성 API를 호출했지만, **HTTP 403 Forbidden** 및 해당 `gamzpot966` 범위에 대한 인증/접근 권한 오류가 반환됨.
- 요청한 최초 설정: 이름 `traffic_app_domain`, 프레임워크 `fastapi`, Root Directory `traffic-api`, 함수 지역 `icn1`. **API가 거부했으므로 생성 성공·설정 적용·Git 연결을 주장하지 않음.**
- 기존 `journalismstudy`, `portfolio-webpage` 설정 변경 없음. GitHub `main`, Supabase DB·인증, 기사, REST 키 및 코드 변경 없음.
- 차기 진행은 해당 Vercel 범위에 대한 사용자 계정 권한/연결 인증 확인 뒤 프로젝트 존재 여부 재조회. 403 오류를 무시하고 다른 Vercel 팀/계정에 프로젝트를 임의 생성하지 않는다.


### 20.7 Vercel 최초 배포 시작 — 사용자 승인 및 GitHub 트리거 (2026-10-20)

- 사용자 승인: **`kakao` 브랜치 README 문서 커밋으로 최초 Vercel 배포 자동 시작을 시도하고 결과를 확인**. `main`, 기존 Supabase 데이터·인증·앱 소스는 수정하지 않는다.
- 사용자 제공 Vercel 화면에서 확인한 설정: 별도 프로젝트 `traffic_app_domain`, GitHub `gamzpot96-cell/traffic_app_domain` 연결, **Production Branch `kakao`**, Framework Preset FastAPI, Root Directory `traffic-api`, Production 환경변수 14개 등록(실제 값은 문서에 포함하지 않음). 배포 직전 Overview에는 **No Production Deployment**로 표시됨.
- 이 README 수정은 **배포 트리거 시도 기록**이다. README는 Root Directory `traffic-api` 밖에 있으므로 Vercel 설정에 따라 **문서 전용 커밋의 빌드가 건너뛰어질 수 있음**. 실제 배포가 생성됐는지는 별도 조회·사용자 화면으로 판정한다.
- 보안: 이전 사용자 스크린샷에 일부 외부 API 키의 실제 값이 노출됨. 비밀 값을 README/로그에 복제하지 않고, 공개 운영 전 해당 키의 교체 필요. 키 교체는 별도 절차로 진행.
- 검증 대기: 배포 생성 여부, 빌드 상태, 배포 URL, 공개·관리자 API 및 DB 연동, 카카오맵 도메인 허용, 데스크톱/390px 화면. **이 절 자체는 배포 성공 기록이 아니다.**


### 20.8 Vercel 최초 Production 빌드 결과 (2026-10-20)

- `kakao` 브랜치 루트 README 커밋 `09faa95cc7bac8d3281d836a8f2328a358f4ad7b` 이후 Vercel 프로젝트 `traffic_app_domain`에 **실제 Production 배포** `dpl_BDeg6HN9qyFqYuU6EmuEbPsmh2ee`가 생성됨. Vercel 배포 기록의 Git ref는 `kakao`, Git SHA는 위 커밋과 일치한다.
- 최초 조회 `BUILDING`, 재조회 **`READY`**. 배포 URL: `https://trafficappdomain-j4rw9xs7p-gamzpot966.vercel.app`. 이는 **Vercel 배포 상태가 READY라는 뜻**이며 홈페이지 HTTP 응답·FastAPI 라우팅·카카오 지도 SDK·Supabase 연결·관리자 인증의 실제 정상 동작을 보증하지 않는다.
- **후속 확인 필수:** `/`, `/news`, `/map`, `/admin` 직접 로딩과 공개/인증 API, Root Directory 기준 정적 파일 제공, Kakao SDK 허용 도메인 및 Production 환경변수의 유효성. 배포 상태 점검 중 실제 기사 저장/DB 수정 호출 금지. 운영 공개 전에 이전 스크린샷에 노출된 외부 키 교체 검토.
- 변경 범위: 이 절의 README 기록만 추가. 애플리케이션 코드, Supabase 데이터·스키마, `main` 브랜치 및 기존 `journalismstudy` 프로젝트 변경 없음.


### 20.9 Vercel 대표 도메인 및 카카오맵 실제 화면 확인 (2026-10-20)

- 사용자 Vercel Domains 화면: 신규 대표 도메인 `https://traffic-app-domain.vercel.app`이 **Valid Configuration / Production**으로 표시됨. 구 `project-z00fk.vercel.app`은 신규 도메인으로 **307 리디렉션** 설정. 배포별 임시 URL과 구분한다.
- 사용자가 Kakao Developers에 새 대표 도메인의 JavaScript SDK 허용 도메인을 등록했다고 보고.
- 사용자 Chrome `https://traffic-app-domain.vercel.app/map` 스크린샷: 이전 SDK 로딩 실패 상태 대신 **카카오맵 지도 타일, 한글 지명, 서울역→잠실역 2호선 출발/도착 마커, 교통상태별 경로선, 당시 예상 43.5분**이 실제 표시됨. 대표 도메인에서 지도 SDK 로딩 및 경로 렌더링 정상 판정.
- **검증 한계:** 사진에 표시된 값은 당시 조회 결과로 실시간 고정 수치가 아니며, 지도 줌 버튼 조작/모바일 390px/기사 링크 재진입/인증·저장 전 과정은 이 캡처만으로 입증되지 않음. 이전 Chrome 일부 화면의 '위험' 경고 표시 원인은 별도 확인 필요.
- **기능정의·DB·환경 반영:** 기존 기능·DB/기사/관리자 인증과 앱 코드는 변경하지 않음. Vercel 대표 도메인 및 Kakao SDK 웹 도메인 설정만 변경됨. `main` 및 `journalismstudy` 변경 없음. API 키 값/비밀번호는 README에 기록하지 않음.


### 20.10 Vercel 관리자 로그인 전후 및 주소창 경고 재확인 (2026-10-20)

- 사용자가 새 Production 대표 도메인 `https://traffic-app-domain.vercel.app/admin` Chrome 화면 2장 제공: (1) 로그인 전 관리자 로그인 폼, (2) 로그인 직후 관리자 작업실의 `관리자 권한 확인 완료` 안내, 뉴스 생성/검토/저장 카드 및 로그아웃 버튼 표시를 확인. **관리자 로그인 후 화면 전환 성공**으로 판정하며 실제 저장을 실행한 검증으로 보지 않는다.
- 두 화면의 Chrome 주소창에 기존 배포별 임시 URL에서 나타났던 **빨간 '위험' 문구가 보이지 않음**. 따라서 새 도메인에서 해당 경고가 재현되지 않았음은 확인되나, 과거 경고의 원인은 **미확인**. Gmail 형식 이메일을 원인으로 단정하지 않는다.
- **잔여 보안 확인:** 비인가/유효하지 않은 인증 차단, 세션 만료, 로그아웃 동작, 실제 브라우저 정책 판정은 캡처만으로 확정되지 않음. 기존 DB 레코드·관리자 계정·인증 설정을 변경하거나 테스트 목적으로 새 기사 저장하지 않음.
- **변경 범위:** 사용자 실브라우저 검증 기록만 추가. 기능정의 및 DB 스키마·데이터 불변, 개발환경의 새 Vercel 도메인에서 로그인 화면 확인. 앱 코드·`main` 변경 없음.


### 20.11 Vercel 관리자 로그아웃 후 로그인 화면 복귀 (2026-10-20)

- 사용자 직접 브라우저 확인: Production 대표 도메인 `/admin`에서 관리자 로그인 후 **로그아웃 버튼을 누르자 다시 로그인 화면으로 돌아옴**. 로그아웃 UI 및 비로그인 화면 복귀 동작을 통과로 기록.
- **검증 한계:** 화면 전환만 확인했으며, 이전 Bearer 토큰의 서버 측 무효화나 로그아웃 후 인증 API에 대한 재요청 차단까지 입증한 것은 아님. 현재 Supabase Auth 기반 서버 검증/허용 UID 확인 로직은 기존대로 유지.
- 변경 범위: README 확인 이력만 갱신. FastAPI 코드·기존 기사·Supabase 데이터/인증 설정·환경변수·`main` 불변. 이번 사용자 확인에 별도 Windows 테스트 재실행 없음.


### 20.12 로그아웃 후 관리자 URL 직접 재접속 검증 (2026-10-20)

- 사용자 확인: Vercel Production 대표 주소 `https://traffic-app-domain.vercel.app/admin`에서 로그아웃한 다음 주소창에 `/admin`을 직접 입력하여 재접속했을 때 **관리자 작업실 대신 로그인 화면만 표시됨**. 로그아웃 후 브라우저 UI 접근 제한 흐름 통과.
- 검증 근거: 사용자 실제 Chrome 조작 결과 보고. 새로운 서버 테스트나 네트워크 응답 확인은 수행하지 않았으며 **이전 토큰의 서버 측 무효화, 강제 인증 API 호출 차단은 이 결과만으로 확인되지 않음**.
- 현행 기능정의·DB·개발환경 변화 없음. Supabase 데이터, 관리자 계정 설정, 앱 소스 및 `main` 불변. README 검증 이력만 추가.


### 20.13 Vercel F19-B 관리자 사용 현황 실화면 검증 (2026-10-20)

- 사용자 제공 Production 대표 주소의 관리자 화면 캡처에서 로그인이 유지된 작업실과 **4. API 사용 현황** 전체 너비 섹션, 수동 `사용 현황 새로고침` 버튼, `사용 현황을 갱신했습니다.` 알림, 4개 요약 카드 및 상세 집계가 표시됨. Vercel 환경 **F19-B 관리자 통계 조회·렌더링 성공**으로 판정.
- 캡처 당시 외부 호출 **0건**, 성공 **0건**, 실패 **0건**, 캐시 HIT/MISS **0/0**, 장소 검색/자동차 길찾기 **0/0**, 최근 외부 요청 실패 **없음**. 집계 시작은 화면상 **2026-10-20 14:58:29 KST**. 이는 해당 서버 프로세스의 익명 계측값이지 카카오 공식 이용량이나 전체 Vercel 인스턴스 합산 통계가 아님.
- **검증 한계:** 실제 Kakao API 호출 뒤 카운터가 증가하는지, 요청 사이의 Vercel 인스턴스 일관성이 있는지는 이 캡처만으로 확인되지 않음. 카운터는 프로세스 메모리 방식이므로 재시작·인스턴스 교체 시 초기화될 수 있음.
- 기능정의·DB·개발환경: 기존 F19-B 설계와 API·DB 스키마·인증 방식에 수정 없음. 이번 변경은 README 실브라우저 검증 기록만 추가하며 앱 코드, Supabase 기록, 환경변수 및 `main` 변경 없음. Windows 84개 시험은 이전 사용자 기록이며 이번에 재실행하지 않음.


### 20.14 Vercel 실제 경로 조회 후 F19-B 카카오 API 카운터 확인 (2026-10-20)

- 사용자 Chrome Vercel Production 대표 도메인 캡처 2장 제공. 지도 `/map`에서 **서울역 → 잠실역** 자동차 경로와 카카오맵의 한글 타일, 출발·도착 마커, 구간별 경로색 및 당시 **예상 42.9분** 표시 확인.
- 해당 조회 후 관리자 `/admin`에서 **사용 현황 새로고침** 결과: 외부 호출 **3건**, 성공 **3건**, 실패 **0건**, 장소 검색 **2건**, 자동차 길찾기 **1건**, 캐시 HIT/MISS **0/1**, 경로 조회 실패 **0건**. 앞선 조회 전 캡처의 외부 호출 **0건**과 달리 카운터 증가 표시를 실브라우저에서 확인. 캡처 표시 집계 시작 시각 **2026-10-20 15:00:04 KST**.
- **판정:** 이 Vercel 실행 인스턴스에서 카카오 API 경로 조회 및 F19-B 통계 집계·관리자 렌더링 정상 확인. `0/1`은 이 관측의 캐시 HIT/MISS이며 지속적 캐시 적중률 검증은 아님.
- **한계:** F19-B는 서버 프로세스 메모리의 익명 계측값으로 인스턴스 교체·재시작 시 초기화될 수 있으며 Vercel 모든 인스턴스 합산/카카오 공식 사용량이 아니다. 실제 네트워크 로그·Kakao 콘솔 과금 수치와 대조하지 않았고, 모바일 390px Production 검증은 별도.
- **영향:** 기능정의·DB 스키마·개발환경 설정 수정 없음. 코드·Supabase 기존 데이터·관리자 인증·환경변수 및 `main` 변경 없이 README 검증 증거만 기록.


### 20.15 Vercel 모바일 390px 사용자 점검 (2026-10-20)

- 사용자 보고: Production 대표 도메인에서 홈 `/`, 지도 `/map`, 뉴스 `/news`를 Chrome **모바일 너비 390px**로 확인했고 정상 동작했다고 전달함. 각 페이지의 모바일 개별 화면 캡처는 이번 메시지에 포함되지 않아 **사용자 수행 확인**으로 기록하고 시각적 세부 배치는 독립 검증으로 단정하지 않는다.
- 첨부된 `/admin` 스크린샷은 상단 데스크톱 내비게이션 및 다열 카드가 보이는 **데스크톱 너비** 화면으로, 관리자 390px의 API 사용 현황 요약 1열 배치 검증 근거가 아님. **Production 관리자 390px 통계 화면은 아직 확인 대기**.
- 기존 F18/F19-A/F19-B 기능, DB 스키마/데이터 및 Vercel 설정 변경 없음. README 확인 기록만 수정. Windows 자동 테스트 재실행 없음. `main` 불변.


### 20.16 Vercel 관리자 390px 실제 화면 검증 (2026-10-20)

- 사용자 Production 대표 도메인 `/admin` Chrome **390px 모바일 전체 길이 캡처** 제공. 관리자 상단 메뉴 모바일 전환, 관리자 작업실 안내, 기사 생성/검토/저장 단계의 세로 배치, 기사 미리보기 및 **4. API 사용 현황** 카드가 화면 너비 내에서 표시되는 것을 확인.
- F19-B 요약 카드 **외부 호출/성공/실패/캐시 HIT·MISS가 모바일 1열**로 배치됨. 수동 `사용 현황 새로고침` 버튼과 하단 세부 집계 문구도 나타남. 캡처 범위에서 통계 카드·버튼의 겹침이나 뚜렷한 가로 넘침이 보이지 않음.
- 캡처 당시 외부 호출 **9건**, 성공 **9건**, 실패 **0건**, 캐시 HIT/MISS **0/0**으로 표시됨. 이는 캡처 당시 해당 Vercel 서버 프로세스의 익명 통계이며, 과거 3건과 동일한 프로세스의 연속 누적을 의미하거나 카카오 공식 전체 호출량을 뜻하지 않는다.
- **검증 판정:** Vercel Production 관리자 390px 브라우저 렌더링과 F19-B 1열 통계 배치 확인 완료. 스마트폰 실기기·여러 모바일 브라우저, 로그인/저장 전체 동작을 이 캡처만으로 확인한 것은 아니다. 코드 수정이나 새 포커스 테두리 추가 없음.
- **기능정의·DB·개발환경:** 기존 기능/DB 스키마 및 운영 환경변수 변경 없음. README 검증 기록만 추가, `main` 및 기존 Supabase 데이터/기사/관리자 인증 불변. 이 문서 작업에서 Windows 테스트를 새로 실행하지 않음.


### 20.17 승인된 관심 경로 메뉴·조회 안내 문구 정합성 개선 설계 (2026-10-20)

- **승인:** 사용자가 지도 화면에서 발견된 두 UI 불일치 수정 승인: (1) 이미 F18로 구현된 공통 내비게이션 `관심 경로 — 준비 중` 표시를 실제 지도 내 관심 경로 영역으로 연결; (2) 출발지/목적지가 채워졌는데도 `출발지와 목적지를 입력하세요.`라고 나오는 초기 경로 결과 안내를 적절한 수동 조회 안내로 변경.
- **구현 설계:** `static/navigation.js`에서 관심 경로를 `/map#favoriteRoutes` 링크로 전환하고 기존 예정 기능 표시는 나머지 메뉴에 유지. `static/map.html`의 `#result` 초기 안내를 `경로 표시 버튼을 눌러 현재 교통정보를 조회하세요.`로 변경. `static/favorites.js`에서 지도 페이지의 즐겨찾기 불러오기 후 `#result` 메시지를 `경로를 불러왔습니다. 경로 표시 버튼을 눌러 현재 교통정보를 조회하세요.`로 갱신하되 **자동 API 호출은 하지 않는다**. 기본 지도 경로 조회 결과와 오류 메시지는 그대로 유지.
- **검증 설계:** 기존 공통 메뉴·즐겨찾기·자동 조회 금지 회귀 테스트 유지, 메뉴 링크·초기 안내·불러오기 안내 관련 검사를 추가. Windows 전체 `unittest discover` 사용자 환경 실행 및 PC/390px 화면 확인 후 정상 여부 판정.
- **기능정의:** F18 기존 완료 기능에 대한 UI 연결·문구만 정리. **DB:** Supabase 데이터·기사·인증·스키마 무변경. **개발환경:** Vercel/Windows/Python/의존성/환경변수 무변경. CSS·포커스 외곽선 신규 추가 금지; `main` 불변.


### 20.18 관심 경로 메뉴·안내 문구 수정 결과 및 검증 대기 (2026-10-20)

- **승인 범위 구현:** 공통 `static/navigation.js`의 '관심 경로'를 '준비 중'에서 `/map#favoriteRoutes` 링크로 전환. 지도 `static/map.html`의 경로 미조회 초기 메시지를 수동 '경로 표시' 안내로 교체. `static/favorites.js`에서 지도 페이지 즐겨찾기를 '불러오기'한 경우 지도 결과 안내를 함께 갱신; API 자동 호출 없음.
- **테스트:** `tests/test_favorites.py`에 메뉴 링크·대상 ID·초기 안내·불러오기 문구·자동 호출 금지에 관한 정적 회귀 테스트 1개 추가. GitHub 파일 재조회에서 지정한 변경 문자열의 존재와 기존 `planned` 표현 제거를 확인함. **Windows 전체 unittest 및 실제 Chrome 화면 테스트는 아직 재실행되지 않았으며 결과 대기.** 기존 84개 통과는 수정 전 기록이고, 현재 테스트 파일에는 새 테스트 1개가 추가됨.
- **개발환경/DB:** Python·Vercel 배포 설정·환경변수·Supabase 테이블/데이터·기사·관리자 인증 **변경 없음**. CSS·포커스 테두리·`main` **변경 없음**. `kakao`의 문서/JS/HTML/테스트 파일만 커밋됨.
- **확인 절차:** 사용자 Windows `C:\workspace\traffic_app_domain\traffic-api`에서 `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v` 실행 후 합격 건수/실패를 기록하고, Vercel `kakao` 배포가 READY인지 확인. 지도 드롭다운 '관심 경로' 링크를 눌러 즐겨찾기 영역으로 이동되는지, 불러오기 뒤 경로를 자동 재조회하지 않고 '경로 표시' 안내가 보이는지 데스크톱·390px에서 점검.


### 20.19 Windows 자동 테스트 85개 통과 (2026-10-20)

- 사용자 제공 Windows PowerShell 실행 로그: 전체 테스트 85개, 1.197초, 최종 OK (실패 0개).
- 새 테스트 test_manual_route_guidance_after_load 포함 모두 통과.
- 라이브러리 경고와 예외 대응 모의 시험 로그는 테스트 실패가 아님.
- traceback의 Python314 경로로 인해 Python 3.10.10 기준과 실제 가상환경 버전 일치 여부를 별도 점검 예정.
- GitHub kakao의 UI 수정 검증 자동 테스트 완료, 사용자 Chrome에서 메뉴 및 안내 문구 수동 확인은 대기.
- 프로그램, DB, 관리자 인증, main 브랜치 변경 없음.


### 20.20 Windows 가상환경 Python 실제 버전 확인 (2026-10-20)

- 사용자 PowerShell에서 `.\.venv\Scripts\python.exe --version` 실행 결과 **Python 3.14.7** 직접 확인. 기존 README의 Python 3.10.10은 이전 학습·환경 기준이었으며 현재 `traffic-api/.venv` 실제 실행 버전과 다르다.
- 같은 Windows 가상환경에서 전체 85개 자동 테스트가 `OK`로 통과한 기록이 있다. 따라서 현재 정상 환경을 재생성하거나 다운그레이드하지 않는다.
- Vercel Production Python 런타임의 실제 버전은 별도 확인 전까지 미확인. 애플리케이션 코드·의존성·Supabase 데이터·관리자 인증·Vercel 설정 및 `main` 브랜치 변경 없음.
- 향후 개발환경 정의는 Windows 실제 Python 3.14.7과 Vercel 런타임을 구분해 관리한다.


### 20.21 관심 경로 공통 메뉴 실제 이동 검증 (2026-10-20)

- 사용자 Vercel Production 실브라우저 점검: 상단 `교통 현황 → 관심 경로` 클릭 시 `/map#favoriteRoutes`의 실제 관심 경로 영역으로 정상 이동한다고 확인.
- F18 완료 기능의 메뉴 오표기('준비 중') 개선 후 실제 메뉴 연결 통과. 경로 즐겨찾기 불러오기 후 `경로 표시` 안내 문구는 별도 사용자 화면 확인 대기.
- 코드 및 DB 스키마/데이터, 환경변수, 관리자 인증, `main` 변경 없음. 이 절은 README 실검증 기록만 추가.


### 20.22 Vercel 즐겨찾기 불러오기 안내 실화면 검증 (2026-10-20)

- 사용자 제공 Production `/map` 스크린샷에서 저장된 `서울역 → 잠실역` 관심 경로, 불러오기·삭제 버튼, 입력된 출발지/목적지 표시 및 **'경로를 불러왔습니다. 경로 표시 버튼을 눌러 현재 교통정보를 조회하세요.'** 안내를 확인.
- 클릭 직후 새 경로 결과가 표시되지 않았으며 수동 조회 안내가 노출됨. 자동 API 요청이 없었다는 것은 화면만으로 확정하지 않고, 별도 통과한 정적 회귀 테스트와 구분한다.
- **UI 2건 최종 화면 검증 완료:** 공통 메뉴 '관심 경로' 링크 이동(20.21절) 및 즐겨찾기 불러오기 후 안내 정합성(본 절). Windows 전체 테스트 85개 OK(20.19절).
- 기능정의 F18 내용 유지, DB 스키마·데이터 및 개발환경 변경 없음. 앱 코드·관리자 인증·포커스 테두리·`main` 변경 없이 README 검증 기록만 추가.

## 21. 기능정의서·실제 소스 재점검과 남은 작업 (2026-10-20)

### 21.1 평가 기준 및 정량 현황

- 평가 대상은 **F01~F23 총 23개 고유 기능 ID**. 이 중 **F01~F18, F22, F23: 20개 기능을 구현 완료로 분류**, **F19/F20/F21: 3개는 부분 구현**으로 분류한다. 따라서 *기능 ID 단위 구현 완료 비율은 20/23 = 약 87.0%*. **부분 기능을 0으로 계산한 보수적 개수 기준**이며 실제 투입 시간·품질·운영 준비율과 동일하지 않음.
- **기능 범위의 차이:** F19의 자동 수집·캐시 통합 목표 중 30초 캐시(F19-A)와 프로세스별 API 성공/실패 계측(F19-B)은 완료. **정기 예약 수집과 DB 영구 적재는 미구현.** F20의 초안 검토/직접 저장은 F13~F15로 구현됐지만 **공개·보류 상태/편집 승인 워크플로**는 미구현. F21의 실패 횟수·유형 현황은 F19-B로 구현됐지만 **지속적 장애 저장·자동 경고**는 미구현.
- 사용 가능한 웹앱과 프로젝트 범위 100% 달성은 구분해야 함. 선택적 메뉴의 FAQ·공지·기사 공유·운영 설정 등도 '준비 중'이며, 기능 ID 통계에 임의로 별도 기능 건수로 중복 계산하지 않는다.

### 21.2 실제 파일 재점검 근거

- `app/main.py`: `/api/route`, `/api/briefing/overview`, `/api/briefing/news`, `/api/news/history`, `/api/news/search`, `/api/traffic/history`, `/api/traffic/routes`, `/api/traffic/export.csv`, `/api/admin/me`, `/api/admin/login`, `/api/admin/news/generate`, `/api/admin/news/save`, `/api/admin/api-usage` 경로 존재 확인. **기사 발행 승인·보류 API 및 스케줄 작업 엔드포인트는 확인되지 않음.**
- `static/news.html`: 검색 폼/추세/CSV UI 존재 확인. `static/map.html` 및 `static/favorites.js`: 즐겨찾기와 수동 조회 흐름 확인. `static/admin.html`: 기사 초안 및 API 현황 UI 확인. `app/api_usage.py`: 익명 메모리 집계. `app/news_database.py`: 기사·저장 경로 DB 처리.
- `sql/traffic_database.sql`은 저장소의 참조 SQL이며 **현재 Supabase 물리 DDL과 일치한다고 검증한 결과는 아님**. 실 DB 보존을 위해 이번 작업에서 마이그레이션/SQL 쓰기 수행하지 않음.
- **테스트 증거:** 사용자 Windows Python **3.14.7** 가상환경에서 **85개 unittest 모두 OK**(20.19~20.20 참조). 이번 소스 재점검은 GitHub 정적 확인이며 Windows 테스트를 새로 실행한 것은 아님. Vercel 지도·관리자·뉴스·390px 실화면의 이전 검증은 20장 기록 참조.

### 21.3 남은 작업 및 자동 처리 경계

1. **바로 처리 가능한 작은 작업:** 오래된 2장 기능 상태와 4장 IA 표기의 현행화(본 커밋), 기능별 완료/부분/미구현 구분, 환경 버전과 Vercel 배포가 19장 초기 인계 시점과 다름을 명시. 과거 개발 이력은 보존.
2. **사용자 범위 승인 후 구현:** F19 정기 자동 수집(주기·쿼터·비용·저장 정책 결정), F20 발행 상태(공개 기준·기사 이력·기존 기사 호환·DB 변경), F21 영구 장애 모니터링(로그 민감정보·보존 기간·알림 방식). 해당 항목들은 서비스 동작/비용/DB 데이터가 바뀔 수 있으므로 구현 전 설계와 승인 필요.
3. **최종 품질·보안 점검:** 기존 화면에 노출된 외부 API 키 교체, 실제 Supabase 스키마 읽기 전용 재검증, 모바일/인증·API/기사 조회/통계 교차 검증, 배포 및 회귀 테스트 기록 정리. 키 값은 README/커밋에 절대 추가하지 않으며 교체는 별도 승인/사용자 계정 작업 전제.
4. **분리 유지:** `main` 병합은 사용자가 지정한 프로젝트 최종 종료 시점에만 수행. 별도 과제 내용은 README에 기록하지 않는다.

### 21.4 기능·DB·개발환경 변경 정의

- **기능정의서:** F16~F22의 옛 상태 표기 정정 및 메뉴 IA의 구현 위치 최신화. **운영 기능 자체 변경 없음**.
- **DB:** 새 테이블/열/인덱스/쿼리·데이터 쓰기 **없음**. 기존 기사·경로 스냅샷·Supabase Auth 유지.
- **개발환경:** Windows `traffic-api/.venv` 실제 Python **3.14.7**(기존 19.4의 3.10.10은 역사적 기준), Vercel `traffic_app_domain`에서 `kakao` Production 배포가 READY로 확인됐으며 대표 도메인은 `https://traffic-app-domain.vercel.app`. Vercel Python 실행 버전은 직접 확인 전 미확인. 프로그램 의존성 변경 없음.

## 22. F19 정기 수집·F20 발행 상태·F21 장애 모니터링 — 통합 구현 승인 설계 (2026-10-20)

> **상태: 설계 작성 / 동작 변경·DB 마이그레이션·스케줄 활성화 승인 대기.** 사용자가 세 기능 전체 구현 방향은 승인했지만 주기, 공개 정책, DB 변경, 알림 정책과 요금 관련 운영 결정은 아직 확정되지 않았다. 승인 전 기존 운영 동작과 데이터를 변경하지 않는다.

### 22.1 현행 구현과 확인 근거

- `app/main.py`에서 기존 공개 라우트, 관리자 Bearer 인증, 기사 초안 생성 및 명시 저장, `/api/admin/api-usage` 확인. 정기 수집 트리거 및 발행·보류 상태 변경 API는 없음.
- `app/news_database.py`는 `traffic_news_articles` + `traffic_route_snapshots`를 저장하며 기존 `generation_id` 중복 방지 유지. `app/api_usage.py` 통계는 현재 서버 프로세스 메모리이며 모든 Vercel 인스턴스 간 영구 집계가 아님.
- **Supabase 읽기 전용 실 DB 메타데이터 확인:** public.traffic_news_articles 컬럼은 `id, title, lead, body, scope_notice, analyzed_route_count, retrieved_at, created_at, generation_id`; public.traffic_route_snapshots 컬럼은 `id, article_id, start_place, end_place, distance_m, duration_seconds, total_road_count, congested_count, congested_distance_m, congestion_ratio, retrieved_at`. public.traffic_information은 기존 수집 테이블이며 `id, road_name, road_type, link_id, speed, travel_time, created_date, created_at, traffic_status, latitude, longitude, collected_at`를 보유. 메타데이터 조회만 수행했으며 기존 레코드·인덱스·RLS의 상세 검사는 후속 읽기 전용 확인이 필요.
- Vercel 배포 프로젝트 `traffic_app_domain`, Root Directory `traffic-api`, Production `kakao`. 기존 `vercel.json`은 Python 함수·정적 라우팅 선언만 있고 `crons` 없음. Windows Python 가상환경 3.14.7에서 최근 85개 unittest OK; Vercel 런타임 Python 버전 미확인.

### 22.2 F19 기능정의 — 자동 수집과 영구 기록

- **목적:** 사용자의 수동 조회와 분리하여 설정된 대표 경로의 당시 거리·시간·정체 수치를 주기적으로 수집. 현재 API 호출 30초 캐시는 유지하고, 수집된 자료는 *기사 승인/발행과 무관한 관측 기록*으로 구분.
- **제안 기본 범위:** 기존 3개 대표 경로를 **하루 1회, KST 09시경** 수집. 실행별 지정 경로의 Local 출발/도착 검색 및 Mobility 길찾기; 가능한 한 요청 과다·요금 위험을 낮추고 중복 실행 시 이중 저장 방지. 이 주기/시간은 **최종 승인 선택사항**이며 운영에서 임의 활성화하지 않음.
- **실행 구조:** Vercel Cron 또는 대체 관리형 스케줄 → 비공개 `GET /api/internal/collect`(제안) → `CRON_SECRET` 인증 확인, 시간 제한·중복 락/DB 유일 식별자 적용 → 정상 조회별 별도 저장. Cron 가용 빈도·시간대 해석·Vercel 프로젝트 요금제 한도는 활성화 전에 공식 현재 설정과 사용자 계정에서 확인.
- **저장 제안:** 신규 `traffic_collection_runs`(실행 ID UUID PK, scheduled_for timestamptz, started_at/finished_at, outcome, count_total/count_succeeded/count_failed, safe_error_code, unique dedupe key)와 `traffic_observations`(ID PK, run_id FK, origin/destination, 조회 시각, 거리/소요시간/정체 비율, source='kakao', unique(run_id,origin,destination)). 기존 `traffic_route_snapshots`는 기사에 연결된 과거 기록이므로 자동 수집 자료를 기존 기사에 가짜로 연결하지 않는다.
- **중요 제약:** 카카오 응답에서 확보하지 못한 지표를 생성하거나 과거 도로 선형을 복원하지 않는다. 서버리스 재시도·일부 경로 실패 시 성공 결과만 저장하고 실행 상태/오류 기록을 남긴다. 외부 API 요금·쿼터 증가 가능성 별도 확인.

### 22.3 F20 기능정의 — 기사 발행·보류와 공개 범위

- **목적:** 기존 관리자 생성→검토→저장 흐름을 유지하면서 '저장된 기사'와 '공개 승인된 기사'를 구분. 기존 `generation_id` 중복 저장 보호 유지.
- **데이터 보존 우선 제안:** 기존 기사/경로 테이블은 즉시 덮어쓰지 않고 신규 `traffic_article_publication`(article_id BIGINT UNIQUE FK, status CHECK draft/review/published/held, changed_at, changed_by 관리자 UID)과 `traffic_article_publication_events`(id PK, article_id FK, old_status, new_status, changed_at, changed_by, note)를 사용해 상태/감사 이력 구성. 실제 FK·기본키·권한·RLS는 읽기 전용 검증 후 정확한 SQL 마이그레이션 설계.
- **공개 정책 제안:** 기존 저장 기사들은 **기존처럼 계속 공개 조회**(상태 레코드 미존재를 legacy_public으로 간주); 새로 저장되는 기사는 기본 `review`로 비공개하고 관리자가 확인 후 `published`로 공개. 단, 새 기사 저장 시 기존 공개 목록에서 즉시 보이지 않게 되는 **사용자 경험 변경이므로 명시 승인 필수**.
- **API/화면 제안:** 관리자 전용 기사 상태 목록·변경 `GET /api/admin/articles`, `PATCH /api/admin/articles/{id}/publication`; 인증 `require_admin`, 화이트리스트 전이 검증, `news.html`의 공개 기사 목록·검색/상세는 공개 상태 필터. 서버 측 필터·총 페이지 수·기사 ID 직접 접근 제어도 일치해야 함. 보류 후 과거 기사 링크 처리 정책 확인 필요. 관리자 새 기사 저장·중복 저장 방지·경로 스냅샷 트랜잭션 보존.
- **안전 제한:** 기존 기사 일괄 비공개/삭제/발행 상태 임의 변경 없음. 편집 이력은 상태 변경 내역부터 시작하며 기사 본문 버전관리까지는 별도 확장으로 둔다.

### 22.4 F21 기능정의 — 지속 가능한 운영 오류 진단

- **목적:** F19-B 메모리 통계와 별도로 정기 수집 실패/외부 API 오류를 지속 기록해 관리자 작업실에서 원인 유형·최종 발생 시각을 볼 수 있게 한다.
- **저장 제안:** 신규 `traffic_operational_events`(id PK, event_time timestamptz, source, event_type, outcome, safe_error_code, http_status nullable, run_id nullable, request_id nullable, occurrence_count). 외부 키, 토큰, 사용자 입력의 원문, 개인정보, API 원본 응답은 저장 금지. 필수 최소 메타데이터만 기록.
- **화면/API:** 관리자 전용 `GET /api/admin/operations` 읽기 전용 진단(최근 실패, 유형별 집계, 수집 성공률). F19-B 기존 프로세스 메모리 대시보드 유지, 공식 Kakao 쿼터로 표현하지 않음.
- **알림 제안:** 초기에는 관리자 화면 경고 + 연속 실패 임계치 초과 시 **명시적 채널 설정 후** 외부 알림. 무승인 외부 이메일·메신저 발송 금지. 보존 기간은 30일(제안), DB 정리 실행도 별도 승인을 받은 뒤 활성화. 기존 기록을 지우지 않음.

### 22.5 DB 마이그레이션·개발환경·수용 검증 계획

- **DB:** 기존 Supabase 데이터를 보존하는 additive migration을 우선. 신규 테이블의 권한/접근 정책, FK, 인덱스/제약, 실패 시 롤백 절차와 과거 기사 호환성을 코드 구현 전에 확정. 신규 SQL 작성만으로 적용 간주 금지. DB 쓰기·백필·인증 정책 변경은 사용자 승인 후 단계적으로 처리.
- **개발환경:** `traffic-api`의 FastAPI + psycopg + 기존 Supabase Auth 보존. 신규 `CRON_SECRET` 생성/등록 필요 시 값은 문서/채팅에 기록 금지. Vercel Cron 구성은 무료 요금제의 지원/실행 한도와 UTC 설정 재확인 후 배포하고, 단순 코드 반영으로 자동 실행 활성화되지 않게 단계 분리.
- **구현 순서:** (A) 정확한 DDL/권한 읽기 전용 확인 및 마이그레이션/실패 테스트 설계 → (B) 승인된 별도 테이블과 테스트 → (C) F20 관리자·공개 상태 제어와 회귀 → (D) F21 운영 이력 기록·관리자 읽기 전용 진단 → (E) F19 수집 처리기·중복방지 및 수동 비운영 테스트 → (F) 스케줄/알림 활성화 및 운영 검증. 단계별 Windows 전체 unittest + 실제 Vercel 읽기 전용 점검 + GitHub `kakao` 커밋.
- **검수 조건:** 기존 기사 개수·원본/스냅샷 보존, 비관리자 401/403, 서명 없는 저장 차단, 신규 기사 출고 전 비공개, 상태 전이/직접 URL 차단, 예약 중복 실행 1회 처리, 일부 실패 복구, 키/개인정보 로그 누출 없음, 기존 F18/F19-A/F19-B 및 PC/390px 회귀.
- **범위 제한:** 사용자의 명시 최종 종료 이전 `main` 병합 금지. 별도 과제는 README에 기록하지 않는다. 모든 새 포커스 테두리/외곽선 추가 금지.

### 22.6 승인 필요한 세 가지 운영 결정 (기본 제안)

1. **F19 수집 주기:** 하루 1회 KST 오전 9시 / 기존 3개 대표 경로. 초기 배포에서 예약 실행은 일단 비활성화하고 수동·테스트 검증 후 활성화.
2. **F20 공개 정책:** 기존 기사는 그대로 공개, 새 기사부터 관리자 승인 전 비공개(`review`), 발행 시 공개. 기존 기사 원본 변경 금지.
3. **F21 알림·보존:** 관리자 화면에 오류 경고 먼저 구현, 외부 알림(메일·메신저)은 별도 채널 승인까지 비활성화. 향후 30일 보존 정책은 제안에 그치며 사용자 승인 전 삭제 작업 금지.

위 사항이 승인되면 세부 구현·테스트·`kakao` 커밋은 일괄 진행하되, 실제 DB 마이그레이션/운영 스케줄 활성화/새 요금 발생이나 외부 알림 연결은 해당 단계의 결과와 위험을 보고 필요한 승인을 다시 확인한다.


### 22.7 운영 정책 승인 및 안전한 1차 코드 반영 (2026-10-20)

- **사용자 승인:** F19 기존 대표 3개 경로 **매일 한국시간 오전 9시** 수집(검증 후 예약 활성화), F20 기존 기사는 공개 유지하고 **신규 기사만 승인 전 비공개**, F21 관리자 화면 경고 우선·외부 알림 보류. 실제 DB 마이그레이션·예약 가동 등 위험 단계는 별도 확인을 요청하도록 승인받음.
- **안전한 1차 구현:** `app/operation_policies.py` 신규 추가. KST 매일 09:00 예약 슬롯을 UTC로 환산하는 순수 함수, 기사 검토/발행/보류 상태 전이와 상태가 없는 기존 기사 공개 유지 판정, 임의 원문 오류·비밀값을 버리고 허용 목록 코드만 남기는 함수 구현. `tests/test_operation_policies.py`에 4개 단위 테스트 추가.
- **현재 비활성 상태:** 새 모듈은 운영 API 라우트, 기존 DB 저장/공개 검색, Vercel Cron, 운영 알림에 **연결하지 않음**. 따라서 새 기사 비공개 정책도 아직 실제 적용되지 않았음. 사용자 승인 범위라도 DB 마이그레이션 전 운영 저장/조회 동작을 부분 교체하면 기존 서비스가 깨지므로 연동은 보류.
- **검증:** 파일 생성과 GitHub kakao 커밋 확인; Windows 전체 자동 회귀는 추가된 테스트 4개 포함 **89개 예상이며 미실행**. 지난 85개 OK를 이번 변경 테스트 결과로 재사용하지 않음.
- **기능정의:** F19/F20/F21 정책 단위 코드 1차 착수(실행 기능 미완료). **DB:** 읽기 전용 스키마 확인만 수행하고 DDL/DML·기존 기사·인증 미변경. **개발환경:** Python 3.14.7 로컬 기록, Vercel Cron/환경변수·의존성 변경 없음. 포커스 외곽선·CSS·`main` 변경 없음.
- **다음 게이트:** 실제 신규 테이블·인덱스·정책을 적용할 정확한 SQL을 별도 작성·검수하고 **사용자에게 마이그레이션 실행 승인**을 받기 전에는 DB를 변경하지 않는다. 승인 이후 기능 연동/회귀 및 Vercel 예약 활성화는 별도 단계.


### 22.8 F19/F20/F21 신규 DB 구조 SQL 초안 (미적용)

- `traffic-api/sql/f19_f20_f21_migration_PROPOSAL.sql` 파일로 기존 테이블을 수정·삭제하지 않고 신규 5개 테이블을 추가하는 **검토용 SQL**을 `kakao`에 저장했다. 실행하지 않았고 실제 DB 테이블 생성 여부를 주장하지 않는다.
- 5개: `traffic_collection_runs`, `traffic_observations`, `traffic_article_publication`, `traffic_article_publication_events`, `traffic_operational_events`. 예정 실행 시각 UNIQUE 및 회차별 경로 UNIQUE, 기사 FK, 발행 상태 제한, 오류 기록 최소화 규칙, 신규 테이블의 RLS 활성화·anon/authenticated 접근 철회를 초안에 포함했다.
- 적용 전 검토 게이트: 실제 Supabase 역할 권한/기존 객체와의 이름 충돌, FK/인덱스/권한과 DB 접속 계정의 INSERT·SELECT 가능 여부, 런타임 코드 전환 원자성, 정상 복구·백업, 초기 신규 기사 비공개 여부를 검증해야 한다. 구 기사 상태 행은 생성하지 않으며 미존재 상태는 공개로 취급하는 설계.
- **승인 전 실행 금지:** SQL 파일은 설계 산출물일 뿐이며 `apply_migration`과 SQL 변경을 실행하지 않았다. Cron 설정·요금/키·기사/DB 데이터도 그대로다.


### 22.9 Windows 전체 89개 자동 테스트 통과 (2026-10-20)

- 사용자 제공 Windows PowerShell 실행 로그에서 `Ran 89 tests in 0.506s`, `OK` 확인. 실패 및 오류 0개. 기존 85개에 신규 `tests/test_operation_policies.py`의 4개 테스트가 추가되어 모두 `ok`.
- 신규 검증 항목: KST 09:00 → UTC 예약 시각 환산, 기사 상태 전환 제한, 기존 기사 공개·신규 검토 상태 비공개 판정, 임의 오류 원문 차단 정책.
- `StarletteDeprecationWarning`과 테스트 중 표시된 DB/카카오 오류는 비치명적 경고 및 의도된 실패 대응 모의 시험이며 테스트 자체는 성공.
- **범위:** 운영 정책 순수 함수·정적 회귀 테스트 합격. 아직 실제 Supabase 신규 테이블 생성, F19 예약 호출, F20 발행 API 연결, F21 오류 기록 저장은 수행·검증하지 않음. 실 DB 데이터, 관리자 인증, `main` 변경 없음.


### 22.10 마이그레이션 전 실 DB 제약·기존 테이블 조회 (2026-10-20)

- Supabase `information_schema.table_constraints`를 **SELECT만 수행**하여 기존 `traffic_information.id`, `traffic_news_articles.id`, `traffic_route_snapshots.id`의 PK 확인. `traffic_route_snapshots.article_id`의 실제 FK 및 `traffic_news_articles.generation_id` UNIQUE 확인. 기존 NOT NULL/CHECK 제약 다수 유지.
- 제안된 신규 다섯 테이블 이름(`traffic_collection_runs`, `traffic_observations`, `traffic_article_publication`, `traffic_article_publication_events`, `traffic_operational_events`)의 현재 public 스키마 조회 결과는 **0건**. SQL 초안은 **실행하지 않음**.
- 기존 기사·경로의 PK/FK와 호환되는 추가 테이블 설계 방향은 가능하나, 기존 데이터 건수/권한·새 테이블 생성 후 쓰기 권한 및 현재 마이그레이션 SQL의 실제 실행 성공은 **아직 검증되지 않음**. 다음 단계는 사용자에게 SQL 실행 승인을 받기 전 권한/롤백 점검.
- 본 확인은 기능 실행이나 DB 구조·데이터·인증·`main` 변경 없이 읽기 전용 조회 및 README 기록만 수행.


### 22.11 신규 테이블 5개 마이그레이션 적용·보존 검증 (2026-10-20)

- 사용자 명시 승인 후 `traffic-api/sql/f19_f20_f21_migration_PROPOSAL.sql`에 기록된 신규 테이블 5개 DDL(기존 BEGIN/COMMIT은 마이그레이션 실행기의 트랜잭션 관리에 맡기고 제거)을 Supabase `apply_migration`으로 실행. 마이그레이션명 `add_f19_f20_f21_operations_tables`; 결과 **success=true**.
- 사전 실 DB 확인: 실행 역할 `postgres`, 스키마 CREATE/기존 기사 REFERENCES 권한 있음, 신규 대상 테이블 0개. 기존 레코드 건수: `traffic_information=30538`, `traffic_news_articles=8`, `traffic_route_snapshots=24`.
- 적용 후 읽기 전용 확인: 신규 `traffic_collection_runs`, `traffic_observations`, `traffic_article_publication`, `traffic_article_publication_events`, `traffic_operational_events` **5개 모두 존재하고 각각 0행**. 기존 세 테이블 건수도 **30538/8/24로 일치**. 기사 원문·관리자 Auth 변경 SQL 없음.
- 보안 검증: 신규 다섯 테이블의 RLS `true`, `anon` 및 `authenticated`에 직접 SELECT 권한 `false`. 신규 테이블 PK/FK/CHECK, 수집 예정 시각 및 수집 경로 중복 방지 UNIQUE 존재 확인.
- **한계 및 후속:** 레코드 건수 일치는 원문 전체 해시 비교가 아니며, 신규 테이블의 실제 서버 DB 연결 계정 INSERT/UPDATE/SELECT와 기사 신규 비공개·발행 상태 API는 아직 검증하지 않았다. F19 Cron/카카오 자동 호출 및 F21 외부 알림 **비활성**. 기존 앱 기능/환경변수, `main` 변경 없음. 이 단계는 DB 스키마 추가 완료이며 F19/F20/F21 기능 전체 구현 완료를 뜻하지 않는다.

## 23. D03 도시 교통 뉴스룸 디자인 시안 승인 및 구현 설계 (2026-10-20)

- **사용자 승인:** 홈·지도·뉴스·관리자 4분할 시안의 '도시 교통 대시보드 + 교통 뉴스룸' 스타일을 실제 사이트에 적용. 네이비 브랜드/교통 상황색 유지, 시각 계층과 카드·배경·버튼 미감 개선. 별도 ZIP 업로드 불필요, GitHub `kakao` 브랜치에서 직접 적용.
- **구현 범위:** 기존 `static/d02-journalism.css` 및 4개 HTML의 핵심 기능과 ID/JS는 유지하고, 별도 `static/d03-urban-traffic.css` 디자인 레이어를 각 페이지의 기존 디자인 CSS 뒤에 로드. 공통 히어로 영역에 도시 도로·차선/빛 흐름을 연상시키는 색/패턴을 구현하며 외부 서비스 종속 이미지·라이선스 미확인 사진을 임의 연결하지 않음. 사용자 선택에 따라 향후 적법한 이미지 리소스를 추가할 수 있도록 배경 교체 가능한 레이어로 설계.
- **페이지별:** 홈 검색 및 3경로 결과·브리핑의 카드 계층, 지도 검색·관심 경로 패널/지도 캔버스의 분리와 강조, 뉴스 검색·기사·차트·내보내기 등 뉴스룸 정보 구조, 관리자 로그인·생성→검토→저장·API 현황 콘솔 배치 강조. 미구현 자동 수집/발행 상태/영구 알림의 가상 작동 UI를 추가하지 않음.
- **기능정의:** D03은 시각 개선만 수행; 실제 Kakao REST/지도, F18 수동 불러오기, F16/F17/F22 검색·차트·CSV, F19-A/B 메모리 캐시·관리자 현황, F13~15 인증·저장은 무변경. 포커스에 테두리/outline/box-shadow 신규 추가 **절대 금지**, 기존 콘텐츠 값/색 범례·접근성 라벨 보존.
- **DB:** Supabase 기존/신규 F19/F20/F21 테이블의 스키마와 데이터 및 관리자 Auth 변경 없음. **개발환경:** 기존 FastAPI+Vanilla JS·Vercel 정적 파일 라우팅 활용, 외부 CSS/JS CDN 의존성 증가 없음, Python 3.14.7 로컬·Vercel 설정 무변경.
- **검증:** 4페이지 D03 CSS 링크/정적 제공 및 필수 ID 보존/포커스 외곽선 미도입 회귀 테스트. 기존 Windows 89개는 D03 적용 *이전* 통과 결과로만 인정. 변경 후 전체 테스트와 실제 PC/390px Chrome 스크린샷 검증 별도 요청. `main` 미변경.


### 23.1 D03 승인 디자인 1차 코드 적용 및 검증 상태 (2026-10-20)

- 사용자 승인된 4화면 도시 교통 뉴스룸 디자인을 `static/d03-urban-traffic.css` 별도 레이어로 구현하고 `index.html`, `map.html`, `news.html`, `admin.html`에 기존 D02 CSS **뒤 순서**로 연결. 외부 이미지/CDN이나 가상 도로 데이터는 추가하지 않았음.
- 네이비 히어로·차로와 빛 흐름 연상 패턴, 밝은 검색·기사·관리자 카드, 뉴스 검색 패널, 카카오 지도 외곽 프레임, 관심 경로 카드, 운영 통계 영역 강조 및 850px/600px 반응형 규칙 적용. 기존 JS/폼/지도/API/기사·CSV·저장 동작, 기존 색 범례/접근권한은 그대로. 포커스 outline/border/box-shadow 신규 규칙 없음.
- `tests/test_navigation.py`에 `test_d03_urban_traffic_theme_on_all_pages` 1개 신규 회귀 테스트 추가: 새 CSS 정적 응답, 핵심 화면 셀렉터, CSS 적용 순서, 새 포커스 스타일 부재 검사. 수정 후 사용자 Windows 전체 테스트 수는 **90개 예상**이며 미실행. 이전 89개 OK는 적용 이전 근거로만 유지.
- **DB:** Supabase F19/F20/F21 신규 테이블 및 기존 기사·경로·인증 변경 없음. **개발환경:** Python·의존성·Vercel 설정·환경변수 변경 없음. `main` 미변경. 실제 Desktop/390px 디자인 및 카카오맵·관리자 화면 동작은 사용자 브라우저 검증 대기.


### 23.2 D03 시안 대비 실제 구현 차이 및 구조 재설계 (2026-10-20)

- **사용자 피드백:** D03 첫 배포 화면의 분위기가 승인 시안과 너무 다름. 현행 D03은 기존 레이아웃 위에 그라데이션/카드 테두리만 추가했으며 승인 시안의 실사 도심 교통 히어로·명확한 지도 2단 패널·기사 썸네일 뉴스룸·관리자 콘솔 정보 밀도를 재현하지 못함. **첫 배포를 디자인 검수 완료로 처리하지 않는다.**
- **재설계 목표:** (A) 홈: 야간 교통 도로 실사 사진을 사용한 큰 히어로, 떠 있는 검색 카드와 실제 API 결과 요약. (B) 지도: 데스크톱 검색·즐겨찾기 좌측 패널과 확대 지도 우측 배치, 390px 세로형. (C) 뉴스: 기존 저장 기사 목록을 읽기 좋은 카드형으로 재배치하며 **기사별 실사진은 실제 제공된 자료가 없으므로 임의 뉴스 증거 사진을 생성하지 않음**; 중립적인 그래픽/사진 배경은 장식임을 구분. (D) 관리자: 기사 생성→검토→저장 작업과 API 현황을 시각적으로 위계화; 미완성 F19/F20/F21 데이터를 작동 중으로 표기하지 않음.
- **사진 조달 기준:** 적법하게 재사용 가능한 라이선스 및 안정적인 파일 제공 경로를 먼저 확인하고 크기/모바일 최적화. 키·개인 정보 노출 금지, 가상 수치 금지, 이미지 로딩 실패 시 배경색·텍스트 가독성 유지. 사진은 장식용이며 실시간 카카오 교통정보 또는 사고 증거로 표현하지 않음.
- **기능·DB·개발환경:** 기존 FastAPI API, Kakao 지도, 기사 검색/CSV, F18 관심 경로, 관리자 인증 및 이미 생성한 F19/F20/F21 DB 테이블을 보존. 실제 DB SQL·스키마/데이터 변경 없음. 기존 디자인 CSS만으로 시안 재현이 불가능하므로 HTML 구조/배치 조정은 허용하되 필수 ID/JS 이벤트/모바일/접근성을 회귀 테스트. 포커스 테두리 추가 금지, `main` 변경 금지.
- **수용 기준:** 네 화면을 실제 1280px 데스크톱과 390px 모바일에서 촬영해 사용자에게 승인 시안과 비교 제공, 기존 기능 자동 테스트 전부 통과. 스크린샷 검수 전에는 완료로 발표하지 않는다.


### 23.3 M03 페이지 단위 상단 메뉴 통합 설계 (2026-10-20)

- **사용자 요청·승인:** 상단 5개 기능별 교차 메뉴(교통 현황/분석·통계/교통 뉴스/서비스 안내/관리자)를 실제 페이지별 4개 메뉴로 통합. 이미 구현한 링크를 보존하고 중복 항목은 합친다. 아직 없는 기능도 미래 배치 위치를 확정하지만 잘못된 URL/가짜 자동 동작은 추가하지 않는다.
- **홈 · 경로 조회** (`/`): `경로 검색`(현재 /), `대표 경로 브리핑`(현재 /의 3경로 비교·종합 조회), `이용 안내·FAQ`(향후 계획; 실제 링크 없음). 홈 즐겨찾기도 기존 동작 그대로 유지.
- **경로 지도** (`/map`): `지도에서 경로 확인`(현재 /map), `관심 경로`(현재 /map#favoriteRoutes), `기사에서 지도 연결`(기존 /news의 개별 기사 링크로 사용; 공통 메뉴에서는 중복 링크를 만들지 않음).
- **교통 뉴스·분석** (`/news`): `기사 검색·아카이브`(현재 /news#historySection), `교통 비교 현황`(현재 /news#trafficDashboard), `시점별 교통 변화`(현재 /news#trafficTrends), `CSV 다운로드`(현재 /news#trafficExport), `기사 공유·읽기 모드`(계획), `교통 데이터 범위·출처`(실제 분석 안내가 있는 /news#trafficDashboard 및 추후 확장). 유사 기사 검색·기간 필터는 한 메뉴로 통합.
- **관리자·운영** (`/admin`): `기사 생성·검토·저장`(현재 /admin; 인증 유지), `API 사용 현황`(현재 /admin#apiUsageSection), `발행·보류 관리`(F20 연동 후), `정기 수집 상태`(F19 연동 후), `장애 기록·경고`(F21 연동 후), `운영 설정·공지`(향후 계획). 미구현 항목은 회색 '준비 중'이며 누를 수 없음.
- **UI·접근성:** 4개 1차 드롭다운/모바일 아코디언 메뉴로 제한. 반복적인 '뉴스'와 '분석' 상위 탭 제거. 각 상위 탭을 클릭하면 해당 페이지 하위 링크만 표시하되 현재 메뉴의 버튼·Escape·모바일 메뉴 토글 기능 유지. 850px 이하 반응형 및 키보드 내비게이션 보존. 신규 포커스 outline/border/box-shadow 금지.
- **기능·DB·개발환경 영향:** `static/navigation.js` 및 테스트, README만 변경. 실제 페이지/기능 이동, 기존 API/JS/인증/DB/배포 환경변수 변경 없음. F19/F20/F21 미구현 부분을 완성으로 표시하지 않음. `main` 미변경.
- **검증:** 기존 네 페이지에서 공통 메뉴 렌더·링크 실제 anchor ID 확인, 메뉴에 '준비 중' 표기, 모바일/PC 회귀, 기존 Windows 자동 테스트(변경 전 89개+ D03 1개=90개 예상)에 신규 메뉴 단위 테스트 추가 후 실행 필요.


### 23.4 M03 페이지 기준 4개 메뉴 적용 결과 (2026-10-20)

- **반영:** 공통 상단 내비게이션을 **경로 조회(/), 경로 지도(/map), 교통 뉴스·분석(/news), 관리자·운영(/admin)** 네 그룹으로 축소. 기존 기능별 5개 그룹(교통 현황/분석·통계/교통 뉴스/서비스 안내/관리자)의 중복 메뉴를 페이지 기반으로 통합.
- 하위 링크: 홈 경로 검색·대표 경로 브리핑 `/#overviewSection`; 지도 `/map`·관심 경로 `/map#favoriteRoutes`; 뉴스 검색·아카이브 `/news#historySection`, 교통 비교 `/news#trafficDashboard`, 교통 변화 `/news#trafficTrends`, CSV `/news#trafficExport`; 관리자 기사 작업실 `/admin`, API 사용 현황 `/admin#apiUsageSection`. 홈에 실제 `id=overviewSection` 추가.
- 추후 항목인 이용 안내·FAQ, 기사 공유, 기사 발행·보류(F20), 정기 수집 상태(F19), 장애 기록·경고(F21), 운영 설정·공지는 **준비 중** 표시 유지. 현재 존재하지 않는 페이지/가짜 URL은 추가하지 않음. F19/F20/F21 활성화 후 해당 페이지의 영역 ID로 점진적 전환.
- **테스트:** `tests/test_navigation.py`에 `test_m03_route_based_menu_links` 추가. 그룹 개수·기존 중복 그룹 제거·실제 HTML 앵커·미구현 메뉴의 planned 표시 검사. 기존 90개 예상(D03 포함)에서 **91개 예상, Windows 실행 결과 미확인**. 이전 89개 OK는 변경 전 결과.
- **영향:** `static/navigation.js`, `static/index.html`, 회귀 테스트와 README만 변경. 기존 공통 메뉴 반응형/드롭다운/ESC 동작, 검색·카카오맵·뉴스·관리자 API는 유지. DB·인증·환경변수·CSS 포커스 테두리·`main` 변경 없음. 실제 데스크톱/390px 사용성 검증 대기.


### 23.5 D03 시안 재현 2차 코드 적용 (2026-10-20)

- **시안 불일치 수정 2차 적용:** 기존 추상 패턴 중심 히어로를 실제 서울 야간 도로 사진 배경으로 교체하고, 홈 대형 히어로 + 겹쳐 올라오는 검색 카드 + 2열 정보 카드, 지도 좌측 경로 입력/관심 경로와 우측 넓은 카카오 지도, 뉴스 사진 히어로 + 기사 2열 카드, 관리자 사진 히어로 및 작업/통계 카드의 구조를 `static/d03-urban-traffic.css`에 강화했다. 850px 이하에는 세로형 구성으로 되돌리는 CSS를 추가.
- **사진 저작권:** Wikimedia Commons `View of Night Traffic from Above in Seoul-1.jpg`, 촬영자 **Immanuelle**, **CC BY 4.0**. 출처: https://commons.wikimedia.org/wiki/File:View_of_Night_Traffic_from_Above_in_Seoul-1.jpg / 라이선스: https://creativecommons.org/licenses/by/4.0/ . 배경에 어두운 오버레이 및 화면비 자르기 적용. 네 HTML 페이지 하단에 촬영자·출처·라이선스·변경 사실과 **실시간 교통정보가 아닌 장식용 과거 사진**임을 명시했다. 외부 Wikimedia 이미지가 로드되지 않더라도 CSS 그라데이션을 제공.
- `map.html`은 `main.map-content`와 `.map-canvas-frame`이 형제 요소라 단순 음수 margin으로 2단이 완성되지 않음. 최종 CSS에서는 `body:has(>.map-content)` 기반 실제 두 열 Grid로 보정하고 모바일 `display:block`으로 복귀하도록 처리. 카카오맵 JS와 경로 API를 변경하지 않았다.
- **검증 코드:** `tests/test_navigation.py`에 실사진 URL·2열 배치·850px 모바일 복귀·4페이지 CC BY 4.0 출처 표시 확인 테스트 1개 추가. 기존 91개 예상에서 **총 92개 예상이며 Windows 실행 전**. 이 수치는 자동 실행 성공 주장이 아니다. 실제 Chrome 데스크톱/390px 카드 배치와 지도 타일·즐겨찾기·관리자 UI 확인은 별도 대기.
- **데이터·기능·환경:** 실제 교통 수치/기사 본문 가공 없음, F19 정기 수집·F20 발행 상태·F21 영구 진단 활성화 없음. 기존 Supabase 데이터·관리자 인증·환경변수·Vercel 설정 및 `main` 무변경. 신규 포커스 테두리 없음.


### 23.6 D03 사용성 피드백 대응 계획 (2026-10-20)

- 사용자 제공 데스크톱 스크린샷 8개 검토: ① 히어로 차량 부족·부자연스러운 광선 ② 지도 관심 경로 라벨·버튼 줄바꿈 난잡 ③ 뉴스 대체로 양호 ④ 관리자 **로그인 전** 좌측 히어로가 흰색 배경에 흰 글자로 표시되는 대비 오류 ⑤ 카드·표 시각적 위계 강화 요청 ⑥ 관리자 로그인 후 작업실 대체로 양호 ⑦ 모바일 390px 사용자 검증 정상.
- **우선 구현:** 차량 중심 교통사진 교체(저작권·출처·수정 표기 포함), 관리자 로그인의 CSS 특이성 충돌을 해결해 어두운 사진 배경 및 텍스트 가독성을 명시적으로 보장, 지도 즐겨찾기 목록의 grid/버튼 줄바꿈·단어 단위 개행·간격 수정, 공통 표·정보 카드·안내문 가독성 보강. 사진은 장식용 과거 사진임을 유지. 기존 기사 목록/로그인 후 작업실과 390px 정상 레이아웃은 광범위 재구성하지 않음.
- **제약:** 앱 API/JS 이벤트·F18 저장 로직/관리자 인증/Supabase DB/F19~F21 운영 상태·main 브랜치 불변. 포커스 테두리·아웃라인·그림자는 신규 추가하지 않음. 기존 ID 유지. 코드 회귀 테스트를 추가하고 Windows 전체 테스트 결과 및 실제 배포 시각 검증을 분리 기록.


### 23.7 D03 사용자 캡처 피드백 패치 적용 결과 (2026-10-20)

- **사용자 요청에 따른 실 코드 수정 및 커밋:** GitHub `kakao` 브랜치의 `static/d03-urban-traffic.css`, 네 페이지 HTML, `tests/test_navigation.py` 수정. 다른 브랜치는 건드리지 않음.
- 배경 사진을 `Gangnam traffic.jpg`로 교체(2022년 서울 강남 차량 교통 실사, 저작자 **kallerna**, 출처 Wikimedia Commons https://commons.wikimedia.org/wiki/File:Gangnam_traffic.jpg , **CC BY-SA 4.0** https://creativecommons.org/licenses/by-sa/4.0/). CSS 어두운 오버레이와 배경 위치 조정, 눈에 띄던 그래픽 광선 장식 제거. 사진을 자르거나 어두운 오버레이 적용했음을 4페이지 footer에 기재하며 실시간 교통 자료와 구분.
- 관리자 로그인 좌측 사진 카드에 대해 `.login-container .admin-login-layout > .admin-hero` 등 **정확히 제한된 선택자**로 dark `background-color`, `background-image`, `color` 우선순위를 높여 공통 '흰색 section' 규칙과의 충돌 해결. 로그인 이후 관리자 작업실에는 동일 규칙을 적용하지 않음.
- 지도 관심 경로 항목을 1열 grid(경로 라벨 위/불러오기·삭제 버튼 아래 2열)로 배치, 한국어 줄바꿈·안내문 line-height·단추 폭 조절. 기존 localStorage 저장/불러오기/삭제 JS 무변경.
- 네 화면 공통 테이블 헤더 대비·교대행 배경·hover·설명문 행간 조절. 기사 데이터/CSV/사용 현황 실제 수치 무변경. 뉴스 및 관리자 로그인 후 레이아웃 대규모 개편 없음. 모바일 390px 사용자가 이전 버전에서 확인한 정상 상태는 보존을 목표로 했으나 **새 변경에 대해 사용자 재검증 필요**.
- `test_d03_photo_led_layout_and_attribution`을 새 이미지 경로/라이선스로 정정하고 `test_d03_admin_login_contrast_and_map_favorite_spacing` 새 테스트 1개 추가. 기존 예상 92개에서 **93개 예상**, Windows `python -m unittest discover ...` 전체 테스트 실실행 결과는 아직 없음. 소스/배포 검증과 브라우저 육안 검증을 혼동하지 않음. 신규 포커스 테두리 없음. DB·관리자 인증·환경변수·`main` 무변경.


### 23.8 D03 지도 패널·히어로 제목 가독성 소폭 보정 (2026-10-20)

- 사용자 제공 /map 관심 경로 패널 및 홈·관리자 로그인 화면 캡처를 기준으로 **배치/타이포그래피만 조정**. 사용자가 이미 제공한 헤딩의 `<br>` 두 줄 구분은 그대로 보존.
- 지도: 좁게 압축된 데스크톱 왼쪽 패널의 Grid 열 폭과 외곽 여백 조정, 관심 경로 카드 내부의 버튼 및 설명문 폭·줄바꿈·행 간격을 보강. 기존 카카오맵·즐겨찾기 로직/ID 변경 없음. 850px 이하 모바일 스택 규칙 유지.
- 홈: `.home-hero h1`을 데스크톱에서 한 줄당 제목이 보이도록 적정 폰트 크기로 축소, 관리자: 로그인 소개 `.admin-hero h1`을 두 줄 제목으로 읽히도록 축소. 390px에서는 자연스러운 줄바꿈 허용(데스크톱에서의 두 줄 요구 사항에 한함). 기존 본문/뉴스/로그인 후 작업실 구성은 변경하지 않음.
- 변경 대상: `static/d03-urban-traffic.css`, 테스트 및 README. 포커스 테두리 추가 없음, DB/API/관리자 인증/환경 변수/`main` 불변. 자동 회귀 검사 추가 후 Windows 전체 테스트는 사용자가 별도로 실행해 검증.


### 23.9 D03 캡처 기반 보정 적용 결과 (2026-10-20)

- 사용자 제공 최신 4개 캡처 기준으로 지도 좌측 패널이 좁고 관심 경로 설명/버튼 줄바꿈이 과도하며, 홈·관리자 로그인 헤딩이 의도한 `<br>` 외에 추가로 자동 줄바꿈되는 문제를 확인.
- **수정:** `static/d03-urban-traffic.css`에 1101px 이상 지도 Grid 좌측 열 `minmax(410px,460px)`, 851~1100px `minmax(340px,37%)`와 좌우 여백 보정, 관심 경로 내부 padding·설명 font·버튼 2열 grid·상태 메시지 line-height 조정. 850px 이하에는 기존 세로 흐름을 유지.
- **제목:** 홈 `h1` 데스크톱 최대 40px, 관리자 로그인 왼쪽 소개 `h1` 최대 33px로 축소하고 각각의 기존 `<br>` 두 줄 구분 유지. 모바일에서는 자연스러운 줄바꿈 허용. 관리자 로그인 이후 작업실과 뉴스는 수정하지 않음.
- **검증:** `tests/test_navigation.py`에 `test_d03_two_line_hero_and_wider_map_sidebar` 회귀 테스트 1개 추가. 직전 예상 93개에서 **94개 예상**; 사용자 Windows 전체 테스트 및 데스크톱 실제 줄바꿈 검증은 아직 수행되지 않음. 포커스 테두리 미도입, 카카오 API/즐겨찾기 JS, DB, 인증 및 `main` 브랜치 무변경.


### 23.10 지도 HTML 종료 태그 회귀 수정 (2026-10-20)

- 사용자 Windows `python -m unittest discover -s tests -p "test_*.py" -v` 실측: **94개 실행, 1개 실패**(`test_kakao_map.KakaoMapTests.test_map_html_tags_close_correctly`). 실패 원인은 map.html 마지막 인라인 `</script>` 뒤에 D03 사진 출처 `<footer>`가 있어 테스트가 요구하는 파일 말미 `</script>\n</body>\n</html>`와 불일치한 것. 다른 93개 테스트는 `ok`. 테스트용 모의 DB 예외 로그 및 StarletteDeprecationWarning은 별도 실패 아님.
- 해결: `static/map.html` 내 사진 출처 `<footer class="d03-photo-credit">`를 마지막 인라인 JS `<script>` **앞**으로 이동(출처·라이선스 표시는 유지), 문서 종료를 `</script>\n</body>\n</html>`로 복원. 기존 지도 JS/API/마커, F18 저장 경로, Admin/DB 변경 없음.
- GitHub 재조회로 footer 1개·스크립트 앞 배치·기대 종료 문자열 일치를 확인함. **수정 후 Windows 94개 테스트 재실행 결과는 아직 제출되지 않음**. `main` 미변경.


### 23.11 F20 기사 발행 상태 제어 1차 연동 (2026-10-20)

- 직전 사용자 Windows 자동 테스트 결과: **94개 실행, 94개 모두 OK**, 의도적인 mock DB 오류 로그 및 StarletteDeprecationWarning은 실패 아님. 본 변경 이전 결과이므로 F20 테스트 통과로 과장하지 않음.
- **F20 FastAPI/DB 기능 연결:** `app/news_database.py` 기사 저장 트랜잭션 내 신규 기사에 `traffic_article_publication.status='review'`와 `traffic_article_publication_events` 생성 감사 이벤트를 동시 INSERT. 동일 `generation_id` 재저장 시 기존 id를 반환하고 기사·경로·상태 중복 생성 방지. 관리자 UID를 `changed_by`에 사용하며 CLI 기존 호출은 `system`으로 처리. 삽입 어느 부분이라도 실패하면 전체 트랜잭션 롤백.
- **공개 자료 보호:** `/api/news/history`, `/api/news/search`, `/api/news/history/{id}`에서 기사별 공개 상태를 DB 서브쿼리로 확인. 명시된 `review`/`held` 기사는 공개 제외하고 기존 기사처럼 상태 레코드가 없는 경우 공개 유지. 기사 건수·검색 결과 모두 같은 규칙. `app/traffic_export.py` F17 조회 시점, F22 저장 경로 선택/CSV 경로 스냅샷도 비공개 기사에 속한 자료는 제외해 우회 노출 방지.
- **관리자 보호 API:** `GET /api/admin/news/publications` 최근 최대 50건 상태 목록, `PATCH /api/admin/news/publications/{article_id}`에 `{status:'review'|'published'|'held'}`로 변환. 둘 다 `Depends(require_admin)`을 강제. 상태 변경은 기존 상태 확인/행 잠금/허용 전이 검사/변경 및 감사 이력을 하나의 DB 트랜잭션에서 수행. 미존재 ID 404, 잘못된 상태 422, 허용되지 않는 전이 409. 기존 공개 기사는 상태 레코드가 없더라도 'published'로 취급.
- **관리자 화면:** 저장 후 공개 링크를 노출하지 않고 검토 중(비공개) 안내; 운영 작업실에 기사 발행 관리 섹션과 명시적 상태 변경 확인창·수동 새로고침을 추가. 로그인/저장/카카오 호출/기존 API 사용 현황과 F19/F21 운영 설정은 유지. 사용자의 포커스 테두리 금지 원칙과 390px 반응형을 고려한 CSS만 추가.
- **회귀 테스트:** `tests/test_publication.py` 신규 **7개 테스트**(익명 관리 API 접근 차단, 관리자 목록 및 상태 변경, 잘못된 상태, 공개 기사 쿼리, 기사+상태 동일 트랜잭션, 공개 CSV·추세 우회 차단, 관리자 UI) 추가. 기존 사용자 검증 94개 + 신규 7개 = **101개 예상**. 개발 도구에서 Windows 실제 101개 테스트는 실행하지 않았으므로 사용자 실행 및 피드백 대기. 적용 후 실제 Supabase 테스트 저장/발행·보류와 공개 뉴스 링크 수동 검증이 별도 필요.
- **데이터·운영 제약:** 기존 기사 상태 일괄 수정·백필 없음, 기존 Supabase 레코드 삭제/변경 SQL 없음, Auth 설정/비밀 키 무변경, F19 스케줄러/ F21 외부 알림 계속 OFF, `main` 미변경.

## 24. 최신 README·소스·상단 메뉴 3중 감사 및 F21 연결 (2026-10-20)

### 24.1 사용자 실측 검증 및 기능 ID 완료율 재점검
- 최신 사용자 Windows 전체 테스트: Ran 101 tests in 0.644s / OK, 실패 0. 기존 F20 신규 7개 테스트 포함. 이후 F21 변경에 대한 재실행 결과는 아직 없음.
- 기존 README 21장 기준 F01~F18, F22~F23 등 20/23개 완료(약 87%). F19/F20/F21 부분 구현. 새 F20 코드의 실제 DB 저장·발행 공개·보류 상태 수동 검증 전이라 완료율을 인위적으로 올리지 않고 20/23을 유지. 코드 수준 구현률과 운영 검증 완료율을 구별한다.

### 24.2 실제 구현 파일·상단 메뉴 불일치 점검
- 확인 파일: README §21~23, app/main.py, app/news_database.py, app/traffic_export.py, app/operation_policies.py, app/api_usage.py, static/navigation.js, static/admin.html 및 vercel.json. 페이지 경로 /, /map, /news, /admin 유지.
- F20 기사 발행·보류는 보호 API 및 관리자 #publicationSection이 구현됐는데도 준비 중이던 표시 오류를 고쳐 /admin#publicationSection로 연결했다.
- F21 장애 기록·경고는 기존에는 메모리 통계뿐이었으나 신규 안전 오류 이력 UI #operationsSection을 구현하여 /admin#operationsSection로 실제 링크 연결했다.
- 미완료로 유지: 정기 수집 상태(F19), 홈 FAQ, 뉴스 공유·읽기 모드, 운영 설정·공지. 구현된 페이지가 없으므로 준비 중 표시 유지.

### 24.3 F21 영구 운영 오류 기록 1차 연동
- app/operational_events.py가 승인된 traffic_operational_events 테이블에 허용된 source/event_type/safe_error_code/http_status만 기록. URL·입력값·API 키·원문 예외·응답 전문 기록 금지. DB 기록 실패가 원래 카카오 호출 오류를 감추지 않게 처리.
- app/kakao_api.py에서 외부 HTTP 시간 초과·오류·네트워크 및 JSON/응답 형식 실패에 안전 코드로 기록하며, 기존 F19-B 인메모리 카운터 유지.
- 관리자 전용 GET /api/admin/operations와 수동 조회 UI 구현. 외부 이메일/메신저 알림·자동 기록 삭제는 구현하지 않음.
- tests/test_operational_events.py 안전 정보 저장, 관리자 인증 및 UI 등 테스트 5개 추가. 기존 실측 101개 + 5개 = 총 106개 예상, 변경 후 Windows 재시험 미확인.

### 24.4 운영 경계
- 기존 DB 테이블·기사 데이터·관리자 인증, 환경변수 및 main 브랜치 변경 없음. F19 예약 실행은 OFF. F20 실 DB 발행·보류 및 F21 실제 오류 저장은 아직 수동 실서비스 검증 대기.
- 다음은 F19 승인된 3개 경로 정기 수집의 비활성 처리기·중복 방지 테스트, 실제 Cron 켜기는 별도 승인 필요.

## 25. F19 비활성 정기 수집 처리기·메뉴 현황 재분류 (2026-10-20)

### 25.1 실제 구현과 4개 페이지 메뉴 대조
- F19: app/collection_runs.py의 별도 호출형 수집 처리기, 정기 슬롯(매일 KST 09:00), DB INSERT 중복 예약 보호, 수집 결과의 검증·저장 및 성공/부분성공/실패 건수 기록. 실제 Cron/엔드포인트 호출/비밀키 스케줄은 만들지 않았으므로 자동으로 Kakao API를 호출하지 않는다.
- 관리자 인증 필수 GET /api/admin/collection-runs로 기존 수집 이력만 읽는다. static/admin.html #collectionRunsSection에 자동 실행 비활성 안내와 수동 조회 버튼을 추가했다.
- 상단 메뉴 '정기 수집 상태'를 실제 존재하는 /admin#collectionRunsSection으로 연결. 이는 수집 자동화 완료를 의미하지 않으며 사용자 화면에서 OFF 명시. F20 발행/보류와 F21 장애 기록도 이미 구현된 관리자 섹션으로 링크 연결. FAQ, 공유·읽기 모드, 설정·공지는 '준비 중' 유지.

### 25.2 안전·기능·개발환경
- F19 실제 3개 경로 호출은 collect_daily_routes(day) 명시적 호출에서만 수행됨. 자동 호출 이벤트, Vercel Cron, 구독/비용 관련 설정을 추가하지 않았다.
- 운영 로그는 허용된 코드만 저장하고 출발지·목적지, API 키, HTTP URL과 응답 본문을 남기지 않음. DB 환경변수가 없는 로컬 환경은 F21 장애 기록만 건너뛰며 교통 요청의 원래 예외와 상태는 유지.
- 기존 기사·경로/인증 DB 데이터, 신규 5개 테이블 스키마, Supabase Auth, Python/배포 환경변수와 main 브랜치 불변.

### 25.3 회귀 테스트와 실제 검증 제한
- tests/test_collection_runs.py 4개 추가: 관리자 접근 제한과 읽기만 하는 조회, 중복 슬롯 차단, 09:00 KST 변환, 수집 비활성 UI.
- 총 자동 테스트 개수: 이전 사용자 실측 101개 + F21 신규 5개 + F19 신규 4개 = 110개 예상. 변경 후 Windows unittest 미실행이므로 통과를 주장하지 않음.
- 필수 후속: Windows 전체 110개 테스트, Vercel 관리자 실제 API 수동 조회, F20 기사 저장·발행/보류 실제 흐름 검증, F21 안전 오류 기록 검증. Cron 실제 활성화 전 비용/쿼터·스케줄 운영 승인 별도 요청.


### 25.4 Windows 110개 전체 자동 테스트 통과 및 최종 README 감사 계획 (2026-10-20)

- 사용자 Windows PowerShell 제출 로그 실측: `Ran 110 tests in 0.785s`, `OK`. 110개 전체 통과, 실패 및 오류 0. F19의 슬롯 중복 방지·수집 미가동, F20의 발행 보호, F21의 안전 오류 기록 및 관리자 전용 API 테스트 포함. `StarletteDeprecationWarning`, 의도된 mock DB 오류 및 카카오 502 실패 출력은 실패 판정이 아님.
- **검증 범위:** 로컬 unittest 성공이며 실제 Supabase 신규 기사 생성/발행·보류, 운영 오류 기록 축적, 카카오 실호출을 포함한 수집 처리기 통합 검증 및 프로덕션 UI 수동 검증까지 완료됐다는 뜻은 아님. F19 예약 수집 활성화는 승인 전까지 OFF 유지.
- **사용자 추가 요청:** 모든 개발 단계와 실제 운영 검증이 마무리되면 `README.md` **전체**를 마지막으로 검수한다. 기능정의서의 F01~F23 진행률·완료 여부, 실제 코드/API/화면/상단 메뉴의 '준비 중' 상태, Supabase DB·RLS/관리자 Auth 정책, Python/Vercel/환경변수 정의, F19 Cron 활성 상태, F20 발행 정책, F21 오류 기록·알림 범위, 테스트 실측 수치, 중복·오래된 설명·번호 충돌과 문서 내 상충 표현을 확인한다. 기록의 역사적 사실은 보존하면서 최상단 '현재 운영 상태/최종 명세'를 최신으로 정리하고, 실제로 확인하지 않은 기능은 완료로 표시하지 않는다. 결과는 `kakao` 브랜치에서 커밋하고 `main` 최종 병합은 사용자 별도 승인 전까지 하지 않는다.


### 25.5 Production 읽기 전용 데이터 점검과 F19 부분 실패 회귀 (2026-10-20)

- 실제 Vercel 배포 SHA `22f4d6b` **READY** 확인 후 Supabase에 SELECT만 실행. 기존 기사 `8`건, 경로 스냅샷 `24`건, F20 상태·변경 이력 `0/0`건, F19 수집 실행·관측 `0/0`건, F21 영구 운영 이벤트 **1건**. 기존 기사·DB 구조·관리자 계정 변경 없이 확인함.
- 저장된 F21 운영 이벤트는 `source=kakao`, `event_type=directions_request`, `safe_error_code=http_error`, `http_status=429`, `outcome=failure`, `occurrence_count=1`. 오류 원문, API 키, 사용자 질의는 이벤트 컬럼 조회에 없음. HTTP 429는 요청 제한/쿼터 가능성을 의미하며 정확한 정책 원인은 Kakao 관리자 콘솔 또는 응답 헤더로 추가 확인이 필요. 따라서 실제 F19 Cron 자동 활성화 불가(별도 비용·쿼터 검증 및 사용자 승인 필요).
- F19 처리기 `tests/test_collection_runs.py`에 대표 3개 경로 중 1개 실패시 2 성공·1 실패·`partial` 결과 및 비공개 예외 문구 비노출을 검증하는 `test_partial_failures_are_counted_without_leaking` 추가. 기존 실측 **110개 OK**에 테스트 1개 추가되어 **111개 예상(새 실행 결과 미확인)**.
- 결론: F21 실제 영구 오류 저장 1회 확인, F20 실제 발행 과정 및 F19 실수집은 미검증. 데이터 변경 없이 안전한 회귀 테스트만 추가했고, 승인 전 자동 수집·외부 알림·DB 정리는 하지 않았음. `main` 불변.

## 26. M03 상단 메뉴 ‘준비 중’ 실제 구현 대조 및 항목 정리 (2026-10-20)

- 사용자 제출 Windows 전체 테스트 로그 **111개 실행/111개 OK** 확인. 이번 UI 개선 전 검증 결과이며 신규 UI 이후 전체 재실행은 미확인.
- 최신 traffic-api/static/navigation.js에서 실제 남아 있던 planned:true 항목은 세 가지: 홈 이용 안내·FAQ, 뉴스 기사 공유·읽기 모드, 관리자 운영 설정·공지. 다른 F19/F20/F21 메뉴는 이미 실제 관리자 보호 화면으로 연결되어 있었으므로 다시 변경하지 않음.
- 홈 static/index.html에 #helpSection을 추가하고 현재 구현 사실 기반 FAQ 네 개(경로 검색, 관심 경로의 브라우저별 보존, 조회 시각과 뉴스의 시점 구분, 카카오 API 실패 안내)를 제공. 메뉴 /#helpSection 연결.
- 뉴스 static/news.html의 실제 기사 본문 앞에 #readingTools를 추가. 집중 읽기 모드 토글, 기본 뉴스 페이지 주소 복사 및 저장된 **공개 기사** 선택 시 /news?article_id=<기사 ID> 고유 링크 복사를 제공. 이 링크를 열면 기존 공개 상세 API로 저장된 기사를 조회하며 새 카카오 API를 호출하지 않는다. 검토/보류 상태의 기사는 서버의 공개 상세 API가 차단한다. 메뉴 '기사 공유·읽기 모드'는 /news#readingTools로 연결.
- 관리자 static/admin.html의 기존 인증 후 작업실에 #operatingGuideSection 추가. 정기 수집 OFF, 신규 기사 review→승인 발행, 외부 오류 알림 OFF, API 메모리 계측을 읽기 전용 문구로 안내. 비밀키/환경변수 설정이나 공지 DB 편집 기능은 제공하지 않음. 메뉴 '운영 정책·공지 안내'로 표기를 제한하여 /admin#operatingGuideSection로 연결.
- 모든 상단 메뉴의 planned:true 항목 제거. 이는 모든 기능이 완성되었다는 뜻이 아니며 F19 실제 Cron과 운영 설정 변경 및 개별 뉴스 링크 공유/공지 CRUD는 여전히 범위 밖. 구현된 설명/컨트롤에 링크를 연결하되 새 비용·DB 조작/업데이트/외부 알림은 가하지 않음.
- static/d03-urban-traffic.css에서 FAQ details, 뉴스 읽기 모드, 운영 안내 카드의 390px 반응형 스타일 추가. 어떠한 포커스 아웃라인·테두리도 신규 추가하지 않음.
- tests/test_navigation.py에 메뉴 앵커 3개, 준비 중 표기 제거, FAQ·읽기 모드·운영 안내 확인 테스트 1개와 공개 기사 고유 링크 검증 테스트 1개 추가. 이전 실측 111개에 2개 추가되어 총 113개 예상(사용자 Windows 재실행 필요).
- 브랜치 kakao만 수정, 기존 데이터·카카오 API·인증, Supabase 테이블과 Vercel Cron 설정 및 main 브랜치 변경 없음. README 최종 전체 감사는 모든 운영 검증 완료 후 별도로 수행.

## 27. README 현행화·배포 보류 기록 (2026-10-20)

- **작업 범위:** README만 수정. 최상단 날짜·현행 기능표·API 목록의 오래된 설명을 최신 소스와 113개 사용자 테스트 결과로 교정하고, 후속 작업용 실행/현황/보안 경계 추가. 0~26장 개발 당시의 진행 메모는 지우지 않고 역사적 기록으로 보존하며 현행 기준은 맨 앞 '최신 개발 현황' 절이라고 명시.
- **대조 근거:** `traffic-api/static/navigation.js` (4개 메뉴 그룹·16개 실제 링크, 준비 중 항목 없음), `app/main.py` (FastAPI 공개/보호 API), `traffic-api/vercel.json` (배포 구조), 기존 F19/F20/F21 개발·검증 이력, 사용자 제출 Windows `Ran 113 tests ... OK`.
- **과장 방지:** 코드와 로컬 테스트 통과를 실제 운영 확인과 구분. 운영 Vercel이 GitHub 최신 수정사항을 적용하지 못한 상황과 **사용자 의사에 따른 배포 보류**를 명시. DB 건수는 특정 시점 실측치로 한정. 보수적 ID 완료율 20/23(87.0%) 유지, F19 Cron/F21 외부 알림 및 비인가 DB 작업은 하지 않음.
- **기능·DB·화면·개발환경 영향:** 코드·DB·인증·환경변수·화면·Vercel 설정 모두 무변경. `kakao` 브랜치의 `README.md`만 커밋; `main` 변경 금지. 새로운 작업 요구사항이 들어오면 기존 프로젝트 변경과 구분해 별도 설계한다.

### 27.1 README 전체 재점검 — 코드와 과거 기록의 구분 (2026-10-20)

- **검토 근거:** GitHub `kakao` 브랜치의 루트 README, `PROJECT_HANDOFF.md`, 전체 파일 트리, `app/main.py`, `app/collection_runs.py`, `app/operation_policies.py`, `app/operational_events.py`, `static/navigation.js`, `tests/test_publication.py`, `tests/test_navigation.py`, `requirements.txt`, `.env.example`. 검토 시작 HEAD는 `0a9b13b5ea7ecf718f411f4fd5f547f54d5296d4`.
- **기능표 정합성:** 원래 현행 기능표에 누락됐던 F23 행을 복원하여 F01~F23 총 23개를 전부 표시. 완료 20개와 운영 검증이 남은 F19/F20/F21 3개를 구분; F22 출처 표기 전 범위도 별도 점검 필요.
- **운영 단계 구분:** F19 30초 인메모리 캐시·사용량 계측 및 `collect_daily_routes()`는 구현됐으나 Cron 호출·실수집 미활성. F20은 관리자 전용 발행 상태 API·비공개 필터와 mock 단위 테스트가 있지만 신규 기사 실 DB 상태 변경을 새로 실증하지 않음. F21은 안전한 오류 코드 기록·관리자 조회 구현, 과거 HTTP 429 기록 1건 확인; 관리자 화면의 최신 실동작·외부 알림은 완료로 표기하지 않음.
- **배포·DB 보존:** Vercel 새 배포는 사용자가 보류했으며 자동 배포를 요청하지 않음. 이번 감사에서 GitHub 문서만 변경; 실제 Supabase DB/인증/기존 기사, 환경변수, 카카오 설정, 페이지 JS/CSS, 배포 설정은 건드리지 않음.
- **검증 사실:** Windows 113개 통과는 사용자 제출 직전 실행 로그를 인용한 과거 확인치. 이번 작업에서는 Windows나 운영 브라우저에서 재실행·재배포하지 않았으며 GitHub 문서 변경이 앱 동작을 바꾸지 않습니다.
- **후속 인계:** Windows 11 PowerShell에서 `kakao` 체크아웃 및 전체 테스트를 확인한 뒤 사용자 브라우저에서 공개 메뉴·모바일 화면을 점검. 운영 작업은 F19 스케줄/비용 승인, F20 관리 기사 상태 실제 검증, F21 관리자 장애 목록 실확인이 별도 필요. 기존 데이터·관리자 인증·포커스 테두리 미추가 원칙 유지. 세부 기능을 수정할 때는 0장의 사전 설계·승인 절차 우선.

### 18.9 F19-B 관리자 현황 카드 디자인 개선 및 Windows 84개 테스트 확인 (2026-10-21)

- F19-B 관리 화면 사용자 승인('ok') 후 `static/admin.html`에서 **API 사용 현황 상단 설명·수동 새로고침 버튼을 좌우 배치**, 조회 전 문구 간결화, 조회 후 4개 통계(외부 호출/성공/실패/캐시 HIT·MISS)와 하단 상세 정보의 시각적 계층·간격 정리. 850px 이하 2열, 390px 이하 1열 유지. 모든 포커스 테두리 신규 추가 금지.
- `tests/test_api_usage.py`에 상세 정보·통계 블록의 구조·반응형/무포커스 회귀 테스트 1개 추가. 이전 전체 83개 예상에서 **84개**로 증가.
- 사용자가 관리자 데스크톱 Chrome 스크린샷을 제출했고 '4. API 사용 현황' 제목 및 설명이 왼쪽, '사용 현황 새로고침' 버튼이 오른쪽에 배치되고 가로 전체 폭 카드가 표시되는 것을 직접 확인함. 스크린샷은 **조회 전 상태**이므로, 개선 후 통계 4개가 조회되어 표시된 화면까지 시각 확인한 것은 아님.
- 사용자가 Windows PowerShell 전체 테스트 로그를 첨부함: **`Ran 84 tests in 0.617s`, `OK`**, 실패·오류 없음. 신규 `test_dashboard_summary_detail_and_responsive_contract`도 `ok`. 로그의 mock DB 예외/Kakao 502 출력은 의도된 오류처리 테스트에 따른 것.
- **잔여 검증:** 새로고침 버튼으로 개선된 4개 숫자 블록 및 상세 정보가 실제 관리자 화면에서 정상 표시되는지, 모바일 390px 배치 사용자 확인. `kakao` README 기록 외 서버·DB·인증·`main` 변경 없음. 이후 단계 전 사용자 확인과 신규 설계 승인 유지.
