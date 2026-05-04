from __future__ import annotations

from pathlib import Path
from typing import Iterator, Sequence

from app.events import Event


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"

INSERT_EVENT_SQL = """
INSERT INTO events (
    event_id,
    event_type,
    actor_role,
    actor_id,
    course_id,
    lecture_id,
    occurred_at,
    device_type,
    platform,
    amount,
    currency,
    error_code
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (event_id) DO NOTHING
"""


def connect(database_url: str):
    """DATABASE_URL을 사용해 PostgreSQL 연결을 생성합니다."""

    try:
        import psycopg
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "psycopg is required. "
            "Install dependencies with: python3 -m pip install -r requirements.txt"
        ) from exc

    return psycopg.connect(database_url)


def initialize_schema(connection, schema_path: Path = DEFAULT_SCHEMA_PATH) -> None:
    """schema.sql을 실행해 이벤트 저장 테이블과 인덱스를 준비합니다."""

    schema_sql = schema_path.read_text(encoding="utf-8")

    with connection.cursor() as cursor:
        cursor.execute(schema_sql)

    connection.commit()


def count_events(connection) -> int:
    """events 테이블에 저장된 전체 이벤트 수를 조회합니다."""

    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM events")
        row = cursor.fetchone()

    return int(row[0])


def insert_events(connection, events: Sequence[Event], *, batch_size: int) -> int:
    """생성된 이벤트 목록을 batch_size 단위로 events 테이블에 저장합니다."""

    if batch_size <= 0:
        raise ValueError("batch_size must be greater than 0")

    inserted_count = 0

    with connection.cursor() as cursor:
        for batch in _chunked(events, batch_size):
            # 여러 이벤트를 한 transaction 안에서 나누어 넣습니다.
            # 초기 seed 적재 시 메모리와 DB 부하를 조절하기 위한 선택입니다.
            cursor.executemany(INSERT_EVENT_SQL, [_event_row(event) for event in batch])
            inserted_count += len(batch)

    connection.commit()
    return inserted_count


def _chunked(events: Sequence[Event], batch_size: int) -> Iterator[list[Event]]:
    """이벤트 목록을 지정한 batch_size 크기의 작은 목록으로 나눕니다."""

    for start in range(0, len(events), batch_size):
        yield list(events[start:start + batch_size])


def _event_row(event: Event) -> tuple[object, ...]:
    """Event 객체를 INSERT SQL 파라미터 순서에 맞는 tuple로 변환합니다."""

    return (
        event.event_id,
        event.event_type,
        event.actor_role,
        event.actor_id,
        event.course_id,
        event.lecture_id,
        event.occurred_at,
        event.device_type,
        event.platform,
        event.amount,
        event.currency,
        event.error_code,
    )
