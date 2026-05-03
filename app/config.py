from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> bool:
        return False


@dataclass(frozen=True)
class Settings:
    database_url: str
    initial_event_count: int
    event_batch_size: int
    event_interval_seconds: int
    analytics_interval_seconds: int


def load_settings() -> Settings:
    load_dotenv()

    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql://liveclass:liveclass@localhost:5432/liveclass",
        ),
        initial_event_count=_get_int("INITIAL_EVENT_COUNT", 50000),
        event_batch_size=_get_int("EVENT_BATCH_SIZE", 100),
        event_interval_seconds=_get_int("EVENT_INTERVAL_SECONDS", 5),
        analytics_interval_seconds=_get_int("ANALYTICS_INTERVAL_SECONDS", 30),
    )


def _get_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer: {raw_value}") from exc
