-- Add missing columns to ads table for save_search / _save_facebook_ad
-- These columns are referenced in db.py but missing on Neon

ALTER TABLE ads ADD COLUMN IF NOT EXISTS search_keywords TEXT[];
ALTER TABLE ads ADD COLUMN IF NOT EXISTS ai_analysis_log_id INTEGER;

-- Add missing columns to advertisers that fb ad join expects
-- (advertisers table should already have page_name, profile_photo_url, page_category, page_like_count)

-- Verify with:
-- SELECT column_name FROM information_schema.columns WHERE table_name IN ('ads', 'advertisers') ORDER BY column_name;