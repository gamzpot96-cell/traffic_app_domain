"""F14 관리자 뉴스 동시 저장 통합 테스트 (수동 실행).

실제 카카오 API를 조회하고 Supabase에 뉴스 1건을 추가할 수 있습니다.
비밀번호/토큰/기사 증표는 출력하거나 파일에 저장하지 않습니다.
"""
import asyncio
from getpass import getpass

import httpx


BASE_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 65.0


async def request_json(client, method, path, *, headers=None, json=None):
    response = await client.request(
        method, path, headers=headers, json=json
    )
    try:
        payload = response.json()
    except ValueError:
        payload = None
    return response.status_code, payload


async def main():
    print("F14 동시 저장 + 필수 페이지 회귀 검사를 시작합니다.")
    print("주의: Supabase에 실제 뉴스 1건과 경로 3건이 추가될 수 있습니다.")
    confirm = input("진행하려면 YES를 입력하세요: ").strip()
    if confirm != "YES":
        print("취소했습니다.")
        return

    email = input("관리자 이메일: ").strip()
    password = getpass("관리자 비밀번호 (화면에 표시되지 않음): ")
    if not email or not password:
        print("이메일과 비밀번호가 필요합니다.")
        return

    async with httpx.AsyncClient(
        base_url=BASE_URL, timeout=TIMEOUT_SECONDS
    ) as client:
        # 기존 공개 화면/API와 미인증 관리자 접근을 확인합니다.
        check_paths = ["/", "/map", "/news", "/admin", "/api/news/history"]
        for path in check_paths:
            result = await client.get(path)
            print("회귀 검사:", path, "HTTP", result.status_code)
            if result.status_code != 200:
                raise RuntimeError("공개 페이지/API의 회귀 검사가 실패했습니다.")

        for path in ["/api/admin/news/generate", "/api/admin/news/save"]:
            status, _ = await request_json(
                client, "POST", path, json={"draft_token": "invalid"}
            )
            print("미인증 차단:", path, "HTTP", status)
            if status != 401:
                raise RuntimeError("미인증 요청이 올바르게 차단되지 않았습니다.")

        # 토큰과 비밀번호는 메모리에만 사용합니다.
        status, login_data = await request_json(
            client, "POST", "/api/admin/login",
            json={"email": email, "password": password}
        )
        password = None
        if status != 200 or not isinstance(login_data, dict):
            raise RuntimeError("관리자 로그인 실패: HTTP " + str(status))
        access_token = login_data.get("access_token")
        if not access_token:
            raise RuntimeError("로그인 응답에 인증 토큰이 없습니다.")

        headers = {"Authorization": "Bearer " + access_token}
        status, generated = await request_json(
            client, "POST", "/api/admin/news/generate", headers=headers
        )
        if status != 200 or not isinstance(generated, dict):
            raise RuntimeError("기사 생성 실패: HTTP " + str(status))

        draft_token = generated.get("draft_token")
        if not draft_token:
            raise RuntimeError("생성된 기사 증표가 없습니다.")
        print("기사 생성 성공. 같은 증표로 저장 요청 두 건을 전송합니다.")

        # 두 요청을 함께 시작합니다. 하나는 신규 저장, 하나는 재전송이어야 합니다.
        request_body = {"draft_token": draft_token}
        results = await asyncio.gather(
            request_json(
                client, "POST", "/api/admin/news/save",
                headers=headers, json=request_body
            ),
            request_json(
                client, "POST", "/api/admin/news/save",
                headers=headers, json=request_body
            )
        )
        for index, (status, data) in enumerate(results, start=1):
            article_id = data.get("article_id") if isinstance(data, dict) else None
            already_saved = data.get("already_saved") if isinstance(data, dict) else None
            print(
                "저장 요청", index, "HTTP", status,
                "article_id", article_id, "already_saved", already_saved
            )

        if any(status != 200 for status, _ in results):
            raise RuntimeError("동시 저장 요청 중 HTTP 오류가 발생했습니다.")
        first = results[0][1]
        second = results[1][1]
        if (
            not isinstance(first, dict)
            or not isinstance(second, dict)
            or first.get("article_id") != second.get("article_id")
            or not isinstance(first.get("article_id"), int)
            or sorted(
                [first.get("already_saved"), second.get("already_saved")]
            ) != [False, True]
        ):
            raise RuntimeError("동시 저장의 중복 방지 응답이 기대와 다릅니다.")

        article_id = first["article_id"]
        detail_status, saved_article = await request_json(
            client, "GET", "/api/news/history/" + str(article_id)
        )
        if detail_status != 200 or not isinstance(saved_article, dict):
            raise RuntimeError("저장된 기사 상세 조회에 실패했습니다.")
        route_count = len(saved_article.get("routes", []))
        print("저장된 기사 상세 조회: HTTP", detail_status, "경로", route_count, "건")
        if route_count != 3:
            raise RuntimeError("저장된 경로 건수가 3건이 아닙니다.")

        print("PASS: 동시 재전송에서 하나의 기사만 저장됨. 기사 ID:", article_id)
        print("토큰/증표는 출력하거나 저장하지 않았습니다.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (httpx.RequestError, RuntimeError) as error:
        print("FAIL:", str(error))
        raise SystemExit(1)
