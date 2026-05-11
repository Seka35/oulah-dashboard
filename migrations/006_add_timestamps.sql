-- Add missing timestamp columns to ads table
-- These columns are used by get_all_raw_data() in db.py

ALTER TABLE ads ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE ads ADD COLUMN IF NOT EXISTS last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Same for tiktok_ads
ALTER TABLE tiktok_ads ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE tiktok_ads ADD COLUMN IF NOT EXISTS last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Verify with:
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'ads' ORDER BY ordinal_position;
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'tiktok_ads' ORDER BY ordinal_position;