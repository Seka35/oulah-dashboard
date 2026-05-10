"""
Pipeline: Classify ads → Track advertisers → Create product opportunities
Run via cron or manually after ad collection
"""

import sys
import re
import hashlib
import argparse
import json
from datetime import datetime
from dotenv import load_dotenv
from psycopg2.extras import DictCursor
load_dotenv()

from classifier import classify_ad, classify_batch
from landing_page_analyzer import extract_price
from db import (
    get_connection,
    save_classification,
    update_advertiser_tracking,
    get_scaling_advertisers,
    save_product_opportunity,
    get_opportunities_needing_landing_pages,
    save_landing_page_analysis,
)

def parse_range_value(val_str):
    """Parse string like '25.0M-30.5M' or '0-1K' into min numeric value"""
    if not val_str or not isinstance(val_str, str):
        return 0
    try:
        # Extract the first number part
        match = re.search(r'([0-9.]+)([KMB]?)', val_str)
        if not match:
            return 0
        num = float(match.group(1))
        suffix = match.group(2)
        if suffix == 'K': num *= 1000
        if suffix == 'M': num *= 1000000
        if suffix == 'B': num *= 1000000000
        return num
    except:
        return 0


def safe_get(data, key, default=None):
    """Safely get a key from data, even if data is a list (takes first element)"""
    if data is None: return default
    if isinstance(data, list):
        if not data: return default
        data = data[0]
    if not isinstance(data, dict): return default
    val = data.get(key, default)
    if isinstance(val, list) and len(val) > 0 and key in ['Ad Dates', 'Ad Details', 'Ad Target Audience Size', 'snapshot', 'cards']:
        val = val[0]
    return val

def score_fb_ad(raw, config):
    """Calculate weighted score for Facebook ad based on config"""
    while isinstance(raw, list) and len(raw) > 0:
        raw = raw[0]
    
    if not isinstance(raw, dict):
        return 0

    score = 0
    snapshot = safe_get(raw, 'snapshot', {})
    cards = safe_get(snapshot, 'cards', [])
    
    for filter in config:
        if not filter.get('enabled'): continue
        field = filter['field']
        weight = filter.get('weight', 0)
        passed = False
        
        if field == 'page_not_deleted':
            passed = not snapshot.get('page_is_deleted', False)
        elif field == 'cta_type':
            target_ctas = [c.lower() for c in filter.get('values', [])]
            card_ctas = [safe_get(c, 'cta_type', '').lower() for c in cards]
            passed = any(cta in target_ctas for cta in card_ctas if cta)
        elif field == 'has_video':
            passed = any(c.get('video_hd_url') for c in cards) or snapshot.get('video_hd_url')
        elif field == 'cards_count_min':
            passed = len(cards) >= filter.get('min', 0)
        elif field == 'eu_reach_min':
            loc = safe_get(raw, 'transparency_by_location', {})
            eu = safe_get(loc, 'eu_transparency', {})
            reach = safe_get(eu, 'eu_total_reach', 0)
            passed = reach >= filter.get('min', 0)
        elif field == 'targets_eu':
            loc = safe_get(raw, 'transparency_by_location', {})
            eu = safe_get(loc, 'eu_transparency', {})
            passed = safe_get(eu, 'targets_eu', False)
        elif field == 'no_violations':
            passed = len(raw.get('violation_types', []) or []) == 0
        elif field == 'body_keywords':
            keywords = [k.lower() for k in filter.get('keywords', [])]
            body = snapshot.get('body', '')
            if isinstance(body, dict): body = body.get('text', '')
            body = str(body or '').lower()
            passed = any(k in body for k in keywords) if keywords else True
        elif field == 'title_keywords':
            keywords = [k.lower() for k in filter.get('keywords', [])]
            title = snapshot.get('title', '')
            if isinstance(title, dict): title = title.get('text', '')
            title = str(title or '').lower()
            passed = any(k in title for k in keywords) if keywords else True
        elif field == 'country_count_min':
            dist = raw.get('demographic_distribution', []) or []
            passed = len(dist) >= filter.get('min', 0)
            
        if passed:
            score += weight
    return score

