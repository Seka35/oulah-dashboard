-- Migration: Add Automation Tables

-- Global settings for automation
CREATE TABLE IF NOT EXISTS automation_settings (
    id SERIAL PRIMARY KEY,
    is_active BOOLEAN DEFAULT FALSE,
    tiktok_frequency_hours INTEGER DEFAULT 24,
    facebook_frequency_hours INTEGER DEFAULT 48,
    etsy_frequency_hours INTEGER DEFAULT 72,
    amazon_frequency_hours INTEGER DEFAULT 72,
    tiktok_max_ads INTEGER DEFAULT 20,
    facebook_max_ads INTEGER DEFAULT 20,
    etsy_max_products INTEGER DEFAULT 20,
    amazon_max_products INTEGER DEFAULT 20,
    last_run_tiktok TIMESTAMP,
    last_run_facebook TIMESTAMP,
    last_run_etsy TIMESTAMP,
    last_run_amazon TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Keywords list with categories
CREATE TABLE IF NOT EXISTS automation_keywords (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100),
    keyword TEXT UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tracking which keyword has been tested on which platform
CREATE TABLE IF NOT EXISTS keyword_platform_status (
    id SERIAL PRIMARY KEY,
    keyword_id INTEGER REFERENCES automation_keywords(id) ON DELETE CASCADE,
    platform VARCHAR(50), -- 'tiktok', 'facebook', 'etsy', 'amazon'
    last_tested_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'completed', 'failed'
    UNIQUE(keyword_id, platform)
);

-- Insert default settings if not exists
INSERT INTO automation_settings (id, is_active)
SELECT 1, FALSE
WHERE NOT EXISTS (SELECT 1 FROM automation_settings WHERE id = 1);

-- Initial keywords from rules.md
-- Note: We will populate this via Python to handle the bulk insert easily
