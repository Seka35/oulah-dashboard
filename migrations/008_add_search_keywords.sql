-- Add search_keywords to tiktok_ads
-- This column is used by save_search / _save_tiktok_ad

ALTER TABLE tiktok_ads ADD COLUMN IF NOT EXISTS search_keywords TEXT[];