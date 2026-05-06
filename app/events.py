from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from random import Random
from uuid import uuid4


@dataclass(frozen=True)
class Event:
    event_id: str
    event_type: str
    actor_role: str
    actor_id: str
    course_id: str | None
    lecture_id: str | None
    occurred_at: datetime
    device_type: str
    platform: str
    amount: int | None
    currency: str | None
    error_code: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "actor_role": self.actor_role,
            "actor_id": self.actor_id,
            "course_id": self.course_id,
            "lecture_id": self.lecture_id,
            "occurred_at": self.occurred_at.isoformat(),
            "device_type": self.device_type,
            "platform": self.platform,
            "amount": self.amount,
            "currency": self.currency,
            "error_code": self.error_code,
        }


@dataclass(frozen=True)
class EventProfile:
    event_type: str
    actor_role: str
    weight: int


# 이벤트 weight는 온라인 강의 플랫폼에서 이벤트별 발생 빈도가 다르다고 가정한 상대 비율입니다.
# 강의 탐색과 재생은 자주 발생하고, 결제 실패나 정산 실패는 상대적으로 드물게 발생하도록 둡니다.
EVENT_PROFILES = (
    EventProfile("course_view", "learner", 30),
    EventProfile("lecture_play", "learner", 28),
    EventProfile("purchase_completed", "learner", 8),
    EventProfile("purchase_failed", "learner", 2),
    EventProfile("course_created", "instructor", 5),
    EventProfile("lecture_uploaded", "instructor", 10),
    EventProfile("dashboard_view", "instructor", 15),
    EventProfile("settlement_completed", "instructor", 6),
    EventProfile("settlement_failed", "instructor", 2),
)

# 금액은 온라인 강의 상품에서 자주 볼 수 있는 KRW 가격대를 사용합니다.
PURCHASE_AMOUNTS = (19000, 29000, 49000, 99000, 149000)
SETTLEMENT_AMOUNTS = (100000, 300000, 500000, 1000000)
PURCHASE_ERROR_CODES = (
    "CARD_DECLINED",
    "INSUFFICIENT_FUNDS",
    "PAYMENT_TIMEOUT",
    "PG_ERROR",
)
SETTLEMENT_ERROR_CODES = (
    "INVALID_BANK_ACCOUNT",
    "PAYOUT_REJECTED",
    "TAX_INFO_MISSING",
)


def generate_events(count: int, *, days: int = 7, seed: int | None = None) -> list[Event]:
    if count < 0:
        raise ValueError("count must be greater than or equal to 0")
    if days <= 0:
        raise ValueError("days must be greater than 0")

    rng = Random(seed)
    now = datetime.now(timezone.utc)
    events = [_generate_event(rng, now=now, days=days) for _ in range(count)]
    # seed 데이터와 차트 결과를 보기 쉽게 시간순으로 정렬합니다.
    return sorted(events, key=lambda event: event.occurred_at)


def _generate_event(rng: Random, *, now: datetime, days: int) -> Event:
    profile = _choose_event_profile(rng)
    # dashboard_view는 강사 작업공간 이벤트이므로 특정 강의에 묶지 않습니다.
    course_id = _course_id(rng) if profile.event_type != "dashboard_view" else None
    lecture_id = (
        _lecture_id(rng, course_id)
        if profile.event_type in {"lecture_play", "lecture_uploaded"} and course_id
        else None
    )
    amount, currency = _money_fields(rng, profile.event_type)
    device_type, platform = _client_context(rng, profile.actor_role)

    return Event(
        event_id=str(uuid4()),
        event_type=profile.event_type,
        actor_role=profile.actor_role,
        actor_id=_actor_id(rng, profile.actor_role),
        course_id=course_id,
        lecture_id=lecture_id,
        occurred_at=_occurred_at(rng, now=now, days=days),
        device_type=device_type,
        platform=platform,
        amount=amount,
        currency=currency,
        error_code=_error_code(rng, profile.event_type),
    )


def _choose_event_profile(rng: Random) -> EventProfile:
    return rng.choices(
        EVENT_PROFILES,
        weights=[profile.weight for profile in EVENT_PROFILES],
        k=1,
    )[0]


def _actor_id(rng: Random, actor_role: str) -> str:
    if actor_role == "learner":
        return f"learner_{rng.randint(1, 20000):06d}"
    if actor_role == "instructor":
        return f"instructor_{rng.randint(1, 2000):06d}"
    raise ValueError(f"unsupported actor_role: {actor_role}")


def _course_id(rng: Random) -> str:
    return f"course_{rng.randint(1, 3000):05d}"


def _lecture_id(rng: Random, course_id: str) -> str:
    course_number = course_id.removeprefix("course_")
    return f"lecture_{course_number}_{rng.randint(1, 50):03d}"


def _occurred_at(rng: Random, *, now: datetime, days: int) -> datetime:
    max_seconds = days * 24 * 60 * 60
    # seed 이벤트를 여러 날짜에 분산해야 시간대별 추이 차트가 의미를 가집니다.
    return now - timedelta(seconds=rng.randint(0, max_seconds))


def _money_fields(rng: Random, event_type: str) -> tuple[int | None, str | None]:
    # 금액과 통화는 구매나 정산처럼 돈의 흐름이 있는 이벤트에만 기록합니다.
    if event_type in {"purchase_completed", "purchase_failed"}:
        return rng.choice(PURCHASE_AMOUNTS), "KRW"
    if event_type in {"settlement_completed", "settlement_failed"}:
        return rng.choice(SETTLEMENT_AMOUNTS), "KRW"
    return None, None


def _error_code(rng: Random, event_type: str) -> str | None:
    # 성공 이벤트와 일반 사용 이벤트에는 error_code를 남기지 않습니다.
    if event_type == "purchase_failed":
        return rng.choice(PURCHASE_ERROR_CODES)
    if event_type == "settlement_failed":
        return rng.choice(SETTLEMENT_ERROR_CODES)
    return None


def _client_context(rng: Random, actor_role: str) -> tuple[str, str]:
    if actor_role == "learner":
        # 수강생은 모바일 기기에서 강의를 소비하는 비중이 높다고 가정합니다.
        return rng.choices(
            (
                ("mobile", "ios"),
                ("mobile", "android"),
                ("desktop", "web"),
                ("tablet", "web"),
            ),
            weights=(35, 35, 25, 5),
            k=1,
        )[0]

    if actor_role == "instructor":
        # 강사는 주로 웹 대시보드에서 강의와 정산 정보를 관리한다고 가정합니다.
        return rng.choices(
            (
                ("desktop", "web"),
                ("mobile", "web"),
                ("tablet", "web"),
            ),
            weights=(85, 10, 5),
            k=1,
        )[0]

    raise ValueError(f"unsupported actor_role: {actor_role}")
