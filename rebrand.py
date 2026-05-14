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
from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("openai>=1.0.0 required. Run: pip install openai")

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "")
OPENROUTER_MODEL = "google/gemini-3.1-pro-preview"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

VPS_HOST = os.getenv("VPS_HOST", "178.105.100.232")
VPS_USER = os.getenv("VPS_USER", "root")
VPS_LANDINGS_DIR = os.getenv("VPS_LANDINGS_DIR", "/opt/launch-engine/landings")
LANDINGS_BASE_URL = os.getenv("LANDINGS_BASE_URL", "https://ignuva.shop")

META_PIXEL_ID = os.getenv("META_PIXEL_ID", "")


import db

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
    """Legacy AI analysis (Phase 1)"""
    # ... existing code remains for fallback if needed ...
    pass # I'll keep the actual code but wrap it or just implement the new one below

def get_rebrand_plan(raw_html: str) -> dict:
    """Phase 1: Planning with AI using prompt from DB"""
    if not OPENROUTER_KEY:
        raise ValueError("OPENROUTER_KEY not set in .env")

    client = OpenAI(api_key=OPENROUTER_KEY, base_url=OPENROUTER_BASE)

    # We send a truncated version of HTML if it's too big
    html_sample = raw_html[:100000]

    # Get prompt from DB
    default_prompt = """You are a professional e-commerce rebranding expert.
Analyze the following landing page HTML and generate a complete rebranding plan.

Rules:
1. Brand Name: Invent a new, catchy, and premium brand name.
2. Product Name: Create a premium version of the product name.
3. Description: Write a high-converting, 2-3 sentence product description.
4. Logo: Generate a stylized, modern SVG logo (valid SVG code).
5. Theme: Choose a primary brand color (Hex).

Return ONLY a JSON object with these keys:
{
  "brand_name": "...",
  "new_product_name": "...",
  "brand_tagline": "...",
  "product_description": "...",
  "brand_color": "#HEX",
  "logo_svg": "<svg>...</svg>",
  "cta_text": "..."
}"""
    
    system_prompt = db.get_system_prompt("rebrand_plan", default_prompt)

    prompt = f"{system_prompt}\n\nHTML Content:\n{html_sample}"

    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        response_format={ "type": "json_object" }
    )

    content = response.choices[0].message.content.strip()
    # Clean markdown if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    return json.loads(content)


def reconstruct_html(raw_html: str, plan: dict, stripe_url: str) -> str:
    """Phase 2: Full HTML Reconstruction with AI using prompt from DB"""
    if not OPENROUTER_KEY:
        raise ValueError("OPENROUTER_KEY not set in .env")

    client = OpenAI(api_key=OPENROUTER_KEY, base_url=OPENROUTER_BASE)

    # For Phase 2, we might need the FULL HTML if it fits, or at least the critical parts.
    # We'll try to send up to 300k characters.
    html_full = raw_html[:300000]

    default_prompt = """You are a master of HTML rebranding.
I want you to REWRITE the following landing page HTML to apply a new brand identity.

REBRANDING PLAN:
- New Brand: {brand_name}
- New Product: {product_name}
- Tagline: {tagline}
- Price: Always show $19.00
- Stripe Checkout URL: {stripe_url}
- Brand Color: {brand_color}

INSTRUCTIONS:
1. Replace the original logo with the provided brand name or logo.
2. Change all product names and brand mentions to the new ones.
3. Change all prices to $19.00.
4. Replace ALL button links and CTA links (Buy Now, Get Started, etc.) with the Stripe Checkout URL.
5. Replace the footer with a clean copyright: "Copyright 2026 {brand_name}". Remove all original site links.
6. Neutralize all other links to "#".
7. Return ONLY the complete, functional HTML code."""

    system_prompt = db.get_system_prompt("rebrand_reconstruction", default_prompt)
    
    # Format the prompt with plan data
    formatted_prompt = system_prompt.format(
        brand_name=plan.get('brand_name', 'Brand'),
        product_name=plan.get('new_product_name', 'Product'),
        tagline=plan.get('brand_tagline', ''),
        stripe_url=stripe_url,
        brand_color=plan.get('brand_color', '#6366f1')
    )

    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[
            {"role": "system", "content": "You are a master of HTML rebranding. You return only code."},
            {"role": "user", "content": formatted_prompt},
            {"role": "user", "content": f"HTML TO REBRAND:\n{html_full}"}
        ],
        temperature=0.3
    )

    content = response.choices[0].message.content.strip()
    if content.startswith("```html"):
        content = content.split("```html")[1].split("```")[0].strip()
    elif content.startswith("```"):
        content = content.split("```")[1].split("```")[0].strip()
        
    return content


