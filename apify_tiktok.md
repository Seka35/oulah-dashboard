data_xplorer/tiktok-ads-library-fast

TikTok Ads Library Scraper

Transform your ad intelligence with our TikTok Ads Library scraper! Whether you're analyzing competitor strategies, monitoring brand campaigns, or conducting market research, this tool efficiently collects and structures advertising data from TikTok's Ad Library.

trends scraper
💎 Why Choose Our TikTok Ads Scraper?

    🎯 Advanced Search Options: Find ads by advertiser name, exact match, advertiser ID or paste TikTok URLs directly
    🚀 High-Volume Collection: Gather up to hundreds of ads in a single run with optimized pagination and intelligent proxy rotation
    🌐 Global Coverage: Access ads from multiple regions with support for all TikTok-supported countries
    📊 Rich Ad Details: Extract comprehensive ad information including media URLs, dates, and performance metrics
    🖼️ Media Access: Capture links to all ad creative assets including videos and images

🔮 How to Power Up Your Search Queries?

        🔤 Keyword Search : Search for ads containing specific words or phrases in their content
        🎯 Exact Match Search : For precise targeting, wrap your search term in quotes to find exact matches
        🆔 Advertiser ID Search : Search directly by TikTok advertiser ID for complete campaign analysis
        🌐 Direct URL: Paste any TikTok Ads Library URL and the scraper will automatically extract all parameters

✨ What You'll Get
📰 Ads Data Structure
Field Description
AD ID Unique identifier for the ad
Advertiser Name Name of the company/entity running the ad
AD Preview URL to the preview image/thumbnail of the ad
Ad Dates First and last shown dates with timestamps
Ad Audience Estimated audience information
Ad Details Comprehensive details including spend, type, audit status, and impressions
Ad Media URLs to all creative assets (videos, images, cover images)
Ad Targeting Detailed targeting data including regions, age groups, and gender
Ad Sponsor Sponsor information from ad details
Ad Target Audience Size Estimated target audience size
Ad Detail URL Direct link to the ad on TikTok Ads Library
🚀 Performance Features
⚡️ Lightning Fast:

    Efficient proxy rotation
    Optimized resource usage
    Smart retry mechanism

🛠️ Smart Handling:

    Automatic URL standardization
    Proxy health monitoring

🌍 Global Coverage:

    Works with any TikTok-supported region
    Standardizes output format

📋 Quick Start
Input Parameters
Parameter Type Default Description
region string "all" Region code for which you want to scrape ads
startDate string "2025-01-01" Start date for ads (format: YYYY-MM-DD)
endDate string "" End date for ads (empty for current date)
queryType string "2" Query type (1=Keyword, 2=Advertiser Name/ID, url=Direct URL)
query string "" Search query (keyword, advertiser name, ID, or full TikTok URL)
maxAds number 20 Maximum number of ads to scrape
fetchDetails boolean true Fetch detailed ad information (set to false for 3x faster scraping)
proxyConfiguration object {useApifyProxy: true, apifyProxyGroups: []} Proxy configuration (datacenter by default)
Input Example

{
  "region": "GB",
  "startDate": "2025-01-01",
  "endDate": "2026-01-01",
  "queryType": "2",
  "query": "\"Netflix International B.V.\"",
  "maxAds": 10,
  "fetchDetails": true,
  "proxyConfiguration": {
    "useApifyProxy": true,
    "apifyProxyGroups": []
  }
}

Output Example

[
  {
    "AD ID": "1820020351685681",
    "Advertiser Name": "Bouazza Helmi",
    "AD Preview": "https://p21-ad-sg.ibyteimg.com/origin/tos-alisg-p-0051c001-sg/okrEGLAREFAKi4BAIb7DgCu8Z5zLfeNwhDWfC8",
    "Ad Dates": [
      {
        "FirstShown": "2025-01-01",
        "FirstShownTimestamp": 1735689600
      },
      {
        "LastShown": "2025-03-08",
        "LastShownTimestamp": 1741392000
      }
    ],
    "Ad Audience": "100K-200K",
    "Ad Details": [
      {
        "Estimated Audience": "100K-200K"
      },
      {
        "Spent": ""
      },
      {
        "Type": "2"
      },
      {
        "Audit Status": "1"
      },
      {
        "Impression": ""
      },
      {
        "Sponsor": "Digital Marketing Agency"
      },
      {
        "Target Audience Size": "5.2M-6.4M"
      }
    ],
    "Ad Media": [
      "Video 1: https://library.tiktok.com/api/v1/cdn/1741534040/video/aHR0cHM6Ly92MTZtLnRpa3Rva2Nkbi5jb20vMDkzMTJhY2RkZDRhYTI1ODhlZmYwZTIwYTYzOTI1NWEvNjdjZTA3Y2MvdmlkZW8vdG9zL2FsaXNnL3Rvcy1hbGlzZy12ZS0wMDUxYzAwMS1zZy9vNER3SGdUQ0VDODR1SUVQOGZiekcyZURUZkJSWkE1V1FLQUJGTi8=/f8eb26d4-832d-465a-a583-9f16dda4eeac?a=475769&bti=PDU2NmYwMy86&ch=0&cr=0&dr=1&cd=0%7C0%7C0%7C0&cv=1&br=908&bt=454&cs=0&ds=1&ft=.NpOcInz7ThMe2OOXq8Zmo&mime_type=video_mp4&qs=0&rc=ZTllOjM8NTtoZ2Y7N2dmZEBpanN1OHg5cmpmdTMzODYzNEAvYC0xM18zXmMxYzQvNC0zYSM1bWkyMmRrc2xgLS1kMC1zcw%3D%3D&vvpl=1&l=2025030915271919A020BE52B2A1947586&btag=e000b8000&cc=3",
      "Cover 1: https://p21-ad-sg.ibyteimg.com/origin/tos-alisg-p-0051c001-sg/okrEGLAREFAKi4BAIb7DgCu8Z5zLfeNwhDWfC8",
      "Image 1: https://p21-ad-sg.ibyteimg.com/origin/tos-alisg-p-0051c001-sg/okrEGLAREFAKi4BAIb7DgCu8Z5zLfeNwhDWfC8"
    ],
    "Ad Targeting": {
      "regions": [
        {
          "region": "FR",
          "impressions": "152K"
        }
      ],
      "age": [
        {
          "region": "FR",
          "13-17": false,
          "18-24": true,
          "25-34": true,
          "35-44": true,
          "45-54": false,
          "55+": false
        }
      ],
      "gender": [
        {
          "region": "FR",
          "female": true,
          "male": true,
          "unknown": false
        }
      ]
    },
    "Ad Sponsor": "Digital Marketing Agency",
    "Ad Target Audience Size": "5.2M-6.4M",
    "Ad Detail URL": "https://library.tiktok.com/ads/detail/?ad_id=1820020351685681"
  }
]

🤝 Support & Resources

Need help? Have questions? We're here to help! If you encounter any issues or have feature requests, please don't hesitate to open an issue.

❤️ Love our scraper? Please leave a review here
