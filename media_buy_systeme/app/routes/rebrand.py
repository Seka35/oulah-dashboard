from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.services.rebrand import rebrand_landing, generate_preview_html
from app.services.publisher import publish_to_vps, test_vps_connection, list_vps_landings

bp = Blueprint("rebrand", __name__, url_prefix="/rebrand")

@bp.route("/")
def index():
    """Main rebrand dashboard tab."""
    vps_status = test_vps_connection()
    vps_landings = list_vps_landings() if vps_status["success"] else {"landings": []}
    return render_template(
        "rebrand.html",
        vps_connected=vps_status["success"],
        vps_message=vps_status["message"],
        published_landings=vps_landings.get("landings", [])
    )

@bp.route("/rebrand", methods=["POST"])
def rebrand():
    """
    Rebrand a landing page from raw HTML input.
    Expects: raw_html (form field containing the HTML)
    """
    raw_html = request.form.get("raw_html", "").strip()
    publish_now = request.form.get("publish") == "1"

    if not raw_html:
        flash("No HTML provided", "danger")
        return redirect(url_for("rebrand.index"))

    try:
        result = rebrand_landing(raw_html)

        if not result.get("success"):
            flash(f"Rebranding failed: {result.get('error', 'Unknown error')}", "danger")
            return redirect(url_for("rebrand.index"))

        # Store result in session for preview
        from flask import session
        session["last_rebrand"] = {
            "brand_name": result.get("brand_name", ""),
            "brand_tagline": result.get("brand_tagline", ""),
            "new_price": result.get("new_price", ""),
            "slug": result.get("slug", ""),
            "cleaned_html": result.get("cleaned_html", ""),
            "cta_text": result.get("cta_text", "Shop Now"),
            "brand_color": result.get("brand_color", "#FF6B35")
        }

        if publish_now:
            publish_result = publish_to_vps(
                slug=result["slug"],
                html_content=result["cleaned_html"]
            )
            if publish_result["success"]:
                session["last_rebrand"]["landing_url"] = publish_result["url"]
                flash(f"✅ Published! <a href='{publish_result['url']}' target='_blank'>{publish_result['url']}</a>", "success")
            else:
                flash(f"⚠️ Rebranded but publish failed: {publish_result['error']}", "warning")

            return redirect(url_for("rebrand.preview"))

        flash(f"✅ Rebranded: {result.get('brand_name')} | Price: ${result.get('new_price')}", "success")
        return redirect(url_for("rebrand.preview"))

    except Exception as e:
        import traceback
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("rebrand.index"))

@bp.route("/preview")
def preview():
    """Preview the last rebranded page."""
    from flask import session
    last = session.get("last_rebrand")
    if not last:
        flash("No rebranded page to preview", "warning")
        return redirect(url_for("rebrand.index"))

    preview_html = generate_preview_html(last)
    return render_template(
        "rebrand_preview.html",
        brand_name=last.get("brand_name", ""),
        brand_tagline=last.get("brand_tagline", ""),
        new_price=last.get("new_price", ""),
        slug=last.get("slug", ""),
        landing_url=last.get("landing_url", ""),
        cta_text=last.get("cta_text", "Shop Now"),
        brand_color=last.get("brand_color", "#FF6B35"),
        preview_html=preview_html,
        cleaned_html=last.get("cleaned_html", "")
    )

@bp.route("/publish", methods=["POST"])
def publish():
    """Publish the last rebranded page to VPS."""
    from flask import session
    last = session.get("last_rebrand")

    if not last:
        flash("No rebranded page to publish", "warning")
        return redirect(url_for("rebrand.index"))

    slug = last.get("slug", "")
    html_content = last.get("cleaned_html", "")

    result = publish_to_vps(slug=slug, html_content=html_content)

    if result["success"]:
        last["landing_url"] = result["url"]
        flash(f"✅ Published! <a href='{result['url']}' target='_blank'>{result['url']}</a>", "success")
    else:
        flash(f"❌ Publish failed: {result['error']}", "danger")

    return redirect(url_for("rebrand.preview"))

@bp.route("/test-vps", methods=["POST"])
def test_vps():
    """Test VPS connection."""
    result = test_vps_connection()
    if result["success"]:
        flash(f"✅ {result['message']}", "success")
    else:
        flash(f"❌ VPS connection failed: {result['message']}", "danger")
    return redirect(url_for("rebrand.index"))