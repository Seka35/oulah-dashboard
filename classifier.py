"""
Digital Product Classifier
Identifie les ads qui vendent des produits digitaux (ebooks, templates, courses, SaaS, tools, plugins)

Criteria are loaded from the database (product_criteria table) with fallback to hardcoded defaults.
Use the back-office API (/api/criteria) to modify criteria.
"""

import re
from urllib.parse import urlparse
from difflib import SequenceMatcher

# ================================================
# HARDCODEO FALLBACKS (used when DB is unavailable)
# ================================================

DEFAULT_DIGITAL_KEYWORDS = {
    # Products types
    'ebook', 'e-book', 'pdf', 'guide', 'report', 'checklist', 'cheatsheet',
    'template', 'notion', 'canva', 'figma', 'miro', 'swipe', 'bundle',
    'course', 'training', 'masterclass', 'workshop', 'bootcamp', 'tutorial',
    'saas', 'software', 'tool', 'app', 'platform', 'extension', 'plugin',
    'membership', 'subscription', 'license', 'dashboard', 'widget',
    'preset', 'lut', 'overlay', 'font', 'icon', 'mockup', 'ui kit',
    'chatgpt', 'gpt', 'prompts', 'ai tools', 'automation',
    # Business models
    'print on demand', 'pod', 'dropshipping', 'shopify', 'etsy',
    'digital download', 'instant download', 'digital product', 'digital good',
    'online course', 'online training', 'digital asset',
    # Price signals
    '47', '97', '197', '27', '37', '67', '147', '$47', '$97', '$197', '$27', '$37', '$67',
    '29', '39', '49', '59', '79', '$29', '$39', '$49', '$59', '$79',
    'free', 'freebie', 'gratis',
}

DEFAULT_DIGITAL_DOMAINS = {
    'gumroad', 'stanford', 'sendowl', 'systeme', 'kajabi', 'teachable',
    'thinkific', 'podia', 'gumroad', 'lemonsqueezy', 'paddle', 'stripe',
    'easygenerator', 'canva', 'figma', 'notion', 'loom', 'cal',
    'loom', 'run', 'app', 'tool', 'platform', 'io', 'co',
}

DEFAULT_PHYSICAL_KEYWORDS = {
    'shirt', 'clothing', 'apparel', 'hoodie', 'jacket', 'sneaker',
    'shoes', 'jewelry', 'watch', 'bag', 'handbag', 'cosmetics',
    'food', 'supplement', 'vitamin', 'cream', 'lotion',
    'furniture', 'chair', 'desk', 'lamp', 'decor', 'art',
    'service de', 'coaching', 'coaching', 'consulting', 'agency',
    'live', 'event', 'ticket', 'reservation',
}

DEFAULT_PRODUCT_CATEGORIES = {
    'ebook': ['ebook', 'e-book', 'pdf guide', 'pdf report', 'checklist', 'cheatsheet'],
    'template': ['template', 'notion template', 'canva template', 'figma template', 'miro template', 'swipe file'],
    'course': ['course', 'training', 'masterclass', 'workshop', 'bootcamp', 'tutorial', 'online course'],
    'saas': ['saas', 'software', 'tool', 'app', 'platform', 'dashboard'],
    'plugin': ['extension', 'plugin', 'addon', 'add-on'],
    'asset': ['preset', 'lut', 'overlay', 'font', 'icon', 'mockup', 'ui kit', 'digital asset'],
    'membership': ['membership', 'subscription', 'community', 'private group'],
    'prompts': ['prompts', 'chatgpt prompts', 'gpt prompts', 'ai prompts'],
    'service': ['service', 'coaching', 'consulting'],
}

DEFAULT_WEIGHTS = {
    'min_confidence': 0.25,
    'title_weight': 2.0,
    'body_weight': 1.0,
    'domain_weight': 3.0,
    'exclusion_penalty': 0.3,
    'min_keywords': 1,
    'normalize_max': 8.0,
}

# ================================================
# CACHE (reload every 5 minutes or on demand)
# ================================================

_cache = {
    'keywords': None,
    'domains': None,
    'exclusions': None,
    'price_signals': None,
    'weights': None,
    'categories': None,
    'loaded_at': 0,
}

_CACHE_TTL = 300  # 5 minutes


