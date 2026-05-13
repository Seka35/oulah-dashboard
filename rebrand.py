"""
Rebrand Service — AI-powered landing page rebranding

Uses OpenRouter (minimax-minimax-m2) to:
1. Analyze product from scraped landing page
2. Generate a new brand name and text logo
3. Set new price
4. Clean HTML of all references to original site
5. Remove other products (keep only main product)
6. Replace payment buttons with Stripe checkout
"""
import os
import re
import json
import stripe
from bs4 import BeautifulSoup

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("openai>=1.0.0 required. Run: pip install openai")

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "")
OPENROUTER_MODEL = os.getenv("MODEL_OPENROUTER", "minimax/minimax-m2.7")
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

VPS_HOST = os.getenv("VPS_HOST", "178.105.100.232")
VPS_USER = os.getenv("VPS_USER", "root")
VPS_LANDINGS_DIR = os.getenv("VPS_LANDINGS_DIR", "/opt/launch-engine/landings")
LANDINGS_BASE_URL = os.getenv("LANDINGS_BASE_URL", "https://ignuva.shop")

META_PIXEL_ID = os.getenv("META_PIXEL_ID", "")


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9\-_]', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug


def extract_product_info(raw_html: str) -> dict:
    soup = BeautifulSoup(raw_html, "lxml")

    name = ""
    for tag in ["h1", "h2", ".product-title", ".title", "[class*=title]"]:
        el = soup.select_one(tag)
        if el and el.get_text(strip=True):
            name = el.get_text(strip=True)
            break

    price = ""
    text = soup.get_text()
    for pattern in [r'[\$€£]?\s*(\d+[.,]\d{2})', r'(\d+[.,]\d{2})\s*[\$€£]']:
        match = re.search(pattern, text)
        if match:
            price = match.group(1).replace(",", ".")
            break

    brand = ""
    brand_el = soup.select_one("[data-testid='product_title-brand-link']")
    if brand_el:
        brand = brand_el.get_text(strip=True)

    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src", "")
        if src and not any(x in src for x in ["logo", "icon", "avatar", "placeholder"]):
            images.append(src)

    return {
        "name": name[:100],
        "price": price,
        "brand": brand,
        "images": images[:10],
        "description": soup.get_text()[:500]
    }