def score_tt_ad(raw, config):
    """Calculate weighted score for TikTok ad based on config"""
    # Robustly ensure raw is a dictionary
    if raw is None: return 0
    while isinstance(raw, list) and len(raw) > 0:
        raw = raw[0]
    
    if not isinstance(raw, dict):
        return 0
    
    score = 0
    for filter in config:
        if not filter.get('enabled'): continue
        field = filter['field']
        weight = filter.get('weight', 0)
        passed = False
        
        if field == 'target_audience_min':
            val = parse_range_value(safe_get(raw, 'Ad Target Audience Size'))
            passed = val >= filter.get('min', 0)
        elif field == 'duration_days':
            dates = safe_get(raw, 'Ad Dates', {})
            first = safe_get(dates, 'FirstShown')
            last = safe_get(dates, 'LastShown')
            if first and last:
                try:
                    d1 = datetime.strptime(first, '%Y-%m-%d')
                    d2 = datetime.strptime(last, '%Y-%m-%d')
                    days = (d2 - d1).days
                    passed = days >= filter.get('min', 0)
                except: pass
        elif field == 'audit_status':
            details = safe_get(raw, 'Ad Details', {})
            passed = safe_get(details, 'Audit Status') == filter.get('value', 1)
        elif field == 'ad_type_video':
            details = safe_get(raw, 'Ad Details', {})
            passed = safe_get(details, 'Type') == 2
        elif field == 'impression_min':
            try:
                details = safe_get(raw, 'Ad Details', {})
                imp = int(safe_get(details, 'Impression') or 0)
                passed = imp >= filter.get('min', 0)
            except: pass
        elif field == 'target_countries':
            targets = [c.upper() for c in filter.get('values', [])]
            targeting = safe_get(raw, 'Ad Targeting', {})
            regions = [safe_get(r, 'region', '').upper() for r in safe_get(targeting, 'regions', [])]
            passed = any(c in regions for c in targets)
        elif field == 'advertiser_name_contains':
            keywords = [k.lower() for k in filter.get('keywords', [])]
            name = (safe_get(raw, 'Advertiser Name', '') or '').lower()
            passed = any(k in name for k in keywords) if keywords else True
            
        if passed:
            score += weight
    return score

def score_amazon_product(product, config):
    """Calculate weighted score for Amazon product based on config"""
    score = 0
    for filter in config:
        if not filter.get('enabled'): continue
        field = filter['field']
        weight = filter.get('weight', 0)
        passed = False
        
        if field == 'stars_min':
            passed = float(product.get('stars') or 0) >= filter.get('min', 0)
        elif field == 'reviews_min':
            passed = int(product.get('reviews_count') or 0) >= filter.get('min', 0)
        elif field == 'price_min':
            passed = float(product.get('price') or 0) >= filter.get('min', 0)
        elif field == 'price_max':
            passed = float(product.get('price') or 0) <= filter.get('max', 500000)
        elif field == 'brand_contains':
            keywords = [k.lower() for k in filter.get('keywords', [])]
            brand = (product.get('brand', '') or '').lower()
            passed = any(k in brand for k in keywords) if keywords else True
        elif field == 'title_keywords':
            keywords = [k.lower() for k in filter.get('keywords', [])]
            title = (product.get('title', '') or '').lower()
            passed = any(k in title for k in keywords) if keywords else True
        elif field == 'category_contains':
            keywords = [k.lower() for k in filter.get('keywords', [])]
            cats = ' '.join(product.get('breadCrumbs', []) or []).lower()
            passed = any(k in cats for k in keywords) if keywords else True
        elif field == 'has_description':
            passed = bool(product.get('description'))
            
        if passed:
            score += weight
    return score

def score_etsy_product(product, config):
    """Calculate weighted score for Etsy product based on config"""
    score = 0
    for filter in config:
        if not filter.get('enabled'): continue
        field = filter['field']
        weight = filter.get('weight', 0)
        passed = False
        
        if field == 'rating_min':
            passed = float(product.get('rating') or 0) >= filter.get('min', 0)
        elif field == 'reviews_min':
            passed = int(product.get('review_count') or 0) >= filter.get('min', 0)
        elif field == 'price_min':
            passed = float(product.get('price') or 0) >= filter.get('min', 0)
        elif field == 'price_max':
            passed = float(product.get('price') or 0) <= filter.get('max', 500000)
        elif field == 'shop_name_contains':
            keywords = [k.lower() for k in filter.get('keywords', [])]
            shop = (product.get('shop_name', '') or '').lower()
            passed = any(k in shop for k in keywords) if keywords else True
        elif field == 'title_keywords':
            keywords = [k.lower() for k in filter.get('keywords', [])]
            title = (product.get('title', '') or '').lower()
            passed = any(k in title for k in keywords) if keywords else True
            
        if passed:
            score += weight
    return score