def _load_from_db():
    """Load all criteria from database, fallback to hardcoded defaults"""
    import time
    now = time.time()

    # Return cache if still fresh
    if _cache['loaded_at'] and (now - _cache['loaded_at']) < _CACHE_TTL:
        return

    try:
        # Use lazy import to avoid circular dependencies at module load
        from db import get_criteria_keywords, get_criteria_domains, get_criteria_price_signals, get_criteria_weights

        # Load keyword rules (positive signals)
        kw_rules = get_criteria_keywords()
        if kw_rules:
            positive_keywords = set()
            exclusion_keywords = set()
            for rule in kw_rules:
                kw = rule.get('keyword', '')
                if kw:
                    if rule.get('is_exclusion'):
                        exclusion_keywords.add(kw.lower())
                    else:
                        positive_keywords.add(kw.lower())
            _cache['keywords'] = positive_keywords
            _cache['exclusions'] = exclusion_keywords
        else:
            _cache['keywords'] = DEFAULT_DIGITAL_KEYWORDS
            _cache['exclusions'] = DEFAULT_PHYSICAL_KEYWORDS

        # Load domain rules
        domain_rules = get_criteria_domains()
        if domain_rules:
            _cache['domains'] = {r['keyword'].lower() for r in domain_rules if r.get('keyword')}
        else:
            _cache['domains'] = DEFAULT_DIGITAL_DOMAINS

        # Load price signals
        price_rules = get_criteria_price_signals()
        if price_rules:
            _cache['price_signals'] = {r['keyword'].lower() for r in price_rules if r.get('keyword')}
        else:
            _cache['price_signals'] = {'47', '97', '197', '27', '37', '67', '147',
                                       '29', '39', '49', '59', '79', 'free'}

        # Load weight configuration
        weight_rules = get_criteria_weights()
        if weight_rules:
            _cache['weights'] = weight_rules
        else:
            _cache['weights'] = DEFAULT_WEIGHTS

        # Categories from DB or default
        _cache['categories'] = DEFAULT_PRODUCT_CATEGORIES

        _cache['loaded_at'] = now

    except Exception as e:
        print(f"⚠️  Classifier DB fallback to hardcoded criteria: {e}")
        _cache['keywords'] = DEFAULT_DIGITAL_KEYWORDS
        _cache['domains'] = DEFAULT_DIGITAL_DOMAINS
        _cache['exclusions'] = DEFAULT_PHYSICAL_KEYWORDS
        _cache['price_signals'] = {'47', '97', '197', '27', '37', '67', '147',
                                    '29', '39', '49', '59', '79', 'free'}
        _cache['weights'] = DEFAULT_WEIGHTS
        _cache['categories'] = DEFAULT_PRODUCT_CATEGORIES
        _cache['loaded_at'] = now


def _get_keywords():
    if _cache['keywords'] is None:
        _load_from_db()
    return _cache['keywords'] or DEFAULT_DIGITAL_KEYWORDS


def _get_exclusions():
    if _cache['exclusions'] is None:
        _load_from_db()
    return _cache['exclusions'] or DEFAULT_PHYSICAL_KEYWORDS


def _get_domains():
    if _cache['domains'] is None:
        _load_from_db()
    return _cache['domains'] or DEFAULT_DIGITAL_DOMAINS


def _get_price_signals():
    if _cache['price_signals'] is None:
        _load_from_db()
    return _cache['price_signals'] or {'47', '97', '197', '27', '37', '67', '147', '29', '39', '49', '59', '79', 'free'}


def _get_weights():
    if _cache['weights'] is None:
        _load_from_db()
    return _cache['weights'] or DEFAULT_WEIGHTS


def _get_categories():
    if _cache['categories'] is None:
        _load_from_db()
    return _cache['categories'] or DEFAULT_PRODUCT_CATEGORIES


def reload_criteria():
    """Force reload of criteria from database (bypass cache)"""
    _cache['loaded_at'] = 0
    _load_from_db()


# ================================================
# CORE CLASSIFICATION
# ================================================

def extract_domain(url):
    """Extract domain from URL"""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '').lower()
        return domain
    except:
        return None


def _score_keywords(text, keywords_set):
    """Score how many keywords appear in text"""
    if not text:
        return 0, []
    text_lower = text.lower()
    score = 0
    matched = []
    for kw in keywords_set:
        if kw.lower() in text_lower:
            score += 1
            matched.append(kw)
    return score, matched


