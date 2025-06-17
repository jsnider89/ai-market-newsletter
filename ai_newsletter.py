# ai_newsletter.py
import anthropic
import openai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
import re
import requests
import json

class RealDataAINewsletterBot:
    def __init__(self):
        # Initialize both AI clients
        self.anthropic_client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        
        self.openai_client = openai.OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        
    def get_market_news(self):
        """Fetch real financial news from Marketaux API"""
        api_key = os.getenv('MARKETAUX_API_KEY')  # Free at marketaux.com
        
        if not api_key:
            return "No Marketaux API key found. Sign up free at marketaux.com"
        
        try:
            url = "https://api.marketaux.com/v1/news/all"
            params = {
                'api_token': api_key,
                'symbols': 'AAPL,TSLA,MSFT,GOOGL,AMZN,SPY,QQQ',
                'filter_entities': 'true',
                'limit': 10,
                'published_after': (datetime.now() - timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%S')
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'data' in data:
                news_items = []
                for article in data['data'][:8]:  # Top 8 articles
                    title = article.get('title', '')
                    description = article.get('description', '')
                    source = article.get('source', '')
                    published = article.get('published_at', '')
                    
                    # Get sentiment if available
                    entities = article.get('entities', [])
                    sentiment_info = ""
                    if entities:
                        entity = entities[0]
                        sentiment = entity.get('sentiment_score', 0)
                        if sentiment > 0.1:
                            sentiment_info = " (Positive sentiment)"
                        elif sentiment < -0.1:
                            sentiment_info = " (Negative sentiment)"
                        else:
                            sentiment_info = " (Neutral sentiment)"
                    
                    news_items.append(f"• {title}\n  {description}\n  Source: {source} | {published[:10]}{sentiment_info}")
                
                return "\\n\\n".join(news_items)
            else:
                return "Unable to fetch market news at this time"
                
        except Exception as e:
            return f"Error fetching news: {str(e)}"
    
    def get_market_data(self):
        """Fetch real market data from Finnhub API"""
        api_key = os.getenv('FINNHUB_API_KEY')  # Free at finnhub.io
        
        if not api_key:
            return "No Finnhub API key found. Sign up free at finnhub.io"
        
        try:
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'SPY', 'QQQ', 'DJI', 'IXIC']
            market_data = []
            
            for symbol in symbols:
                url = f"https://finnhub.io/api/v1/quote"
                params = {
                    'symbol': symbol,
                    'token': api_key
                }
                
                response = requests.get(url, params=params, timeout=5)
                data = response.json()
                
                if 'c' in data:  # Current price
                    current = data['c']
                    change = data.get('d', 0)
                    change_pct = data.get('dp', 0)
                    
                    direction = "📈" if change >= 0 else "📉"
                    market_data.append(f"{symbol}: ${current:.2f} {direction} {change:+.2f} ({change_pct:+.2f}%)")
            
            return "\\n".join(market_data) if market_data else "Unable to fetch market data"
            
        except Exception as e:
            return f"Error fetching market data: {str(e)}"
    
    def get_economic_calendar(self):
        """Fetch economic calendar from Finnhub"""
        api_key = os.getenv('FINNHUB_API_KEY')
        
        if not api_key:
            return "Economic calendar unavailable - no Finnhub API key"
        
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            
            url = f"https://finnhub.io/api/v1/calendar/economic"
            params = {
                'from': today,
                'to': tomorrow,
                'token': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'economicCalendar' in data and data['economicCalendar']:
                events = []
                for event in data['economicCalendar'][:10]:  # Top 10 events
                    time = event.get('time', '')
                    event_name = event.get('event', '')
                    impact = event.get('impact', '')
                    country = event.get('country', '')
                    
                    if event_name and time:
                        # Convert timestamp to readable time
                        try:
                            dt = datetime.fromtimestamp(int(time))
                            time_str = dt.strftime('%I:%M %p ET')
                        except:
                            time_str = "TBD"
                        
                        events.append(f"• {time_str}: {event_name} ({country}) - Impact: {impact}")
                
                return "\\n".join(events) if events else "No major economic events scheduled"
            else:
                return "No economic events found for today/tomorrow"
                
        except Exception as e:
            return f"Error fetching economic calendar: {str(e)}"
    
    def get_morning_prompt(self, news_data, market_data, calendar_data):
        """Morning summary prompt with real data"""
        return f"""I have gathered REAL current market data for you to analyze. Please create a comprehensive morning market summary based on this actual data:

CURRENT MARKET PRICES & PERFORMANCE:
{market_data}

RECENT FINANCIAL NEWS (Last 12 hours with sentiment):
{news_data}

TODAY'S ECONOMIC CALENDAR:
{calendar_data}

You are provided with REAL, current market data above. Please analyze this actual information and provide:

1. **Market Performance Analysis**: Review the current market prices and movements shown above. Which stocks/indices are up or down? What are the significant percentage moves?

2. **News Impact Assessment**: Based on the actual news headlines provided, explain:
   - What are the key stories affecting markets?
   - How might the sentiment (positive/negative/neutral) impact trading?
   - Any earnings, economic data, or central bank developments

3. **Economic Calendar Priorities**: From the scheduled events listed above, which ones should traders watch most closely today?

4. **Trading Outlook**: Given this real market data, what themes and opportunities should investors focus on?

Please write this as a professional morning briefing using the actual data provided above. Do not search for additional information - analyze what I've given you."""

    def get_evening_prompt(self, news_data, market_data, calendar_data):
        """Evening summary prompt with real data"""
        return f"""I have gathered REAL current market data for you to analyze. Please create a comprehensive evening market summary based on this actual data:

TODAY'S FINAL MARKET PERFORMANCE:
{market_data}

TODAY'S FINANCIAL NEWS STORIES:
{news_data}

TOMORROW'S ECONOMIC CALENDAR:
{calendar_data}

You are provided with REAL, current market data above. Please analyze this actual information and provide:

1. **Today's Market Wrap-Up**: Review the market performance data shown above. How did major stocks and indices close? What were the biggest winners and losers?

2. **News-Driven Market Moves**: Based on the actual news stories provided, explain:
   - Which headlines likely drove market action today?
   - How did sentiment (positive/negative/neutral) play out in trading?
   - Key earnings, economic releases, or policy developments

3. **Tomorrow's Key Events**: From the economic calendar provided, what should traders prepare for tomorrow?

4. **Market Themes**: What were today's dominant themes based on this real performance and news data?

Please write this as a professional end-of-day briefing using the actual data provided above. Do not search for additional information - analyze what I've given you."""

    def query_claude(self, prompt):
        """Get response from Claude"""
        try:
            print("🤖 Querying Claude with real market data...")
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ]
            )
            return message.content[0].text
            
        except Exception as e:
            return f"Claude Error: {str(e)}"
    
    def query_chatgpt(self, prompt):
        """Get response from ChatGPT"""
        try:
            print("🤖 Querying ChatGPT with real market data...")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a professional financial analyst. The user will provide you with REAL current market data, news, and economic events. Your job is to analyze this actual data and provide insights. Do not attempt to search for additional information - work only with the data provided to you."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=4000,
                temperature=0.1
            )
            return response.choices[0].message.content
            
        except Exception as e:
            return f"ChatGPT Error: {str(e)}"
    
    def generate_dual_summary(self):
        """Generate summaries from both AIs with real data"""
        
        current_hour = datetime.now().hour
        
        # Fetch real market data
        print("📊 Fetching real market data...")
        market_data = self.get_market_data()
        
        print("📰 Fetching financial news...")
        news_data = self.get_market_news()
        
        print("📅 Fetching economic calendar...")
        calendar_data = self.get_economic_calendar()
        
        # Determine prompt based on time
        if current_hour == 11 or current_hour < 14:  # Morning summary
            prompt_claude = self.get_morning_prompt(news_data, market_data, calendar_data)
            prompt_chatgpt = self.get_morning_prompt(news_data, market_data, calendar_data)
            summary_type = "Morning Market Summary"
        else:  # Evening summary
            prompt_claude = self.get_evening_prompt(news_data, market_data, calendar_data)
            prompt_chatgpt = self.get_evening_prompt(news_data, market_data, calendar_data)
            summary_type = "Evening Market Summary"
        
        print(f"📝 Generating {summary_type} with real data...")
        
        # Query both AIs with the same real data
        claude_response = self.query_claude(prompt_claude)
        chatgpt_response = self.query_chatgpt(prompt_chatgpt)
        
        # Combine responses
        combined_summary = f"""# {summary_type} - {datetime.now().strftime('%B %d, %Y')}

## 📊 Real Market Data Used

**Current Market Snapshot:**
{market_data.replace(chr(10), chr(10))}

---

## 🤖 Claude's Analysis

{claude_response}

---

## 🧠 ChatGPT's Analysis

{chatgpt_response}

---

## 📊 Data Sources

- **Market Data**: Finnhub API (Real-time prices)
- **Financial News**: Marketaux API (Last 12 hours)
- **Economic Calendar**: Finnhub API (Today/Tomorrow)

Both AI models analyzed the same real market data above. Compare their interpretations and insights!
"""
        
        return combined_summary
    
    def send_email_summary(self, ai_response):
        """Email the dual AI summary"""
        
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        recipient_email = os.getenv('RECIPIENT_EMAIL')
        
        if not all([sender_email, sender_password, recipient_email]):
            print("Error: Missing email configuration. Check your secrets.")
            return
        
        # Determine summary type for subject line
        current_hour = datetime.now().hour
        if current_hour == 11 or current_hour < 14:
            summary_type = "Morning"
            emoji = "🌅"
        else:
            summary_type = "Evening"
            emoji = "🌆"
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"{emoji} Real Data AI Market Analysis - {datetime.now().strftime('%B %d, %Y')}"
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        # Convert to HTML
        html_content = self.convert_markdown_to_html(ai_response)
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
                print("✅ Real data AI summary sent successfully!")
                print(f"   Type: {summary_type} Summary")
                print(f"   Models: Claude + ChatGPT with real market data")
                print(f"   Sent to: {recipient_email}")
                print(f"   At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"❌ Email error: {e}")
    
    def convert_markdown_to_html(self, content):
        """Convert markdown-style content to HTML for email"""
        
        # Convert headers
        content = re.sub(r'^### (.*?)$', r'<h3>\\1</h3>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.*?)$', r'<h2>\\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^# (.*?)$', r'<h1>\\1</h1>', content, flags=re.MULTILINE)
        
        # Convert bold text
        content = re.sub(r'\\*\\*(.*?)\\*\\*', r'<strong>\\1</strong>', content)
        
        # Convert bullet points
        lines = content.split('\\n')
        in_list = False
        formatted_lines = []
        
        for line in lines:
            if line.strip().startswith('•') or (line.strip().startswith('*') and not line.strip().startswith('**')):
                if not in_list:
                    formatted_lines.append('<ul>')
                    in_list = True
                item_text = line.strip()[1:].strip()
                formatted_lines.append(f'<li>{item_text}</li>')
            else:
                if in_list:
                    formatted_lines.append('</ul>')
                    in_list = False
                formatted_lines.append(line)
        
        if in_list:
            formatted_lines.append('</ul>')
        
        content = '\\n'.join(formatted_lines)
        
        # Handle horizontal rules
        content = content.replace('---', '<hr>')
        
        # Convert paragraphs
        paragraphs = content.split('\\n\\n')
        formatted_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if (para.startswith('<') and para.endswith('>')) or '<h' in para or '<ul>' in para or '<hr>' in para:
                formatted_paragraphs.append(para)
            else:
                formatted_paragraphs.append(f'<p>{para}</p>')
        
        content = '\\n'.join(formatted_paragraphs)
        
        # Clean up
        content = re.sub(r'<p>\\s*</p>', '', content)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{ 
                    color: #2c3e50; 
                    border-bottom: 3px solid #3498db; 
                    padding-bottom: 15px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                h2 {{ 
                    color: #34495e; 
                    margin-top: 40px;
                    margin-bottom: 20px;
                    padding: 15px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 8px;
                    text-align: center;
                    font-size: 1.3em;
                }}
                h3 {{ 
                    color: #7f8c8d; 
                    margin-top: 25px;
                    border-left: 4px solid #3498db;
                    padding-left: 15px;
                }}
                ul {{ 
                    margin: 15px 0; 
                    padding-left: 25px; 
                    background: #f8f9fa;
                    padding: 15px 25px;
                    border-radius: 5px;
                    border-left: 4px solid #e9ecef;
                }}
                li {{ 
                    margin: 10px 0; 
                    line-height: 1.5;
                }}
                p {{ 
                    margin: 15px 0; 
                    line-height: 1.6;
                }}
                hr {{ 
                    border: none; 
                    border-top: 3px solid #3498db; 
                    margin: 40px 0;
                    opacity: 0.6;
                }}
                .market-data {{
                    background: #e8f4fd;
                    border: 1px solid #3498db;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                    font-family: monospace;
                }}
                .footer {{ 
                    margin-top: 50px; 
                    padding-top: 25px; 
                    border-top: 2px solid #eee;
                    font-size: 13px;
                    color: #7f8c8d;
                    text-align: center;
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                }}
                strong {{
                    color: #2c3e50;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                {content}
                
                <div class="footer">
                    <p><strong>🚀 Real Data AI Market Analysis</strong></p>
                    <p>Claude + ChatGPT analyzing live market data from Finnhub & Marketaux APIs</p>
                    <p>Generated automatically via GitHub Actions</p>
                    <p>Repository: <a href="https://github.com/{os.getenv('GITHUB_REPOSITORY', 'your-repo')}" style="color: #3498db;">{os.getenv('GITHUB_REPOSITORY', 'your-repo')}</a></p>
                    <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def run_daily_summary(self):
        """Main function to generate and send dual AI summary with real data"""
        current_hour = datetime.now().hour
        summary_type = "Morning" if (current_hour == 11 or current_hour < 14) else "Evening"
        
        print(f"🚀 Starting Real Data AI {summary_type} summary...")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"   Models: Claude + ChatGPT")
        print(f"   Data: Live APIs (Finnhub + Marketaux)")
        
        # Generate dual summary with real data
        dual_summary = self.generate_dual_summary()
        
        if "Error" in dual_summary and len(dual_summary) < 500:
            print(f"❌ AI Error: {dual_summary}")
            return
        
        print("✅ Real data AI summary generated successfully!")
        print(f"   Length: {len(dual_summary)} characters")
        
        # Send via email
        print("📧 Sending real data comparison email...")
        self.send_email_summary(dual_summary)
        
        print("🎉 Real data AI summary process completed!")

if __name__ == "__main__":
    bot = RealDataAINewsletterBot()
    bot.run_daily_summary()