def analyze_with_ai(product_info: dict, raw_html: str) -> dict:
    if not OPENROUTER_KEY:
        raise ValueError("OPENROUTER_KEY not set in .env")

    client = OpenAI(api_key=OPENROUTER_KEY, base_url=OPENROUTER_BASE)

    prompt = """You are an expert e-commerce rebranding AI.

Given the following product scraped from a landing page, generate a complete rebranding plan.

Product Info:
- Name: """ + product_info.get('name', 'Unknown') + """
- Current Price: """ + product_info.get('price', 'Unknown') + """
- Description: """ + product_info.get('description', '')[:300] + """

Your task:
1. Create an ORIGINAL brand name (MUST be completely different from any known brand)
2. Create a NEW product name (e.g., 'Eco-Flex Performance Trousers' instead of 'LOFOTEN OFF')
3. Create a brand tagline (short, catchy)
4. Set a NEW selling price in USD or EUR (choose a price that makes sense for dropshipping, typically 2-5x product cost)
5. Choose a brand color theme (hex code)
6. Design a TEXT-ONLY logo concept (describe it as CSS/SVG, no images)
7. Provide INSTRUCTIONS to clean the HTML: what to remove, what to keep, what to change

IMPORTANT RULES:
- The brand name MUST be unique and invented (not any real brand)
- The NEW product name should be descriptive and premium
- Remove ALL references to the original site/shop name
- Remove ALL other products shown on the page (keep only the main product)
- Remove navigation menus, footers, search bars, account links, related products sections
- Keep the product images as they are (just remove other products)
- New price should be realistic for dropshipping (usually $29-$99 range)

Return your response as a JSON object with these exact keys:
{
  "brand_name": "Your invented brand name",
  "new_product_name": "Your new product name",
  "brand_tagline": "A catchy tagline",
  "new_price": "39.99",
  "brand_color": "#FF6B35",
  "logo_text": "BRAND" or "BRAND NAME" (uppercase, simple),
  "logo_font": "Arial Black, sans-serif",
  "cta_text": "Shop Now"
}

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
    if content.startswith("```"):
        parts = content.split("```")
        content = parts[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    return json.loads(content)


def create_stripe_payment_link(product_name, price_eur, brand_name, brand_color="#FF6B35", image_url=None):
    """
    Create a Stripe Product and Price, and return a Checkout Session URL.
    Note: Requires STRIPE_SECRET_KEY in .env
    """
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        print("⚠️ STRIPE_SECRET_KEY not set")
        return None

    stripe.api_key = stripe_key
    
    try:
        # Update Stripe Account Branding to match LP color (GLOBAL SETTING)
        try:
            stripe.Account.modify(
                settings={
                    "branding": {
                        "primary_color": brand_color if brand_color.startswith("#") else "#FF6B35",
                    }
                }
            )
        except Exception as e:
            print(f"⚠️ Could not update Stripe branding: {e}")

        # 1. Create Product
        product = stripe.Product.create(
            name=f"{brand_name} - {product_name}",
            description=f"Premium product from {brand_name}",
            images=[image_url] if image_url else []
        )
        
        # 2. Create Price (Stripe uses cents)
        price_cents = int(float(str(price_eur).replace(",", ".")) * 100)
        price = stripe.Price.create(
            product=product.id,
            unit_amount=price_cents,
            currency="eur",
        )
        
        # 3. Create a Payment Link (or we could use a Session, but Link is easier for static HTML)
        # However, for a one-time checkout, a Session is more professional.
        # But since we are generating static HTML to be hosted elsewhere, 
        # a Payment Link is the ONLY way it works without a backend.
        payment_link = stripe.PaymentLink.create(
            line_items=[{"price": price.id, "quantity": 1}],
        )
        
        return payment_link.url
    except Exception as e:
        print(f"Stripe Error: {e}")
        return "https://checkout.stripe.com/preview"


def generate_payment_page(brand_name, brand_tagline, new_price, brand_color, logo_font, product_title):
    """Generate a self-contained Stripe payment page HTML."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>""" + brand_name + """ - Checkout</title>
    <script src="https://js.stripe.com/v3/"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .checkout-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
            max-width: 480px;
            width: 100%;
            overflow: hidden;
        }
        .checkout-header {
            background: """ + brand_color + """;
            padding: 30px;
            text-align: center;
        }
        .checkout-logo {
            font-family: """ + logo_font + """;
            font-size: 28px;
            font-weight: 900;
            color: white;
            text-transform: uppercase;
            letter-spacing: 4px;
            margin-bottom: 6px;
        }
        .checkout-tagline {
            color: rgba(255,255,255,0.9);
            font-size: 13px;
        }
        .checkout-body { padding: 35px; }
        .product-info { text-align: center; margin-bottom: 25px; }
        .product-name {
            font-size: 20px;
            font-weight: 600;
            color: #1a1a2e;
            margin-bottom: 8px;
        }
        .product-price {
            font-size: 44px;
            font-weight: 700;
            color: """ + brand_color + """;
        }
        .product-price small {
            font-size: 18px;
            font-weight: 400;
            color: #888;
        }
        #card-element {
            padding: 14px;
            border: 2px solid #e8e8e8;
            border-radius: 10px;
            margin-bottom: 15px;
        }
        #card-errors {
            color: #dc3545;
            font-size: 13px;
            margin-bottom: 12px;
            text-align: center;
        }
        .checkout-btn {
            width: 100%;
            padding: 16px;
            background: """ + brand_color + """;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 17px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .checkout-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.25); }
        .checkout-btn:disabled { opacity: 0.65; cursor: not-allowed; transform: none; }
        .stripe-badge {
            text-align: center;
            margin-top: 18px;
            font-size: 12px;
            color: #aaa;
        }
    </style>
</head>
<body>
    <div class="checkout-container">
        <div class="checkout-header">
            <div class="checkout-logo">""" + brand_name + """</div>
            <div class="checkout-tagline">""" + brand_tagline + """</div>
        </div>
        <div class="checkout-body">
            <div class="product-info">
                <div class="product-name">""" + product_title + """</div>
                <div class="product-price"><small>$</small>""" + new_price + """</div>
            </div>
            <form id="payment-form">
                <div id="card-element"></div>
                <div id="card-errors" role="alert"></div>
                <button type="submit" class="checkout-btn" id="submit-btn">Pay $""" + new_price + """</button>
            </form>
            <div class="stripe-badge">&#128274; Secured by Stripe</div>
        </div>
    </div>
    <script>
        var stripe = Stripe('pk_live_51T4LbaJeP02Orxhl2QNj9L7CYgbmgwCXzQJkKwezozSWObVvoQAhRNpvi1tFSwQMiqc4c5qxxvjNG07X4Uf0FmGL00hYhUuoeM');
        var elements = stripe.elements();
        var card = elements.create('card', {hidePostalCode: true});
        card.mount('#card-element');
        card.on('change', function(event) {
            var displayError = document.getElementById('card-errors');
            if (event.error) {
                displayError.textContent = event.error.message;
            } else {
                displayError.textContent = '';
            }
        });
        document.getElementById('payment-form').addEventListener('submit', function(event) {
            event.preventDefault();
            var btn = document.getElementById('submit-btn');
            btn.disabled = true;
            btn.textContent = 'Processing...';
            stripe.createToken(card).then(function(result) {
                if (result.error) {
                    document.getElementById('card-errors').textContent = result.error.message;
                    btn.disabled = false;
                    btn.textContent = 'Pay $""" + new_price + """';
                } else {
                    // In production: send result.token.id to your backend to create a charge
                    // For demo: show success after 1.5s
                    btn.textContent = 'Verifying...';
                    setTimeout(function() {
                        btn.textContent = '&#10003; Order Confirmed!';
                        btn.style.background = '#28a745';
                        document.getElementById('card-errors').style.color = '#28a745';
                        document.getElementById('card-errors').textContent = 'Payment successful! Check your email.';
                    }, 1500);
                }
            });
        });
    </script>
</body>
</html>"""
    return html


