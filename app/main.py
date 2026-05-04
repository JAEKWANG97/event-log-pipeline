from __future__ import annotations

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
            if existing_event_count > 0:
                print(f"existing_event_count={existing_event_count}")
                print("initial_seed=skipped")
                return

            seed_events = generate_events(settings.initial_event_count)
            inserted_count = insert_events(
                connection,
                seed_events,
                batch_size=settings.event_batch_size,
            )
    except RuntimeError as exc:
        print(f"ERROR={exc}")
        raise SystemExit(1)

    print(f"seeded_event_count={inserted_count}")


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
