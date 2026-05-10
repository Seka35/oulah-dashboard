dz_omar/google-ads-scraper

🔍 Google Ads Intelligence Scraper

Uncover competitor advertising strategies, analyze ad creatives, and monitor campaigns across all Google platforms with comprehensive data from Google's official Ads Transparency Center.

Extract complete ad data including creative previews, impression statistics, regional targeting, platform distribution, and advertiser information - all in structured, analysis-ready format.

Google Ads Scraper
🎯 What You Can Extract
Complete Ad Intelligence

    Ad Creatives - Preview URLs for all ad formats (video, image, text)
    Advertiser Information - IDs, transparency URLs, and verification data
    Performance Metrics - Impression ranges across regions and platforms
    Targeting Data - Geographic regions where ads were shown
    Platform Distribution - Performance breakdown across YouTube, Search, Shopping, Maps, and Play
    Time Analytics - First and last shown dates for each creative

Structured Output Data

Every ad returns a complete JSON object with:

    Advertiser ID and Creative ID
    Direct links to Google Ads Transparency pages
    Preview URLs for immediate creative viewing
    Regional statistics with impression counts
    Platform-specific performance data
    Format type (VIDEO, IMAGE, TEXT)

Why Choose This Scraper?
Built for Performance

    Lightning Fast - Optimized parallel processing for multiple searches
    Smart Filtering - Precise control over platforms, formats, regions, and dates
    Batch Processing - Handle unlimited search targets in one run
    Auto-Retry Logic - Reliable extraction even with temporary API issues

Flexible Search Options

    Keywords - "nike shoes", "saas software", "fitness app"
    Advertiser IDs - Direct extraction with AR123... format
    Domains - Find all ads from "shopify.com" or "apple.com"
    Google Ads URLs - Paste full transparency URLs with embedded filters

Global Coverage

    200+ Regions Supported - From United States to Tuvalu
    Multi-Platform - YouTube, Search, Shopping, Maps, Google Play
    All Ad Formats - Video, image, and text creatives
    Historical Data - Access ads from any time period

📥 Input Configuration
Quick Start Example

{
  "searchTargets": [
    "fitness apps",
    "AR04619580580634296321",
    "https://adstransparency.google.com/advertiser/AR12345?region=US&platform=YOUTUBE"
  ],
  "resultsPerQuery": 20,
  "targetPlatform": "YOUTUBE",
  "adFormatType": "VIDEO",
  "timeRangePreset": "LAST_30_DAYS"
}

Input Parameters
Parameter Type Description
🎯 searchTargets array Required. Keywords, advertiser IDs (AR...), domains, or full Google Ads Transparency URLs
📊 resultsPerQuery integer Max ads per search target (0 = unlimited) Default: 10
📱 targetPlatform string Filter by platform: ALL, YOUTUBE, SEARCH, SHOPPING, MAPS, PLAY
🎬 adFormatType string Filter by format: ALL, VIDEO, IMAGE, TEXT
🌍 geoTargetRegion string Filter by country/region where ads appeared
📅 timeRangePreset string Quick date selection: ALL_TIME, LAST_30_DAYS, LAST_7_DAYS, YESTERDAY, TODAY
📅 customStartDate string Custom start date (YYYY-MM-DD) - overrides preset
📅 customEndDate string Custom end date (YYYY-MM-DD) - overrides preset
👥 maxAdvertiserAccounts integer Max advertisers per keyword search. Default: 3
🌐 maxDomainMatches integer Max domains when multiple match (0 = unlimited). Default: 1
🔗 enableUrlFiltering boolean Extract filters from Google Ads URLs. Default: true
🔒 proxyConfig object Proxy configuration (Apify Proxy recommended)
📤 Output Structure
Example Output (Single Ad)