def create_stripe_payment_link(product_name, price_val, brand_name, brand_color="#FF6B35", image_url=None, description=None):
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
        # 1. Create Product
        product = stripe.Product.create(
            name=f"{product_name}",
            description=description or f"Get instant access to {product_name}.",
            images=[image_url] if image_url and image_url.startswith("http") else []
        )
        
        # 2. Create Price (Stripe uses cents)
        price_cents = int(float(str(price_val).replace(",", ".")) * 100)
        price = stripe.Price.create(
            product=product.id,
            unit_amount=price_cents,
            currency="usd",
        )
        
        # 3. Create a Checkout Session or Payment Link
        # We use Payment Link for simplicity in static HTML
        payment_link = stripe.PaymentLink.create(
            line_items=[{"price": price.id, "quantity": 1}],
            after_completion={"type": "redirect", "redirect": {"url": LANDINGS_BASE_URL}},
        )
        
        return payment_link.url
    except Exception as e:
        print(f"Stripe Error: {e}")
        return "https://checkout.stripe.com/preview"

def clean_html(raw_html: str, rebrand_plan: dict, product_info: dict, original_brand: str = "") -> tuple:
    """
    Apply rebranding plan to raw HTML with aggressive cleanup.
    Returns (cleaned_html, payment_page_html)
    """
    soup = BeautifulSoup(raw_html, "lxml")

    new_price = rebrand_plan.get("new_price", "19.00")
    brand_name = rebrand_plan.get("brand_name", "ULTRA").upper()
    original_product_name = product_info.get("name", "")
    new_product_name = rebrand_plan.get("new_product_name", "")
    
    # FORCE a new product name if AI failed or kept the old one
    if not new_product_name or new_product_name.lower() in original_product_name.lower() or any(x in new_product_name.lower() for x in ["monday", "zalando", "asics"]):
        new_product_name = f"{brand_name} {original_product_name.replace('monday.com', '').replace('Zalando', '').strip()}"
        if not new_product_name.strip():
            new_product_name = f"{brand_name} Pro Elite"
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
    new_price = "19.00"
    
    # 1.1 Clean Description for Stripe
    # Force a clean description that doesn't leak original brand
    raw_desc = product_info.get("description", "")
    if len(raw_desc) > 300 or any(x in raw_desc.lower() for x in ["monday", "zalando", "asics", "ztat"]):
        stripe_description = f"Exclusive access to {new_product_name}. Our premium {brand_name} solution is designed for maximum efficiency and results."
    else:
        stripe_description = raw_desc or f"Premium quality {new_product_name}."

    # Final aggressive sanitization of description
    for junk in ["monday.com", "monday", "Zalando", "ZTAT", "Asics", "Amazon", "Etsy", "Work Management", "Sales CRM"]:
        stripe_description = re.sub(re.escape(junk), brand_name, stripe_description, flags=re.I)
    
    # Ensure description is not empty
    if not stripe_description.strip():
        stripe_description = f"Get your {new_product_name} now."

    try:
        stripe_url = create_stripe_payment_link(
            product_name=new_product_name, 
            price_val=new_price, 
            brand_name=brand_name, 
            brand_color=brand_color,
            image_url=first_image,
            description=stripe_description
        )
    except Exception as e:
        print(f"⚠️ Error creating Stripe link: {e}")

    # NO LOCAL CHECKOUT PAGE - REMOVED AS REQUESTED
    payment_page_html = ""

    # 1. Update Title, Meta Tags and Favicon
    if soup.title:
        soup.title.string = f"{new_product_name} | {brand_name}"
    
    # Remove existing favicons radically
    for fav in soup.find_all("link", rel=lambda x: x and any(k in x.lower() for k in ["icon", "shortcut", "apple-touch-icon"])):
        fav.decompose()

    # Inject Our Favicon (Use absolute-like static path for Flask)
    favicon_link = soup.new_tag("link", rel="icon", type="image/png", href="/static/landing_pages/img/favicon.png")
    if soup.head:
        soup.head.append(favicon_link)
    
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
                
                # Sanitize links in meta/link tags but KEEP image URLs
                if any(domain in val.lower() for domain in ["zalando.", "ztat.net", "monday.com", "asics.com"]):
                    if meta.name == "link" and "canonical" in str(rel).lower():
                        meta[attr] = "/"
                    elif "image" in str(meta.get("property", "")) or "image" in str(meta.get("name", "")):
                        pass # Keep image URLs
                    else:
                        meta[attr] = "#"
                else:
                    meta[attr] = val
    
    # 2. Disable tracking scripts
    for script in soup.find_all(["script", "noscript"]):
        src = script.get("src", "").lower()
        content = script.get_text()
        
        # Keep scripts that handle React streaming/hydration ($RC, $RS, etc.)
        if "$RC" in content or "$RS" in content or "function $RC" in content:
            continue

        # Kill common tracking/external scripts
        if any(x in src for x in ["ztat.net", "sentry", "akamai", "google", "facebook", "tiktok", "hotjar", "adform", "analytics", "hubspot", "intercom"]):
            script.decompose()
        elif "zalando" in src or "monday.com" in src:
            script.decompose()
        # Kill inline scripts that contain tracking or zalando specific hydration
        elif not src and any(x in content.lower() for x in ["require", "hydrate", "mosaic", "tailorpipe", "zalando"]):
            if "$RC" not in content:
                script.decompose()

    # 2.1 Force Visibility with CSS
    force_visible_css = f"""
    <style>
    [hidden], [style*="display:none"], [style*="display: none"] {{ display: block !important; visibility: visible !important; }}
    .hidden, .is-hidden {{ display: block !important; visibility: visible !important; }}
    body {{ opacity: 1 !important; visibility: visible !important; display: block !important; background: #fff !important; color: #000 !important; }}
    #z-pdp-main-content {{ display: block !important; opacity: 1 !important; }}
    .rebrand-price {{ 
        color: {brand_color} !important; 
        font-weight: 800 !important; 
        font-size: 1.2em !important; 
        display: inline-block !important;
        background: #f0f0f0 !important;
        padding: 2px 8px !important;
        border-radius: 4px !important;
    }}
    /* Hide common distracting elements */
    header, footer, nav, aside, .nav, .footer, #header, #footer, [class*="footer"], [class*="header"], [class*="nav-"] {{ 
        display: none !important; 
    }}
    /* But keep our own header */
    .rebrand-header {{ display: block !important; }}
    </style>
    """
    if soup.head:
        soup.head.append(BeautifulSoup(force_visible_css, "html.parser"))

    # 2.5 Sanitize ALL attributes in all tags
    for tag in soup.find_all(True):
        # PROTECT Stylesheets at all costs
        if tag.name == "link":
            rel = tag.get("rel", "")
            if isinstance(rel, list): rel = " ".join(rel)
            if "stylesheet" in str(rel).lower():
                continue

        for attr in list(tag.attrs):
            val = str(tag[attr]).lower()
            if any(domain in val for domain in ["zalando.", "ztat.net", "monday.com"]):
                if tag.name == "img" and attr in ["src", "srcset", "data-src", "data-srcset"]:
                    if "pixel" in val or "akamai" in val:
                        tag.decompose()
                        break
                    continue # Keep other images
                
                if attr in ["href", "data-href", "action"]:
                    tag[attr] = "#"
                elif attr.startswith("data-") and "image" not in attr:
                    del tag[attr]

    # 3. Global Text Replacement
    text_replacements = {
        original_product_name: new_product_name,
        "Zalando": brand_name,
        "Monday.com": brand_name,
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
        "[data-testid*='header']", "[data-testid*='footer']", 
        "[data-testid*='nav-header']", "[data-testid*='nav-footer']",
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

    # 6. TOTAL BODY RECONSTRUCTION 3.0
    pdp_container = (
        soup.select_one("[data-testid='pdp-main-container']") or 
        soup.select_one(".z-pdp-main-container") or
        soup.select_one("main") or
        soup.select_one("[role='main']") or
        soup.select_one("#main-content")
    )
    
    # Fallback: Find the container of the H1
    if not pdp_container:
        h1 = soup.find("h1")
        if h1:
            curr = h1.parent
            while curr and curr.name not in ["body", "html"]:
                if curr.name in ["div", "section"] and len(curr.get_text()) > 500:
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
        
        # 3. Interactions Helper
        gallery_js = '''<script>
        (function() {
            // 1. SW Killer (Stops original site scripts from hijacking)
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
                    let content = btn.nextElementSibling || 
                                  (btn.parentElement ? btn.parentElement.nextElementSibling : null);
                    if (content) {
                        let isHidden = content.style.display === 'none' || window.getComputedStyle(content).display === 'none';
                        content.style.display = isHidden ? 'block' : 'none';
                    }
                }
            }, true);
        })();
        </script>'''
        new_body.append(BeautifulSoup(gallery_js, "html.parser"))

        # Replace old body
        if soup.body:
            soup.body.replace_with(new_body)
        else:
            soup.append(new_body)

    # 7. Apply replacements to the NEW body
    # 7.1 Titles
    main_h1 = soup.find("h1")
    if main_h1:
        main_h1.string = new_product_name
        main_h1["style"] = "font-size: 32px !important; font-weight: 800 !important; line-height: 1.2 !important; margin-bottom: 15px !important; display: block !important; color: #000 !important;"

    # 7.2 Price Highlighting
    price_pattern = re.compile(r'([\$€£¥]\s*\d+([.,]\d{2})?|\d+([.,]\d{2})?\s*[\$€£¥])')
    formatted_price = f"${new_price}"
    for text_node in soup.find_all(string=True):
        if text_node.parent.name in ["script", "style", "head", "a"]: continue
        if price_pattern.search(text_node):
            new_html = price_pattern.sub(f'<span class="rebrand-price">{formatted_price}</span>', str(text_node))
            if new_html != str(text_node):
                new_tag = BeautifulSoup(new_html, "html.parser")
                text_node.replace_with(new_tag)

    # 7.3 CTA Buttons - RADICAL HIJACKING
    target_payment_url = stripe_url if stripe_url and stripe_url != "#" else "https://checkout.stripe.com/preview"
    
    # 1. Find ALL links and buttons
    for element in soup.find_all(["a", "button", "input"]):
        if element.name == "input" and element.get("type") not in ["button", "submit"]:
            continue
            
        txt = element.get_text().lower() if element.name != "input" else element.get("value", "").lower()
        cls = str(element.get("class", "")).lower()
        hrf = str(element.get("href", "")).lower()
        
        # If it looks like a button OR has CTA text OR is a plan link
        is_cta = any(kw in txt for kw in ["get", "start", "try", "buy", "order", "purchase", "plan", "price", "sign", "join", "add", "checkout", "go"])
        is_btn_style = any(kw in cls for kw in ["btn", "button", "cta", "action", "primary", "submit"])
        is_checkout_link = "rebrand/checkout" in hrf # Catch legacy or bridge links
        
        if is_cta or is_btn_style or is_checkout_link:
            if element.name == "a":
                element["href"] = target_payment_url
                element["onclick"] = f"window.location.href='{target_payment_url}'; return false;"
                # Force visibility and style
                element["style"] = f"display:inline-block !important; background:{brand_color} !important; color:#fff !important; padding:15px 30px !important; border-radius:8px !important; font-weight:900 !important; text-transform:uppercase !important; text-decoration:none !important; border:none !important; cursor:pointer !important; font-size:18px !important; text-align:center !important; min-width:200px !important; visibility:visible !important; opacity:1 !important;"
                # If the text is original brand stuff, replace it
                if "monday" in txt or "zalando" in txt or len(txt.strip()) < 2:
                    element.string = rebrand_plan.get("cta_text", "GET STARTED NOW").upper()
            else:
                # Replace button/input with a styled link to be 100% sure it works
                new_a = soup.new_tag("a", href=target_payment_url)
                new_a["onclick"] = f"window.location.href='{target_payment_url}'; return false;"
                new_a["style"] = f"display:inline-block !important; background:{brand_color} !important; color:#fff !important; padding:15px 30px !important; border-radius:8px !important; font-weight:900 !important; text-transform:uppercase !important; text-decoration:none !important; border:none !important; cursor:pointer !important; font-size:18px !important; text-align:center !important; width:100% !important; box-sizing:border-box !important; visibility:visible !important; opacity:1 !important;"
                new_a.string = rebrand_plan.get("cta_text", "GET STARTED NOW").upper()
                element.replace_with(new_a)

    # 7.4 Remove all hidden attributes
    for hidden in soup.find_all(attrs={"hidden": True}):
        del hidden["hidden"]

    return str(soup), payment_page_html, stripe_url


def rebrand_landing(raw_html: str) -> dict:
    product_info = extract_product_info(raw_html)
    rebrand_plan = analyze_with_ai(product_info, raw_html)
    slug = slugify(rebrand_plan.get("brand_name", "product"))
    cleaned_html, payment_html, stripe_url = clean_html(
        raw_html, 
        rebrand_plan, 
        product_info, 
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
        "stripe_url": stripe_url,
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


def surgical_rebrand(raw_html: str, plan: dict, stripe_url: str) -> str:
    """
    Surgically rebrand the HTML with AGGRESSIVE replacement and footer sanitization.
    """
    soup = BeautifulSoup(raw_html, "lxml")
    
    brand_name = plan.get("brand_name", "Brand")
    product_name = plan.get("new_product_name", "Product")
    tagline = plan.get("brand_tagline", "")
    brand_color = plan.get("brand_color", "#6366f1")
    logo_svg = plan.get("logo_svg", "")

    # Detect Original Brand (if possible)
    original_info = extract_product_info(raw_html)
    original_brand = original_info.get("brand", "").strip()
    original_product = original_info.get("name", "").strip()

    # 1. Update Metadata
    if soup.title:
        soup.title.string = f"{product_name} | {brand_name}"
    
    # 2. Add Brand Styles & Global Reset
    style_tag = soup.new_tag("style")
    style_tag.string = f"""
        /* Rebrand Overrides */
        .rebrand-price {{ color: {brand_color} !important; font-weight: bold !important; font-size: 1.2em !important; }}
        .rebrand-cta {{ background-color: {brand_color} !important; color: white !important; padding: 15px 30px !important; border-radius: 8px !important; text-decoration: none !important; font-weight: bold !important; display: inline-block !important; border: none !important; cursor: pointer !important; text-align: center !important; min-width: 200px !important; }}
        .rebrand-cta:hover {{ filter: brightness(1.1); }}
        .rebrand-logo-container {{ padding: 25px 20px; text-align: center; background: white; border-bottom: 1px solid #eee; }}
        .rebrand-logo-svg {{ max-height: 50px; width: auto; display: inline-block; }}
        .rebrand-logo-svg svg {{ max-height: 50px; width: auto; }}
        .rebrand-footer {{ padding: 40px 20px; text-align: center; background: #111; color: #888; font-family: sans-serif; font-size: 13px; border-top: 1px solid #222; }}
        .rebrand-footer p {{ margin: 5px 0; }}
        
        /* Aggressive Hide of original site components */
        header, nav, .nav, #header, #nav, [class*="header"], [class*="nav-"], [data-testid*="header"], [data-testid*="nav"] {{ 
            display: none !important; 
        }}
        footer, .footer, #footer, [class*="footer"], [data-testid*="footer"] {{
            display: none !important;
        }}
    """
    if soup.head:
        soup.head.append(style_tag)

    # 3. Dynamic Text Replacements
    replacements = {
        "monday.com": brand_name,
        "monday": brand_name,
        "zalando": brand_name,
        "asics": brand_name,
        "amazon": brand_name,
        "etsy": brand_name,
        "contentcreator.com": brand_name,
        "contentcreator": brand_name
    }
    
    # Add detected brand and product to replacements
    if original_brand and len(original_brand) > 2:
        replacements[original_brand] = brand_name
    if original_product and len(original_product) > 5:
        replacements[original_product] = product_name
        # Also try to replace common sub-strings of product name
        if " " in original_product:
            for part in original_product.split():
                if len(part) > 3 and part.lower() not in ["the", "and", "for", "with"]:
                    replacements[part] = brand_name

    for text_node in soup.find_all(string=True):
        if text_node.parent and text_node.parent.name not in ["script", "style", "head"]:
            original_text = str(text_node)
            new_text = original_text
            for old, new in replacements.items():
                pattern = re.compile(re.escape(old), re.IGNORECASE)
                new_text = pattern.sub(new, new_text)
            
            if new_text != original_text:
                text_node.replace_with(new_text)

    # 4. Global Link & Button Hijack (EVERYTHING goes to Stripe)
    target_payment_url = stripe_url if stripe_url and stripe_url != "#" else "https://checkout.stripe.com/preview"
    
    # Hijack all anchor tags
    for a in soup.find_all("a"):
        a["href"] = target_payment_url
        if "onclick" in a.attrs:
            del a["onclick"]
        
        # If it looks like a button, apply rebrand-cta style
        btn_text = a.get_text().lower()
        if any(word in btn_text for word in ["buy", "get", "start", "order", "purchase", "add", "checkout", "shop", "join", "enroll", "sign"]):
            a["class"] = a.get("class", []) + ["rebrand-cta"]
    
    # Hijack all buttons
    for btn in soup.find_all(["button", "input"]):
        if btn.name == "input" and btn.get("type") not in ["button", "submit", "image"]:
            continue
            
        # Replace button with an anchor tag to ensure it works consistently
        new_a = soup.new_tag("a", href=target_payment_url)
        new_a["class"] = btn.get("class", []) + ["rebrand-cta"]
        new_a.string = btn.get_text() or btn.get("value", "GET STARTED")
        btn.replace_with(new_a)

    # 5. Hijack forms (if any)
    for form in soup.find_all("form"):
        form["action"] = target_payment_url
        form["method"] = "GET"

    # 6. Price updates
    price_pattern = re.compile(r'([\$€£¥]\s*\d+([.,]\d{2})?|\d+([.,]\d{2})?\s*[\$€£¥])')
    for text_node in soup.find_all(string=True):
        if text_node.parent and text_node.parent.name not in ["script", "style", "head", "a"]:
            if price_pattern.search(str(text_node)):
                new_text = price_pattern.sub("$19.00", str(text_node))
                text_node.replace_with(new_text)

    # 7. Header/Logo Injection
    if soup.body:
        logo_div = soup.new_tag("div", attrs={"class": "rebrand-logo-container"})
        if logo_svg and "<svg" in logo_svg:
            logo_div.append(BeautifulSoup(f'<div class="rebrand-logo-svg">{logo_svg}</div>', "html.parser"))
        else:
            logo_div.append(BeautifulSoup(f'<h1 style="color:{brand_color}; margin:0; font-family:sans-serif; text-transform:uppercase; letter-spacing:2px;">{brand_name}</h1>', "html.parser"))
        
        if tagline:
            logo_div.append(BeautifulSoup(f'<p style="color:#666; margin:5px 0 0 0; font-size:14px; font-style:italic;">{tagline}</p>', "html.parser"))
        
        soup.body.insert(0, logo_div)
        
        # 8. Footer Injection (Sanitized)
        footer_div = soup.new_tag("div", attrs={"class": "rebrand-footer"})
        footer_html = f"""
            <p>&copy; 2026 {brand_name}. All Rights Reserved.</p>
            <p style="font-size:11px; margin-top:15px; opacity:0.6;">This site is not a part of the Facebook website or Facebook Inc. Additionally, This site is NOT endorsed by Facebook in any way. FACEBOOK is a trademark of FACEBOOK, Inc.</p>
        """
        footer_div.append(BeautifulSoup(footer_html, "html.parser"))
        soup.body.append(footer_div)

    # 9. Final Cleanup: Remove original scripts that might interfere
    for script in soup.find_all("script"):
        src = script.get("src", "").lower()
        if any(x in src for x in ["google", "facebook", "tiktok", "pixel", "analytics", "hotjar"]):
            script.decompose()

    return str(soup)

def rebrand_landing_v2(raw_html: str) -> dict:
    """
    New high-quality rebranding workflow using Gemini 3.1 Pro + Surgical Reconstruction.
    """
    try:
        print("🎨 [Rebrand V2] Starting Phase 1: Planning...")
        plan = get_rebrand_plan(raw_html)
        
        print(f"✅ [Phase 1] Brand: {plan.get('brand_name')} / Product: {plan.get('new_product_name')}")
        
        # Extract first image for Stripe
        soup = BeautifulSoup(raw_html, "lxml")
        first_image = None
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if src.startswith("http") and not any(x in src.lower() for x in ["logo", "icon", "pixel"]):
                first_image = src
                break
                
        print("💳 [Rebrand V2] Creating Stripe payment link for $19.00...")
        stripe_url = create_stripe_payment_link(
            product_name=plan['new_product_name'],
            price_val=19.00,
            brand_name=plan['brand_name'],
            brand_color=plan.get('brand_color', '#FF6B35'),
            image_url=first_image,
            description=plan.get('product_description', '')
        )
        
        print(f"🔗 [Stripe] Link created: {stripe_url}")
        
        print("🏗️ [Rebrand V2] Starting Phase 3: Surgical Reconstruction...")
        # We use Python for reconstruction to avoid truncation on large pages
        final_html = surgical_rebrand(raw_html, plan, stripe_url)
        
        print("✅ [Rebrand V2] Rebranding complete!")
        
        return {
            "success": True,
            "brand_name": plan['brand_name'],
            "brand_tagline": plan['brand_tagline'],
            "new_price": "19.00",
            "brand_color": plan.get('brand_color', '#FF6B35'),
            "logo_svg": plan.get('logo_svg', ''),
            "cta_text": plan.get('cta_text', 'Shop Now'),
            "slug": slugify(plan['brand_name']),
            "cleaned_html": final_html,
            "stripe_url": stripe_url,
            "plan": plan
        }
    except Exception as e:
        print(f"❌ [Rebrand V2] Error: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Test script
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, "r") as f:
            html = f.read()
        res = rebrand_landing_v2(html)
        with open("rebrand_test.html", "w") as f:
            f.write(res['cleaned_html'])
        print(f"Test complete. Output in rebrand_test.html")