def is_likely_digital(url, title, body, advertiser_name):
    """Determine if ad is likely a digital product"""
    if not url and not title and not body:
        return False, None, 0.0, []

    keywords = _get_keywords()
    exclusions = _get_exclusions()
    domains = _get_domains()
    weights = _get_weights()
    price_signals = _get_price_signals()

    # Check URL domain first
    domain = extract_domain(url) if url else None
    digital_domain_signal = 0
    if domain:
        for dd in domains:
            if dd in domain:
                digital_domain_signal = weights.get('domain_weight', 3.0) * 0.1
                break

    # Score title
    title_score, title_matched = _score_keywords(title, keywords)

    # Score body
    body_score, body_matched = _score_keywords(body, keywords)

    # Score advertiser name
    adv_score, adv_matched = _score_keywords(advertiser_name, keywords)

    # Check for physical/service exclusion
    all_text = f"{title} {body} {advertiser_name}".lower()
    physical_matches = []
    for pk in exclusions:
        if pk.lower() in all_text:
            physical_matches.append(pk)

    # Combine scores with configurable weights
    title_weight = weights.get('title_weight', 2.0)
    body_weight = weights.get('body_weight', 1.0)
    normalize_max = weights.get('normalize_max', 8.0)

    total_score = (title_score * title_weight +
                   body_score * body_weight +
                   adv_score * 1.5 +
                   digital_domain_signal)

    # Normalize to 0-1
    confidence = min(total_score / normalize_max, 1.0)

    # If exclusion keywords found, apply penalty
    if physical_matches:
        penalty = weights.get('exclusion_penalty', 0.3)
        confidence *= penalty

    # All matched keywords
    all_matched = list(set(title_matched + body_matched + adv_matched))

    # Determine if it's digital (configurable min_confidence and min_keywords)
    min_confidence = weights.get('min_confidence', 0.25)
    min_keywords = weights.get('min_keywords', 1)
    is_digital = confidence >= min_confidence and len(all_matched) >= min_keywords

    # Detect category
    category = detect_category(all_matched)

    return is_digital, category, confidence, all_matched


def detect_category(keywords):
    """Detect product category from matched keywords"""
    if not keywords:
        return 'unknown'

    categories = _get_categories()
    keyword_str = ' '.join(keywords).lower()

    for category, patterns in categories.items():
        for pattern in patterns:
            if pattern in keyword_str:
                return category

    return 'other'


def classify_ad(ad):
    """
    Classify a single ad.

    Args:
        ad: dict with keys: title, body_text, link_url, advertiser_name, platform

    Returns:
        dict with: is_digital_product, classification_type, confidence_score,
                 matched_keywords, url_domain, product_category
    """
    url = ad.get('link_url', '') or ad.get('ad_detail_url', '') or ''
    title = ad.get('title', '') or ad.get('body_text', '')[:200]
    body = ad.get('body_text', '') or ''
    advertiser = ad.get('advertiser_name', '') or ad.get('page_name', '')

    is_digital, category, confidence, matched = is_likely_digital(url, title, body, advertiser)

    domain = extract_domain(url)

    return {
        'is_digital_product': is_digital,
        'classification_type': category if is_digital else 'unknown',
        'confidence_score': round(confidence, 2),
        'matched_keywords': matched,
        'url_domain': domain,
        'product_category': category if is_digital else None,
    }


def classify_batch(ads):
    """Classify a batch of ads, returns list of results"""
    results = []
    for ad in ads:
        classification = classify_ad(ad)
        classification['ad_id'] = ad.get('id') or ad.get('ad_archive_id') or ad.get('tiktok_ad_id')
        classification['platform'] = ad.get('platform', 'unknown')
        results.append(classification)
    return results


if __name__ == '__main__':
    # Test with hardcoded fallback (no DB required)
    test_ads = [
        {
            'id': 'test_1',
            'title': 'Make $10K/month with this Shopify dropshipping template',
            'body_text': 'Get my complete ebook with 50+ swipe files and a Notion dashboard. Only $47.',
            'link_url': 'https://gumroad.com/l/mytemplate',
            'advertiser_name': 'Digital Products Master',
            'platform': 'facebook'
        },
        {
            'id': 'test_2',
            'title': 'Buy this t-shirt now',
            'body_text': 'Cotton t-shirt, free shipping, $29',
            'link_url': 'https://shop.com/tshirt',
            'advertiser_name': 'T-Shirt Shop',
            'platform': 'facebook'
        },
        {
            'id': 'test_3',
            'title': 'AI Prompts Bundle - 500 ChatGPT prompts for marketers',
            'body_text': 'Instant download. Get the ultimate AI prompts collection. $27 only',
            'link_url': 'https://gumroad.com/l/ai-prompts',
            'advertiser_name': 'AI Tools Co',
            'platform': 'tiktok'
        }
    ]

    for result in classify_batch(test_ads):
        print(f"\n[{result['ad_id']}] {result['platform'].upper()}")
        print(f"  Digital: {result['is_digital_product']}")
        print(f"  Category: {result['classification_type']}")
        print(f"  Confidence: {result['confidence_score']}")
        print(f"  Keywords: {result['matched_keywords']}")
        print(f"  Domain: {result['url_domain']}")