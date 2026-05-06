-- 구매/정산 완료 이벤트와 실패 이벤트를 함께 놓고 실패성 이벤트 비율을 계산합니다.
-- 결제와 정산처럼 돈의 흐름이 있는 이벤트의 운영 리스크를 확인하기 위한 지표입니다.
WITH target_events AS (
    SELECT
        event_type,
        COUNT(*) AS event_count
    FROM events
    WHERE event_type IN (
        'purchase_completed',
        'purchase_failed',
        'settlement_completed',
        'settlement_failed'
    )
    GROUP BY event_type
),
summary AS (
    SELECT
        COALESCE(SUM(event_count), 0) AS total_event_count,
        COALESCE(
            SUM(event_count) FILTER (
                WHERE event_type IN ('purchase_failed', 'settlement_failed')
            ),
            0
        ) AS failed_event_count
    FROM target_events
)
SELECT
    total_event_count,
    failed_event_count,
    ROUND(
        failed_event_count * 100.0 / NULLIF(total_event_count, 0),
        2
    ) AS failure_rate_percent
FROM summary;
