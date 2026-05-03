CREATE TABLE IF NOT EXISTS events (
    event_id UUID PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    actor_role VARCHAR(20) NOT NULL,
    actor_id VARCHAR(50) NOT NULL,
    course_id VARCHAR(50),
    lecture_id VARCHAR(50),
    occurred_at TIMESTAMPTZ NOT NULL,
    device_type VARCHAR(20),
    platform VARCHAR(20),
    amount INTEGER,
    currency CHAR(3),
    error_code VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT events_event_type_check CHECK (
        event_type IN (
            'course_view',
            'lecture_play',
            'purchase_completed',
            'purchase_failed',
            'course_created',
            'lecture_uploaded',
            'dashboard_view',
            'settlement_failed'
        )
    ),
    CONSTRAINT events_actor_role_check CHECK (
        actor_role IN ('learner', 'instructor')
    ),
    CONSTRAINT events_amount_check CHECK (
        amount IS NULL OR amount >= 0
    )
);

CREATE INDEX IF NOT EXISTS idx_events_occurred_at
    ON events (occurred_at);

CREATE INDEX IF NOT EXISTS idx_events_event_type
    ON events (event_type);

CREATE INDEX IF NOT EXISTS idx_events_actor_role
    ON events (actor_role);
