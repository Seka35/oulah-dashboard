from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Product, Creative, Event, Setting
import json

bp = Blueprint("dashboard", __name__)

@bp.route("/")
def index():
    stats = Product.get_stats()
    # Fetch last testing products
    testing_products = Product.fetch_all({"status": "testing"})[:5]
    # Fetch pending approvals
    pending_approvals = Product.fetch_all({"status": "draft"})
    
    is_worker_active = Setting.get("meta_tool_active", "false").lower() == "true"

    return render_template(
        "dashboard.html",
        stats=stats,
        testing_products=testing_products,
        pending_approvals=pending_approvals,
        is_worker_active=is_worker_active
    )

@bp.route("/toggle-worker", methods=["POST"])
def toggle_worker():
    current = Setting.get("meta_tool_active", "false").lower() == "true"
    new_state = "false" if current else "true"
    Setting.set("meta_tool_active", new_state)
    flash(f"Automation worker is now {'ENABLED' if new_state == 'true' else 'DISABLED'}")
    return redirect(url_for("dashboard.index"))

@bp.route("/approve-product/<product_id>", methods=["POST"])
def approve_product(product_id):
    Product.update_status(product_id, "approved")
    flash(f"Product {product_id} approved for launch")
    return redirect(url_for("dashboard.index"))

@bp.route("/product/<product_id>")
def product_detail(product_id):
    product = Product.fetch_one(product_id)
    creatives = Creative.fetch_for_product(product_id, status=None) # Fetch all
    events = Event.fetch_all({"product_id": product_id}, order_by="created_at DESC")
    
    return render_template(
        "product_detail.html",
        product=product,
        creatives=creatives,
        events=events
    )