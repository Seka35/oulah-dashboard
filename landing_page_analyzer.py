"""
Landing Page Analyzer
Scrapes and analyzes landing pages from ad URLs to extract:
- Hero headline, subheadline
- Main offer / pricing
- CTA text and URL
- Checkout technology (Stripe, Gumroad, etc.)
- Trust signals
"""

import re
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
load_dotenv()

import requests
from bs4 import BeautifulSoup

# Checkout platforms signatures
CHECKOUT_SIGNATURES = {
    'stripe': ['stripe', 'js.stripe.com', 'stripe.com/pay', 'checkout.stripe.com'],
    'gumroad': ['gumroad', 'gum.co', 'gumroad.com/l/', 'assets.gumroad.com'],
    'paddle': ['paddle', 'paddle.com', 'paddle.io', 'cdn.paddle.com'],
    'sendowl': ['sendowl', 'sendowl.com', 'sellfy', 'sellfy.com'],
    'woocommerce': ['woocommerce', 'wc-api', 'wp-content/plugins/woocommerce'],
    'shopify': ['shopify', 'shopify.com/checkout', 'cdn.shopify.com'],
    'systeme': ['systeme.io', 'systeme.fr'],
    'kajabi': ['kajabi', 'kajabi.com', 'cdn.kajabi.com'],
    'teachable': ['teachable', ' Teachable', 'courses.teachable.com'],
    'thinkific': ['thinkific', 'thinkific.com'],
    'podia': ['podia', 'podia.com'],
    'lemonsqueezy': ['lemonsqueezy', 'lemonsqueezy.com', 'ls.s棱'],
    'payhip': ['payhip', 'payhip.com'],
    'gumroad_embed': ['gumroad.com/embed', 'gum.co'],
}

TRUST_SIGNALS = {
    'money_back': ['money back', 'refund', '30-day guarantee', '60-day guarantee', 'satisfaction guaranteed', 'guarantee', 'risky-free', 'no questions asked'],
    'testimonials': ['testimonials', 'reviews', 'what they say', 'customer reviews', '★★★★★', '4.9/5', '4.8/5'],
    'ssl': ['ssl', 'secure', 'https://', 'encrypted'],
    'social_proof': ['10,000+ customers', '50,000+ students', 'sold', 'students', 'customers', 'people have', 'trusted by'],
    'scarcity': ['limited', 'only 3 left', 'offer ends', 'bonus expires', 'today only', 'last chance', 'final call'],
}

# Price patterns
PRICE_PATTERN = re.compile(r'[\$€£¥]\s*[\d,]+(?:\.\d{2})?|[\d,]+\s*(?:USD|EUR|GBP|\$|€|£)')
CURRENCY_MAP = {'$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY'}


def extract_domain(url):
    if not url:
        return None
    try:
        return urlparse(url).netloc.replace('www.', '').lower()
    except:
        return None


def detect_checkout_tech(html_content, url):
    """Detect which checkout platform is used"""
    url_lower = url.lower()
    html_lower = html_content.lower() if html_content else ''

    for platform, signatures in CHECKOUT_SIGNATURES.items():
        for sig in signatures:
            if sig in url_lower or sig in html_lower:
                return platform
    return 'unknown'


def extract_price(text):
    """Extract price from text, return (amount, currency, raw_text)"""
    if not text:
        return None, None, ''

    # Find price patterns
    for match in PRICE_PATTERN.finditer(text):
        raw = match.group(0)
        # Extract numeric value
        nums = re.findall(r'[\d,]+(?:\.\d+)?', raw)
        if nums:
            amount = float(nums[0].replace(',', ''))
            # Detect currency
            currency = 'USD'
            for curr, sym in CURRENCY_MAP.items():
                if sym in raw or curr in raw:
                    currency = curr
                    break
            return amount, currency, raw

    return None, None, ''


