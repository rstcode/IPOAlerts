import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Union
from dotenv import load_dotenv

load_dotenv()


def create_ipo_email_template(ipo_data: Union[Dict, List]) -> str:
    """
    Create a rich HTML email template for IPO data
    
    Args:
        ipo_data: IPO data as dictionary or list of IPOs (JSON format)
    
    Returns:
        HTML formatted email body
    """
    
    # Convert to dict if string
    if isinstance(ipo_data, str):
        ipo_data = json.loads(ipo_data)
    
    # Ensure it's a list
    ipos = ipo_data.get("ipos", []) if isinstance(ipo_data, dict) else ipo_data
    week_info = ipo_data.get("week", "N/A") if isinstance(ipo_data, dict) else "N/A"
    
    html_body = f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .header p {{
                    margin: 5px 0 0 0;
                    font-size: 14px;
                    opacity: 0.95;
                }}
                .week-info {{
                    background-color: #f0f4ff;
                    padding: 10px;
                    border-left: 4px solid #667eea;
                    margin-bottom: 20px;
                    border-radius: 4px;
                }}
                .ipo-card {{
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 20px;
                    background-color: #fafafa;
                }}
                .ipo-header {{
                    border-bottom: 2px solid #667eea;
                    padding-bottom: 10px;
                    margin-bottom: 15px;
                }}
                .company-name {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #667eea;
                }}
                .sector {{
                    display: inline-block;
                    background-color: #667eea;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    margin-left: 10px;
                }}
                .info-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin-bottom: 15px;
                }}
                .info-item {{
                    background-color: white;
                    padding: 10px;
                    border-radius: 4px;
                    border-left: 3px solid #764ba2;
                }}
                .info-label {{
                    font-size: 12px;
                    color: #666;
                    font-weight: bold;
                    text-transform: uppercase;
                }}
                .info-value {{
                    font-size: 16px;
                    color: #333;
                    font-weight: bold;
                    margin-top: 5px;
                }}
                .subscription {{
                    background-color: white;
                    padding: 12px;
                    border-radius: 4px;
                    margin: 10px 0;
                }}
                .subscription-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 8px 0;
                    border-bottom: 1px solid #eee;
                }}
                .subscription-row:last-child {{
                    border-bottom: none;
                }}
                .demand-badge {{
                    display: inline-block;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                    margin-right: 10px;
                }}
                .demand-strong {{
                    background-color: #d4edda;
                    color: #155724;
                }}
                .demand-moderate {{
                    background-color: #fff3cd;
                    color: #856404;
                }}
                .demand-weak {{
                    background-color: #f8d7da;
                    color: #721c24;
                }}
                .risk-low {{
                    background-color: #d4edda;
                    color: #155724;
                }}
                .risk-medium {{
                    background-color: #fff3cd;
                    color: #856404;
                }}
                .risk-high {{
                    background-color: #f8d7da;
                    color: #721c24;
                }}
                .suitable-for {{
                    background-color: white;
                    padding: 10px;
                    border-radius: 4px;
                    margin-top: 10px;
                }}
                .suitable-for ul {{
                    margin: 5px 0;
                    padding-left: 20px;
                }}
                .suitable-for li {{
                    margin: 5px 0;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    color: #666;
                    font-size: 12px;
                    border-top: 1px solid #e0e0e0;
                    margin-top: 20px;
                }}
                .no-ipos {{
                    text-align: center;
                    padding: 40px 20px;
                    color: #666;
                    font-size: 16px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📈 IPO Alerts</h1>
                    <p>Weekly IPO Opening Summary - India</p>
                </div>
                
                <div class="week-info">
                    <strong>Week:</strong> {week_info}
                </div>
    """
    
    # Add IPO cards
    if ipos:
        for ipo in ipos:
            demand_class = f"demand-{ipo.get('demand_level', 'Moderate').lower()}"
            risk_class = f"risk-{ipo.get('risk_level', 'Medium').lower()}"
            
            subscription = ipo.get('subscription', {})
            suitable_for = ipo.get('suitable_for', [])
            
            html_body += f"""
                <div class="ipo-card">
                    <div class="ipo-header">
                        <div>
                            <span class="company-name">{ipo.get('company_name', 'N/A')}</span>
                            <span class="sector">{ipo.get('sector', 'N/A')}</span>
                        </div>
                    </div>
                    
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Price Band</div>
                            <div class="info-value">{ipo.get('price_band', 'N/A')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">GMP</div>
                            <div class="info-value">{ipo.get('gmp', 'N/A')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Opening Date</div>
                            <div class="info-value">{ipo.get('open_date', 'N/A')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Closing Date</div>
                            <div class="info-value">{ipo.get('close_date', 'N/A')}</div>
                        </div>
                    </div>
                    
                    <div class="subscription">
                        <div class="subscription-row">
                            <strong>Retail Subscription:</strong>
                            <span>{subscription.get('retail', 'N/A')}</span>
                        </div>
                        <div class="subscription-row">
                            <strong>QIB Subscription:</strong>
                            <span>{subscription.get('qib', 'N/A')}</span>
                        </div>
                        <div class="subscription-row">
                            <strong>Overall Subscription:</strong>
                            <span>{subscription.get('overall', 'N/A')}</span>
                        </div>
                    </div>
                    
                    <div>
                        <span class="demand-badge {demand_class}">Demand: {ipo.get('demand_level', 'N/A')}</span>
                        <span class="demand-badge {risk_class}">Risk: {ipo.get('risk_level', 'N/A')}</span>
                    </div>
            """
            
            if suitable_for:
                html_body += """
                    <div class="suitable-for">
                        <strong>Suitable For:</strong>
                        <ul>
                """
                for item in suitable_for:
                    html_body += f"<li>{item}</li>"
                html_body += """
                        </ul>
                    </div>
                """
            
            html_body += """
                </div>
            """
    else:
        html_body += """
                <div class="no-ipos">
                    <p>No IPOs are opening this week.</p>
                </div>
        """
    
    html_body += """
                <div class="footer">
                    <p>⚠️ This is an informational alert. Please consult a financial advisor before investing.</p>
                    <p>© 2026 IPO Alerts. All rights reserved.</p>
                </div>
            </div>
        </body>
    </html>
    """
    
    return html_body


def send_ipo_email(ipo_data: Union[Dict, str, List], subject: str = None) -> bool:
    """
    Send IPO data email with rich HTML template
    
    Args:
        ipo_data: IPO data as dictionary, JSON string, or list
        subject: Email subject line (optional)
    
    Returns:
        True if sent successfully, False otherwise
    """
    sender_email = "sagar.rebba9@gmail.com"
    sender_password = os.getenv("GMail_Password")
    receiver_email = "sagar.rebba@gmail.com"
    
    if not sender_password:
        print("[ERROR] GMail_Password environment variable is not set")
        return False
    
    # Create the email structure
    msg = MIMEMultipart("alternative")
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject or "📈 IPO Alerts - Weekly Summary"
    
    # Generate HTML template
    html_body = create_ipo_email_template(ipo_data)
    
    # Attach HTML content
    msg.attach(MIMEText(html_body, 'html'))
    
    try:
        # Connect to Gmail's SMTP server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print("✅ IPO Email sent successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


def send_email():
    """Legacy function for backward compatibility"""
    sender_email = "sagar.rebba9@gmail.com"
    sender_password = os.getenv("GMail_Password")
    receiver_email = "sagar.rebba@gmail.com"
    
    # Create the email structure
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Test Email from Python"

    # Email body content
    body = "Hello! This is a test email sent from Python code."
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to Gmail's SMTP server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print("✅ Email sent successfully!")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    send_email()