def classify_existing_ads():
    """Classify all unclassified ads in the database"""
    conn = get_connection()
    cursor = conn.cursor()

    # Get Facebook ads without classification
    cursor.execute("""
        SELECT a.ad_archive_id, a.raw_json, adv.page_name, a.start_date_formatted, a.end_date_formatted
        FROM ads a
        LEFT JOIN advertisers adv ON a.page_id = adv.page_id
        LEFT JOIN digital_product_classification dc ON a.ad_archive_id = dc.ad_archive_id
        WHERE dc.id IS NULL AND a.raw_json IS NOT NULL
        LIMIT 2000
    """)

    ads_to_classify = []
    for row in cursor.fetchall():
        archive_id, raw_json, page_name, start_date, end_date = row
        if not raw_json:
            continue
        # Extract link_url from cards
        link_url = ''
        body_text = ''
        title = ''
        snapshot = raw_json.get('snapshot', {}) or {}
        cards = snapshot.get('cards', []) or []
        if cards:
            link_url = cards[0].get('linkUrl') or cards[0].get('link_url', '')
            body_text = cards[0].get('body', '') or snapshot.get('body', '')
            if isinstance(body_text, dict): body_text = body_text.get('text', '')
            title = cards[0].get('title', '') or snapshot.get('title', '')
            if isinstance(title, dict): title = title.get('text', '')

        ads_to_classify.append({
            'id': archive_id,
            'ad_archive_id': archive_id,
            'platform': 'facebook',
            'title': title,
            'body_text': body_text,
            'link_url': link_url,
            'advertiser_name': page_name,
            'first_seen': start_date,
            'last_seen': end_date,
            '_raw': raw_json,
        })

    # Get TikTok ads without classification
    cursor.execute("""
        SELECT t.ad_id, t.advertiser_name, t.ad_detail_url, t.first_shown_date, t.last_shown_date, t.raw_json
        FROM tiktok_ads t
        LEFT JOIN digital_product_classification dc ON t.ad_id = dc.tiktok_ad_id
        WHERE dc.id IS NULL AND t.raw_json IS NOT NULL
        LIMIT 2000
    """)

    for row in cursor.fetchall():
        ad_id, advertiser_name, ad_detail_url, first_shown, last_shown, raw_json = row
        if not raw_json:
            continue
        ads_to_classify.append({
            'id': ad_id,
            'tiktok_ad_id': ad_id,
            'platform': 'tiktok',
            'title': raw_json.get('Advertiser Name', ''),
            'body_text': '',
            'link_url': ad_detail_url,
            'advertiser_name': advertiser_name,
            'first_seen': first_shown,
            'last_seen': last_shown,
            '_raw': raw_json,
        })

    cursor.close()
    conn.close()

    print(f"📊 Found {len(ads_to_classify)} ads to classify")

    classified = 0
    digital_count = 0
    for ad in ads_to_classify:
        result = classify_ad(ad)
        archive_id = ad.get('ad_archive_id')
        tiktok_id = ad.get('tiktok_ad_id')

        save_classification(archive_id, tiktok_id, result)
        classified += 1
        if result['is_digital_product']:
            digital_count += 1

    print(f"✅ Classified {classified} ads, {digital_count} are digital products")
    return classified, digital_count

