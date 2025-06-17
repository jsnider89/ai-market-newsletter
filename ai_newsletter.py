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
        
    def get_morning_prompt(self):
        """Morning summary prompt focusing on overnight developments"""
        return """Please search the web and summarize all major developments that occurred overnight (from the U.S. perspective) in macroeconomics, politics, and technology. Use your web search capabilities to find current information from Asia, Europe, and early-morning U.S. markets.

Prioritize:
• Central bank activity (BoJ, ECB, RBA, etc.) - search for any overnight decisions or statements
• Economic indicators released overnight (e.g., CPI, GDP, sentiment indices, PMI) from Asian and European markets
• Political news or conflicts (G7 statements, international diplomacy, major elections)
• Tech sector updates, including corporate earnings or announcements from overseas markets
• Major financial market movements in Asia and Europe (indices, forex, commodities)

After the overnight summary, search for today's economic calendar and include a forward-looking briefing of what's happening later today. Present the calendar in a table with event names, scheduled times (ET), and relevance to markets.

Please use web search to get current, real-time information for today's date."""

    def get_evening_prompt(self):
        """Evening summary prompt focusing on the day's events and tomorrow's outlook"""
        return """Please search the web and summarize today's major market developments in macroeconomics, politics, and technology. Use your web search capabilities to find current information about today's key events.

Focus on:
• Major U.S. economic data releases and their market impact
• Federal Reserve or other central bank statements/actions
• Significant political developments affecting markets
• Key earnings reports or tech announcements
• Major market movements (stocks, bonds, commodities, forex)
• Any breaking news that moved markets today

After today's summary, search for tomorrow's economic calendar and provide an outlook for upcoming events. Present tomorrow's key events in a table with event names, scheduled times (ET), and expected market relevance.

Please use web search to get current, real-time information for today's events and tomorrow's calendar."""

    def generate_market_summary(self):
        """Send time-appropriate prompt to Claude with web search instruction"""
        
        current_hour = datetime.now().hour
        
        # Determine if this is morning or evening summary based on UTC time
        # 11 UTC = 7 AM ET (morning), 21 UTC = 5 PM ET (evening)
        if current_hour == 11 or current_hour < 14:  # Morning summary
            prompt = self.get_morning_prompt()
            summary_type = "Morning Market Summary"
        else:  # Evening summary
            prompt = self.get_evening_prompt()
            summary_type = "Evening Market Summary"

        try:
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
            
            # Add context about which type of summary this is
            response = f"# {summary_type} - {datetime.now().strftime('%B %d, %Y')}\n\n"
            response += message.content[0].text
            
            return response
            
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
        
        # Determine summary type for subject line
        current_hour = datetime.now().hour
        if current_hour == 11 or current_hour < 14:
            summary_type = "Morning"
        else:
            summary_type = "Evening"
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🌅 {summary_type} AI Market Summary - {datetime.now().strftime('%B %d, %Y')}"
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        # Convert markdown to HTML for better formatting
        html_content = self.convert_markdown_to_html(ai_response)
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
                print("✅ AI summary sent successfully!")
                print(f"   Type: {summary_type} Summary")
                print(f"   Sent to: {recipient_email}")
                print(f"   At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"❌ Email error: {e}")
    
    def convert_markdown_to_html(self, content):
        """Convert markdown-style content to HTML for email"""
        
        # Convert headers
        content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
        
        # Convert bold text
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        
        # Convert bullet points
        lines = content.split('\n')
        in_list = False
        formatted_lines = []
        
        for line in lines:
            if line.strip().startswith('•') or line.strip().startswith('-'):
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
        
        content = '\n'.join(formatted_lines)
        
        # Convert line breaks to paragraphs
        paragraphs = content.split('\n\n')
        content = '</p><p>'.join(paragraphs)
        content = f'<p>{content}</p>'
        
        # Clean up empty paragraphs
        content = re.sub(r'<p>\s*</p>', '', content)
        
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
                li {{ margin: 8px 0; }}
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
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                p {{ margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="content">
                {content}
            </div>
            
            <div class="footer">
                <p>Generated automatically by Claude AI via GitHub Actions</p>
                <p>Repository: <a href="https://github.com/{os.getenv('GITHUB_REPOSITORY', 'your-repo')}">{os.getenv('GITHUB_REPOSITORY', 'your-repo')}</a></p>
                <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            </div>
        </body>
        </html>
        """
    
    def run_daily_summary(self):
        """Main function to generate and send daily summary"""
        current_hour = datetime.now().hour
        summary_type = "Morning" if (current_hour == 11 or current_hour < 14) else "Evening"
        
        print(f"🚀 Starting {summary_type} AI summary generation...")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        # Get AI summary
        print(f"📡 Generating {summary_type} AI summary with web search...")
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
