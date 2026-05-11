-- Migration: Add products table for scraping pipeline + system settings
-- Run this on Neon DB after migration

BEGIN;

-- ============================================
-- Table: products
-- Stocke les produits validés pour le dashboard
-- ============================================
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    opportunity_id VARCHAR(100) UNIQUE,
    origin_type VARCHAR(50) NOT NULL,  -- 'scrape', 'ai', 'manual'
    source_ad_id VARCHAR(255),          -- ad_archive_id ou tiktok_ad_id
    source_platform VARCHAR(50),        -- 'meta', 'tiktok', 'google', 'etsy', 'amazon'
    source_tag VARCHAR(255),            -- keyword qui a déclenché le scraping

    -- Product info
    product_name TEXT,
    product_description TEXT,

    -- AI Analysis fields
    what_is_it TEXT,
    is_relevant BOOLEAN,
    relevance_reason TEXT,
    skip_reason TEXT,
    digital_repackage_idea TEXT,
    suggested_price TEXT,               -- ex: "$19-$39"
    suggested_price_min DECIMAL(10,2),
    suggested_price_max DECIMAL(10,2),
    estimated_margin TEXT,
    production_effort VARCHAR(20),      -- 'LOW', 'MEDIUM', 'HIGH'
    demand_level VARCHAR(20),            -- 'LOW', 'MEDIUM', 'HIGH', 'MASSIVE'
    demand_evidence TEXT,
    priority VARCHAR(20),                -- 'LOW', 'MEDIUM', 'HIGH'
    priority_reason TEXT,
    suggested_concepts TEXT[],           -- JSON array of concepts
    warnings TEXT[],

    -- Status workflow
    status VARCHAR(50) DEFAULT 'scraping_pending',  -- scraping_pending, pending_review, validated, duplicated, archived
    verdict_priority VARCHAR(20),

    -- Media
    thumbnail_url TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
CREATE INDEX IF NOT EXISTS idx_products_source ON products(source_platform, source_ad_id);
CREATE INDEX IF NOT EXISTS idx_products_origin ON products(origin_type);

-- ============================================
-- Table: settings (ajouter les clés manquantes)
-- ============================================
CREATE TABLE IF NOT EXISTS settings (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Table: product_tags (tags pour produits digitaux)
-- ============================================
CREATE TABLE IF NOT EXISTS product_tags (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL,          -- 'winning', 'trending', 'validated', 'archived'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_product_tags ON product_tags(product_id, tag);

-- ============================================
-- Table: system_prompt_history (historique des modifications)
-- ============================================
CREATE TABLE IF NOT EXISTS system_prompt_history (
    id SERIAL PRIMARY KEY,
    previous_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(255) DEFAULT 'system',
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMIT;