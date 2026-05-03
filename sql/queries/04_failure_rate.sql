-- 구매 완료, 구매 실패, 정산 실패 이벤트 중 실패성 이벤트 비율을 계산합니다.
-- settlement_failed는 성공 counterpart가 없으므로 엄밀한 정산 실패율이 아니라 운영 리스크 지표로 해석합니다.
WITH target_events AS (
    SELECT
        event_type,
        COUNT(*) AS event_count
    FROM events
    WHERE event_type IN (
        'purchase_completed',
        'purchase_failed',
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