def clean_html(raw_html: str, rebrand_plan: dict, original_product_name: str, original_brand: str = "") -> tuple:
    """
    Apply rebranding plan to raw HTML with aggressive cleanup.
    Returns (cleaned_html, payment_page_html)
    """
    soup = BeautifulSoup(raw_html, "lxml")

    new_price = rebrand_plan.get("new_price", "39.99")
    brand_name = rebrand_plan.get("brand_name", "BRAND")
    new_product_name = rebrand_plan.get("new_product_name", original_product_name or "Premium Product")
    brand_color = rebrand_plan.get("brand_color", "#FF6B35")
    logo_font = rebrand_plan.get("logo_font", "Arial Black, sans-serif")
    brand_tagline = rebrand_plan.get("brand_tagline", "")

    # Get first image for Stripe
    first_image = None
    img_tags = soup.find_all("img")
    if img_tags:
        for img in img_tags:
            src = img.get("src", "")
            if src.startswith("http") and "ztat.net" in src:
                first_image = src
                break

    # 1. Create Real Stripe Checkout Link
    stripe_url = "#"
    try:
        stripe_url = create_stripe_payment_link(
            product_name=new_product_name, 
            price_eur=new_price, 
            brand_name=brand_name, 
            brand_color=brand_color,
            image_url=first_image
        )
    except Exception as e:
        print(f"⚠️ Error creating Stripe link: {e}")

    # No more fake payment page
    payment_page_html = ""

    # 1. Update Title and Meta Tags
    if soup.title:
        soup.title.string = f"{new_product_name} | {brand_name}"
    
    # 1.5 Sanitize Meta and Link tags (SEO/Social)
    for meta in soup.find_all(["meta", "link"]):
        # EXEMPT CSS from sanitization so styling works
        rel = meta.get("rel", "")
        if isinstance(rel, list): rel = " ".join(rel)
        if "stylesheet" in str(rel).lower():
            continue

        for attr in ["content", "href"]:
            if meta.has_attr(attr):
                val = str(meta[attr])
                # Replace product name and brand name in meta content
                if original_product_name and original_product_name in val:
                    val = val.replace(original_product_name, new_product_name)
                if "Zalando" in val:
                    val = val.replace("Zalando", brand_name)
                
                # Sanitize links in meta/link tags
                if any(domain in val.lower() for domain in ["zalando.", "ztat.net"]):
                    if meta.name == "link" and "canonical" in str(rel).lower():
                        meta[attr] = "/"
                    elif "og:image" in str(meta.get("property", "")) or "twitter:image" in str(meta.get("name", "")):
                        pass # Keep image URLs
                    else:
                        meta[attr] = "#"
                else:
                    meta[attr] = val
    
    # 2. Disable tracking scripts but KEEP React/Mosaic "move" scripts (critical for SSR content)
    for script in soup.find_all(["script", "noscript"]):
        src = script.get("src", "").lower()
        content = script.get_text()
        
        # Keep scripts that handle React streaming/hydration ($RC, $RS, etc.)
        if "$RC" in content or "$RS" in content or "function $RC" in content:
            continue

        # Kill common tracking/external scripts
        if any(x in src for x in ["ztat.net", "sentry", "akamai", "google", "facebook", "tiktok", "hotjar", "adform", "analytics"]):
            script.decompose()
        elif "zalando" in src:
            script.decompose()
        # Kill inline scripts that contain tracking or zalando specific hydration (not the move scripts)
        elif not src and any(x in content.lower() for x in ["require", "hydrate", "mosaic", "tailorpipe", "zalando"]):
            if "$RC" not in content:
                script.decompose()

    # 2.1 Force Visibility with CSS
    # Some SPAs hide body/content until JS runs. We force it visible.
    force_visible_css = """
    <style>
    [hidden], [style*="display:none"], [style*="display: none"] { display: block !important; visibility: visible !important; }
    .hidden, .is-hidden { display: block !important; visibility: visible !important; }
    body { opacity: 1 !important; visibility: visible !important; display: block !important; }
    #z-pdp-main-content { display: block !important; opacity: 1 !important; }
    </style>
    """
    if soup.head:
        soup.head.append(BeautifulSoup(force_visible_css, "html.parser"))

    # 2.5 Sanitize ALL attributes in all tags for Zalando/Ztat domains
    for tag in soup.find_all(True):
        # PROTECT Stylesheets at all costs
        if tag.name == "link":
            rel = tag.get("rel", "")
            if isinstance(rel, list): rel = " ".join(rel)
            if "stylesheet" in str(rel).lower():
                continue

        for attr in list(tag.attrs):
            val = str(tag[attr]).lower()
            if any(domain in val for domain in ["zalando.", "ztat.net"]):
                if tag.name == "img" and attr == "src":
                    if "pixel" in val or "akamai" in val:
                        tag.decompose()
                        break
                    continue # Keep other images
                
                if attr in ["href", "data-href", "action"]:
                    tag[attr] = "#"
                elif attr.startswith("data-"):
                    del tag[attr]

    # 3. Global Text Replacement
    text_replacements = {
        original_product_name: new_product_name,
        "Zalando": brand_name,
        "shipped by Zalando": f"shipped by {brand_name}",
        "shipped by": f"shipped by {brand_name}",
        "Sold by": f"Sold by {brand_name}",
        "Free standard delivery over €29,90": "Free Express Shipping Today",
        "30-day return policy": "Lifetime Quality Guarantee",
        "30 day return policy": "Lifetime Quality Guarantee",
        "Sell it back": "Certified Quality"
    }

    for text_node in soup.find_all(string=True):
        parent = text_node.parent
        if parent and parent.name not in ["script", "style", "head"]:
            new_text = str(text_node)
            for old, new in text_replacements.items():
                if old and old.lower() in new_text.lower():
                    # Case insensitive replacement
                    pattern = re.compile(re.escape(old), re.IGNORECASE)
                    new_text = pattern.sub(new, new_text)
            if new_text != str(text_node):
                text_node.replace_with(new_text)

    # 4. Remove unwanted components
    unwanted_selectors = [
        "header", "footer", "nav", "aside",
        "[data-testid='header']", "[data-testid='footer']", 
        "[data-testid='z-nav-header']", "[data-testid='z-nav-footer']",
        "[data-testid='assistant']", "#zalando-assistant-entrypoint",
        ".z-nav-header", ".z-nav-footer", ".z-nav-header-container", ".z-nav-footer-container",
        "[role='navigation']", "[role='banner']", "[role='contentinfo']",
        ".sidebar", ".newsletter-section", ".related-products",
        ".breadcrumb", ".breadcrumbs", "[data-testid='breadcrumbs']",
        ".social-sharing", ".share-buttons",
        ".search-input-container", "#search-input-container",
        ".z-pdp__more-from-brand", ".z-pdp__recommendations",
        ".z-pdp__more-brands", ".z-pdp__more-inspiration",
        ".z-pdp__similar-items", ".z-pdp__better-together"
    ]
    for sel in unwanted_selectors:
        for tag in soup.select(sel):
            tag.decompose()

    # 6.1 Global Interaction Fixer (Gallery + Accordions)
    gallery_js = '''<script>
    (function() {
        // 1. SW Killer
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.getRegistrations().then(regs => regs.forEach(r => r.unregister()));
        }

        // 2. Global Click Handler
        document.body.addEventListener('click', function(e) {
            let img = e.target.closest('img');
            if (img && img.src) {
                let allImgs = Array.from(document.querySelectorAll('img'));
                let hero = allImgs.find(i => i.offsetWidth > 250 || i.naturalWidth > 250) || allImgs[0];
                if (hero && hero !== img) {
                    hero.src = img.src;
                    if (img.srcset) hero.srcset = img.srcset;
                    hero.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    return;
                }
            }

            // Accordion Logic
            let btn = e.target.closest('button, [role="button"], [data-testid*="accordion"]');
            if (btn) {
                // Find content: next sibling or child or sibling of parent
                let content = btn.nextElementSibling || 
                              (btn.parentElement ? btn.parentElement.nextElementSibling : null) ||
                              document.querySelector('[data-testid*="content"]');
                
                if (content) {
                    let isHidden = content.style.display === 'none' || window.getComputedStyle(content).display === 'none';
                    content.style.display = isHidden ? 'block' : 'none';
                    content.style.height = isHidden ? 'auto' : '0px';
                    content.style.opacity = isHidden ? '1' : '0';
                }
            }
        }, true);

        // 3. Force Styles for Reconstruction
        const style = document.createElement('style');
        style.innerHTML = `
            body { background: #fff !important; margin: 0; padding: 0; }
            [data-testid="pdp-main-container"], .z-pdp-main-container { 
                max-width: 1200px !important; 
                margin: 0 auto !important; 
                padding: 20px !important;
                display: block !important;
            }
            /* Hide annoying sticky bars */
            [data-testid*="sticky"], .z-pdp-sticky-bottom { display: none !important; }
        `;
        document.head.appendChild(style);
    })();
    </script>'''

    # 6. TOTAL BODY RECONSTRUCTION 2.0 (Keep ONLY the product info + Our Helper)
    pdp_container = (
        soup.select_one("[data-testid='pdp-main-container']") or 
        soup.select_one(".z-pdp-main-container") or
        soup.select_one("main") or
        soup.select_one("[role='main']")
    )
    
    # Fallback: Find the container of the H1
    if not pdp_container:
        h1 = soup.find("h1")
        if h1:
            curr = h1.parent
            while curr and curr.name not in ["body", "html"]:
                if curr.name in ["div", "section"] and len(curr.get_text()) > 1000:
                    pdp_container = curr
                    break
                curr = curr.parent

    if pdp_container:
        # Create a new clean body
        new_body = soup.new_tag("body")
        
        # 1. Logo
        logo_html = f"""
        <div class="rebrand-header" style="text-align:center;padding:30px 20px;background:#fff;border-bottom:1px solid #eee;box-shadow:0 2px 10px rgba(0,0,0,0.05);margin-bottom:20px;">
            <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@900&display=swap" rel="stylesheet">
            <a href="/" style="font-family:'Montserrat', sans-serif;font-size:32px;font-weight:900;color:{brand_color};text-transform:uppercase;letter-spacing:4px;text-decoration:none;display:inline-block;border:4px solid {brand_color};padding:10px 25px;">{brand_name}</a>
            <div style="margin-top:10px;font-family:'Montserrat', sans-serif;font-size:12px;color:#666;letter-spacing:2px;text-transform:uppercase;">{rebrand_plan.get('brand_tagline', '')}</div>
        </div>
        """
        new_body.append(BeautifulSoup(logo_html, "html.parser"))
        
        # 2. Product
        new_body.append(pdp_container)
        
        # 3. Interactions Helper (Gallery + Accordions)
        new_body.append(BeautifulSoup(gallery_js, "html.parser"))

        # Replace old body
        if soup.body:
            soup.body.replace_with(new_body)
        else:
            soup.append(new_body)

    # 7. Apply replacements to the NEW body
    # 7.1 Titles and Links (DIRECT REPLACE + STYLE ENFORCEMENT)
    main_h1 = soup.find("h1")
    if main_h1:
        main_h1.string = new_product_name
        # Keep original font but enforce size and weight
        main_h1["style"] = "font-size: 32px !important; font-weight: 800 !important; line-height: 1.2 !important; margin-bottom: 15px !important; display: block !important; color: #000 !important;"

    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        testid = str(a.get("data-testid", "")).lower()
        if "product_title" in testid or "brand-link" in testid:
            a.string = brand_name
            a["href"] = "javascript:void(0)"
            a["style"] = f"color: {brand_color}; font-weight: bold; text-decoration: none;"
        elif not any(p in href for p in ["stripe", "checkout", "payment"]):
            a["href"] = "javascript:void(0)"

    # 7.2 Prices and Brand Mentions
    price_re = re.compile(r'[\$€£¥]?\s*\d+[.,]\d{2}|\d+[.,]\d{2}\s*[\$€£¥]')
    formatted_price = f"{new_price}€"
    for text_node in soup.find_all(string=True):
        parent = text_node.parent
        if parent and parent.name not in ["script", "style", "head", "title"]:
            old_text = str(text_node)
            new_text = old_text
            if price_re.search(new_text):
                if len(new_text.strip()) < 40:
                    new_text = price_re.sub(formatted_price, new_text)
            new_text = re.sub(r'Zalando', brand_name, new_text, flags=re.IGNORECASE)
            if original_brand and len(original_brand) > 2:
                new_text = re.sub(re.escape(original_brand), brand_name, new_text, flags=re.IGNORECASE)
            if "sold by" in new_text.lower() or "shipped by" in new_text.lower():
                if len(new_text.strip()) < 100:
                    new_text = f"Sold and Shipped by {brand_name}"
            if new_text != old_text:
                text_node.replace_with(new_text)

    # 7.3 CTA Buttons
    cta_keywords = ["add to", "buy", "order", "purchase", "bag", "cart", "checkout"]
    for btn in soup.find_all(["button", "a"]):
        txt = btn.get_text().lower()
        if any(kw in txt for kw in cta_keywords):
            btn["href"] = stripe_url
            btn["style"] = f"background-color: {brand_color} !important; color: white !important; font-weight: bold; text-transform: uppercase; padding: 15px 30px; border-radius: 5px; display: inline-block; text-decoration: none; border: none; cursor: pointer; text-align: center; width: 100%; box-sizing: border-box; font-size: 18px;"
            btn.string = rebrand_plan.get("cta_text", "BUY NOW")
            if btn.name == "button":
                btn.name = "a"

    # 7.4 Remove all hidden attributes
    for hidden in soup.find_all(attrs={"hidden": True}):
        del hidden["hidden"]

    return str(soup), payment_page_html


