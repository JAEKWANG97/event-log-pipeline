-- actor_role별 이벤트 수를 집계합니다.
-- learner와 instructor 활동량을 비교해 양면 플랫폼의 사용 패턴을 확인합니다.
SELECT
    actor_role,
    COUNT(*) AS event_count
FROM events
GROUP BY actor_role
ORDER BY event_count DESC;
