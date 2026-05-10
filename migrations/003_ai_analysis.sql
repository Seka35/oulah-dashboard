-- Add AI analysis column to store structured verdicts from Claude
ALTER TABLE etsy_products ADD COLUMN IF NOT EXISTS ai_analysis JSONB;
ALTER TABLE amazon_products ADD COLUMN IF NOT EXISTS ai_analysis JSONB;
ALTER TABLE ads ADD COLUMN IF NOT EXISTS ai_analysis JSONB;
ALTER TABLE tiktok_ads ADD COLUMN IF NOT EXISTS ai_analysis JSONB;

-- Create a table for batches of AI analysis if needed, but per-product is better for now.
CREATE TABLE IF NOT EXISTS ai_analysis_log (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50),
    external_id VARCHAR(255),
    verdict JSONB,
    model VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
