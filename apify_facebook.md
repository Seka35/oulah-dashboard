curious_coder/facebook-ads-library-scraper

The Facebook ad library scraper is an Apify actor designed to extract ads from Meta or Facebook ad library
and also scrape ads run by given list of facebook pages.

With Meta ad library you can search all of the ads currently running across Meta technologies, as well as ads about social issues, elections or politics that have run in the past seven years, Ads that have run anywhere in the EU in the past year.
Facebook ads library scraper data fields

You can get all the fields listed in below table (and more) from this scraper
💼 Ad ID 🌐 Ad Archive ID 🗄️ Archive Types
📚 Categories 💻 Contains Digitally Created Media 📊 Collation Count
📊 Collation ID 💵 Currency 🕒 End Date
🌐 Entity Type 📈 Gated Type ❌ Has User Reported
🚨 Hidden Safety Data 🔍 Hide Data Status 🔄 Impressions With Index
🌐 Is AAA Eligible 🚀 Is Active 📋 Is Profile Page
📜 Page ID 📜 Page Name 🌐 Political Countries
🌐 Reach Estimate 🔍 Report Count 📸 Snapshot of Ads creatives)
💰 Spend 🕒 Start Date 🚩 State Media Run Label
🚀 Publisher Platform 📚 Menu Items 🏢 Advertiser
📊 Insights 🚀 AAA Info 
Features

Proxy Support: To enhance reliability and avoid rate limiting issues, the actor supports proxy usage. You can provide a list of proxies that will be rotated automatically to ensure smooth and uninterrupted scraping.

Scalability and Performance: The actor is built on the Apify platform, which ensures scalability and excellent performance. It utilizes parallel processing to scrape multiple pages simultaneously, maximizing efficiency and minimizing the overall scraping time.

Data Export and Integration: Once the scraping process is complete, you can easily export the extracted data in various formats such as JSON, CSV, or Excel. This allows for seamless integration with other tools and platforms for further analysis and utilization.

Automatic Retry and Error Handling: In case of temporary issues like network failures or timeouts, the actor has built-in automatic retry functionality. It intelligently handles errors to ensure a smooth and uninterrupted scraping experience.
How to scrape facebook ad library

Facebook ads search results page

    Visit facebook ad library
    page and search for ads based on your requirements
    Copy the URL from the browser's address bar
    Go to Facebook ad library scraper
    on the Apify platform
    Click the Try for free button
    Enter the ad library search results page Url
    If you want to scrape additional ad details such as EU transparency, EU total reach, etc, enable "Scrape ad details" option
    Select a proxy
    Click the Start button
    When the run has finished, click the Export button to download the ads

How to scrape ads run by facebook pages

Facebook page ads scraping options

    Create a list of facebook page URLs to scrape ads
    Go to actor's input page
    Select action to perform as 'Scrape ads of facebook pages'
    Go to 'Scrape ads of facebook pages' section and click on 'Bulk edit' and paste the page URLs into the text box
    Select a proxy to use and run the scraper

Sample data

Click here
to inspect the sample json output of this actor

Scraped facebook ads data sample
Related Facebook Scrapers

For comprehensive Facebook data extraction, check out these related scrapers. The Facebook Post Scraper
extracts posts from Facebook pages, groups, profiles and facebook search with engagement metrics and comments. To scrape detailed profile information from Facebook pages and profiles, use the Facebook Profile Scraper
. For extracting comments from any Facebook post including author details and replies, check out the Facebook Comment Scraper
. You can also collect member information from Facebook groups using the Facebook Group Member Scraper
. For finding email addresses from Facebook profiles, use the Facebook Profile Email Finder
.
Integrations

You can use Make
to integrate Facebook ad library scraper to any other SaaS platform by designing your own automation flows.
How to extract ads data from Facebook using API?

You can also run the scraper using API and get the collected data using the API. For more information, Go to Facebook ad library scraper API integration
page.

Here is an example of fetching the ads data via API using Postman:

Facebook ads search API
How much will it cost me to scrape Facebook ads ?

Based on historical data our scraper costs an average of $0.2 per thousand Facebook ads as usage credits. You can scrape upto 25k Facebook ads per month with Apify starter plan
