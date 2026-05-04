from __future__ import annotations

import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


METABASE_URL = os.getenv("METABASE_URL", "http://metabase:3000")
METABASE_EMAIL = os.getenv("METABASE_EMAIL", "admin@liveclass.local")
METABASE_PASSWORD = os.getenv("METABASE_PASSWORD", "Liveclass!2026")
METABASE_SITE_NAME = os.getenv("METABASE_SITE_NAME", "Liveclass Event Pipeline")
METABASE_DATABASE_NAME = os.getenv("METABASE_DATABASE_NAME", "Liveclass Events")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "liveclass")
POSTGRES_USER = os.getenv("POSTGRES_USER", "liveclass")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "liveclass")


def main() -> None:
    """Metabase 초기 관리자와 PostgreSQL datasource를 자동으로 준비합니다."""

    wait_for_metabase()
    session_id = ensure_admin_session()
    ensure_postgres_database(session_id)
    print("metabase_setup=completed")


def wait_for_metabase() -> None:
    """Metabase API가 응답할 때까지 기다립니다."""

    for attempt in range(1, 61):
        try:
            get_json("/api/session/properties")
            print(f"metabase_ready=true attempt={attempt}")
            return
        except (HTTPError, URLError, TimeoutError):
            print(f"metabase_ready=false attempt={attempt}")
            time.sleep(2)

    raise RuntimeError("Metabase did not become ready in time")


def ensure_admin_session() -> str:
    """초기 설정 여부에 따라 admin을 생성하거나 기존 admin으로 로그인합니다."""

    properties = get_json("/api/session/properties")

    if not properties.get("has-user-setup"):
        print("metabase_admin=creating")
        return create_admin(properties["setup-token"])

    print("metabase_admin=login")
    return login_admin()


def create_admin(setup_token: str) -> str:
    """Metabase 최초 실행 시 관리자 계정을 생성하고 session id를 반환합니다."""

    response = post_json(
        "/api/setup",
        {
            "token": setup_token,
            "user": {
                "email": METABASE_EMAIL,
                "first_name": "Liveclass",
                "last_name": "Admin",
                "password": METABASE_PASSWORD,
            },
            "prefs": {
                "site_name": METABASE_SITE_NAME,
                "site_locale": "ko",
            },
        },
    )
    return response["id"]


def login_admin() -> str:
    """이미 설정된 Metabase에서는 기존 admin 계정으로 session id를 발급받습니다."""

    response = post_json(
        "/api/session",
        {
            "username": METABASE_EMAIL,
            "password": METABASE_PASSWORD,
        },
    )
    return response["id"]


def ensure_postgres_database(session_id: str) -> None:
    """Liveclass Events datasource가 없을 때만 PostgreSQL 연결을 추가합니다."""

    databases = get_json("/api/database", session_id=session_id)
    database_items = databases.get("data", databases if isinstance(databases, list) else [])

    if any(database.get("name") == METABASE_DATABASE_NAME for database in database_items):
        print("metabase_database=exists")
        return

    print("metabase_database=creating")
    post_json(
        "/api/database",
        {
            "name": METABASE_DATABASE_NAME,
            "engine": "postgres",
            "details": {
                "host": POSTGRES_HOST,
                "port": POSTGRES_PORT,
                "dbname": POSTGRES_DB,
                "user": POSTGRES_USER,
                "password": POSTGRES_PASSWORD,
                "ssl": False,
            },
            "auto_run_queries": True,
            "is_full_sync": True,
            "schedules": {},
        },
        session_id=session_id,
    )


def get_json(path: str, *, session_id: str | None = None) -> dict:
    """Metabase API에 GET 요청을 보내고 JSON 응답을 반환합니다."""

    return request_json("GET", path, session_id=session_id)


def post_json(path: str, payload: dict, *, session_id: str | None = None) -> dict:
    """Metabase API에 POST 요청을 보내고 JSON 응답을 반환합니다."""

    return request_json("POST", path, payload=payload, session_id=session_id)


def request_json(
    method: str,
    path: str,
    *,
    payload: dict | None = None,
    session_id: str | None = None,
) -> dict:
    """표준 라이브러리만 사용해 Metabase API 요청을 실행합니다."""

    headers = {"Content-Type": "application/json"}
    if session_id is not None:
        headers["X-Metabase-Session"] = session_id

    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = Request(
        f"{METABASE_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )

    with urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8")

    if not body:
        return {}
    return json.loads(body)


if __name__ == "__main__":
    main()
