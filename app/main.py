from __future__ import annotations

import time
from urllib.parse import urlsplit, urlunsplit

from app.config import load_settings
from app.events import generate_events
from app.storage import connect, count_events, initialize_schema, insert_events


def main() -> None:
    settings = load_settings()

    print("event-log-pipeline starting")
    print(f"DATABASE_URL={_mask_database_url(settings.database_url)}")
    print(f"INITIAL_EVENT_COUNT={settings.initial_event_count}")
    print(f"EVENT_BATCH_SIZE={settings.event_batch_size}")
    print(f"EVENT_INTERVAL_SECONDS={settings.event_interval_seconds}")
    print(f"ANALYTICS_INTERVAL_SECONDS={settings.analytics_interval_seconds}")

    try:
        with connect(settings.database_url) as connection:
            initialize_schema(connection)

            existing_event_count = count_events(connection)
            # 재실행 시 초기 seed 50,000건이 계속 누적되지 않도록 기존 데이터가 있으면 건너뜁니다.
            if existing_event_count > 0:
                print(f"existing_event_count={existing_event_count}")
                print("initial_seed=skipped")
            else:
                seed_events = generate_events(settings.initial_event_count)
                inserted_count = insert_events(
                    connection,
                    seed_events,
                    batch_size=settings.event_batch_size,
                )
                print(f"seeded_event_count={inserted_count}")

            run_event_loop(connection, settings.event_batch_size, settings.event_interval_seconds)
    except RuntimeError as exc:
        print(f"ERROR={exc}")
        raise SystemExit(1)


def run_event_loop(connection, event_batch_size: int, interval_seconds: int) -> None:
    """앱 컨테이너가 종료되지 않도록 주기적으로 새 이벤트를 저장합니다."""

    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be greater than 0")

    while True:
        events = generate_events(event_batch_size, days=1)
        inserted_count = insert_events(
            connection,
            events,
            batch_size=event_batch_size,
        )
        total_event_count = count_events(connection)
        print(
            f"inserted_event_count={inserted_count} "
            f"total_event_count={total_event_count}"
        )
        time.sleep(interval_seconds)


def _mask_database_url(database_url: str) -> str:
    parsed = urlsplit(database_url)
    if parsed.password is None:
        return database_url

    host = parsed.hostname or ""
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"

    username = parsed.username or ""
    netloc = f"{username}:***@{host}" if username else host
    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


if __name__ == "__main__":
    main()
