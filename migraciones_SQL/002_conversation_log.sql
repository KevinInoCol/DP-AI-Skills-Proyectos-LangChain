CREATE TABLE IF NOT EXISTS conversation_log (
    id          BIGSERIAL PRIMARY KEY,
    session_id  TEXT        NOT NULL,
    role        TEXT        NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT        NOT NULL,
    tools_used  JSONB       NOT NULL DEFAULT '[]'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_conversation_log_session
    ON conversation_log (session_id, created_at);
