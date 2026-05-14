from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Product, Creative

bp = Blueprint("products", __name__, url_prefix="/products")

@bp.route("")
def index():
    filters = {
        "status": request.args.get("status"),
        "niche": request.args.get("niche"),
    }
    filters = {k: v for k, v in filters.items() if v}
    products = Product.fetch_all(filters if filters else None)
    return render_template("products.html", products=products, filters=filters)

@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        data = {
            "name": request.form.get("name"),
            "sales_title": request.form.get("sales_title"),
            "niche": request.form.get("niche"),
            "lp_url": request.form.get("lp_url"),
            "testing_daily_budget": request.form.get("budget", 5),
            "status": "draft"
        }
        # In a real app we'd use a Product.create method
        # For now, let's just implement a simple insert in models.py if needed
        # Or I can just redirect back for now.
        flash("Product creation is handled by the scraper/ai, but you can approve them here.")
        return redirect(url_for("products.index"))
    
    return render_template("product_edit.html", product=None)

@bp.route("/<product_id>/delete", methods=["POST"])
def delete(product_id):
    # Product.delete(product_id)
    flash("Delete not implemented for safety")
    return redirect(url_for("products.index"))
