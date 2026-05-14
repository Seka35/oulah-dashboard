"""
Rebrand Service — AI-powered landing page rebranding

Uses OpenRouter (minimax-minimax-m2) to:
1. Analyze product from scraped landing page
2. Generate a new brand name and text logo
3. Set new price
4. Clean HTML of all references to original site
5. Remove other products (keep only main product)
"""
import os
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("openai>=1.0.0 required. Run: pip install openai")

# OpenRouter config from .env
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "")
OPENROUTER_MODEL = os.getenv("MODEL_OPENROUTER", "minimax/minimax-m2.7")
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# VPS publishing
VPS_HOST = os.getenv("VPS_HOST", "178.105.100.232")
VPS_USER = os.getenv("VPS_USER", "root")
VPS_LANDINGS_DIR = os.getenv("VPS_LANDINGS_DIR", "/opt/launch-engine/landings")
LANDINGS_BASE_URL = os.getenv("LANDINGS_BASE_URL", "https://ignuva.shop")

# Meta Pixel ID for injection
META_PIXEL_ID = os.getenv("META_PIXEL_ID", "")


def slugify(name: str) -> str:
    """Convert product name to URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9\-_]', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug


def extract_product_info(raw_html: str) -> dict:
    """
    Extract basic product info from raw HTML (before AI analysis).
    Returns: {name, price, description, images}
    """
    soup = BeautifulSoup(raw_html, "lxml")

    # Try to find product name
    name = ""
    for tag in ["h1", "h2", ".product-title", ".title", "[class*=title]"]:
        el = soup.select_one(tag)
        if el and el.get_text(strip=True):
            name = el.get_text(strip=True)
            break

    # Try to find price
    price = ""
    price_patterns = [
        r'[\$€£]?\s*(\d+[.,]\d{2})',
        r'(\d+[.,]\d{2})\s*[\$€£]',
    ]
    text = soup.get_text()
    for pattern in price_patterns:
        match = re.search(pattern, text)
        if match:
            price = match.group(1).replace(",", ".")
            break

    # Collect images
    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src", "")
        if src and not any(x in src for x in ["logo", "icon", "avatar", "placeholder"]):
            images.append(src)

    return {
        "name": name[:100],
        "price": price,
        "images": images[:10],
        "description": soup.get_text()[:500]
    }


def analyze_with_ai(product_info: dict, raw_html: str) -> dict:
    """
    Send product info + HTML to OpenRouter AI and get rebranding plan.
    Returns: {brand_name, brand_tagline, new_price, brand_color, logo_text, instructions}
    """
    if not OPENROUTER_KEY:
        raise ValueError("OPENROUTER_KEY not set in .env")

    client = OpenAI(
        api_key=OPENROUTER_KEY,
        base_url=OPENROUTER_BASE
    )

    # Truncate HTML to avoid token limits (first 8000 chars)
    html_snippet = raw_html[:8000]

    prompt = f"""You are an expert e-commerce rebranding AI.

Given the following product scraped from a landing page, generate a complete rebranding plan.

Product Info:
- Name: {product_info.get('name', 'Unknown')}
- Current Price: {product_info.get('price', 'Unknown')}
- Description: {product_info.get('description', '')[:300]}

Your task:
1. Create an ORIGINAL brand name (MUST be completely different from any known brand)
2. Create a brand tagline (short, catchy)
3. Set a NEW selling price in USD (choose a price that makes sense for dropshipping, typically 2-5x product cost)
4. Choose a brand color theme (hex code)
5. Design a TEXT-ONLY logo concept (describe it as CSS/SVG, no images)
6. Provide INSTRUCTIONS to clean the HTML: what to remove, what to keep, what to change