def update_all_advertiser_tracking():
    """Recalculate scaling metrics for all advertisers"""
    conn = get_connection()
    cursor = conn.cursor()

    # Facebook advertisers
    cursor.execute("""
        SELECT adv.page_id, adv.page_name,
               COUNT(DISTINCT a.ad_archive_id) as ad_count,
               MIN(a.start_date_formatted) as first_seen,
               MAX(a.end_date_formatted) as last_seen
        FROM advertisers adv
        JOIN ads a ON adv.page_id = a.page_id
        WHERE a.is_active = TRUE
        GROUP BY adv.page_id, adv.page_name
    """)

    fb_advertisers = cursor.fetchall()

    # TikTok advertisers
    cursor.execute("""
        SELECT advertiser_name,
               COUNT(DISTINCT ad_id) as ad_count,
               MIN(first_shown_date) as first_seen,
               MAX(last_shown_date) as last_seen
        FROM tiktok_ads
        GROUP BY advertiser_name
    """)

    tt_advertisers = cursor.fetchall()

    cursor.close()
    conn.close()

    updated = 0
    scaling = 0
    for adv in fb_advertisers:
        page_id, page_name, ad_count, first_seen, last_seen = adv
        is_scaling, score, tier = update_advertiser_tracking(
            page_id, page_name, 'facebook', ad_count, first_seen, last_seen
        )
        updated += 1
        if is_scaling:
            scaling += 1

    for adv in tt_advertisers:
        advertiser_name, ad_count, first_seen, last_seen = adv
        # Use hash of name as page_id for TikTok
        name_str = str(advertiser_name or 'Unknown')
        page_id = hashlib.md5(name_str.encode()).hexdigest()[:16]
        is_scaling, score, tier = update_advertiser_tracking(
            page_id, advertiser_name, 'tiktok', ad_count, first_seen, last_seen
        )
        updated += 1
        if is_scaling:
            scaling += 1

    print(f"✅ Updated {updated} advertisers, {scaling} are scaling")
    return updated, scaling

def create_opportunities_from_digital_ads(filters=None):
    """Create product_opportunities from classified digital ads"""
    if filters is None:
        filters = {}
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)

    # Get all digital classified ads (both Facebook and TikTok)
    cursor.execute("""
        SELECT dc.ad_archive_id, dc.tiktok_ad_id, dc.is_digital_product,
               dc.confidence_score, dc.classification_type, dc.url_domain,
               dc.matched_keywords, dc.product_category,
               a.page_id, a.raw_json, adv.page_name
        FROM digital_product_classification dc
        LEFT JOIN ads a ON dc.ad_archive_id = a.ad_archive_id
        LEFT JOIN advertisers adv ON a.page_id = adv.page_id
        LIMIT 5000
    """)
    digital_ads = cursor.fetchall()

    # Also get TikTok ads that are digital (via tiktok_ad_id)
    cursor.execute("""
        SELECT t.ad_id, t.advertiser_name, t.ad_detail_url, t.raw_json,
               t.first_shown_date, t.last_shown_date,
               dc.confidence_score, dc.classification_type, dc.url_domain
        FROM tiktok_ads t
        JOIN digital_product_classification dc ON t.ad_id = dc.tiktok_ad_id
        LIMIT 5000
    """)
    tiktok_digital = cursor.fetchall()

    cursor.close()
    conn.close()

    print(f"📊 Found {len(digital_ads)} Facebook + {len(tiktok_digital)} TikTok digital ads")

    print(f"   Found {len(digital_ads)} digital FB ads and {len(tiktok_digital)} digital TT ads")
    
    created = 0

    # Process Facebook ads
    fb_config = filters.get('facebook', [])
    for row in digital_ads:
        row = dict(row)
        archive_id = row.get('ad_archive_id')
        raw = row.get('raw_json') or {}
        
        # Calculate score based on configuration
        intel_score = score_fb_ad(raw, fb_config)
        
        if intel_score == 0:
            print(f"   [DEBUG] FB Ad {archive_id}: Score 0. Keys: {list(raw.keys())}")
        
        # Only create opportunity if score passes min threshold (default 1)
        min_score = float(filters.get('fb_min_score', 1))
        if intel_score < min_score:
            continue

        snapshot = raw.get('snapshot', {}) or {}
        cards = snapshot.get('cards', []) or []
        link_url = ''
        body_text = ''
        title = ''
        if cards:
            link_url = cards[0].get('linkUrl') or cards[0].get('link_url', '')
            body_text = cards[0].get('body', '')
            if isinstance(body_text, dict): body_text = body_text.get('text', '')
            title = cards[0].get('title', '')
            if isinstance(title, dict): title = title.get('text', '')
        if not link_url:
            link_url = raw.get('url', '')

        opp_data = {
            'product_name': row.get('classification_type', 'Digital').title(),
            'product_category': row.get('classification_type', 'other'),
            'product_description': body_text[:500] if body_text else title[:500],
            'price_text': extract_price(body_text + ' ' + title),
            'advertiser_page_id': row.get('page_id') or archive_id,
            'advertiser_name': row.get('page_name') or 'Unknown',
            'advertiser_platform': 'facebook',
            'advertiser_page_url': f"https://www.facebook.com/{row.get('page_id')}" if row.get('page_id') else '',
            'scaling_score': intel_score,
            'scaling_tier': 'high' if intel_score >= float(filters.get('high_threshold', 20)) else 'medium' if intel_score >= float(filters.get('medium_threshold', 10)) else 'low',
            'active_days': 0, 
            'ad_count': len(cards),
            'is_scaling': intel_score >= float(filters.get('scaling_threshold', 15)) or len(cards) >= int(filters.get('min_ads_scaling', 5)),
            'landing_page_url': link_url,
            'status': 'fresh_lead',
        }

        opp_id = save_product_opportunity(opp_data)
        if opp_id:
            created += 1

    # Process TikTok ads
    tt_config = filters.get('tiktok', [])
    for row in tiktok_digital:
        row = dict(row)
        ad_id = row.get('ad_id')
        raw = row.get('raw_json') or {}
        
        # Calculate score based on configuration
        intel_score = score_tt_ad(raw, tt_config)
        print(f"   [DEBUG] TT Ad {ad_id}: Score {intel_score} (Min required: {filters.get('tt_min_score', 1)})")
        
        min_score = float(filters.get('tt_min_score', 1))
        if intel_score < min_score:
            continue

        link_url = row.get('ad_detail_url', '')
        name_str = str(row.get('advertiser_name') or 'Unknown')
        page_id = hashlib.md5(name_str.encode()).hexdigest()[:16]

        opp_data = {
            'product_name': row.get('classification_type', 'Digital').title(),
            'product_category': row.get('classification_type', 'other'),
            'product_description': row.get('advertiser_name', '')[:500],
            'price_text': '',
            'advertiser_page_id': page_id,
            'advertiser_name': row.get('advertiser_name', 'Unknown'),
            'advertiser_platform': 'tiktok',
            'advertiser_page_url': link_url,
            'scaling_score': intel_score,
            'scaling_tier': 'high' if intel_score >= float(filters.get('high_threshold', 20)) else 'medium' if intel_score >= float(filters.get('medium_threshold', 10)) else 'low',
            'active_days': 0,
            'ad_count': 1, # Base count for TT
            'is_scaling': intel_score >= float(filters.get('scaling_threshold', 15)),
            'landing_page_url': link_url,
            'status': 'fresh_lead',
        }

        opp_id = save_product_opportunity(opp_data)
        if opp_id:
            created += 1

    print(f"✅ Created {created} product opportunities")
    return created

