-- System Prompts table for AI analyzer
-- Stores active prompts and their output schemas

CREATE TABLE IF NOT EXISTS system_prompts (
    id SERIAL PRIMARY KEY,
    prompt_key VARCHAR(100) NOT NULL UNIQUE,  -- e.g., 'product_analyzer', 'classifier'
    prompt_text TEXT NOT NULL,
    output_schema JSONB,                       -- Expected JSON output structure
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default product analyzer prompt
INSERT INTO system_prompts (prompt_key, prompt_text, description, is_active)
VALUES (
    'product_analyzer',
    'You are an expert e-commerce analyst specializing in digital products...',
    'System prompt for AI product analysis',
    TRUE
) ON CONFLICT (prompt_key) DO NOTHING;

-- Function to update system_prompts and auto-log to history
CREATE OR REPLACE FUNCTION update_system_prompt_with_history()
RETURNS TRIGGER AS $$
BEGIN
    -- Log old value to history before update
    IF OLD.prompt_text IS DISTINCT FROM NEW.prompt_text THEN
        INSERT INTO system_prompt_history (previous_value, new_value, changed_by)
        VALUES (OLD.prompt_text, NEW.prompt_text, 'system');
    END IF;
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-log changes
DROP TRIGGER IF EXISTS trg_system_prompts_update ON system_prompts;
CREATE TRIGGER trg_system_prompts_update
    BEFORE UPDATE ON system_prompts
    FOR EACH ROW
    EXECUTE FUNCTION update_system_prompt_with_history();

-- Verify
-- SELECT * FROM system_prompts;
-- SELECT * FROM system_prompt_history;