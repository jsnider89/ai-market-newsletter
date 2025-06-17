# clean_market_aggregator.py
# Built from scratch - Clean RSS + Market Data Aggregator

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
import re
import requests

class CleanMarketAggregator:
    def __init__(self):
        self.symbols = ['QQQ', 'SPY', 'DXY', 'IWM', 'GLD', 'BTCUSD', 'MP']
        self.rss_feeds = [
            ('Federal Reserve - Commercial Paper', 'https://www.federalreserve.gov/feeds/Data/CP_OUTST.xml'),
            ('Federal Reserve - Press Monetary', 'https://www.federalreserve.gov/feeds/press_monetary.xml'),
            ('Fox News Latest', 'https://feeds.feedburner.com/foxnews/latest'),
            ('The Hill Home News', 'https://thehill.com/homenews/feed/'),
            ('Daily Caller', 'https://dailycaller.com/feed/'),
            ('Daily Wire', 'https://www.dailywire.com/feeds/rss.xml'),
            ('The Blaze', 'https://www.theblaze.com/feeds/feed.rss'),
            ('News Busters', 'https://newsbusters.org/blog/feed'),
            ('Daily Signal', 'https://www.dailysignal.com/feed'),
            ('Newsmax Headlines', 'https://www.newsmax.com/rss/Headline/76'),
            ('Newsmax Finance', 'https://www.newsmax.com/rss/FinanceNews/4'),
            ('Newsmax Economy', 'https://www.newsmax.com/rss/Economy/2'),
            ('Newsmax World', 'https://www.newsmax.com/rss/GlobalTalk/162'),
            ('Newsmax US', 'https://www.newsmax.com/rss/US/18'),
            ('Newsmax Tech', 'https://www.newsmax.com/rss/SciTech/20'),
            ('Newsmax Wire', 'https://www.newsmax.com/rss/TheWire/118'),
            ('Newsmax Politics', 'https://www.newsmax.com/rss/Politics/1'),
            ('MarketWatch Top Stories', 'https://feeds.content.dowjones.io/public/rss/mw_topstories'),
            ('MarketWatch Real-time', 'https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines'),
            ('CNBC Markets', 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664'),
            ('CNBC Finance', 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258'),
            ('CNBC Economy', 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910')
        ]

    def fetch_market_data(self):
        """Get current market data for specified symbols"""
        api_key = os.getenv('FINNHUB_API_KEY')
        
        if not api_key:
            return "❌ No Finnhub API key configured"
        
        market_results = []
        market_results.append("📊 CURRENT MARKET DATA")
        market_results.append("=" * 50)
        
        for symbol in self.symbols:
            try:
                url = "https://finnhub.io/api/v1/quote"
                params = {'symbol': symbol, 'token': api_key}
                
                response = requests.get(url, params=params, timeout=8)
                data = response.json()
                
                if 'c' in data and data['c'] is not None:
                    current = float(data['c'])
                    change = float(data.get('d', 0) or 0)
                    change_pct = float(data.get('dp', 0) or 0)
                    
                    direction = "🟢" if change >= 0 else "🔴"
                    market_results.append(f"{symbol:8} | ${current:10.2f} | {direction} {change:+8.2f} ({change_pct:+6.2f}%)")
                else:
                    market_results.append(f"{symbol:8} | No data available")
                    
            except Exception as e:
                market_results.append(f"{symbol:8} | Error: {str(e)}")
        
        market_results.append("=" * 50)
        market_results.append(f"Data retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        return "\n".join(market_results)

    def parse_rss_feed(self, source_name, feed_url):
        """Parse a single RSS feed and extract articles"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(feed_url, timeout=15, headers=headers)
            
            if response.status_code != 200:
                return f"❌ {source_name}: HTTP {response.status_code}"
            
            content = response.text
            
            # Extract items from RSS
            items = re.findall(r'<item[^>]*>(.*?)</item>', content, re.DOTALL | re.IGNORECASE)
            if not items:
                # Try alternative patterns
                items = re.findall(r'<entry[^>]*>(.*?)</entry>', content, re.DOTALL | re.IGNORECASE)
            
            if not items:
                return f"⚠️ {source_name}: No articles found in feed"
            
            articles = []
            for item in items[:5]:  # Top 5 articles per source
                # Extract title
                title_match = re.search(r'<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item, re.DOTALL | re.IGNORECASE)
                title = "No title"
                if title_match:
                    title = title_match.group(1).strip()
                    title = re.sub(r'<[^>]+>', '', title)  # Remove HTML tags
                
                # Extract description/summary
                desc_patterns = [
                    r'<description[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>',
                    r'<summary[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</summary>',
                    r'<content[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</content>'
                ]
                
                description = ""
                for pattern in desc_patterns:
                    desc_match = re.search(pattern, item, re.DOTALL | re.IGNORECASE)
                    if desc_match:
                        description = desc_match.group(1).strip()
                        description = re.sub(r'<[^>]+>', '', description)  # Remove HTML tags
                        description = description[:300] + "..." if len(description) > 300 else description
                        break
                
                # Extract publish date
                date_patterns = [
                    r'<pubDate[^>]*>(.*?)</pubDate>',
                    r'<published[^>]*>(.*?)</published>',
                    r'<updated[^>]*>(.*?)</updated>'
                ]
                
                pub_date = "No date"
                for pattern in date_patterns:
                    date_match = re.search(pattern, item, re.IGNORECASE)
                    if date_match:
                        pub_date = date_match.group(1).strip()
                        break
                
                if title and title != "No title":
                    articles.append({
                        'title': title,
                        'description': description,
                        'date': pub_date
                    })
            
            if not articles:
                return f"⚠️ {source_name}: Articles found but couldn't parse content"
            
            # Format results
            result = [f"✅ {source_name} ({len(articles)} articles):"]
            result.append("-" * 60)
            
            for i, article in enumerate(articles, 1):
                result.append(f"Article {i}:")
                result.append(f"  Title: {article['title']}")
                if article['description']:
                    result.append(f"  Summary: {article['description']}")
                result.append(f"  Date: {article['date']}")
                result.append("")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"❌ {source_name}: Error - {str(e)}"

    def fetch_all_rss_feeds(self):
        """Fetch and parse all RSS feeds"""
        rss_results = []
        rss_results.append("📰 RSS FEED AGGREGATION")
        rss_results.append("=" * 80)
        rss_results.append(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        rss_results.append(f"Total feeds to process: {len(self.rss_feeds)}")
        rss_results.append("=" * 80)
        rss_results.append("")
        
        successful_feeds = 0
        total_articles = 0
        
        for source_name, feed_url in self.rss_feeds:
            print(f"Processing: {source_name}")
            
            result = self.parse_rss_feed(source_name, feed_url)
            rss_results.append(result)
            rss_results.append("")
            
            if result.startswith("✅"):
                successful_feeds += 1
                # Count articles in successful feeds
                article_count = result.count("Article ")
                total_articles += article_count
        
        # Add summary
        rss_results.append("=" * 80)
        rss_results.append("📊 RSS FEED SUMMARY")
        rss_results.append("=" * 80)
        rss_results.append(f"Successful feeds: {successful_feeds}/{len(self.rss_feeds)}")
        rss_results.append(f"Total articles collected: {total_articles}")
        rss_results.append(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        return "\n".join(rss_results)

    def create_full_report(self):
        """Create complete data aggregation report"""
        print("🚀 Starting clean market data aggregation...")
        
        # Header
        report = []
        report.append("🔍 CLEAN MARKET DATA AGGREGATION REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} UTC")
        report.append(f"Purpose: Raw data collection for AI analysis")
        report.append("=" * 80)
        report.append("")
        
        # Market data
        print("📊 Fetching market data...")
        market_data = self.fetch_market_data()
        report.append(market_data)
        report.append("")
        report.append("")
        
        # RSS feeds
        print("📰 Fetching RSS feeds...")
        rss_data = self.fetch_all_rss_feeds()
        report.append(rss_data)
        report.append("")
        
        # Footer
        report.append("=" * 80)
        report.append("📋 REPORT NOTES")
        report.append("=" * 80)
        report.append("• Market data: Real-time from Finnhub API")
        report.append("• RSS feeds: Latest articles from 22 sources")
        report.append("• Symbols tracked: QQQ, SPY, DXY, IWM, GLD, BTCUSD, MP")
        report.append("• Feed sources: Fed Reserve, Conservative, Mainstream Financial")
        report.append("• Next step: This raw data will be sent to AI for analysis")
        report.append("=" * 80)
        
        full_report = "\n".join(report)
        print(f"✅ Report generated - {len(full_report):,} characters")
        
        return full_report

    def send_report_email(self, report):
        """Email the aggregation report"""
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        recipient_email = os.getenv('RECIPIENT_EMAIL')
        
        if not all([sender_email, sender_password, recipient_email]):
            print("❌ Missing email configuration")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['Subject'] = f"📊 Clean Market Data Report - {datetime.now().strftime('%B %d, %Y')}"
            msg['From'] = sender_email
            msg['To'] = recipient_email
            
            # Simple HTML formatting
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: 'Consolas', 'Monaco', monospace;
                        font-size: 12px;
                        line-height: 1.4;
                        color: #333;
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f8f9fa;
                    }}
                    .container {{
                        background-color: white;
                        padding: 25px;
                        border-radius: 8px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                        white-space: pre-wrap;
                        overflow-x: auto;
                    }}
                    .header {{
                        color: #2c3e50;
                        font-size: 16px;
                        font-weight: bold;
                        text-align: center;
                        margin-bottom: 20px;
                        border-bottom: 2px solid #3498db;
                        padding-bottom: 10px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">📊 CLEAN MARKET DATA AGGREGATION</div>
                    {report.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, 'html'))
            
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            print("✅ Report emailed successfully!")
            print(f"   Sent to: {recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False

    def run(self):
        """Main execution function"""
        print("🔥 CLEAN MARKET AGGREGATOR - Starting Fresh")
        print(f"   Symbols: {', '.join(self.symbols)}")
        print(f"   RSS Feeds: {len(self.rss_feeds)} sources")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print("-" * 60)
        
        # Generate report
        report = self.create_full_report()
        
        # Email report
        print("📧 Sending report email...")
        if self.send_report_email(report):
            print("🎉 Clean aggregation completed successfully!")
        else:
            print("⚠️ Aggregation completed but email failed")
        
        print(f"📊 Final report size: {len(report):,} characters")

if __name__ == "__main__":
    aggregator = CleanMarketAggregator()
    aggregator.run()