def analyze_landing_pages():
    """Scrape landing pages for opportunities that need analysis"""
    from landing_page_analyzer import analyze_landing_page

    opportunities = get_opportunities_needing_landing_pages(limit=30)
    if not opportunities:
        print("   No landing pages to analyze")
        return 0

    print(f"   Found {len(opportunities)} landing pages to analyze")
    analyzed = 0
    for opp in opportunities:
        url = opp.get('landing_page_url')
        if not url or url in ['N/A', '', 'null']:
            continue

        print(f"   🔍 {opp['advertiser_name'][:30]}... → {url[:60]}")
        result = analyze_landing_page(url, timeout=15)
        save_landing_page_analysis(opp['opportunity_id'], result)
        analyzed += 1

    print(f"   ✅ Analyzed {analyzed} landing pages")
    return analyzed

def cross_reference_amazon(filters):
    """Cross-reference product opportunities with Amazon data to validate products"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    amz_config = filters.get('amazon', [])
    
    cursor.execute("SELECT * FROM amazon_products ORDER BY stars DESC LIMIT 500")
    amazon_products = cursor.fetchall()

    cursor.execute("SELECT id, opportunity_id, advertiser_name, advertiser_page_url, scaling_score FROM product_opportunities WHERE status = 'fresh_lead'")
    opps = cursor.fetchall()

    updated = 0
    for opp in opps:
        opp_id = opp[1]
        adv_name = (opp[2] or '').lower()

        for amz in amazon_products:
            brand = (amz.get('brand') or '').lower()
            title = (amz.get('title') or '').lower()
            
            if (brand and (brand in adv_name or adv_name in brand)) or (adv_name and len(adv_name)>3 and adv_name in title):
                boost = score_amazon_product(amz, amz_config)
                if boost <= 0: continue
                
                new_score = (opp[4] or 0) + boost
                if new_score < float(filters.get('amz_min_score', 1)): continue
                
                cursor.execute("""
                    UPDATE product_opportunities
                    SET scaling_score = %s, 
                        scaling_tier = %s, 
                        is_scaling = TRUE,
                        notes = COALESCE(notes || ' | ', '') || 'Amazon validated: ' || %s || ' (' || %s || ' stars)'
                    WHERE opportunity_id = %s
                """, (new_score, 'high' if new_score >= float(filters.get('high_threshold', 20)) else 'medium', amz.get('brand') or "Amazon", str(amz.get('stars')), opp_id))
                updated += 1
                break

    cursor.close()
    conn.close()
    print(f"   ✅ Amazon cross-reference: boosted {updated} opportunities")
    return updated

def cross_reference_etsy(filters):
    """Cross-reference product opportunities with Etsy data to validate products"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    etsy_config = filters.get('etsy', [])

    cursor.execute("SELECT * FROM etsy_products ORDER BY rating DESC LIMIT 500")
    etsy_products = cursor.fetchall()

    cursor.execute("SELECT id, opportunity_id, advertiser_name, advertiser_page_url, scaling_score FROM product_opportunities WHERE status = 'fresh_lead'")
    opps = cursor.fetchall()

    updated = 0
    for opp in opps:
        opp_id = opp[1]
        adv_name = (opp[2] or '').lower()

        for etsy in etsy_products:
            shop_name = (etsy.get('shop_name') or '').lower()
            title = (etsy.get('title') or '').lower()

            if (shop_name and adv_name and (shop_name in adv_name or adv_name in shop_name)) or (adv_name and len(adv_name)>3 and adv_name in title):
                boost = score_etsy_product(etsy, etsy_config)
                if boost <= 0: continue
                
                new_score = (opp[4] or 0) + boost
                if new_score < float(filters.get('etsy_min_score', 1)): continue
                
                cursor.execute("""
                    UPDATE product_opportunities
                    SET scaling_score = %s, 
                        scaling_tier = %s, 
                        is_scaling = TRUE,
                        notes = COALESCE(notes || ' | ', '') || 'Etsy validated: ' || %s || ' (' || %s || ' rating)'
                    WHERE opportunity_id = %s
                """, (new_score, 'high' if new_score >= float(filters.get('high_threshold', 20)) else 'medium' if new_score >= float(filters.get('medium_threshold', 10)) else 'low', etsy.get('shop_name') or "Etsy", str(etsy.get('rating')), opp_id))
                updated += 1
                break

    cursor.close()
    conn.close()
    print(f"   ✅ Etsy cross-reference: boosted {updated} opportunities")
    return updated

