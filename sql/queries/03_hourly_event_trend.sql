SELECT
    DATE_TRUNC('hour', occurred_at) AS event_hour,
    COUNT(*) AS event_count
FROM events
GROUP BY event_hour
ORDER BY event_hour;
