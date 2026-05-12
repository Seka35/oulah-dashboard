from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Campaign
from app.services.r2 import R2Client

bp = Blueprint("campaigns", __name__, url_prefix="/campaigns")


def _get_creatives():
    try:
        r2 = R2Client()
        return r2.list_creatives()
    except Exception:
        return []


@bp.route("")
def index():
    filters = {
        "launched": request.args.get("launched"),
        "status": request.args.get("status"),
        "countries": request.args.get("countries"),
    }
    # Remove None values
    filters = {k: v for k, v in filters.items() if v}

    campaigns = Campaign.fetch_all(filters if filters else None)
    return render_template("campaigns.html", campaigns=campaigns, filters=filters)


@bp.route("/new", methods=["GET"])
def new():
    return render_template("campaign_edit.html", campaign=None, creatives=_get_creatives(), form_action="/campaigns")


@bp.route("/<int:campaign_id>", methods=["GET"])
def edit(campaign_id):
    campaign = Campaign.fetch_one(campaign_id)
    if not campaign:
        flash("Campaign not found", "error")
        return redirect(url_for("campaigns.index"))
    return render_template("campaign_edit.html", campaign=campaign, creatives=_get_creatives(), form_action=f"/campaigns/{campaign_id}")


@bp.route("", methods=["POST"])
def create():
    data = {
        "name": request.form.get("name"),
        "objective": request.form.get("objective", "OUTCOME_LEADS"),
        "budget": int(float(request.form.get("budget", 50)) * 100),
        "budget_type": request.form.get("budget_type", "DAILY"),
        "countries": request.form.get("countries", "FR"),
        "age_min": int(request.form.get("age_min", 18)),
        "age_max": int(request.form.get("age_max", 65)),
        "creative_key": request.form.get("creative_key") or None,
        "ad_title": request.form.get("ad_title") or None,
        "ad_body": request.form.get("ad_body") or None,
        "cta_link": request.form.get("cta_link") or None,
        "status": request.form.get("status", "PAUSED"),
    }
    Campaign.create(data)
    flash("Campaign created", "success")
    return redirect(url_for("campaigns.index"))


@bp.route("/<int:campaign_id>", methods=["POST"])
def update(campaign_id):
    campaign = Campaign.fetch_one(campaign_id)
    if not campaign:
        flash("Campaign not found", "error")
        return redirect(url_for("campaigns.index"))

    data = {
        "id": campaign_id,
        "name": request.form.get("name"),
        "objective": request.form.get("objective", "OUTCOME_LEADS"),
        "budget": int(float(request.form.get("budget", 50)) * 100),
        "budget_type": request.form.get("budget_type", "DAILY"),
        "countries": request.form.get("countries", "FR"),
        "age_min": int(request.form.get("age_min", 18)),
        "age_max": int(request.form.get("age_max", 65)),
        "creative_key": request.form.get("creative_key") or None,
        "ad_title": request.form.get("ad_title") or None,
        "ad_body": request.form.get("ad_body") or None,
        "cta_link": request.form.get("cta_link") or None,
        "status": request.form.get("status", "PAUSED"),
    }
    Campaign.update(campaign_id, data)
    flash("Campaign updated", "success")
    return redirect(url_for("campaigns.index"))


@bp.route("/<int:campaign_id>/delete", methods=["POST"])
def delete(campaign_id):
    Campaign.delete(campaign_id)
    flash("Campaign deleted", "success")
    return redirect(url_for("campaigns.index"))