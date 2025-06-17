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
                        "content": "You are a financial analyst. The user is asking for current market information. If you cannot access real-time data, clearly explain your limitations but then provide the most helpful analysis you can based on general market principles and typical patterns. Be specific about what data sources the user should check for real-time information."
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
        
        # Handle markdown tables first (before other conversions)
        content = self.convert_tables_to_html(content)
        
        # Convert headers
        content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
        
        # Convert bold text
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        
        # Convert numbered lists
        content = self.convert_numbered_lists(content)
        
        # Convert bullet points
        lines = content.split('\n')
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
        
        content = '\n'.join(formatted_lines)
        
        # Handle horizontal rules
        content = content.replace('---', '<hr>')
        
        # Convert paragraphs (but preserve existing HTML tags)
        paragraphs = content.split('\n\n')
        formatted_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            # Don't wrap HTML elements in paragraphs
            if (para.startswith('<') and para.endswith('>')) or '<table>' in para or '<h' in para or '<ul>' in para or '<hr>' in para:
                formatted_paragraphs.append(para)
            else:
                formatted_paragraphs.append(f'<p>{para}</p>')
        
        content = '\n'.join(formatted_paragraphs)
        
        # Clean up
        content = re.sub(r'<p>\s*</p>', '', content)
        
        return content
        
    def convert_tables_to_html(self, content):
        """Convert markdown tables to HTML tables"""
        lines = content.split('\n')
        result_lines = []
        in_table = False
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this line starts a table (contains |)
            if '|' in line and not in_table:
                # Look ahead to see if next line is a separator
                if i + 1 < len(lines) and '---' in lines[i + 1] and '|' in lines[i + 1]:
                    # Start of table
                    in_table = True
                    result_lines.append('<table>')
                    
                    # Process header row
                    headers = [cell.strip() for cell in line.split('|') if cell.strip()]
                    result_lines.append('<thead><tr>')
                    for header in headers:
                        result_lines.append(f'<th>{header}</th>')
                    result_lines.append('</tr></thead>')
                    
                    # Skip separator line
                    i += 2
                    result_lines.append('<tbody>')
                    continue
                else:
                    result_lines.append(line)
            elif in_table and '|' in line:
                # Table row
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                result_lines.append('<tr>')
                for cell in cells:
                    result_lines.append(f'<td>{cell}</td>')
                result_lines.append('</tr>')
            elif in_table and '|' not in line.strip():
                # End of table
                result_lines.append('</tbody>')
                result_lines.append('</table>')
                result_lines.append(line)
                in_table = False
            else:
                result_lines.append(line)
            
            i += 1
        
        # Close table if we ended while still in one
        if in_table:
            result_lines.append('</tbody>')
            result_lines.append('</table>')
        
        return '\n'.join(result_lines)
    
    def convert_numbered_lists(self, content):
        """Convert numbered lists to HTML"""
        lines = content.split('\n')
        result_lines = []
        in_numbered_list = False
        
        for line in lines:
            # Check for numbered list item (1. 2. etc.)
            if re.match(r'^\s*\d+\.\s+', line):
                if not in_numbered_list:
                    result_lines.append('<ol>')
                    in_numbered_list = True
                item_text = re.sub(r'^\s*\d+\.\s+', '', line)
                result_lines.append(f'<li>{item_text}</li>')
            else:
                if in_numbered_list:
                    result_lines.append('</ol>')
                    in_numbered_list = False
                result_lines.append(line)
        
        if in_numbered_list:
            result_lines.append('</ol>')
        
        return '\n'.join(result_lines)
        
    def get_html_template(self, content):
        """Generate the complete HTML email template"""
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
                ol {{ 
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
                .ai-section {{
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 25px;
                    margin: 20px 0;
                    border-left: 5px solid #3498db;
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
                table {{ 
                    border-collapse: collapse; 
                    width: 100%; 
                    margin: 20px 0;
                    background: white;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                th {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    font-weight: bold;
                    padding: 15px 12px;
                    text-align: left;
                }}
                td {{ 
                    border-bottom: 1px solid #eee;
                    padding: 12px;
                    text-align: left;
                }}
                tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                tr:hover {{
                    background-color: #e8f4fd;
                }}
                .comparison-header {{
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    margin: 30px 0;
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
                    <p><strong>🤖 Dual AI Market Analysis</strong></p>
                    <p>Claude (Anthropic) vs ChatGPT (OpenAI) • Same prompt, different perspectives</p>
                    <p>Generated automatically via GitHub Actions</p>
                    <p>Repository: <a href="https://github.com/{os.getenv('GITHUB_REPOSITORY', 'your-repo')}" style="color: #3498db;">{os.getenv('GITHUB_REPOSITORY', 'your-repo')}</a></p>
                    <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                </div>
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
