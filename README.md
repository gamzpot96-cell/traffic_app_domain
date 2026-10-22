# 서울 도로교통정보·뉴스 브리핑 서비스

FastAPI 기반의 자동차 경로 조회·교통정보 분석·뉴스 브리핑 서비스입니다. 카카오 API에서 **선택한 자동차 경로**의 거리, 예상 소요시간, 도로 구간별 정체·지체 정보를 조회하며, 서울 전체 도로 현황을 대표하지 않습니다.

## 이용 조건

이 프로젝트의 **직접 작성한 소스코드**는 [MIT License](LICENSE)를 따릅니다. 코드 재사용 시 저작권 표시와 라이선스 문구를 유지해야 합니다. **외부 데이터·지도·사진·API 서비스에는 MIT 라이선스가 적용되지 않으며**, 각 제공자의 별도 조건을 확인해야 합니다.

| 자료 | 출처 | 이용 조건 |
|---|---|---|
| 프로젝트 소스코드 | 이 저장소의 [LICENSE](LICENSE) | **MIT** — 저작권 표시와 라이선스 고지 유지 |
| 자동차 길찾기·교통 분석 원천 데이터 | [카카오모빌리티 Directions API](https://developers.kakaomobility.com/guide/navi-api/start) · [요금·한도](https://developers.kakaomobility.com/en/price/) | 등록된 앱의 REST API 키로 경로·예상 소요시간 등을 서비스에 활용할 수 있으며 이용량·요금 기준을 준수해야 함. **원본 응답의 독립적인 재판매·일괄 재배포나 외부 AI 전송·뉴스 공개까지 포괄 허가한 것으로 해석하지 않음** |
| 장소 검색·좌표 정보 | [Kakao Local API](https://developers.kakao.com/docs/ko/local/dev-guide) · [서비스 약관](https://developers.kakao.com/terms/ko/site-terms) | 등록 앱의 REST API 키로 장소명·좌표 등을 조회하는 기능. 서비스 약관과 운영정책 및 쿼터 준수, 무단 수집·제3자 제공·권리 침해 금지. **조회 결과의 무제한 저장·독립 재배포 권한을 부여하는 라이선스가 아님** |
| 웹 지도 | [Kakao Maps JavaScript SDK](https://apis.map.kakao.com/web/guide/) · [운영정책](https://developers.kakao.com/terms/ko/site-policies) | JavaScript 키 발급과 허용 도메인 등록 후 SDK를 통해 지도 표시. 서비스 약관·운영정책 준수. **지도 타일·이미지의 별도 추출·복제·재배포 허가로 간주하지 않음** |
| 기본 지도 데이터 | [OpenStreetMap](https://www.openstreetmap.org/copyright) | **ODbL 1.0** — © OpenStreetMap contributors 출처 표시 및 해당 데이터 라이선스 준수 |
| 상단 교통 사진 `Gangnam traffic.jpg` | [kallerna / Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Gangnam_traffic.jpg) | **CC BY-SA 4.0** — 저작자·라이선스·출처 표시, 수정 시 변경 내용 표시, 수정본 공유 시 동일계열 라이선스 적용 |
| AI 기사 생성에 사용하는 모델 서비스 | [OpenAI API](https://openai.com/ko-KR/policies/services-agreement/) · [서비스 약관](https://openai.com/ko-KR/policies/service-terms/) | 적용 법률 범위에서 고객은 출력물에 대한 권리를 보유하지만, 입력 자료에 필요한 사용 권한을 확보해야 하고 결과의 적법성·정확성·공개 적절성을 직접 검토해야 함. **제3자 원천 데이터의 이용 허가를 대신하지 않음** |

**유의:** 카카오 API로 조회한 경로별 예상 소요시간은 조회 시점의 API 예상값이며, 서울 전체 교통상황이나 별도의 독립 관측 자료를 뜻하지 않습니다. **공식 문서에서 확인한 SDK·API의 일반적인 사용 방법은 응답 데이터의 영구 저장·외부 AI 서비스 전송·기사 공개·제3자 재배포에 대한 개별 허가를 의미하지 않습니다.** 이러한 이용의 구체적인 허용 범위는 해당 제공자의 계약·승인 내용에 따라 달라질 수 있으므로, 별도 허가가 필요한 경우 제공자에게 직접 문의해야 합니다. 이 절의 확인 기준: 2026-10-22.

## 핵심 기능

| 영역 | 현재 기능 |
|---|---|
| 경로 조회 | Kakao Local API 장소 검색, Kakao Mobility 자동차 길찾기 및 구간별 교통정보 |
| 지도 | Kakao Maps JavaScript SDK 기반 경로·마커 표시, 기존 지도 페이지 별도 유지 |
| 데이터 분석 | 선택된 3개 경로의 거리, 예상 이동시간, 정체·지체 구간 수 및 거리 비율 |
| 뉴스 | 관리자가 OpenAI API로 기사 초안을 작성하고 사실 검토 후 비공개 저장·발행, 일반 방문자는 발행 기사만 조회 |
| 뉴스 이력 | 저장된 기사 검색·상세·페이지네이션·기사→지도 연결 |
| 데이터 활용 | 저장된 경로의 조회 시점별 추세, CSV 내려받기 |
| 운영 | 관리자 인증, API 사용 현황, 관심 경로, 기사 발행 상태, 운영 오류 확인 |

정기 수집(F19), 기사 발행 상태 전환(F20), 장애 모니터링(F21)은 코드·테스트와 실제 운영 검증 범위를 구분해야 합니다. 자동 실행이나 운영 배포가 확인됐다는 뜻은 아닙니다.

## 구성 및 데이터베이스

| 구성 | 사용 기술·데이터 |
|---|---|
| 서버 | Python, FastAPI |
| 화면 | HTML, CSS, JavaScript |
| 지도·교통 데이터 | Kakao Maps, Kakao Local, Kakao Mobility Directions |
| AI 기사 작성 | OpenAI API (서버 측, 관리자 전용) |
| DB·인증 | Supabase PostgreSQL 및 Supabase Auth |
| 주요 DB | `traffic_news_articles` (기사), `traffic_route_snapshots` (경로별 수치), `traffic_article_publication` (발행 상태), `traffic_article_publication_events` (상태 변경 이력) |
| 운영 관련 | 반복 수집·API 현황·오류 기록 관련 테이블 및 관리 기능은 문서와 실제 환경에서 확인 |

새 기사는 검토 상태로 저장되며 관리자 발행 절차를 거치기 전에는 공개하지 않습니다. 기존 기사와 DB 데이터는 별도로 삭제하거나 변경하지 않았습니다.

## 주요 화면 및 API

| 경로 | 역할 |
|---|---|
| `/` | 경로 조회 및 브리핑 |
| `/map` | 카카오 지도와 경로 표시 |
| `/news` | 저장·발행된 교통 기사, 검색·분석 |
| `/admin` | 관리자 로그인, AI 기사 작성·검토·저장·발행 |
| `GET /api/route` | 자동차 경로 조회 |
| `GET /api/news/search` | 공개 기사 검색 |
| `GET /api/news/history/{article_id}` | 공개 기사 상세 |
| `POST /api/admin/news/generate` | 관리자 전용 AI 기사 생성 |
| `POST /api/admin/news/save` | 관리자 기사 검토 후 저장 |

## 로컬 실행 및 검증

```powershell
cd traffic-api
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

개발용 `.env`의 값은 저장소에 올리지 않습니다. 필요한 설정 이름은 [환경변수 예시](traffic-api/.env.example)를 참조하세요. 별도 터미널에서 테스트합니다.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

기록상 Windows 로컬 자동 테스트 **119개 통과**가 보고됐습니다(2026-10-20). 이 결과는 실제 운영 환경·외부 API 호출의 성공을 대신하지 않습니다. Vercel 배포는 별도 승인 전까지 진행하지 않습니다.

## 개발 설계·검증 기록

README가 길어지는 것을 방지하기 위해 이전 상세 설계·구현·테스트 기록을 아래 별도 Markdown 파일에 보관합니다. 기록에 있는 계획 또는 과거 결과를 현재 운영 상태로 오해하지 마세요.

| 문서 | 내용 |
|---|---|
| [개발 원칙·이전 화면 설계·확장 제안](docs/development/00-project-management.md) | 단계별 정책과 과거 화면 구상 |
| [F13·F14·F15 상세 설계](docs/development/07-f13-f15-design.md) | 관리자 기사 저장·중복 방지·검증 |
| [M01 공통 메뉴 / F16 뉴스 검색 검토안](docs/development/09-m01-f16-search.md) | 요청된 9번 내용 전문 |
| [기타 승인 절차·디자인·F23·F17·F22](docs/development/08-12-design-and-tests.md) | 단계별 설계와 시험 기록 |
| [카카오맵 전환·관리자 UI·캐시](docs/development/13-15-maps-admin-cache.md) | 13~15장 |
| [시각 디자인·관심 경로·API 현황](docs/development/16-18-design-favorites-usage.md) | 16~18장 |
| [운영·발행·정기 수집·배포 이력](docs/development/19-27-operations-and-release.md) | 19~27장 |

