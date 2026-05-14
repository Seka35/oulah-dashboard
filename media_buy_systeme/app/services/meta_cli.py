import json
import time
import os
import tempfile
import requests
from app.config import Config

class MetaAPI:
    """Direct Meta Marketing API client."""

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
                        error_subcode = err.get("error_subcode")
                    except Exception:
                        msg = resp.text
                        code = None
                        error_subcode = None
                    
                    print(f"[MetaAPI] Error: {msg} (code: {code}, subcode: {error_subcode})")
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return {"error": True, "code": code, "subcode": error_subcode, "msg": msg}
                return resp.json()
            except Exception as e:
                print(f"[MetaAPI] Exception: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return {"error": True, "msg": str(e)}
        return {"error": True, "msg": "Max retries exceeded"}

    def upload_image(self, image_path):
        """Uploads image and returns hash."""
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

    def upload_video(self, video_path):
        """Uploads video and returns video_id."""
        # Simple upload for smaller files. For large files, chunked upload is needed.
        with open(video_path, "rb") as f:
            result = self._request(
                "POST",
                f"{self.act_id}/advideos",
                files={"source": (os.path.basename(video_path), f, "video/mp4")},
            )
        if result.get("error"):
            return None
        return result.get("id")

    def create_campaign(self, name, objective="OUTCOME_SALES", status="PAUSED"):
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

    def create_ad_set(self, name, campaign_id, daily_budget, countries, status="PAUSED"):
        targeting = {
            "geo_locations": {"countries": countries if isinstance(countries, list) else [countries]},
        }
        
        # Note: daily_budget is in cents for CLI doc, but API expects micro-units or strings depending on currency.
        # Meta API daily_budget is usually in the smallest unit of the currency (e.g. cents for USD/EUR).
        
        result = self._request(
            "POST",
            f"{self.act_id}/adsets",
            data={
                "name": name,
                "campaign_id": campaign_id,
                "daily_budget": str(daily_budget),
                "billing_event": "IMPRESSIONS",
                "optimization_goal": "OFFSITE_CONVERSIONS",
                "promoted_object": json.dumps({"pixel_id": self.pixel_id, "custom_event_type": "PURCHASE"}),
                "status": status,
                "targeting": json.dumps(targeting),
            },
        )
        return result.get("id") if not result.get("error") else None

    def create_ad_creative(self, name, product_data, creative_data):
        """
        creative_data: {url, type, hash_or_id}
        product_data: {sales_title, lp_url}
        """
        object_story_spec = {
            "page_id": self.page_id,
        }
        
        link_data = {
            "link": product_data["lp_url"],
            "message": product_data.get("sales_title", "Check this out!"),
            "call_to_action": {"type": "SHOP_NOW"},
        }

        if creative_data["type"] == "image":
            link_data["image_hash"] = creative_data["hash_or_id"]
        elif creative_data["type"] == "video":
            # For video, we use video_data instead of link_data for some ad types, 
            # or video_id inside link_data.
            link_data["video_id"] = creative_data["hash_or_id"]
            link_data["image_url"] = creative_data["url"] # Thumbnail

        object_story_spec["link_data"] = link_data

        result = self._request(
            "POST",
            f"{self.act_id}/adcreatives",
            params={
                "name": name,
                "object_story_spec": json.dumps(object_story_spec),
            },
        )
        return result.get("id") if not result.get("error") else None

    def create_ad(self, name, adset_id, creative_id, status="PAUSED"):
        result = self._request(
            "POST",
            f"{self.act_id}/ads",
            params={
                "name": name,
                "adset_id": adset_id,
                "creative": json.dumps({"creative_id": creative_id}),
                "status": status,
                "tracking_specs": json.dumps([{"action.type": ["offsite_conversion"], "fb_pixel": [self.pixel_id]}])
            },
        )
        return result.get("id") if not result.get("error") else None

    def update_status(self, entity_id, status):
        """Update status of campaign, adset, or ad."""
        return self._request("POST", entity_id, params={"status": status})

    def get_insights(self, level="campaign", filters=None, date_preset="today"):
        """Fetch insights for a campaign or adset."""
        endpoint = f"{filters['id']}/insights" if filters and "id" in filters else f"{self.act_id}/insights"
        params = {
            "level": level,
            "date_preset": date_preset,
            "fields": "spend,purchase_roas,impressions,clicks,cpc,ctr,cpm,actions",
        }
        result = self._request("GET", endpoint, params=params)
        if result.get("error") or not result.get("data"):
            return None
        
        data = result["data"][0]
        # Parse actions for purchases, atc, ic
        actions = data.get("actions", [])
        metrics = {
            "spend": float(data.get("spend", 0)),
            "ctr": float(data.get("ctr", 0)) * 100,
            "cpm": float(data.get("cpm", 0)),
            "cpc": float(data.get("cpc", 0)),
            "roas": float(data.get("purchase_roas", [{"value": 0}])[0]["value"]),
            "purchases": 0,
            "atc": 0,
            "ic": 0,
            "conversion_value": 0,
        }
        
        for action in actions:
            if action["action_type"] == "purchase":
                metrics["purchases"] = int(action["value"])
            elif action["action_type"] == "offsite_conversion.fb_pixel_purchase":
                 metrics["purchases"] = int(action["value"])
            elif action["action_type"] == "offsite_conversion.fb_pixel_add_to_cart":
                metrics["atc"] = int(action["value"])
            elif action["action_type"] == "offsite_conversion.fb_pixel_initiate_checkout":
                metrics["ic"] = int(action["value"])
        
        action_values = data.get("action_values", [])
        for av in action_values:
            if av["action_type"] == "purchase" or av["action_type"] == "offsite_conversion.fb_pixel_purchase":
                metrics["conversion_value"] = float(av["value"])

        return metrics

class MetaCLI:
    """Wrapper for high-level operations."""
    def __init__(self, max_retries=3):
        self.api = MetaAPI(max_retries=max_retries)

    def _download_file(self, url):
        try:
            resp = requests.get(url, stream=True, timeout=60)
            if resp.status_code == 200:
                ext = url.split(".")[-1].split("?")[0]
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
                for chunk in resp.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                tmp.close()
                return tmp.name
        except Exception as e:
            print(f"[MetaCLI] Download failed: {e}")
        return None

    def launch_product_ads(self, product, creatives):
        """Full pipeline for a product."""
        results = {"success": False, "errors": []}
        
        # 1. Create Campaign
        campaign_name = f"{product['sales_title']} | {product['niche']} | Test"
        campaign_id = self.api.create_campaign(campaign_name)
        if not campaign_id:
            results["errors"].append("Failed to create campaign")
            return results
        
        # 2. Create AdSet
        adset_name = f"{product['niche']} - Targeting"
        # Budget from product or default
        budget = int(float(product.get("testing_daily_budget", 5)) * 100) # Assuming product budget is in EUR/USD
        adset_id = self.api.create_ad_set(adset_name, campaign_id, budget, ["FR", "US"]) # Default countries
        if not adset_id:
            results["errors"].append("Failed to create adset")
            return results
        
        launched_ads = []
        for creative in creatives:
            # 3. Upload & Create Creative
            local_file = self._download_file(creative["url"])
            if not local_file:
                results["errors"].append(f"Failed to download creative: {creative['url']}")
                continue
            
            hash_or_id = None
            if creative["type"] == "image":
                hash_or_id = self.api.upload_image(local_file)
            else:
                hash_or_id = self.api.upload_video(local_file)
            
            os.unlink(local_file)
            
            if not hash_or_id:
                results["errors"].append(f"Failed to upload creative: {creative['url']}")
                continue
            
            creative_id = self.api.create_ad_creative(
                f"Creative {creative['id']}", 
                product, 
                {"url": creative["url"], "type": creative["type"], "hash_or_id": hash_or_id}
            )
            
            if not creative_id:
                results["errors"].append(f"Failed to create Meta creative for {creative['id']}")
                continue
            
            # 4. Create Ad
            ad_id = self.api.create_ad(f"Ad {creative['id']}", adset_id, creative_id)
            if ad_id:
                launched_ads.append({"creative_id": creative["id"], "meta_ad_id": ad_id})
            else:
                results["errors"].append(f"Failed to create Ad for creative {creative['id']}")

        # 5. Activate (Campaign -> AdSet -> Ads)
        if launched_ads:
            self.api.update_status(campaign_id, "ACTIVE")
            self.api.update_status(adset_id, "ACTIVE")
            for ad in launched_ads:
                self.api.update_status(ad["meta_ad_id"], "ACTIVE")
            
            results["success"] = True
            results["campaign_id"] = campaign_id
            results["adset_id"] = adset_id
            results["launched_ads"] = launched_ads
            results["ad_account_id"] = self.api.account_id
            results["ad_account_name"] = "Meta Ads Account" # Fetching real name is optional
        
        return results