-- ================================================
-- Product Criteria - Back-office Management
-- ================================================

CREATE TABLE IF NOT EXISTS product_criteria (
    id SERIAL PRIMARY KEY,
    -- Identify the rule
    rule_id VARCHAR(100) UNIQUE NOT NULL,  -- e.g., 'digital_keyword_ebook', 'price_signal_47'
    rule_type VARCHAR(50) NOT NULL,       -- 'keyword', 'price_signal', 'domain', 'exclusion', 'weight_config'
    platform VARCHAR(50) NOT NULL,         -- 'facebook', 'tiktok', 'etsy', 'amazon', 'all'
    category VARCHAR(100),                 -- 'ebook', 'template', 'course', 'saas', 'physical', 'service', NULL for weight_config

    -- The actual criteria
    keyword VARCHAR(255),                  -- the keyword/pattern to match
    weight DECIMAL(4,2) DEFAULT 1.0,      -- weight multiplier (e.g., 2.0 for title, 1.0 for body)
    is_exclusion BOOLEAN DEFAULT FALSE,   -- TRUE = this rule excludes the product
    score_boost INTEGER DEFAULT 0,        -- points added when matched (can be negative for exclusions)

    -- Threshold / config (for weight_config type)
    config_key VARCHAR(100),              -- e.g., 'min_confidence', 'title_weight', 'body_weight'
    config_value DECIMAL(10,4),           -- e.g., 0.25 (min confidence), 2.0 (title weight)

    -- Rule metadata
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    description TEXT,                     -- human-readable description
    examples TEXT,                        -- example texts that should match
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_criteria_platform ON product_criteria(platform);
CREATE INDEX IF NOT EXISTS idx_criteria_category ON product_criteria(category);
CREATE INDEX IF NOT EXISTS idx_criteria_type ON product_criteria(rule_type);
CREATE INDEX IF NOT EXISTS idx_criteria_active ON product_criteria(is_active) WHERE is_active = TRUE;

-- ================================================
-- Default criteria (seed data)
-- ================================================

INSERT INTO product_criteria (rule_id, rule_type, platform, category, keyword, weight, is_exclusion, score_boost, display_order, description, examples) VALUES
-- DIGITAL KEYWORDS (positive signals)
('digital_ebook_1', 'keyword', 'all', 'ebook', 'ebook', 2.0, FALSE, 2, 1, 'Ebook keyword', 'Get my ebook about...'),
('digital_ebook_2', 'keyword', 'all', 'ebook', 'e-book', 2.0, FALSE, 2, 2, 'E-book keyword', 'Download this e-book'),
('digital_ebook_3', 'keyword', 'all', 'ebook', 'pdf guide', 2.0, FALSE, 2, 3, 'PDF guide', 'Free PDF guide'),
('digital_ebook_4', 'keyword', 'all', 'ebook', 'pdf report', 2.0, FALSE, 2, 4, 'PDF report keyword', 'Annual PDF report'),
('digital_template_1', 'keyword', 'all', 'template', 'template', 2.0, FALSE, 2, 10, 'Template keyword', 'Notion template'),
('digital_template_2', 'keyword', 'all', 'template', 'canva template', 2.0, FALSE, 2, 11, 'Canva template', 'Canva social media template'),
('digital_template_3', 'keyword', 'all', 'template', 'figma template', 2.0, FALSE, 2, 12, 'Figma template', 'Figma UI kit'),
('digital_course_1', 'keyword', 'all', 'course', 'course', 2.0, FALSE, 2, 20, 'Course keyword', 'Online course'),
('digital_course_2', 'keyword', 'all', 'course', 'masterclass', 2.0, FALSE, 2, 21, 'Masterclass keyword', 'Video masterclass'),
('digital_course_3', 'keyword', 'all', 'course', 'workshop', 2.0, FALSE, 2, 22, 'Workshop keyword', 'Live workshop'),
('digital_course_4', 'keyword', 'all', 'course', 'bootcamp', 2.0, FALSE, 2, 23, 'Bootcamp keyword', '30-day bootcamp'),
('digital_saas_1', 'keyword', 'all', 'saas', 'saas', 2.0, FALSE, 2, 30, 'SaaS keyword', 'My SaaS tool'),
('digital_saas_2', 'keyword', 'all', 'saas', 'software', 2.0, FALSE, 2, 31, 'Software keyword', 'Software platform'),
('digital_saas_3', 'keyword', 'all', 'saas', 'tool', 2.0, FALSE, 1, 32, 'Tool keyword', 'AI tool'),
('digital_prompts_1', 'keyword', 'all', 'prompts', 'prompts', 2.0, FALSE, 2, 40, 'ChatGPT prompts', '500 ChatGPT prompts'),
('digital_prompts_2', 'keyword', 'all', 'prompts', 'chatgpt prompts', 2.0, FALSE, 2, 41, 'ChatGPT prompts full', 'ChatGPT prompts for marketers'),

-- PRICE SIGNALS (positive, digital products typically use these price points)
('price_47', 'price_signal', 'all', NULL, '47', 1.0, FALSE, 1, 100, '$47 price point common for digital products', '$47, 47€, $47 one-time'),
('price_97', 'price_signal', 'all', NULL, '97', 1.0, FALSE, 1, 101, '$97 price point common for digital products', '$97, 97€'),
('price_197', 'price_signal', 'all', NULL, '197', 1.0, FALSE, 1, 102, '$197 price point high-ticket digital', '$197, $197 one-time'),
('price_27', 'price_signal', 'all', NULL, '27', 1.0, FALSE, 1, 103, '$27 entry-level digital product', '$27, €27'),
('price_37', 'price_signal', 'all', NULL, '37', 1.0, FALSE, 1, 104, '$37 price point', '$37'),
('price_67', 'price_signal', 'all', NULL, '67', 1.0, FALSE, 1, 105, '$67 price point', '$67'),
('price_29', 'price_signal', 'all', NULL, '29', 1.0, FALSE, 1, 106, '$29 price point', '$29'),
('price_39', 'price_signal', 'all', NULL, '39', 1.0, FALSE, 1, 107, '$39 price point', '$39'),
('price_49', 'price_signal', 'all', NULL, '49', 1.0, FALSE, 1, 108, '$49 price point', '$49'),
('price_59', 'price_signal', 'all', NULL, '59', 1.0, FALSE, 1, 109, '$59 price point', '$59'),
('price_79', 'price_signal', 'all', NULL, '79', 1.0, FALSE, 1, 110, '$79 price point', '$79'),
('price_free', 'price_signal', 'all', NULL, 'free', 0.5, FALSE, 0, 111, 'Free digital product', 'free, free download, free ebook'),

-- DIGITAL DOMAINS (positive signal - URL contains these domains)
('domain_gumroad', 'domain', 'all', NULL, 'gumroad', 3.0, FALSE, 3, 200, 'Gumroad domain - strong digital product indicator', 'gumroad.com/l/...'),
('domain_kajabi', 'domain', 'all', NULL, 'kajabi', 3.0, FALSE, 3, 201, 'Kajabi - course platform', 'kajabi.com/...'),
('domain_teachable', 'domain', 'all', NULL, 'teachable', 3.0, FALSE, 3, 202, 'Teachable - course platform', 'teachable.com/...'),
('domain_thinkific', 'domain', 'all', NULL, 'thinkific', 3.0, FALSE, 3, 203, 'Thinkific - course platform', 'thinkific.com/...'),
('domain_podia', 'domain', 'all', NULL, 'podia', 3.0, FALSE, 3, 204, 'Podia - course platform', 'podia.com/...'),
('domain_lemonsqueezy', 'domain', 'all', NULL, 'lemonsqueezy', 3.0, FALSE, 3, 205, 'Lemon Squeezy - digital products', 'lemonsqueezy.com/...'),
('domain_paddle', 'domain', 'all', NULL, 'paddle', 2.0, FALSE, 2, 206, 'Paddle - checkout for SaaS', 'paddle.com/...'),
('domain_stripe', 'domain', 'all', NULL, 'stripe', 1.0, FALSE, 1, 207, 'Stripe - payment processor', 'checkout.stripe.com/...'),
('domain_systeme', 'domain', 'all', NULL, 'systeme', 3.0, FALSE, 3, 208, 'Systeme - funnel builder', 'systeme.io/...'),

-- PHYSICAL PRODUCTS EXCLUSIONS (negative signals - likely NOT digital)
('excl_clothing', 'keyword', 'all', 'physical', 'shirt', 1.0, TRUE, -3, 300, 'Clothing item - physical product', 'buy t-shirt, shirt design'),
('excl_apparel', 'keyword', 'all', 'physical', 'clothing', 1.0, TRUE, -3, 301, 'Clothing keyword', 'clothing brand, apparel'),
('excl_hoodie', 'keyword', 'all', 'physical', 'hoodie', 1.0, TRUE, -3, 302, 'Hoodie - physical apparel', 'custom hoodie'),
('excl_sneaker', 'keyword', 'all', 'physical', 'sneaker', 1.0, TRUE, -3, 303, 'Sneaker - physical shoes', 'sneakers for sale'),
('excl_jewelry', 'keyword', 'all', 'physical', 'jewelry', 1.0, TRUE, -3, 304, 'Jewelry - physical product', 'gold jewelry'),
('excl_food', 'keyword', 'all', 'physical', 'food', 1.0, TRUE, -3, 305, 'Food - physical consumable', 'organic food'),
('excl_supplement', 'keyword', 'all', 'physical', 'supplement', 1.0, TRUE, -3, 306, 'Supplement - physical health product', 'vitamin supplement'),
('excl_furniture', 'keyword', 'all', 'physical', 'furniture', 1.0, TRUE, -3, 307, 'Furniture - physical home item', 'buy desk, furniture'),
('excl_service', 'keyword', 'all', 'service', 'coaching', 1.0, TRUE, -2, 308, 'Coaching service - not digital product', '1-on-1 coaching'),
('excl_consulting', 'keyword', 'all', 'service', 'consulting', 1.0, TRUE, -2, 309, 'Consulting - service not product', 'marketing consulting'),
('excl_live_event', 'keyword', 'all', 'service', 'live event', 1.0, TRUE, -2, 310, 'Live event - service', 'live workshop ticket'),

-- WEIGHT CONFIGURATION (how to combine signals)
('config_min_confidence', 'weight_config', 'all', NULL, NULL, NULL, FALSE, 0, 400, 'Minimum confidence to classify as digital', '0.25 = 25% confidence required'),
('config_title_weight', 'weight_config', 'all', NULL, NULL, NULL, FALSE, 0, 401, 'Weight multiplier for title keyword matches', '2.0 = title matches worth double'),
('config_body_weight', 'weight_config', 'all', NULL, NULL, NULL, FALSE, 0, 402, 'Weight multiplier for body text matches', '1.0 = body matches worth normal'),
('config_domain_weight', 'weight_config', 'all', NULL, NULL, NULL, FALSE, 0, 403, 'Weight multiplier for domain matches', '3.0 = domain matches worth 3x'),
('config_exclusion_penalty', 'weight_config', 'all', NULL, NULL, NULL, FALSE, 0, 404, 'Confidence multiplier when exclusion keywords found', '0.3 = reduce confidence to 30%'),
('config_min_keywords', 'weight_config', 'all', NULL, NULL, NULL, FALSE, 0, 405, 'Minimum matched keywords to consider digital', '1 = at least 1 keyword must match'),
('config_normalize_max', 'weight_config', 'all', NULL, NULL, NULL, FALSE, 0, 406, 'Maximum score for normalization (divisor)', '8.0 = normalize to 0-1 by dividing by 8')
ON CONFLICT (rule_id) DO NOTHING;