# ai_newsletter.py
import anthropic
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import re

class AINewsletterBot:
    def __init__(self):
        self.anthropic_client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        
    def generate_market_summary(self):
        """Send your exact prompt to Claude"""
        
        current_time = datetime.now()
        time_context = "morning summary" if current_time.hour < 14 else "evening summary"
        
        prompt = f"""Please summarize all major developments that occurred overnight (from the U.S. perspective) in macroeconomics, politics, and technology. Focus on events and releases from Asia, Europe, and early-morning U.S. markets.

Prioritize:
- Central bank activity (BoJ, ECB, RBA, etc.)
- Economic indicators released overnight (e.g., CPI, GDP, sentiment indices, PMI)
- Political news or conflicts (G7 statements, international diplomacy, major elections)
- Tech sector updates, including corporate earnings or announcements abroad
- Major financial market movements in Asia and Europe (indices, forex, commodities)

After the overnight summary, include a forward-looking briefing of what's happening later today, using economic calendars as a source. Present it in a table with event names, scheduled times (ET), and relevance to markets.

Note: This is a {time_context} for {current_time.strftime('%B %d, %Y')}."""

        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
            
        except Exception as e:
            return f"Error generating summary: {str(e)}\n\nPlease check your API key and try again."
    
    def send_email_summary(self, ai_response):
        """Email the AI-generated summary"""
        
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        recipient_email = os.getenv('RECIPIENT_EMAIL')
        
        if not all([sender_email, sender_password, recipient_email]):
            print("Error: Missing email configuration. Check your secrets.")
            return
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🤖 Daily AI Market Summary - {datetime.now().strftime('%B %d, %Y')}"
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        # Create HTML email
        html_content = f"""
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
                }}
                h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                h3 {{ color: #7f8c8d; }}
                .header {{ 
                    background: #f8f9fa; 
                    padding: 15px; 
                    border-left: 4px solid #3498db;
                    margin-bottom: 20px;
                }}
                .footer {{ 
                    margin-top: 30px; 
                    padding-top: 20px; 
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #7f8c8d;
                }}
                ul {{ margin: 10px 0; padding-left: 20px; }}
                li {{ margin: 5px 0; }}
                table {{ 
                    border-collapse: collapse; 
                    width: 100%; 
                    margin: 15px 0;
                }}
                th, td {{ 
                    border: 1px solid #ddd; 
                    padding: 8px; 
                    text-align: left;
                }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 Daily AI Market Summary</h1>
                <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p ET')}</p>
            </div>
            
            <div class="content">
                <div style="white-space: pre-wrap; line-height: 1.6;">
                    {ai_response.replace('<', '&lt;').replace('>', '&gt;')}
                </div>
            </div>
            
            <div class="footer">
                <p>Generated automatically by Claude AI via GitHub Actions</p>
                <p>Repository: <a href="https://github.com/{os.getenv('GITHUB_REPOSITORY', 'your-repo')}">{os.getenv('GITHUB_REPOSITORY', 'your-repo')}</a></p>
            </div>
        </body>
        </html>
        """
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
                print("✅ AI summary sent successfully!")
                print(f"   Sent to: {recipient_email}")
                print(f"   At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"❌ Email error: {e}")
    
    def run_daily_summary(self):
        """Main function to generate and send daily summary"""
        print(f"🚀 Starting daily AI summary generation...")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        # Get AI summary
        print("📡 Generating AI summary...")
        ai_summary = self.generate_market_summary()
        
        if "Error generating summary" in ai_summary:
            print(f"❌ AI Error: {ai_summary}")
            return
        
        print("✅ AI summary generated successfully!")
        print(f"   Length: {len(ai_summary)} characters")
        
        # Send via email
        print("📧 Sending email...")
        self.send_email_summary(ai_summary)
        
        print("🎉 Daily AI summary process completed!")

if __name__ == "__main__":
    bot = AINewsletterBot()
    bot.run_daily_summary()
