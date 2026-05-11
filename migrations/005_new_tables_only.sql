-- ============================================================
-- NEW TABLES for R2 + Dashboard Migration
-- ============================================================
-- Run this AFTER tables exist
-- Idempotent: uses IF NOT EXISTS
-- ============================================================

-- Product Tags (for digital product tagging: winning, trending, etc.)
-- Note: products.id is UUID on Neon, so product_id must be UUID too
DROP TABLE IF EXISTS product_tags;

CREATE TABLE product_tags (
    id SERIAL PRIMARY KEY,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_product_tags ON product_tags(product_id, tag);

-- ============================================================
-- Verify with:
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
-- ============================================================