def create_opportunities_from_amazon(filters):
    """Create product_opportunities directly from high-scoring Amazon products"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    amz_config = filters.get('amazon', [])
    min_score = float(filters.get('amz_min_score', 5))
    
    cursor.execute("SELECT * FROM amazon_products LIMIT 1000")
    products = cursor.fetchall()
    created = 0
    
    for p in products:
        score = score_amazon_product(p, amz_config)
        if score < min_score: continue
        
        opp_data = {
            'product_name': p.get('title', 'Amazon Product')[:255],
            'product_category': 'amazon_product',
            'product_description': p.get('description', '')[:500] or p.get('title', ''),
            'price_text': str(p.get('price', '')),
            'advertiser_page_id': p.get('asin', ''),
            'advertiser_name': p.get('brand', 'Unknown'),
            'advertiser_platform': 'amazon',
            'advertiser_page_url': p.get('url', ''),
            'scaling_score': score,
            'scaling_tier': 'high' if score >= float(filters.get('high_threshold', 20)) else 'medium' if score >= float(filters.get('medium_threshold', 10)) else 'low',
            'active_days': 0,
            'ad_count': 0,
            'is_scaling': score >= float(filters.get('scaling_threshold', 15)),
            'landing_page_url': p.get('url', ''),
            'status': 'fresh_lead',
        }
        if save_product_opportunity(opp_data):
            created += 1
            
    cursor.close()
    conn.close()
    print(f"   ✅ Created {created} opportunities from Amazon products")
    return created

def create_opportunities_from_etsy(filters):
    """Create product_opportunities directly from high-scoring Etsy products"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    etsy_config = filters.get('etsy', [])
    min_score = float(filters.get('etsy_min_score', 5))
    
    cursor.execute("SELECT * FROM etsy_products LIMIT 1000")
    products = cursor.fetchall()
    created = 0
    
    for p in products:
        score = score_etsy_product(p, etsy_config)
        if score < min_score: continue
        
        opp_data = {
            'product_name': p.get('title', 'Etsy Product')[:255],
            'product_category': 'etsy_product',
            'product_description': p.get('title', ''),
            'price_text': str(p.get('price', '')),
            'advertiser_page_id': p.get('listing_id', ''),
            'advertiser_name': p.get('shop_name', 'Unknown'),
            'advertiser_platform': 'etsy',
            'advertiser_page_url': p.get('url', ''),
            'scaling_score': score,
            'scaling_tier': 'high' if score >= float(filters.get('high_threshold', 20)) else 'medium' if score >= float(filters.get('medium_threshold', 10)) else 'low',
            'active_days': 0,
            'ad_count': 0,
            'is_scaling': score >= float(filters.get('scaling_threshold', 15)),
            'landing_page_url': p.get('url', ''),
            'status': 'fresh_lead',
        }
        if save_product_opportunity(opp_data):
            created += 1
            
    cursor.close()
    conn.close()
    print(f"   ✅ Created {created} opportunities from Etsy products")
    return created