def rebrand_landing(raw_html: str) -> dict:
    product_info = extract_product_info(raw_html)
    rebrand_plan = analyze_with_ai(product_info, raw_html)
    slug = slugify(rebrand_plan.get("brand_name", "product"))
    cleaned_html, payment_html = clean_html(
        raw_html, 
        rebrand_plan, 
        product_info.get("name", ""), 
        product_info.get("brand", "")
    )

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
        "payment_html": payment_html,
        "product_info": product_info
    }


def publish_to_vps(slug: str, html_content: str, payment_html: str = None, assets_local_path: str = None) -> dict:
    import subprocess
    import shutil
    from pathlib import Path
    import tempfile

    VPS_SSH_KEY = os.getenv("VPS_SSH_KEY", os.path.expanduser("~/.ssh/id_rsa"))

    temp_dir = Path(tempfile.mkdtemp(prefix="landing_"))
    slug_dir = temp_dir / slug
    slug_dir.mkdir(exist_ok=True)

    try:
        index_path = slug_dir / "index.html"
        index_path.write_text(html_content, encoding="utf-8")

        if payment_html:
            checkout_path = slug_dir / "checkout.html"
            checkout_path.write_text(payment_html, encoding="utf-8")

        if assets_local_path and os.path.exists(assets_local_path):
            assets_dest = slug_dir / "assets"
            if assets_dest.exists():
                shutil.rmtree(assets_dest)
            shutil.copytree(assets_local_path, assets_dest)

        ssh_cmd = "ssh -i " + VPS_SSH_KEY + " -o StrictHostKeyChecking=no"
        rsync_cmd = [
            "rsync", "-avz", "-e", ssh_cmd,
            str(slug_dir) + "/",
            VPS_USER + "@" + VPS_HOST + ":" + VPS_LANDINGS_DIR + "/" + slug + "/"
        ]

        result = subprocess.run(rsync_cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            return {"success": False, "url": "", "error": result.stderr}

        public_url = LANDINGS_BASE_URL + "/" + slug
        return {
            "success": True,
            "url": public_url,
            "slug": slug,
            "vps_path": VPS_LANDINGS_DIR + "/" + slug
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "url": "", "error": "rsync timeout (60s)"}
    except Exception as e:
        return {"success": False, "url": "", "error": str(e)}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_vps_connection() -> dict:
    import subprocess
    VPS_SSH_KEY = os.getenv("VPS_SSH_KEY", os.path.expanduser("~/.ssh/id_rsa"))

    result = subprocess.run(
        ["ssh", "-i", VPS_SSH_KEY, "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=10",
         VPS_USER + "@" + VPS_HOST, "echo ok"],
        capture_output=True, text=True, timeout=15
    )

    if result.returncode == 0 and "ok" in result.stdout:
        return {"success": True, "message": "Connected to " + VPS_HOST}
    else:
        return {"success": False, "message": result.stderr or "Connection failed"}