def analyze_landing_page(url, timeout=60):
    """
    Scrape and analyze a landing page URL.

    Returns dict with:
        - domain, hero_headline, hero_subheadline
        - main_offer, price_text, price_amount
        - cta_text, cta_url
        - checkout_type, technology_stack
        - trust_signals
        - full_text_content (for later analysis)
        - scrape_error
    """
    result = {
        'url': url,
        'domain': extract_domain(url),
        'hero_headline': '',
        'hero_subheadline': '',
        'main_offer': '',
        'price_text': '',
        'price_amount': None,
        'currency': 'USD',
        'cta_text': '',
        'cta_url': '',
        'checkout_type': 'unknown',
        'technology_stack': [],
        'trust_signals': [],
        'full_text_content': '',
        'html_content': '',
        'scrape_error': None,
    }

    if not url or url in ['N/A', '', 'null']:
        result['scrape_error'] = 'No URL provided'
        return result

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        html = response.text
        status_code = response.status_code

        if status_code != 200:
            result['scrape_error'] = f'HTTP {status_code}'
            return result

        result['html_content'] = html[:50000]  # Store first 50k chars

        soup = BeautifulSoup(html, 'lxml')

        # Extract all text
        text_content = soup.get_text(separator=' ', strip=True)
        result['full_text_content'] = text_content[:10000]

        # Detect checkout technology
        result['checkout_type'] = detect_checkout_tech(html, url)
        if result['checkout_type'] != 'unknown':
            result['technology_stack'].append(result['checkout_type'])

        # Find meta tags for og:title, og:description
        og_title = soup.find('meta', property='og:title')
        og_desc = soup.find('meta', property='og:description')
        title_tag = soup.find('title')

        # Hero headline: og:title > title tag > h1
        if og_title and og_title.get('content'):
            result['hero_headline'] = og_title['content'].strip()
        elif title_tag:
            result['hero_headline'] = title_tag.get_text(strip=True)
        else:
            h1 = soup.find('h1')
            if h1:
                result['hero_headline'] = h1.get_text(strip=True)[:200]

        # Hero subheadline: og:description > meta description > h2
        if og_desc and og_desc.get('content'):
            result['hero_subheadline'] = og_desc['content'].strip()
        else:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                result['hero_subheadline'] = meta_desc['content'].strip()[:200]
            else:
                h2 = soup.find('h2')
                if h2:
                    result['hero_subheadline'] = h2.get_text(strip=True)[:200]

        # Extract price from visible text
        price_amount, currency, price_text = extract_price(text_content)
        if price_amount:
            result['price_amount'] = price_amount
            result['price_text'] = price_text
            result['currency'] = currency

        # CTA: look for buttons and links with action words
        cta_patterns = ['buy now', 'get it now', 'order now', 'start now', 'get access', 'download', 'enroll', 'sign up', 'get started', 'learn more', 'try free', 'checkout', 'add to cart', 'get it', 'download now']
        buttons = soup.find_all(['button', 'a', 'input'])
        for btn in buttons:
            btn_text = (btn.get_text(strip=True) or btn.get('value', '') or '').lower()
            btn_href = btn.get('href', '') or ''

            for pattern in cta_patterns:
                if pattern in btn_text or pattern in btn_href:
                    result['cta_text'] = btn.get_text(strip=True) or pattern
                    if btn.name == 'a' and btn.get('href'):
                        result['cta_url'] = btn['href']
                    break
            if result['cta_text']:
                break

        # Also check for main CTA link
        if not result['cta_url']:
            cta_link = soup.find('a', class_=re.compile(r'btn|cta|action|purchase|buy', re.I))
            if cta_link and cta_link.get('href'):
                result['cta_url'] = cta_link['href']
                result['cta_text'] = cta_link.get_text(strip=True) or 'Get Started'

        # Trust signals
        text_lower = text_content.lower()
        detected_signals = []
        for signal_type, keywords in TRUST_SIGNALS.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    detected_signals.append(signal_type)
                    break
        result['trust_signals'] = list(set(detected_signals))

        # Extract main offer (paragraph after headline)
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            p_text = p.get_text(strip=True)
            if 30 < len(p_text) < 300 and p_text != result['hero_headline']:
                result['main_offer'] = p_text
                break

    except requests.Timeout:
        result['scrape_error'] = 'Timeout'
    except requests.RequestException as e:
        result['scrape_error'] = f'Request error: {str(e)[:50]}'
    except Exception as e:
        result['scrape_error'] = f'Parse error: {str(e)[:50]}'

    return result


def analyze_batch(urls, max_workers=5):
    """Analyze multiple landing pages"""
    import concurrent.futures

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(analyze_landing_page, url): url for url in urls if url}
        for future in concurrent.futures.as_completed(future_to_url, timeout=60):
            url = future_to_url[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({'url': url, 'scrape_error': str(e)})
    return results


if __name__ == '__main__':
    # Test with sample URLs
    test_urls = [
        'https://gumroad.com/l/digital-product',  # Gumroad
        'https://www.shopify.com',  # Shopify
    ]

    print("Testing landing page analyzer...")
    for url in test_urls:
        print(f"\n🔍 Analyzing: {url}")
        result = analyze_landing_page(url, timeout=10)
        print(f"   Domain: {result['domain']}")
        print(f"   Headline: {result['hero_headline'][:80] if result['hero_headline'] else 'N/A'}")
        print(f"   Price: {result['price_text'] or 'N/A'}")
        print(f"   Checkout: {result['checkout_type']}")
        print(f"   Error: {result['scrape_error'] or 'None'}")