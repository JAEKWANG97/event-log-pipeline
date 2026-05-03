-- 이벤트 타입별 발생 횟수를 집계합니다.
-- 서비스에서 어떤 행동이 가장 많이 발생하는지 확인하는 기본 볼륨 지표입니다.
SELECT
    event_type,
    COUNT(*) AS event_count
FROM events
GROUP BY event_type
ORDER BY event_count DESC;
