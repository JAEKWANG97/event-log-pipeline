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
