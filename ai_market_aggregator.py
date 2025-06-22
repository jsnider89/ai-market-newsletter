# ai_market_aggregator.py

# Enhanced version with AI analysis integration

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
import re
import requests
import json

class AIMarketAggregator:
def **init**(self):
self.symbols = [‘QQQ’, ‘SPY’, ‘DXY’, ‘IWM’, ‘GLD’, ‘BTCUSD’, ‘MP’]
self.rss_feeds = [
(‘Federal Reserve - Commercial Paper’, ‘https://www.federalreserve.gov/feeds/Data/CP_OUTST.xml’),
(‘Federal Reserve - Press Monetary’, ‘https://www.federalreserve.gov/feeds/press_monetary.xml’),
(‘Fox News Latest’, ‘https://feeds.feedburner.com/foxnews/latest’),
(‘The Hill Home News’, ‘https://thehill.com/homenews/feed/’),
(‘Daily Caller’, ‘https://dailycaller.com/feed/’),
(‘Daily Wire’, ‘https://www.dailywire.com/feeds/rss.xml’),
(‘The Blaze’, ‘https://www.theblaze.com/feeds/feed.rss’),
(‘News Busters’, ‘https://newsbusters.org/blog/feed’),
(‘Daily Signal’, ‘https://www.dailysignal.com/feed’),
(‘Newsmax Headlines’, ‘https://www.newsmax.com/rss/Headline/76’),
(‘Newsmax Finance’, ‘https://www.newsmax.com/rss/FinanceNews/4’),
(‘Newsmax Economy’, ‘https://www.newsmax.com/rss/Economy/2’),
(‘Newsmax World’, ‘https://www.newsmax.com/rss/GlobalTalk/162’),
(‘Newsmax US’, ‘https://www.newsmax.com/rss/US/18’),
(‘Newsmax Tech’, ‘https://www.newsmax.com/rss/SciTech/20’),
(‘Newsmax Wire’, ‘https://www.newsmax.com/rss/TheWire/118’),
(‘Newsmax Politics’, ‘https://www.newsmax.com/rss/Politics/1’),
(‘MarketWatch Top Stories’, ‘https://feeds.content.dowjones.io/public/rss/mw_topstories’),
(‘MarketWatch Real-time’, ‘https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines’),
(‘MarketWatch Market Pulse’, ‘https://feeds.content.dowjones.io/public/rss/mw_marketpulse’),
(‘CNBC Markets’, ‘https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664’),
(‘CNBC Finance’, ‘https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258’),
(‘CNBC Economy’, ‘https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910’)
]

```
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
            return f"❌ {source_name}: HTTP {response.status_code}", []
        
        content = response.text
        
        # Extract items from RSS
        items = re.findall(r'<item[^>]*>(.*?)</item>', content, re.DOTALL | re.IGNORECASE)
        if not items:
            items = re.findall(r'<entry[^>]*>(.*?)</entry>', content, re.DOTALL | re.IGNORECASE)
        
        if not items:
            return f"⚠️ {source_name}: No articles found in feed", []
        
        articles = []
        for item in items[:5]:  # Top 5 articles per source
            # Extract title
            title_match = re.search(r'<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item, re.DOTALL | re.IGNORECASE)
            title = "No title"
            if title_match:
                title = title_match.group(1).strip()
                title = re.sub(r'<[^>]+>', '', title)
            
            # Extract description
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
                    description = re.sub(r'<[^>]+>', '', description)
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
                    'date': pub_date,
                    'source': source_name
                })
        
        status = f"✅ {source_name} ({len(articles)} articles)"
        return status, articles
        
    except Exception as e:
        return f"❌ {source_name}: Error - {str(e)}", []

def fetch_all_rss_feeds(self):
    """Fetch and parse all RSS feeds"""
    all_articles = []
    feed_statuses = []
    
    print("📰 Fetching RSS feeds...")
    for source_name, feed_url in self.rss_feeds:
        print(f"  Processing: {source_name}")
        status, articles = self.parse_rss_feed(source_name, feed_url)
        feed_statuses.append(status)
        all_articles.extend(articles)
    
    print(f"✅ Collected {len(all_articles)} total articles from {len(self.rss_feeds)} sources")
    return all_articles, feed_statuses

def prepare_ai_prompt(self, market_data, articles):
    """Prepare the prompt for AI analysis"""
    # Format articles for the prompt
    articles_text = []
    for i, article in enumerate(articles, 1):
        articles_text.append(f"Article {i} from {article['source']}:")
        articles_text.append(f"Title: {article['title']}")
        if article['description']:
            articles_text.append(f"Summary: {article['description']}")
        articles_text.append(f"Date: {article['date']}")
        articles_text.append("")
    
    # Get tomorrow's date for the looking ahead section
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime('%A, %B %d')
    
    prompt = f"""You are a financial news analyst tasked with creating a daily news briefing. Analyze the following market data and news articles to create a comprehensive daily report.
```

## TODAY’S MARKET DATA:

{market_data}

## NEWS ARTICLES FROM 23 SOURCES:

{chr(10).join(articles_text)}

## YOUR TASK:

Create a daily briefing with THREE DISTINCT SECTIONS:

**SECTION 1 - MARKET PERFORMANCE:**
Present the market data in a clean, formatted way. For each ticker, show:

- The symbol
- Current/closing price
- Change in dollars
- Change in percentage
- Use 🟢 for positive changes and 🔴 for negative changes
  Keep the original formatting style from the input data.

**SECTION 2 - TOP MARKET & ECONOMY STORIES (5 stories):**
Identify the 5 most important MARKET and ECONOMY-SPECIFIC stories based on:

- TIMELINESS: Most recent stories get priority (today’s news over older news)
- REPETITION: Stories covered by multiple sources are more important
- Must be directly related to:
  - Stock market movements
  - Federal Reserve decisions
  - Economic data releases (inflation, jobs, GDP, etc.)
  - Major financial institution news
  - Currency/commodity movements
  - Corporate earnings or major business deals

**SECTION 3 - GENERAL NEWS STORIES (10 stories):**
Identify the 10 most important remaining news stories based on:

- Frequency of coverage across sources
- General significance (politics, technology, geopolitics, etc.)
- Breaking news or major developments
- Policy changes or legislative news
- International affairs

**FOR EACH STORY IN BOTH NEWS SECTIONS:**

- Write a clear, descriptive headline
- Provide a full paragraph (4-6 sentences) that explains:
  - What happened
  - Why it’s significant
  - The broader context or implications
  - Any relevant background information
- Include source attribution (which outlets reported it)

**IMPORTANT:** Keep the news summaries focused on the stories themselves. Do NOT force connections to specific tickers or constantly mention how each story affects QQQ, SPY, etc. Just tell me what happened and why it matters in general terms.

**LOOKING AHEAD SECTION:**
End with a specific “Looking Ahead” section for {tomorrow_str} that includes:

- Specific economic data releases scheduled (if any mentioned in the articles)
- Key earnings reports expected
- Federal Reserve events or speeches
- Important government meetings or hearings
- Any other concrete events mentioned in today’s news that will occur tomorrow
  Be specific with times if mentioned. If no specific events are mentioned for tomorrow, note key themes to watch.

**FORMAT GUIDELINES:**

- Start with “MARKET PERFORMANCE” section
- Follow with “TOP MARKET & ECONOMY STORIES” section (5 stories)
- Then “GENERAL NEWS” section (10 stories)
- Number stories 1-5 and 1-10 in their respective sections
- Use clear section breaks between all three sections
- End with the specific “Looking Ahead” section

**WRITING STYLE:**

- Professional but conversational
- Focus on clarity and readability
- Be objective and balanced
- Prioritize timeliness for market stories

Please create this briefing now.”””

```
    return prompt

def call_openai_api(self, prompt):
    """Call OpenAI API for analysis"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ No OpenAI API key configured")
        return None
    
    try:
        print(f"   API Key found: {api_key[:8]}...")
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'o4-mini-2025-04-16',  # Using the new o4-mini model
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a professional financial market analyst creating daily briefings.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.7,
            'max_tokens': 4000
        }
        
        print(f"   Sending request to OpenAI (o4-mini)...")
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=60
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Successfully received AI analysis")
            return result['choices'][0]['message']['content']
        else:
            print(f"❌ OpenAI API error: {response.status_code}")
            print(f"   Error details: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error calling OpenAI API: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def call_anthropic_api(self, prompt):
    """Call Anthropic Claude API for analysis"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("❌ No Anthropic API key configured")
        return None
    
    try:
        print(f"   API Key found: {api_key[:8]}...")
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }
        
        data = {
            'model': 'claude-3-5-haiku-20241022',  # Fast and cost-effective
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': 4000,
            'temperature': 0.7
        }
        
        print(f"   Sending request to Anthropic...")
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=data,
            timeout=60
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Successfully received AI analysis")
            return result['content'][0]['text']
        else:
            print(f"❌ Anthropic API error: {response.status_code}")
            print(f"   Error details: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error calling Anthropic API: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def get_ai_analysis(self, prompt, market_data):
    """Get AI analysis from available API"""
    # Try OpenAI first
    if os.getenv('OPENAI_API_KEY'):
        print("🤖 Calling OpenAI for analysis...")
        analysis = self.call_openai_api(prompt)
        if analysis:
            return analysis, "OpenAI o4-mini"
    
    # Try Anthropic if OpenAI fails or not configured
    if os.getenv('ANTHROPIC_API_KEY'):
        print("🤖 Calling Anthropic Claude for analysis...")
        analysis = self.call_anthropic_api(prompt)
        if analysis:
            return analysis, "Anthropic Claude"
    
    # Fallback to basic analysis if no AI available
    print("⚠️ No AI API configured - using basic analysis")
    return self.create_basic_analysis(market_data), "Basic Analysis"

def create_basic_analysis(self, market_data):
    """Create a basic analysis without AI"""
    return f"""**MARKET PERFORMANCE**
```

{datetime.now().strftime(’%B %d, %Y’)}

{market_data}

**TOP MARKET & ECONOMY STORIES**

**Note:** AI analysis unavailable. Please configure OPENAI_API_KEY or ANTHROPIC_API_KEY for full analysis.

**GENERAL NEWS**

Based on article frequency, major themes in today’s news include Federal Reserve policy, technology sector developments, and geopolitical events. For detailed analysis and the top 15 stories with full summaries, please enable AI integration.

**Looking Ahead:** Market participants await tomorrow’s economic data releases and corporate earnings reports.”””

```
def convert_markdown_to_html(self, text):
    """Convert markdown-style formatting to HTML"""
    # Bold text
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # Format market data section specially
    if 'MARKET PERFORMANCE' in text:
        lines = text.split('\n')
        formatted_lines = []
        in_market_section = False
        
        for line in lines:
            if 'MARKET PERFORMANCE' in line:
                in_market_section = True
                formatted_lines.append(line)
            elif 'TOP MARKET & ECONOMY STORIES' in line or 'GENERAL NEWS' in line or 'Looking Ahead' in line:
                in_market_section = False
                formatted_lines.append(line)
            elif in_market_section and line.strip() and any(ticker in line for ticker in self.symbols):
                # Format market data lines with colors
                if '🟢' in line:
                    line = line.replace('🟢', '<span style="color: #27ae60;">🟢</span>')
                if '🔴' in line:
                    line = line.replace('🔴', '<span style="color: #e74c3c;">🔴</span>')
                # Make the line monospaced for better alignment
                formatted_line = '<div style="font-family: monospace; font-size: 14px; margin: 5px 0;">' + line + '</div>'
                formatted_lines.append(formatted_line)
            else:
                formatted_lines.append(line)
        
        text = '\n'.join(formatted_lines)
    
    # Convert headers - properly closed regex
    text = re.sub(r'^#{2,3} (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    
    # Line breaks and paragraphs
    text = text.replace('\n\n', '</p><p>')
    text = '<p>' + text + '</p>'
    
    # Clean up empty paragraphs and fix formatting
    text = text.replace('<p></p>', '')
    text = text.replace('<p><h3>', '<h3>')
    text = text.replace('</h3></p>', '</h3>')
    text = text.replace('<p><div', '<div')
    text = text.replace('</div></p>', '</div>')
    
    return text

def format_email_html(self, ai_analysis, analysis_source):
    """Format the AI analysis for email"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 3px solid #2c3e50;
            }}
            .header h1 {{
                color: #2c3e50;
                margin: 0;
                font-size: 28px;
            }}
            .meta {{
                color: #666;
                font-size: 14px;
                text-align: center;
                margin-top: 10px;
            }}
            .market-section {{
                background-color: #f0f8ff;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 30px;
                border-left: 4px solid #4169e1;
            }}
            .market-section h2 {{
                color: #2c3e50;
                margin-top: 0;
            }}
            .news-section {{
                margin-top: 30px;
            }}
            .news-section h2 {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            .story {{
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 1px solid #eee;
            }}
            .story:last-child {{
                border-bottom: none;
            }}
            .story h3 {{
                color: #2c3e50;
                font-size: 18px;
                margin-bottom: 10px;
            }}
            .story p {{
                color: #444;
                margin: 10px 0;
            }}
            .sources {{
                font-style: italic;
                color: #666;
                font-size: 14px;
            }}
            .ticker {{
                font-family: 'Courier New', monospace;
                font-weight: bold;
                color: #4169e1;
                background-color: #f0f8ff;
                padding: 2px 4px;
                border-radius: 3px;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #eee;
                text-align: center;
                color: #666;
                font-size: 12px;
            }}
            strong {{
                color: #2c3e50;
            }}
            hr {{
                border: none;
                border-top: 1px solid #eee;
                margin: 20px 0;
            }}
            pre {{
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
                font-family: 'Courier New', monospace;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Daily Market & News Briefing</h1>
                <div class="meta">
                    Generated: {timestamp}<br>
                    Analysis by: {source}
                </div>
            </div>
            
            <div class="content">
                {content}
            </div>
            
            <div class="footer">
                <p>This report was automatically generated by AI Market Aggregator</p>
                <p>Tracking: QQQ | SPY | DXY | IWM | GLD | BTCUSD | MP</p>
            </div>
        </div>
    </body>
    </html>
    """.format(
        timestamp=datetime.now().strftime('%B %d, %Y at %I:%M %p UTC'),
        source=analysis_source,
        content=self.convert_markdown_to_html(ai_analysis)
    )
    
    return html_template

def send_report_email(self, html_content):
    """Email the AI-analyzed report"""
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    recipient_email = os.getenv('RECIPIENT_EMAIL')
    
    if not all([sender_email, sender_password, recipient_email]):
        print("❌ Missing email configuration")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"📊 AI Market Intelligence - {datetime.now().strftime('%B %d, %Y')}"
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print("✅ AI analysis emailed successfully!")
        print(f"   Sent to: {recipient_email}")
        return True
        
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def run(self):
    """Main execution function"""
    print("🚀 AI MARKET AGGREGATOR - Starting Analysis")
    print(f"   Symbols: {', '.join(self.symbols)}")
    print(f"   RSS Feeds: {len(self.rss_feeds)} sources")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("-" * 60)
    
    # Step 1: Fetch market data
    print("\n📊 Step 1: Fetching market data...")
    market_data = self.fetch_market_data()
    
    # Step 2: Fetch RSS feeds
    print("\n📰 Step 2: Collecting news articles...")
    articles, feed_statuses = self.fetch_all_rss_feeds()
    
    # Step 3: Prepare AI prompt
    print(f"\n🧮 Step 3: Preparing AI analysis ({len(articles)} articles)...")
    prompt = self.prepare_ai_prompt(market_data, articles)
    print(f"   Prompt size: {len(prompt):,} characters")
    
    # Step 4: Get AI analysis
    print("\n🤖 Step 4: Getting AI analysis...")
    ai_analysis, analysis_source = self.get_ai_analysis(prompt, market_data)
    
    # Step 5: Format and send email
    print("\n📧 Step 5: Formatting and sending email...")
    html_content = self.format_email_html(ai_analysis, analysis_source)
    
    if self.send_report_email(html_content):
        print("\n🎉 AI market analysis completed successfully!")
    else:
        print("\n⚠️ Analysis completed but email failed")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Articles processed: {len(articles)}")
    print(f"Analysis source: {analysis_source}")
    print(f"Email sent: {'Yes' if self.send_report_email else 'No'}")
    print(f"Total execution time: Check GitHub Actions logs")
```

if **name** == “**main**”:
aggregator = AIMarketAggregator()
aggregator.run()
