# ai_newsletter.py
import anthropic
import openai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import re

class DualAINewsletterBot:
    def __init__(self):
        # Initialize both AI clients
        self.anthropic_client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        
        # OpenAI client
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.openai_client = openai.OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        
    def get_morning_prompt(self):
        """Morning summary prompt focusing on overnight developments"""
        return """Please search the web and summarize all major developments that occurred overnight (from the U.S. perspective) in macroeconomics, politics, and technology. Focus on events and releases from Asia, Europe, and early-morning U.S. markets.

Prioritize:
• Central bank activity (BoJ, ECB, RBA, etc.) - any overnight decisions or statements
• Economic indicators released overnight (e.g., CPI, GDP, sentiment indices, PMI) from Asian and European markets
• Political news or conflicts (G7 statements, international diplomacy, major elections)
• Tech sector updates, including corporate earnings or announcements from overseas markets
• Major financial market movements in Asia and Europe (indices, forex, commodities)

After the overnight summary, include a forward-looking briefing of what's happening later today. Present today's key events in a table with event names, scheduled times (ET), and relevance to markets.

Please use current, real-time information for today's date."""

    def get_evening_prompt(self):
        """Evening summary prompt focusing on the day's events and tomorrow's outlook"""
        return """Please search the web and summarize today's major market developments in macroeconomics, politics, and technology. Focus on today's key events that moved markets.

Focus on:
• Major U.S. economic data releases and their market impact today
• Federal Reserve or other central bank statements/actions today
• Significant political developments affecting markets today
• Key earnings reports or tech announcements today
• Major market movements today (stocks, bonds, commodities, forex)
• Any breaking news that moved markets today

After today's summary, provide an outlook for tomorrow's key events. Present tomorrow's events in a table with event names, scheduled times (ET), and expected market relevance.

Please use current, real-time information for today's events and tomorrow's outlook."""

    def query_claude(self, prompt):
        """Get response from Claude"""
        try:
            print("🤖 Querying Claude...")
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
            
        except Exception as e:
            return f"Claude Error: {str(e)}"
    
    def query_chatgpt(self, prompt):
        """Get response from ChatGPT"""
        try:
            print("🤖 Querying ChatGPT...")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Latest GPT-4 model with web browsing
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a financial analyst with access to current market data. Use web browsing to get real-time information."
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
        """Generate summaries from both AIs"""
        
        current_hour = datetime.now().hour
        
        # Determine prompt based on time
        if current_hour == 11 or current_hour < 14:  # Morning summary
            prompt = self.get_morning_prompt()
            summary_type = "Morning Market Summary"
        else:  # Evening summary
            prompt = self.get_evening_prompt()
            summary_type = "Evening Market Summary"
        
        print(f"📝 Using {summary_type} prompt...")
        
        # Query both AIs with the same prompt
        claude_response = self.query_claude(prompt)
        chatgpt_response = self.query_chatgpt(prompt)
        
        # Combine responses
        combined_summary = f"""# {summary_type} - {datetime.now().strftime('%B %d, %Y')}

## 🤖 Claude's Analysis

{claude_response}

---

## 🧠 ChatGPT's Analysis

{chatgpt_response}

---

## 📊 Comparison Summary

Both AI models were given identical prompts requesting current market analysis. Above you can see how each interpreted and responded to the same request.

**Key Differences to Note:**
- Data sources and recency
- Analysis style and depth
- Specific insights highlighted
- Formatting and organization
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
        msg['Subject'] = f"{emoji} Dual AI Market Comparison - {datetime.now().strftime('%B %d, %Y')}"
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
                print("✅ Dual AI summary sent successfully!")
                print(f"   Type: {summary_type} Summary")
                print(f"   Models: Claude + ChatGPT")
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
        
        # Handle horizontal rules
        content = content.replace('---', '<hr>')
        
        # Convert paragraphs
        paragraphs = content.split('\n\n')
        content = '</p><p>'.join(paragraphs)
        content = f'<p>{content}</p>'
        
        # Clean up
        content = re.sub(r'<p>\s*</p>', '', content)
        content = re.sub(r'<p>\s*<h', '<h', content)
        content = re.sub(r'</h([1-6])>\s*</p>', '</h\\1>', content)
        content = re.sub(r'<p>\s*<hr>', '<hr>', content)
        content = re.sub(r'<hr>\s*</p>', '<hr>', content)
        content = re.sub(r'<p>\s*<ul>', '<ul>', content)
        content = re.sub(r'</ul>\s*</p>', '</ul>', content)
        
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
                }}
                h1 {{ 
                    color: #2c3e50; 
                    border-bottom: 3px solid #3498db; 
                    padding-bottom: 10px;
                    text-align: center;
                }}
                h2 {{ 
                    color: #34495e; 
                    margin-top: 30px;
                    padding: 10px;
                    background: #f8f9fa;
                    border-left: 4px solid #3498db;
                }}
                h3 {{ color: #7f8c8d; }}
                ul {{ margin: 10px 0; padding-left: 20px; }}
                li {{ margin: 8px 0; }}
                p {{ margin: 12px 0; }}
                hr {{ 
                    border: none; 
                    border-top: 2px solid #eee; 
                    margin: 30px 0;
                }}
                .footer {{ 
                    margin-top: 40px; 
                    padding-top: 20px; 
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #7f8c8d;
                    text-align: center;
                }}
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
            </style>
        </head>
        <body>
            <div class="content">
                {content}
            </div>
            
            <div class="footer">
                <p><strong>Dual AI Market Analysis</strong></p>
                <p>Claude (Anthropic) vs ChatGPT (OpenAI) • Same prompt, different perspectives</p>
                <p>Generated automatically via GitHub Actions</p>
                <p>Repository: <a href="https://github.com/{os.getenv('GITHUB_REPOSITORY', 'your-repo')}">{os.getenv('GITHUB_REPOSITORY', 'your-repo')}</a></p>
                <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            </div>
        </body>
        </html>
        """
    
    def run_daily_summary(self):
        """Main function to generate and send dual AI summary"""
        current_hour = datetime.now().hour
        summary_type = "Morning" if (current_hour == 11 or current_hour < 14) else "Evening"
        
        print(f"🚀 Starting Dual AI {summary_type} summary generation...")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"   Models: Claude + ChatGPT")
        
        # Generate dual summary
        dual_summary = self.generate_dual_summary()
        
        if "Error" in dual_summary and len(dual_summary) < 500:
            print(f"❌ AI Error: {dual_summary}")
            return
        
        print("✅ Dual AI summary generated successfully!")
        print(f"   Length: {len(dual_summary)} characters")
        
        # Send via email
        print("📧 Sending comparison email...")
        self.send_email_summary(dual_summary)
        
        print("🎉 Dual AI summary process completed!")

if __name__ == "__main__":
    bot = DualAINewsletterBot()
    bot.run_daily_summary()