def reset_opportunities():
    """Clear all product opportunities for a fresh start"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        print("🗑️ Resetting product opportunities table...")
        cursor.execute("TRUNCATE TABLE product_opportunities CASCADE")
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def run_full_pipeline(filters=None, reset=False):
    """Run the complete intelligence pipeline"""
    if filters is None:
        filters = {}
        
    print("=" * 50)
    print("🚀 Starting Digital Product Intelligence Pipeline")
    print(f"   Filters: {len(filters)} parameters active")
    print("=" * 50)

    start = datetime.now()

    if reset or filters.get('reset_data'):
        reset_opportunities()

    # Step 1: Classify ads
    print("\\n📦 Step 1: Classifying ads...")
    classified, digital = classify_existing_ads()

    # Step 2: Update advertiser tracking
    print("\\n📦 Step 2: Updating advertiser tracking...")
    updated, scaling = update_all_advertiser_tracking()

    # Step 3: Create product opportunities
    print("\\n📦 Step 3: Creating product opportunities...")
    opportunities = create_opportunities_from_digital_ads(filters)

    # Step 4: Analyze landing pages
    print("\\n📦 Step 4: Analyzing landing pages...")
    landing_pages_analyzed = analyze_landing_pages()

    # Step 5: Cross-reference with Etsy/Amazon
    print("\\n📦 Step 5: Cross-referencing and Creating standalone opportunities...")
    etsy_boosted = cross_reference_etsy(filters)
    amazon_boosted = cross_reference_amazon(filters)
    etsy_standalone = create_opportunities_from_etsy(filters)
    amazon_standalone = create_opportunities_from_amazon(filters)

    # Summary
    print("\\n" + "=" * 50)
    print("📊 PIPELINE SUMMARY")
    print("=" * 50)
    print(f"   Ads classified: {classified}")
    print(f"   Digital products found: {digital}")
    print(f"   Advertisers tracked: {updated}")
    print(f"   Advertisers scaling: {scaling}")
    print(f"   Opportunities created: {opportunities + etsy_standalone + amazon_standalone}")
    print(f"   Landing pages analyzed: {landing_pages_analyzed}")
    print(f"   Etsy validated: {etsy_boosted}")
    print(f"   Amazon validated: {amazon_boosted}")
    print(f"   Time: {(datetime.now() - start).total_seconds():.1f}s")

    print("\\n🔥 TOP SCALING ADVERTISERS:")
    top = get_scaling_advertisers(min_score=14, limit=5)
    for a in top:
        print(f"   [{a['scaling_tier'].upper()}] {a['page_name'][:40]} | Score: {a['scaling_score']} | Ads: {a['ad_count']} | Days: {a['active_days']}")

    print("\\n✅ Pipeline complete!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run intelligence pipeline with filters")
    parser.add_argument('--quick', action='store_true', help='Just classify new ads')
    parser.add_argument('--config', type=str, help='Path to JSON config file')
    parser.add_argument('--reset', action='store_true', help='Clear opportunities before running')
    
    args = parser.parse_args()

    filters = {}
    if args.config:
        try:
            with open(args.config, 'r') as f:
                filters = json.load(f)
        except Exception as e:
            print(f"❌ Error loading config file: {e}")

    if args.quick:
        classify_existing_ads()
    else:
        run_full_pipeline(filters, reset=args.reset)