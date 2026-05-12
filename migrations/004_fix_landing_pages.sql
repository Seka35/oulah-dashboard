-- Migration: Fix landing_pages table (add missing columns if not exist)

-- Add missing columns if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'landing_pages' AND column_name = 'ad_archive_id') THEN
        ALTER TABLE landing_pages ADD COLUMN ad_archive_id VARCHAR(255);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'landing_pages' AND column_name = 'status') THEN
        ALTER TABLE landing_pages ADD COLUMN status VARCHAR(50) DEFAULT 'pending';
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'landing_pages' AND column_name = 'scrape_error') THEN
        ALTER TABLE landing_pages ADD COLUMN scrape_error TEXT;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'landing_pages' AND column_name = 'scraped_at') THEN
        ALTER TABLE landing_pages ADD COLUMN scraped_at TIMESTAMP;
    END IF;
END $$;

-- Recreate indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_landing_pages_ad_archive_id ON landing_pages(ad_archive_id);
CREATE INDEX IF NOT EXISTS idx_landing_pages_status ON landing_pages(status);