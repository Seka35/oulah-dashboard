from app.services.meta_cli import MetaCLI
from app.models import Product, Creative, Event

class CampaignLauncher:
    def __init__(self, max_retries=3, dry_run=False):
        self.meta_cli = MetaCLI(max_retries=max_retries)
        self.dry_run = dry_run

    def process_product(self, product):
        product_id = product["id"]
        product_name = product.get("sales_title") or product.get("name")
        
        # 1. Fetch approved creatives
        creatives = Creative.fetch_for_product(product_id, status="approved")
        if not creatives:
            print(f"  [Launcher] No approved creatives for product {product_id}")
            Event.log(product_id, "meta_launch_failed", {"reason": "No approved creatives"})
            return {"success": False, "error": "No approved creatives"}

        print(f"  [Launcher] Launching ads for: {product_name} ({len(creatives)} creatives)")
        
        if self.dry_run:
            print(f"  [Launcher] DRY RUN: Would launch campaign for {product_name}")
            return {"success": True, "dry_run": True}

        # 2. Update status to 'testing' immediately to avoid double processing
        Product.update_status(product_id, "testing")
        
        # 3. Launch via Meta CLI wrapper
        result = self.meta_cli.launch_product_ads(product, creatives)
        
        if not result["success"]:
            error_msg = "; ".join(result["errors"])
            print(f"  [Launcher] Failed: {error_msg}")
            Product.update_status(product_id, "approved") # Reset to approved so it can be retried
            Event.log(product_id, "meta_launch_failed", {"reason": error_msg})
            return {"success": False, "error": error_msg}

        # 4. Mark testing in DB with Meta IDs
        Product.mark_testing(product_id, {
            "campaign_id": result["campaign_id"],
            "adset_id": result["adset_id"],
            "ad_account_id": result["ad_account_id"],
            "ad_account_name": result["ad_account_name"],
            "daily_budget": product.get("testing_daily_budget", 5)
        })
        
        # 5. Link Ads to Creatives
        for launched_ad in result["launched_ads"]:
            Creative.link_ad(launched_ad["creative_id"], launched_ad["meta_ad_id"])
            Event.log(product_id, "meta_ad_created", {
                "ad_id": launched_ad["meta_ad_id"],
                "creative_id": str(launched_ad["creative_id"]),
                "campaign_id": result["campaign_id"]
            })

        Event.log(product_id, "meta_ads_launched", {
            "campaign_id": result["campaign_id"],
            "ad_count": len(result["launched_ads"]),
            "product_name": product_name
        })
        
        print(f"  [Launcher] Successfully launched: {result['campaign_id']}")
        return {"success": True, "campaign_id": result["campaign_id"]}

    def sync_metrics_all(self):
        """Fetch daily metrics for all products in 'testing' status."""
        testing_products = Product.fetch_all({"status": "testing"})
        print(f"  [Launcher] Syncing metrics for {len(testing_products)} products...")
        
        for product in testing_products:
            if not product.get("meta_campaign_id"):
                continue
            
            metrics = self.meta_cli.api.get_insights(filters={"id": product["meta_campaign_id"]})
            if metrics:
                # Update product level metrics
                Product.update_metrics(product["id"], metrics)
                
                # Upsert into meta_adsets table for granular tracking
                MetaAdset.upsert({
                    "product_id": product["id"],
                    "campaign_id": product["meta_campaign_id"],
                    "adset_id": product["meta_adset_id"],
                    "adset_name": f"{product['niche']} - Targeting",
                    "status": "active",
                    "daily_budget": product.get("testing_daily_budget", 5),
                    "amount_spent": metrics["spend"],
                    "purchases": metrics["purchases"],
                    "conversion_value": metrics["conversion_value"],
                    "cpm": metrics["cpm"],
                    "ctr": metrics["ctr"],
                    "cpc": metrics["cpc"],
                    "atc": metrics["atc"],
                    "ic": metrics["ic"],
                    "roas": metrics["roas"]
                })
                
                Event.log(product["id"], "meta_result_updated", metrics)
                print(f"    - Updated {product['sales_title']}: Spend {metrics['spend']}€")