IMPORTANT RULES:
- The brand name MUST be unique and invented (not any real brand)
- Remove ALL references to the original site/shop name
- Remove ALL other products shown on the page (keep only the main product)
- Remove all external links except payment links
- Keep the overall structure and design (don't redesign from scratch)
- Keep the product images as they are (just remove other products)
- New price should be realistic for dropshipping (usually $29-$99 range)

Return your response as a JSON object with these exact keys:
{{
  "brand_name": "Your invented brand name",
  "brand_tagline": "A catchy tagline",
  "new_price": "39.99",
  "brand_color": "#FF6B35",
  "logo_text": "BRAND" or "BRAND NAME" (uppercase, simple),
  "logo_font": "font-family like 'Arial Black', sans-serif",
  "remove_elements": ["selector1", "selector2"],
  "keep_elements": ["selector1", "selector2"],
  "text_replacements": {{"old_text": "new_text"}},
  "cta_text": "Shop Now"
}}

Return ONLY the JSON, no markdown, no explanation."""

    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[
            {"role": "system", "content": "You are a rebranding expert AI."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1500
    )

    content = response.choices[0].message.content.strip()

    # Clean up potential markdown code blocks
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    return json.loads(content)


def clean_html(raw_html: str, rebrand_plan: dict, product_name: str) -> str:
    """
    Apply rebranding plan to raw HTML.
    - Remove tracking scripts (hotjar, intercom, crisp, tawk, etc.)
    - Remove external links except payment
    - Remove other products
    - Update price
    - Inject logo (text-based CSS)
    - Inject Meta Pixel
    """
    soup = BeautifulSoup(raw_html, "lxml")

    # 1. Remove tracking scripts
    trackers = ["hotjar", "intercom", "crisp", "tawk", "drift", "zendesk", "smartsupp"]
    for script in soup.find_all("script", src=True):
        src = script.get("src", "")
        if any(t in src.lower() for t in trackers):
            script.decompose()

    # 2. Remove external links (make them # or remove)
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http") and "ignuva.shop" not in href:
            # Check if it's a payment link
            if any(p in href for p in ["stripe", "paypal", "checkout", "payment"]):
                continue
            # Keep internal or make relative
            if href.startswith("http"):
                a["href"] = "#"

    # 3. Remove elements marked for removal
    for selector in rebrand_plan.get("remove_elements", []):
        try:
            for el in soup.select(selector):
                el.decompose()
        except Exception:
            pass

    # 4. Apply text replacements
    for old, new in rebrand_plan.get("text_replacements", {}).items():
        for text in soup.find_all(string=True):
            if old in text:
                text.replace_with(text.replace(old, new))

    # 5. Update price elements
    new_price = rebrand_plan.get("new_price", "")
    if new_price:
        for el in soup.find_all(class_=lambda c: c and "price" in c.lower()):
            el.string = f"${new_price}"
        # Also search for price patterns in text
        for text in soup.find_all(string=True):
            if re.match(r'[\$€£]?\s*\d+[.,]\d{2}', text):
                new_text = re.sub(r'[\$€£]?\s*\d+[.,]\d{2}', f"${new_price}", text)
                text.replace_with(new_text)

    # 6. Create and inject text logo
    logo_text = rebrand_plan.get("logo_text", "BRAND")
    logo_font = rebrand_plan.get("logo_font", "Arial Black, sans-serif")
    brand_color = rebrand_plan.get("brand_color", "#FF6B35")

    logo_html = f"""
    <style>
    .ignuva-logo {{
        font-family: {logo_font};
        font-size: 28px;
        font-weight: 900;
        color: {brand_color};
        text-transform: uppercase;
        letter-spacing: 3px;
        text-decoration: none;
        display: inline-block;
    }}
    </style>
    <a href="/" class="ignuva-logo">{logo_text}</a>
    """

    # Find header/nav and inject logo
    header = soup.find("header") or soup.find("nav") or soup.find("body")
    if header:
        logo_tag = BeautifulSoup(logo_html, "html.parser")
        header.insert(0, logo_tag)

    # 7. Update CTA buttons
    cta_text = rebrand_plan.get("cta_text", "Shop Now")
    for btn in soup.find_all(["button", "a"], class_=lambda c: c and "btn" in c.lower()):
        if btn.string and len(btn.get_text(strip=True)) < 30:
            btn.string = cta_text
        # Also check data attributes
        if btn.name == "a" and btn.get("href"):
            if not any(x in btn["href"] for x in ["stripe", "paypal", "checkout"]):
                btn["href"] = "#"

    # 8. Inject Meta Pixel
    if META_PIXEL_ID:
        pixel_script = f"""
        <script>
        !function(f,b,e,v,n,t,s)
        {{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
        n.callMethod.apply(n,arguments):n.queue.push(arguments)}};
        if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
        n.queue=[];t=b.createElement(e);t.async=!0;
        t.src=v;s=b.getElementsByTagName(e)[0];
        s.parentNode.insertBefore(t,s)}}(window, document,'script',
        'https://connect.facebook.net/en_US/fbevents.js');
        fbq('init', '{META_PIXEL_ID}');
        fbq('track', 'PageView');
        </script>
        """
        head = soup.find("head")
        if head:
            head.append(BeautifulSoup(pixel_script, "html.parser"))

    # 9. Clean up any remaining external references in src/href
    for tag in soup.find_all(lambda t: t.has_attr("src") or t.has_attr("href")):
        for attr in ["src", "href"]:
            val = tag.get(attr)
            if val and val.startswith("http") and "ignuva.shop" not in val:
                # Check if it's an image we want to keep
                if any(ext in val for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]):
                    continue
                # Remove or make relative
                if attr == "src" and not any(ext in val for ext in [".jpg", ".png", ".gif", ".svg"]):
                    tag[attr] = "#"

    # 10. Remove noscript/iframe from external sources
    for tag in soup.find_all(["noscript", "iframe"]):
        src = tag.get("src", "")
        if src and "ignuva.shop" not in src:
            tag.decompose()

    return str(soup)


def rebrand_landing(raw_html: str) -> dict:
    """
    Main entry point — rebrand a landing page.
    Returns: {
        "success": bool,
        "brand_name": str,
        "new_price": str,
        "landing_url": str (empty if not published),
        "slug": str,
        "cleaned_html": str
    }
    """
    # Step 1: Extract product info
    product_info = extract_product_info(raw_html)

    # Step 2: AI analysis and rebranding plan
    rebrand_plan = analyze_with_ai(product_info, raw_html)

    # Step 3: Apply cleaning
    slug = slugify(rebrand_plan.get("brand_name", "product"))
    cleaned_html = clean_html(raw_html, rebrand_plan, product_info.get("name", ""))

    return {
        "success": True,
        "brand_name": rebrand_plan.get("brand_name", ""),
        "brand_tagline": rebrand_plan.get("brand_tagline", ""),
        "new_price": rebrand_plan.get("new_price", ""),
        "brand_color": rebrand_plan.get("brand_color", "#FF6B35"),
        "logo_text": rebrand_plan.get("logo_text", ""),
        "cta_text": rebrand_plan.get("cta_text", "Shop Now"),
        "slug": slug,
        "cleaned_html": cleaned_html,
        "product_info": product_info
    }


def generate_preview_html(rebrand_result: dict) -> str:
    """Generate a preview HTML string to display in dashboard."""
    html = rebrand_result.get("cleaned_html", "")
    # Wrap with preview header
    preview_header = f"""
    <div style="background:#{'333'.strip()};color:white;padding:10px;margin-bottom:20px;font-family:sans-serif">
        <strong>Preview:</strong> {rebrand_result.get('brand_name', '')} | {rebrand_result.get('brand_tagline', '')} | Price: ${rebrand_result.get('new_price', '')}
    </div>
    """
    return preview_header + html