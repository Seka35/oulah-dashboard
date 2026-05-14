#!/usr/bin/env python3
import time
import sys
import os
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import Product, Setting
from app.services.campaign_launcher import CampaignLauncher

def run_worker(dry_run=False, interval=60):
    print(f"🚀 Meta Ads Automation Worker Started (Dry run: {dry_run})")
    print(f"   Polling every {interval}s...")
    
    launcher = CampaignLauncher(dry_run=dry_run)
    
    last_sync = 0
    sync_interval = 3600 * 6 # Sync metrics every 6 hours
    
    while True:
        try:
            # 1. Check if tool is active
            is_active = Setting.get("meta_tool_active", "false").lower() == "true"
            if not is_active:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏸️  Tool is paused (meta_tool_active=false)")
                time.sleep(interval)
                continue
            
            # 2. Poll for approved products
            approved_products = Product.fetch_approved()
            if approved_products:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Found {len(approved_products)} approved products to launch")
                for product in approved_products:
                    launcher.process_product(product)
            
            # 3. Periodically sync metrics
            if time.time() - last_sync > sync_interval:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 Running scheduled metrics sync...")
                launcher.sync_metrics_all()
                last_sync = time.time()

        except Exception as e:
            print(f"❌ Error in worker loop: {e}")
            import traceback
            traceback.print_exc()
        
        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Meta Ads Automation Worker")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually call Meta API")
    parser.add_argument("--interval", type=int, default=60, help="Polling interval in seconds")
    parser.add_argument("--sync-now", action="store_true", help="Run metrics sync immediately and exit")
    args = parser.parse_args()

    if args.sync_now:
        launcher = CampaignLauncher()
        launcher.sync_metrics_all()
        sys.exit(0)

    run_worker(dry_run=args.dry_run, interval=args.interval)