{
  "advertiserId": "AR04619580580634296321",
  "creativeId": "CR14567271621866815489",
  "format": "VIDEO",
  "creativeRegions": ["United States", "Canada", "United Kingdom"],
  "adTransparencyUrl": "<https://adstransparency.google.com/advertiser/AR04619580580634296321/creative/CR14567271621866815489?region=anywhere>",
  "previewUrls": [
    "https://displayads-formats.googleusercontent.com/ads/preview/content.js?client=ads-integrity..."
  ],
  "regionStats": [
    {
      "regionNumber": 2840,
      "regionCode": "US",
      "regionName": "United States",
      "firstShown": 20240115,
      "lastShown": 20241022,
      "impressions": {
        "lowerBound": 10000,
        "upperBound": 50000
      },
      "platformStats": [
        {
          "surfaceName": "YouTube",
          "impressions": {
            "lowerBound": 8000,
            "upperBound": 40000
          }
        },
        {
          "surfaceName": "Google Search",
          "impressions": {
            "lowerBound": 2000,
            "upperBound": 10000
          }
        }
      ]
    }
  ]
}

Output Fields Explained
Core Ad Data

    advertiserId - Unique advertiser identifier (AR...)
    creativeId - Unique creative/ad identifier (CR...)
    format - Ad type: VIDEO, IMAGE, or TEXT
    adTransparencyUrl - Direct link to Google's transparency page
    previewUrls - Array of URLs to preview the actual ad creative

Geographic & Targeting Data

    creativeRegions - List of all regions where ad appeared
    regionStats - Detailed breakdown per region including:
        Region name and code (US, GB, etc.)
        First and last shown dates (YYYYMMDD format)
        Total impression ranges (lower/upper bounds)
        Platform-specific performance data

Platform Performance

    platformStats - For each region, shows distribution across:
        YouTube
        Google Search
        Google Shopping
        Google Maps
        Google Play

Professional Use Cases
Competitive Intelligence

    Monitor Competitors - Track advertising strategies of direct competitors
    Ad Creative Analysis - Study successful ad formats and messaging
    Budget Estimation - Gauge competitor spend based on impression data
    Market Positioning - Understand how competitors target different regions

Market Research

    Industry Trends - Analyze advertising patterns in your niche
    Seasonal Campaigns - Track when competitors increase ad spend
    Regional Strategies - Discover which markets competitors prioritize
    Platform Preferences - See which Google platforms work best in your industry

Media Planning

    Campaign Planning - Learn from successful campaigns in your space
    Platform Selection - Data-driven decisions on YouTube vs Search vs Shopping
    Geographic Targeting - Identify high-potential regions based on competitor activity
    Creative Inspiration - Access preview URLs for creative reference

Business Intelligence

    Brand Monitoring - Track mentions and ads from specific domains
    Partnership Discovery - Find companies advertising complementary products
    Merger & Acquisition Research - Monitor advertising activity of target companies
    Market Entry Analysis - Understand advertising landscape before entering new markets

Data & Automation

    API Integration - Feed data into business intelligence dashboards
    Automated Monitoring - Schedule regular scans of competitor activity
    Alert Systems - Trigger notifications when competitors launch new campaigns
    Data Warehousing - Build comprehensive advertising databases

🎯 Advanced Search Techniques

1. Keyword-Based Discovery

Perfect for finding advertisers in your industry:

{
  "searchTargets": ["saas software", "project management tool"],
  "maxAdvertiserAccounts": 10
}

1. Direct Advertiser Tracking

Monitor specific competitors:

{
  "searchTargets": [
    "AR04619580580634296321",
    "AR12345678901234567890"
  ],
  "resultsPerQuery": 0
}

1. Domain-Based Analysis

All ads from a specific website:

{
  "searchTargets": ["shopify.com", "wix.com"],
  "maxDomainMatches": 0
}

1. URL Filter Extraction

Preserve filters from Google Ads Transparency URLs:

{
  "searchTargets": [
    "https://adstransparency.google.com/advertiser/AR123?region=US&platform=YOUTUBE&format=VIDEO"
  ],
  "enableUrlFiltering": true
}

1. Multi-Platform Comparison

Compare performance across platforms:

{
  "searchTargets": ["nike"],
  "targetPlatform": "ALL",
  "maxAdvertiserAccounts": 5,
  "resultsPerQuery": 50
}

Technical Details
Performance Metrics

    Speed: 2-5 seconds per advertiser
    Throughput: Process 100+ search targets in under 10 minutes
    Accuracy: Direct data from Google's official API
    Reliability: Built-in retry logic with exponential backoff

Infrastructure

    Proxy Support - Automatic rotation with Apify Proxy integration
    Error Handling - Graceful degradation on temporary failures
    Rate Limiting - Smart request throttling to avoid blocks
    Parallel Processing - Concurrent execution for maximum speed

