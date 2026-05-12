from flask import Blueprint, request, redirect, url_for, flash, jsonify
from app.models import Campaign
from app.services.campaign_launcher import CampaignLauncher

bp = Blueprint("launch", __name__, url_prefix="/launch")


@bp.route("/<int:campaign_id>", methods=["POST"])
def launch_one(campaign_id):
    campaign = Campaign.fetch_one(campaign_id)
    if not campaign:
        flash("Campaign not found", "error")
        return redirect(url_for("dashboard.index"))

    if campaign["launched"]:
        flash("Campaign already launched", "warning")
        return redirect(url_for("campaigns.index"))

    launcher = CampaignLauncher()
    result = launcher.launch(campaign)

    if result["success"]:
        flash(f"Campaign launched! Meta ID: {result['meta_campaign_id']}", "success")
    else:
        flash(f"Launch failed: {result.get('error')}", "error")

    return redirect(url_for("campaigns.index"))


@bp.route("/bulk", methods=["POST"])
def launch_bulk():
    launcher = CampaignLauncher()
    results = launcher.launch_all_pending()

    launched = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    if launched:
        flash(f"Launched {len(launched)} campaign(s)", "success")
    if failed:
        flash(f"Failed: {', '.join(r['name'] for r in failed)}", "error")

    return redirect(url_for("campaigns.index"))