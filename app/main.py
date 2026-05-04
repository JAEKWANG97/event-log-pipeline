from __future__ import annotations

import json
from urllib.parse import urlsplit, urlunsplit

from app.config import load_settings
from app.events import generate_events


def main() -> None:
    settings = load_settings()

    print("event-log-pipeline configuration loaded")
    print(f"DATABASE_URL={_mask_database_url(settings.database_url)}")
    print(f"INITIAL_EVENT_COUNT={settings.initial_event_count}")
    print(f"EVENT_BATCH_SIZE={settings.event_batch_size}")
    print(f"EVENT_INTERVAL_SECONDS={settings.event_interval_seconds}")
    print(f"ANALYTICS_INTERVAL_SECONDS={settings.analytics_interval_seconds}")
    print("SAMPLE_EVENTS=")
    for event in generate_events(5, seed=42):
        print(json.dumps(event.to_dict(), sort_keys=True))


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
