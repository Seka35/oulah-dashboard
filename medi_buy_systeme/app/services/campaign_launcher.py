from app.services.meta_cli import MetaCLI
from app.services.r2 import R2Client
from app.models import Campaign


class CampaignLauncher:
    def __init__(self, max_retries=3, dry_run=False):
        self.meta_cli = MetaCLI(max_retries=max_retries)
        self.r2_client = R2Client()
        self.dry_run = dry_run

    def launch(self, campaign_row):
        campaign_id = campaign_row.get("id")

        try:
            creative_url = None
            if campaign_row.get("creative_key"):
                creative_url = self.r2_client.get_creative_url(campaign_row["creative_key"])

            result = self.meta_cli.create_campaign(campaign_row, creative_url, dry_run=self.dry_run)

            if result.get("error"):
                return {"success": False, "error": result.get("msg")}

            meta_campaign_id = result.get("id")
            if not meta_campaign_id:
                return {"success": False, "error": "No campaign ID returned"}

            # Mark launched in DB
            if not self.dry_run:
                Campaign.mark_launched(campaign_id, str(meta_campaign_id))

            return {"success": True, "meta_campaign_id": str(meta_campaign_id)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def launch_all_pending(self):
        pending = Campaign.fetch_pending()
        results = []
        for row in pending:
            result = self.launch(row)
            results.append({"campaign_id": row["id"], "name": row["name"], **result})
        return results