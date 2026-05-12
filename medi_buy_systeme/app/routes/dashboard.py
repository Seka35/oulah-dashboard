from flask import Blueprint, render_template
from app.models import Campaign
from app.services.r2 import R2Client

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    stats = Campaign.get_stats()
    last_campaigns = Campaign.fetch_all()[:10]

    r2_client = R2Client()
    try:
        creatives = r2_client.list_creatives()
    except Exception:
        creatives = []

    return render_template(
        "dashboard.html",
        stats=stats,
        last_campaigns=last_campaigns,
        creatives=creatives,
    )