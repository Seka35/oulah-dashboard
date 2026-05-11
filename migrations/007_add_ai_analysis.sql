-- Add ai_analysis column to ads and tiktok_ads tables
-- This column stores AI product analysis results

ALTER TABLE ads ADD COLUMN IF NOT EXISTS ai_analysis JSONB;
ALTER TABLE tiktok_ads ADD COLUMN IF NOT EXISTS ai_analysis JSONB;

-- Verify
-- SELECT column_name FROM information_schema.columns WHERE table_name IN ('ads', 'tiktok_ads') AND column_name = 'ai_analysis';