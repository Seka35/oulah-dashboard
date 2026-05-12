-- Migration: Add landing_pages table
-- Run this to add the landing pages table to your database

CREATE TABLE IF NOT EXISTS landing_pages (
    id SERIAL PRIMARY KEY,
    ad_archive_id VARCHAR(255),
    source_url TEXT NOT NULL,
    scraped_html TEXT,
    local_html_path TEXT,
    local_assets_path TEXT,
    domain VARCHAR(255),
    headline TEXT,
    price_amount DECIMAL(10,2),
    price_text TEXT,
    currency VARCHAR(10) DEFAULT 'USD',
    checkout_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    scrape_error TEXT,
    scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ad_archive_id, source_url)
);

CREATE INDEX IF NOT EXISTS idx_landing_pages_ad_archive_id ON landing_pages(ad_archive_id);
CREATE INDEX IF NOT EXISTS idx_landing_pages_status ON landing_pages(status);