Data Quality

    Official Source - All data from Google Ads Transparency Center
    No Estimates - Real impression ranges, not extrapolated data
    Up-to-Date - Access to the latest advertising activity
    Comprehensive - All ad formats, platforms, and regions

Typical Use Patterns
Small Business Owner

{
  "searchTargets": ["local coffee shop", "neighborhood cafe"],
  "geoTargetRegion": "United States",
  "timeRangePreset": "LAST_30_DAYS",
  "resultsPerQuery": 10
}

Marketing Agency

{
  "searchTargets": [
    "AR123...",
    "AR456...",
    "AR789..."
  ],
  "resultsPerQuery": 100,
  "targetPlatform": "ALL"
}

Enterprise Research Team

{
  "searchTargets": [
    "software", "technology", "cloud computing",
    "artificial intelligence", "machine learning"
  ],
  "maxAdvertiserAccounts": 20,
  "resultsPerQuery": 0,
  "timeRangePreset": "ALL_TIME"
}

🛡️ Legal & Compliance

This actor extracts publicly available advertising data from Google's official Ads Transparency Center. All data is information that Google makes accessible to promote advertising transparency.

Important Considerations:

    ✅ Data is publicly accessible to all users
    ✅ No authentication or private data accessed
    ✅ Complies with Google's transparency initiatives
    ⚠️ Respect rate limits and use proxies responsibly
    ⚠️ Review Google's Terms of Service for your use case
    ⚠️ Ensure compliance with data protection laws (GDPR, CCPA, etc.)

Recommended Use:

    ✅ Competitive analysis and market research
    ✅ Academic research on advertising trends
    ✅ Transparency and accountability journalism
    ✅ Business intelligence and strategic planning

🚀 Getting Started

1. Configure Your Search

Add keywords, advertiser IDs, domains, or full Google Ads URLs
2. Apply Filters (Optional)

Narrow results by platform, format, region, or date range
3. Set Limits

Define how many ads per target and max advertisers per keyword
4. Enable Proxy (Recommended)

Use Apify Proxy for reliable, unblocked access
5. Run & Export

Execute the actor and download results in JSON, CSV, or Excel
Optimization Tips

    Use resultsPerQuery limits to control costs
    Set maxAdvertiserAccounts based on needs
    Enable enableUrlFiltering for faster URL-based searches
    Use proxies only when necessary (reduces costs)

📊 Export & Integration
Export Formats

    JSON - Full structured data with all nested objects
    CSV - Flattened view for Excel and spreadsheet tools
    Excel - Formatted tables with multiple sheets
    API - Direct programmatic access via Apify API

Integration Examples
Python

from apify_client import ApifyClient

client = ApifyClient("YOUR_API_TOKEN")
run = client.actor("dz_omar/google-ads-scraper").call(
    run_input={
        "searchTargets": ["nike"],
        "resultsPerQuery": 50
    }
)

# Fetch results

for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)

JavaScript

import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: 'YOUR_API_TOKEN' });
const run = await client.actor("dz_omar/google-ads-scraper").call({
    searchTargets: ["nike"],
    resultsPerQuery: 50
});

const { items } = await client.dataset(run.defaultDatasetId).listItems();
console.log(items);

🔧 Troubleshooting
No Results Returned

Possible Causes:

    Advertiser ID doesn't exist or has no public ads
    Region filter too restrictive
    Date range excludes all ad activity
    Domain has no verified Google Ads presence

Solutions:

    Verify advertiser ID format (AR followed by 20 digits)
    Try removing region/date filters first
    Search by keyword instead of domain
    Check Google Ads Transparency manually first

Slow Performance

Possible Causes:

    Many search targets with unlimited results
    No rate limiting enabled
    Network latency without proxy

Solutions:

    Set reasonable resultsPerQuery limits
    Enable Apify Proxy for faster processing
    Reduce maxAdvertiserAccounts per keyword
    Split large jobs into smaller batches

Proxy Errors

Possible Causes:

    Insufficient proxy credits
    Wrong proxy group selected
    Proxy blocked by Google

Solutions:

    Verify Apify account has proxy credits
    Use RESIDENTIAL proxy group for best results
    Try without proxy for small tests
    Contact Apify support for persistent issues
