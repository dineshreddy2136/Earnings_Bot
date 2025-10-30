#!/usr/bin/env python3
"""
Email Test Script - SMTP Configuration Test
Tests email sending functionality for future alert features
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime


def test_smtp_connection():
    """Test SMTP email sending functionality"""
    
    # SMTP server configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587  # use 465 for SSL
    
    # Email credentials - REPLACE THESE WITH YOUR ACTUAL VALUES
    # For Gmail: Use App Password, not your regular password
    # Generate at: https://myaccount.google.com/apppasswords
    email_user = "dineshreddyk2136@gmail.com"  # ⚠️ REPLACE THIS
    email_password = "kwsbbrbleccgixsa"  # ⚠️ REPLACE THIS (16-char app password)
    
    # Multiple recipients - can be a single email or a list
    recipient_emails = [
        "dineshreddyk569@gmail.com",
        "dineshreddykankanala@gmail.com",  # Uncomment and add more emails as needed
        # "third_email@example.com",
    ]
    
    # Validate configuration
    if "your_email" in email_user or "your_app" in email_password:
        print("❌ ERROR: Please configure your email credentials first!")
        print("\n📝 Setup Instructions:")
        print("1. Open test_email_smtp.py")
        print("2. Replace 'your_email@gmail.com' with your actual Gmail address")
        print("3. Generate an App Password at: https://myaccount.google.com/apppasswords")
        print("4. Replace 'your_app_password' with the generated 16-character password")
        print("5. Add recipient email(s) to the recipient_emails list")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "📊 Earnings Bot - Test Email"
        msg["From"] = email_user
        msg["To"] = ", ".join(recipient_emails)  # Join multiple recipients with commas
        
        # Create both plain text and HTML versions
        text_content = f"""
        Earnings Bot Email Test
        
        This is a test email sent from your Earnings Bot application.
        
        Test Details:
        - Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        - SMTP Server: {smtp_server}
        - Port: {smtp_port}
        
        If you received this email, your SMTP configuration is working correctly!
        
        Next Steps:
        - You can now implement email alerts for earnings events
        - Set up notifications for high IV stocks
        - Create weekly earnings summaries
        
        ---
        Earnings Bot v2.0
        """
        
        html_content = f"""
        <html>
          <head></head>
          <body>
            <h2>📊 Earnings Bot Email Test</h2>
            <p>This is a test email sent from your <strong>Earnings Bot</strong> application.</p>
            
            <h3>Test Details:</h3>
            <ul>
              <li><strong>Sent at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
              <li><strong>SMTP Server:</strong> {smtp_server}</li>
              <li><strong>Port:</strong> {smtp_port}</li>
            </ul>
            
            <p>✅ If you received this email, your SMTP configuration is working correctly!</p>
            
            <h3>Next Steps:</h3>
            <ul>
              <li>Implement email alerts for earnings events</li>
              <li>Set up notifications for high IV stocks</li>
              <li>Create weekly earnings summaries</li>
            </ul>
            
            <hr>
            <p><em>Earnings Bot v2.0</em></p>
          </body>
        </html>
        """
        
        # Attach both versions
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)
        
        print("📧 Attempting to send test email...")
        print(f"   From: {email_user}")
        print(f"   To: {', '.join(recipient_emails)} ({len(recipient_emails)} recipient(s))")
        print(f"   Server: {smtp_server}:{smtp_port}")
        print()
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            print("🔌 Connecting to SMTP server...")
            server.starttls()  # Upgrade the connection to secure TLS
            print("🔐 Starting TLS encryption...")
            
            server.login(email_user, email_password)  # Login to SMTP server
            print("✅ Login successful!")
            
            server.sendmail(email_user, recipient_emails, msg.as_string())
            print("📨 Email sent successfully!")
        
        print("\n✅ TEST PASSED - Email sent successfully!")
        print(f"   Email sent to {len(recipient_emails)} recipient(s):")
        for email in recipient_emails:
            print(f"   - {email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("\n❌ TEST FAILED - Authentication Error")
        print("\nPossible issues:")
        print("1. Incorrect email or password")
        print("2. Using regular password instead of App Password")
        print("3. 2-Factor Authentication not enabled")
        print("\n📝 For Gmail:")
        print("   - Enable 2FA on your Google account")
        print("   - Generate App Password: https://myaccount.google.com/apppasswords")
        print("   - Use the 16-character App Password (no spaces)")
        return False
        
    except smtplib.SMTPException as e:
        print(f"\n❌ TEST FAILED - SMTP Error: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ TEST FAILED - Unexpected Error: {e}")
        return False


def test_earnings_alert_email():
    """Example: Send an earnings alert email (template for future use)"""
    
    # This is a template for future implementation
    sample_earnings_data = {
        'symbol': 'AAPL',
        'company_name': 'Apple Inc.',
        'earnings_date': '2025-11-05',
        'earnings_time': 'AMC',
        'eps_estimate': 1.45,
        'iv_rank': 72.5,
        'expected_move': 5.2
    }
    
    print("\n" + "="*60)
    print("📋 SAMPLE EARNINGS ALERT EMAIL TEMPLATE")
    print("="*60)
    print(f"""
Subject: 🚨 Earnings Alert: {sample_earnings_data['symbol']} - {sample_earnings_data['earnings_date']}

{sample_earnings_data['company_name']} ({sample_earnings_data['symbol']})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Earnings Date: {sample_earnings_data['earnings_date']}
⏰ Timing: {sample_earnings_data['earnings_time']} (After Market Close)
💰 EPS Estimate: ${sample_earnings_data['eps_estimate']}

📊 Options Analysis:
   • IV Rank: {sample_earnings_data['iv_rank']}% (HIGH - Volatility Expensive)
   • Expected Move: ±{sample_earnings_data['expected_move']}%

💡 Trading Insight: High IV Rank suggests selling premium might be favorable.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Powered by Earnings Bot v2.0
    """)
    print("="*60)
    print("\n💡 To enable this feature:")
    print("   1. Configure SMTP settings")
    print("   2. Run test_smtp_connection() successfully")
    print("   3. Integrate alert logic into the app")


if __name__ == "__main__":
    print("="*60)
    print("📧 EARNINGS BOT - EMAIL SMTP TEST")
    print("="*60)
    print()
    
    # Run SMTP test
    result = test_smtp_connection()
    
    if result:
        print("\n" + "="*60)
        print("🎉 CONGRATULATIONS! Email is configured correctly.")
        print("="*60)
        
        # Show example alert template
        test_earnings_alert_email()
    else:
        print("\n" + "="*60)
        print("⚠️  Please fix the configuration and try again.")
        print("="*60)
