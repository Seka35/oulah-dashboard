import json
import time
import os
import tempfile
from app.config import Config


class MetaAPI:
    """Direct Meta Marketing API client (bypasses meta-ads CLI bugs)."""

    def __init__(self, max_retries=3):
        self.access_token = Config.META_ACCESS_TOKEN
        raw_acc = Config.META_AD_ACCOUNT_ID or ""
        self.account_id = raw_acc.replace("act_", "") if raw_acc.startswith("act_") else raw_acc
        self.act_id = f"act_{self.account_id}"
        self.page_id = Config.META_PAGE_ID
        self.pixel_id = Config.META_PIXEL_ID
        self.api_version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self.max_retries = max_retries

    def _request(self, method, endpoint, **kwargs):
        import requests
        url = f"{self.base_url}/{endpoint}"
        kwargs.setdefault("params", {})
        kwargs["params"]["access_token"] = self.access_token

        for attempt in range(self.max_retries):
            try:
                resp = getattr(requests, method.lower())(url, timeout=60, **kwargs)
                if resp.status_code != 200:
                    try:
                        err = resp.json().get("error", {})
                        msg = err.get("message", resp.text)
                        code = err.get("code")
                    except Exception:
                        msg = resp.text
                        code = None
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return {"error": True, "code": code, "msg": msg}
                return resp.json()
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return {"error": True, "msg": str(e)}
        return {"error": True, "msg": "Max retries exceeded"}

    def upload_image(self, image_path):
        with open(image_path, "rb") as f:
            result = self._request(
                "POST",
                f"{self.act_id}/adimages",
                files={"file": (os.path.basename(image_path), f, "image/jpeg")},
            )
        if result.get("error"):
            return None
        images = result.get("images", {})
        for key, val in images.items():
            return val.get("hash")
        return None

    def create_campaign(self, name, objective="OUTCOME_LEADS", status="PAUSED"):
        result = self._request(
            "POST",
            f"{self.act_id}/campaigns",
            json={
                "name": name,
                "objective": objective,
                "status": status,
                "special_ad_categories": [],
                "is_adset_budget_sharing_enabled": False,
            },
        )
        return result.get("id") if not result.get("error") else None

    def create_ad_set(self, name, campaign_id, daily_budget, countries, age_min, age_max, status):
        targeting = {
            "age_min": age_min,
            "age_max": age_max,
            "genders": [0],
            "geo_locations": {"countries": countries},
        }
        result = self._request(
            "POST",
            f"{self.act_id}/adsets",
            data={
                "name": name,
                "campaign_id": campaign_id,
                "daily_budget": str(daily_budget),
                "billing_event": "IMPRESSIONS",
                "optimization_goal": "LINK_CLICKS",
                "bid_amount": "500",
                "status": status,
                "dsa_beneficiary": "NONE",
                "dsa_payor": "NONE",
                "targeting": json.dumps(targeting),
            },
        )
        return result.get("id") if not result.get("error") else None

    def create_ad_creative(self, name, image_hash, primary_text, headline, link, status):
        result = self._request(
            "POST",
            f"{self.act_id}/adcreatives",
            params={
                "name": name,
                "object_story_spec": json.dumps({
                    "link_data": {
                        "image_hash": image_hash,
                        "link": link,
                        "message": primary_text,
                        "name": headline,
                        "call_to_action": {"type": "LEARN_MORE", "value": {"link": link}},
                    },
                    "page_id": self.page_id,
                }),
                "status": status,
            },
        )
        return result.get("id") if not result.get("error") else None

    def create_ad(self, name, adset_id, creative_id, status):
        result = self._request(
            "POST",
            f"{self.act_id}/ads",
            params={
                "name": name,
                "adset_id": adset_id,
                "creative": json.dumps({"creative_id": creative_id}),
                "status": status,
            },
        )
        return result.get("id") if not result.get("error") else None


class MetaCLI:
    def __init__(self, max_retries=3):
        self.account_id = Config.META_AD_ACCOUNT_ID
        self.access_token = Config.META_ACCESS_TOKEN
        self.max_retries = max_retries

    def create_campaign(self, row, creative_url, dry_run=False):
        """Create campaign + adset + ad via direct API calls."""
        status = row.get("status", "PAUSED")
        if status == "DRAFT":
            status = "PAUSED"

        countries = row.get("countries", "FR")
        if isinstance(countries, str):
            countries = [c.strip() for c in countries.replace(",", " ").split() if c.strip()]

        api = MetaAPI(max_retries=self.max_retries)

        if dry_run:
            return {"id": "dry_run_id", "status": "dry_run"}

        # 1. Create campaign
        campaign_id = api.create_campaign(row["name"], row.get("objective", "OUTCOME_LEADS"), status)
        if not campaign_id:
            return {"error": True, "msg": "Failed to create campaign"}
        print(f"Campaign created: {campaign_id}")

        # 2. Create adset
        adset_id = api.create_ad_set(
            name=f"{row['name']} – Ad Set",
            campaign_id=campaign_id,
            daily_budget=row.get("budget", 5000),
            countries=countries,
            age_min=row.get("age_min", 18),
            age_max=row.get("age_max", 65),
            status=status,
        )
        if not adset_id:
            return {"error": True, "msg": "Failed to create adset"}
        print(f"AdSet created: {adset_id}")

        # 3. Upload image + create creative + create ad
        if creative_url:
            # Download from R2 if needed
            local_path = self._download_creative(creative_url)
            if local_path:
                image_hash = api.upload_image(local_path)
                if image_hash:
                    creative_id = api.create_ad_creative(
                        name=f"{row['name']} – Creative",
                        image_hash=image_hash,
                        primary_text=row.get("ad_body", ""),
                        headline=row.get("ad_title", ""),
                        link=row.get("cta_link", "https://example.com"),
                        status=status,
                    )
                    if creative_id:
                        ad_id = api.create_ad(f"{row['name']} – Ad", adset_id, creative_id, status)
                        print(f"Ad created: {ad_id}")

                # Cleanup temp file
                if local_path != creative_url:
                    try:
                        os.unlink(local_path)
                    except Exception:
                        pass

        return {"id": campaign_id}

    def _download_creative(self, url):
        if not url or not url.startswith("http"):
            return url

        import boto3
        try:
            s3 = boto3.client(
                "s3",
                endpoint_url=Config.R2_ENDPOINT,
                aws_access_key_id=Config.R2_ACCESS_KEY_ID,
                aws_secret_access_key=Config.R2_SECRET_ACCESS_KEY,
                region_name="auto",
            )
            parts = url.replace(Config.R2_PUBLIC_URL + "/", "").split("/")
            key = "/".join(parts)
            tmp_path = os.path.join(tempfile.gettempdir(), f"creative_{os.getpid()}_{time.time()}")
            s3.download_file(Config.R2_BUCKET, key, tmp_path)
            return tmp_path
        except Exception as e:
            print(f"[MetaCLI] Download failed: {e}")
            return None

    def delete_campaign(self, campaign_id):
        api = MetaAPI()
        return api._request("POST", campaign_id, params={"status": "DELETED"})