import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Union
from dotenv import load_dotenv

load_dotenv()


def create_ipo_email_template(ipo_data):
    """
    HTML email template for Daily High GMP IPO Alerts
    """

    ipos = ipo_data.get("ipos", [])
    report_date = ipo_data.get("week", "Today")

    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f6f8fa;
                padding: 20px;
            }}
            .container {{
                max-width: 720px;
                margin: auto;
                background: #ffffff;
                border-radius: 8px;
                padding: 24px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            }}
            h1 {{
                color: #111827;
                margin-bottom: 4px;
            }}
            .subtitle {{
                color: #6b7280;
                font-size: 14px;
                margin-bottom: 20px;
            }}
            .ipo {{
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 16px;
                margin-bottom: 16px;
            }}
            .ipo-title {{
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 6px;
            }}
            .badge {{
                display: inline-block;
                padding: 4px 10px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: bold;
                background-color: #dcfce7;
                color: #166534;
            }}
            .row {{
                margin-top: 6px;
                font-size: 14px;
            }}
            .label {{
                color: #6b7280;
            }}
            .footer {{
                margin-top: 24px;
                font-size: 12px;
                color: #6b7280;
                border-top: 1px solid #e5e7eb;
                padding-top: 12px;
            }}
        </style>
    </head>

    <body>
        <div class="container">
            <h1>🚀 High GMP IPO Alert</h1>
            <div class="subtitle">
                IPOs with Grey Market Premium ≥ 20% <br/>
                Date: {report_date}
            </div>
    """

    for ipo in ipos:
        html += f"""
            <div class="ipo">
                <div class="ipo-title">
                    {ipo["company_name"]}
                    <span class="badge">High GMP</span>
                </div>

                <div class="row">
                    <span class="label">Open:</span> {ipo["open_date"]}
                    &nbsp; | &nbsp;
                    <span class="label">Close:</span> {ipo["close_date"]}
                </div>

                <div class="row">
                    <span class="label">IPO Price:</span> {ipo["price_band"]}
                </div>

                <div class="row">
                    <span class="label">GMP:</span> {ipo["gmp"]}
                </div>

                <div class="row">
                    <span class="label">Market View:</span>
                    Strong grey market interest (informational)
                </div>
            </div>
        """

    html += """
            <div class="footer">
                <strong>Disclaimer:</strong><br/>
                This alert is based on Grey Market Premium (GMP) data from public sources.
                GMP is unofficial and unregulated. This email is for informational and
                educational purposes only and does not constitute investment advice.
            </div>
        </div>
    </body>
    </html>
    """

    return html


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