-- occurred_at을 1시간 단위로 묶어 시간대별 이벤트 추이를 집계합니다.
-- Metabase line chart로 시각화하면 사용량이 몰리는 시간대를 확인할 수 있습니다.
-- 초기 seed 이벤트를 최근 7일 범위에 분산 생성하면 로컬 데모에서도 시간대별 패턴을 볼 수 있습니다.
SELECT
    DATE_TRUNC('hour', occurred_at) AS event_hour,
    COUNT(*) AS event_count
FROM events
GROUP BY event_hour
ORDER BY event_hour;
