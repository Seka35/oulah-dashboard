-- ================================================
-- ADD-ON: Digital Product Intelligence Schema
-- ================================================

-- Classify ads as digital products or not
CREATE TABLE IF NOT EXISTS digital_product_classification (
    id SERIAL PRIMARY KEY,
    ad_archive_id VARCHAR(255),  -- Facebook
    tiktok_ad_id VARCHAR(255),   -- TikTok (mutually exclusive)
    classification_type VARCHAR(50),  -- 'digital', 'physical', 'service', 'unknown'
    confidence_score DECIMAL(3,2),    -- 0.00 to 1.00
    matched_keywords TEXT[],         -- which keywords matched
    url_domain TEXT,                 -- landing page domain
    is_digital_product BOOLEAN,
    product_category VARCHAR(100),    -- ebook, template, course, saas, tool, plugin, etc.
    product_name TEXT,               -- inferred product name
    raw_classification JSONB,
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ad_archive_id)
);

-- Track advertisers over time to detect scaling behavior
CREATE TABLE IF NOT EXISTS advertiser_tracking (
    id SERIAL PRIMARY KEY,
    page_id VARCHAR(255),            -- from advertisers.page_id
    page_name TEXT,
    platform VARCHAR(50),            -- facebook, tiktok, google
    ad_count INTEGER DEFAULT 0,      -- distinct active ads
    first_seen_at TIMESTAMP,
    last_seen_at TIMESTAMP,
    active_days INTEGER,             -- days between first and last ad
    total_spend_estimate TEXT,
    is_scaling BOOLEAN DEFAULT FALSE, -- 3+ ads active 7+ days
    scaling_score INTEGER DEFAULT 0, -- ad_count * active_days
    scaling_tier VARCHAR(20),        -- 'low' (<14), 'medium' (14-30), 'high' (>30)
    last_calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(page_id, platform)
);

-- Unified product opportunities (the main output)
CREATE TABLE IF NOT EXISTS product_opportunities (
    id SERIAL PRIMARY KEY,
    opportunity_id VARCHAR(100) UNIQUE,  -- e.g., 'FB_prodigital_2024_001'

    -- Product info
    product_name TEXT,
    product_category VARCHAR(100),
    product_description TEXT,
    price_text TEXT,              -- e.g., "$47" or "€29"
    price_amount DECIMAL(10,2),

    -- Advertiser info
    advertiser_page_id VARCHAR(255),
    advertiser_name TEXT,
    advertiser_platform VARCHAR(50),
    advertiser_page_url TEXT,

    -- Scalability metrics
    scaling_score INTEGER DEFAULT 0,
    scaling_tier VARCHAR(20),
    active_days INTEGER,
    ad_count INTEGER,
    is_scaling BOOLEAN DEFAULT FALSE,

    -- Landing page
    landing_page_url TEXT,
    landing_page_scraped BOOLEAN DEFAULT FALSE,
    landing_page_score DECIMAL(3,2),

    -- Status pipeline
    status VARCHAR(50) DEFAULT 'fresh_lead',  -- fresh_lead, analyzing, validated, duplicated, archived
    priority INTEGER DEFAULT 5,  -- 1=highest, 5=lowest

    -- Tracking
    first_detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Store scraped landing page data
CREATE TABLE IF NOT EXISTS landing_pages (
    id SERIAL PRIMARY KEY,
    opportunity_id VARCHAR(100) REFERENCES product_opportunities(opportunity_id),
    url TEXT UNIQUE,
    domain TEXT,
    hero_headline TEXT,
    hero_subheadline TEXT,
    main_offer TEXT,
    price_text TEXT,
    price_amount DECIMAL(10,2),
    currency VARCHAR(10),
    cta_text TEXT,
    cta_url TEXT,
    checkout_type VARCHAR(50),       -- stripe, gumroad, paddle, woocommerce, shopify, etc.
    checkout_domain VARCHAR(255),
    technology_stack TEXT[],          -- detected tech: ['stripe', 'cloudflare', 'wordpress', etc.]
    trust_signals TEXT[],             -- 'money-back guarantee', 'ssl', 'testimonials', etc.
    full_text_content TEXT,
    html_content TEXT,
    screenshot_path TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scrape_error TEXT
);

-- Store creative assets for each opportunity
CREATE TABLE IF NOT EXISTS opportunity_creatives (
    id SERIAL PRIMARY KEY,
    opportunity_id VARCHAR(100) REFERENCES product_opportunities(opportunity_id),
    source_ad_archive_id VARCHAR(255),  -- Facebook
    source_tiktok_ad_id VARCHAR(255),  -- TikTok
    platform VARCHAR(50),
    creative_type VARCHAR(50),          -- image, video
    original_url TEXT,
    local_path TEXT,
    downloaded BOOLEAN DEFAULT FALSE,
    ad_first_seen DATE,
    ad_last_seen DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_classification_digital ON digital_product_classification(is_digital_product) WHERE is_digital_product = TRUE;
CREATE INDEX IF NOT EXISTS idx_tracking_scaling ON advertiser_tracking(is_scaling, scaling_tier);
CREATE INDEX IF NOT EXISTS idx_opportunities_score ON product_opportunities(scaling_score DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_status ON product_opportunities(status);
CREATE INDEX IF NOT EXISTS idx_landing_pages_domain ON landing_pages(domain);
CREATE INDEX IF NOT EXISTS idx_creatives_opportunity ON opportunity_creatives(opportunity_id);
-- Etsy Products (for product validation - high reviews/ratings = proven products)
CREATE TABLE IF NOT EXISTS etsy_products (
    id SERIAL PRIMARY KEY,
    listing_id VARCHAR(255) UNIQUE,
    title TEXT,
    price TEXT,
    currency VARCHAR(10),
    price_amount DECIMAL(10,2),
    shop_name TEXT,
    shop_url TEXT,
    rating DECIMAL(2,1),
    review_count INTEGER,
    url TEXT UNIQUE,
    search_keyword TEXT,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_json JSONB
);

-- Index for Etsy products
CREATE INDEX IF NOT EXISTS idx_etsy_shop ON etsy_products(shop_name);
CREATE INDEX IF NOT EXISTS idx_etsy_rating ON etsy_products(rating DESC);
CREATE INDEX IF NOT EXISTS idx_etsy_reviews ON etsy_products(review_count DESC);
