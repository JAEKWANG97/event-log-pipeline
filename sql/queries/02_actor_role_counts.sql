SELECT
    actor_role,
    COUNT(*) AS event_count
FROM events
GROUP BY actor_role
ORDER BY event_count DESC;
