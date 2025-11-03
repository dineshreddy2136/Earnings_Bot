"""
Email Service - Earnings Bot

Handles email generation and sending via Gmail SMTP
Uses GCP Secret Manager for credentials
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, date
import logging
from typing import Dict, List
from google.cloud import secretmanager
import os
from firestore_db import FirestoreDB

logger = logging.getLogger(__name__)


class EmailService:
    """Email service using Gmail SMTP with GCP Secret Manager"""
    
    def __init__(self, db: FirestoreDB):
        """
        Initialize email service
        
        Args:
            db: FirestoreDB instance
        """
        self.db = db
        self.project_id = os.environ.get('GCP_PROJECT')
        
        # Load email configuration from Secret Manager
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        self.sender_email = self._get_secret('smtp-sender-email')
        self.sender_password = self._get_secret('smtp-password')
        self.recipients = self._get_secret('smtp-recipients').split(',')
        
        logger.info(f"Email service initialized for {len(self.recipients)} recipient(s)")
    
    def _get_secret(self, secret_name: str) -> str:
        """
        Retrieve secret from GCP Secret Manager
        
        Args:
            secret_name: Name of the secret
            
        Returns:
            str: Secret value
        """
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8").strip()
        except Exception as e:
            logger.error(f"Error retrieving secret {secret_name}: {e}")
            raise
    
    def send_weekly_report(self) -> Dict:
        """
        Send weekly earnings report
        
        Returns:
            dict: Send summary
        """
        # Get this week's earnings
        today = date.today()
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        sunday = monday + timedelta(days=6)
        
        earnings_list = self.db.get_earnings_by_date_range(
            monday.strftime('%Y-%m-%d'),
            sunday.strftime('%Y-%m-%d')
        )
        
        if not earnings_list:
            logger.warning("No earnings data for this week - skipping email")
            return {
                'sent': False,
                'reason': 'No data',
                'recipients_count': 0,
                'companies_count': 0
            }
        
        # Get options data
        symbols = [e['symbol'] for e in earnings_list]
        options_data = self.db.get_options_data(symbols)
        
        # Generate email
        subject = f"💼 {len(earnings_list)} Earnings This Week | {monday.strftime('%b %d')} - {sunday.strftime('%b %d')}"
        html_body = self._create_html_email(earnings_list, monday, sunday, "This Week", options_data)
        text_body = self._create_text_email(earnings_list, monday, sunday, "This Week", options_data)
        
        # Send email
        self._send_email(subject, html_body, text_body)
        
        logger.info(f"✅ Email sent: {len(earnings_list)} companies to {len(self.recipients)} recipient(s)")
        
        return {
            'sent': True,
            'recipients_count': len(self.recipients),
            'companies_count': len(earnings_list),
            'format': 'HTML + Plain Text'
        }
    
    def _send_email(self, subject: str, html_body: str, text_body: str):
        """
        Send email via Gmail SMTP
        
        Args:
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = ", ".join(self.recipients)
            
            # Attach parts
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            # Send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipients, msg.as_string())
            
            logger.info("Email sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise
    
    def _create_html_email(self, earnings_list: List[Dict], start_date: date, 
                          end_date: date, time_period: str, options_data: Dict) -> str:
        """Create HTML formatted email"""
        
        html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 5px;">
          
          <h2 style="color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px;">
            Earnings Report: {time_period}
          </h2>
          
          <p style="color: #666; font-size: 14px;">
            <strong>Period:</strong> {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}<br>
            <strong>Total Companies:</strong> {len(earnings_list)}<br>
            <strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
          </p>
          
          <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
            <thead>
              <tr style="background-color: #4CAF50; color: white;">
                <th style="padding: 10px; text-align: left;">Symbol</th>
                <th style="padding: 10px; text-align: left;">Company</th>
                <th style="padding: 10px; text-align: left;">Date</th>
                <th style="padding: 10px; text-align: left;">Time</th>
                <th style="padding: 10px; text-align: right;">Price</th>
                <th style="padding: 10px; text-align: right;">EPS Est.</th>
                <th style="padding: 10px; text-align: right;">Exp. Move %</th>
                <th style="padding: 10px; text-align: right;">Exp. Move $</th>
              </tr>
            </thead>
            <tbody>
"""
        
        for idx, earning in enumerate(earnings_list):
            symbol = earning['symbol']
            company_name = earning['company_name']
            earnings_date = earning['earnings_date']
            earnings_time = earning.get('earnings_time', 'N/A')
            
            price = f"${earning['current_price']:.2f}" if earning.get('current_price') else 'N/A'
            eps = f"${earning['eps_estimate']:.2f}" if earning.get('eps_estimate') else 'N/A'
            
            bg_color = "#f9f9f9" if idx % 2 == 0 else "white"
            
            html += f"""
              <tr style="background-color: {bg_color}; border-bottom: 1px solid #ddd;">
                <td style="padding: 10px; font-weight: bold;">{symbol}</td>
                <td style="padding: 10px;">{company_name}</td>
                <td style="padding: 10px;">{earnings_date}</td>
                <td style="padding: 10px;">{earnings_time}</td>
                <td style="padding: 10px; text-align: right;">{price}</td>
                <td style="padding: 10px; text-align: right;">{eps}</td>
"""
            
            if symbol in options_data:
                opt = options_data[symbol]
                exp_move_pct = opt.get('expected_move_percent')
                exp_move_dollar = opt.get('expected_move_dollar')
                
                move_pct = f"±{exp_move_pct:.1f}%" if exp_move_pct else '-'
                move_dollar = f"±${exp_move_dollar:.2f}" if exp_move_dollar else '-'
            else:
                move_pct = '-'
                move_dollar = '-'
            
            html += f"""
                <td style="padding: 10px; text-align: right;">{move_pct}</td>
                <td style="padding: 10px; text-align: right;">{move_dollar}</td>
              </tr>
"""
        
        html += """
            </tbody>
          </table>
          
          <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 12px; text-align: center;">
            This report is for informational purposes only. Not financial advice.<br>
            © 2025 Earnings Bot
          </p>
          
        </div>
      </body>
    </html>
"""
        
        return html
    
    def _create_text_email(self, earnings_list: List[Dict], start_date: date,
                          end_date: date, time_period: str, options_data: Dict) -> str:
        """Create plain text formatted email"""
        
        text = f"""
================================================================================
                    EARNINGS REPORT: {time_period.upper()}
================================================================================

Period:       {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}
Companies:    {len(earnings_list)}
Generated:    {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

================================================================================

"""
        
        for earning in earnings_list:
            symbol = earning['symbol']
            company_name = earning['company_name']
            earnings_date = earning['earnings_date']
            earnings_time = earning.get('earnings_time', 'N/A')
            sector = earning.get('sector', 'N/A')
            
            price = f"${earning['current_price']:.2f}" if earning.get('current_price') else 'N/A'
            eps = f"${earning['eps_estimate']:.2f}" if earning.get('eps_estimate') else 'N/A'
            
            text += f"""
{symbol} - {company_name}
{'-' * 80}
Earnings Date:    {earnings_date}
Time:             {earnings_time}
Sector:           {sector}
Current Price:    {price}
EPS Estimate:     {eps}
"""
            
            if symbol in options_data:
                opt = options_data[symbol]
                iv_percentile = opt.get('iv_percentile')
                exp_move_pct = opt.get('expected_move_percent')
                exp_move_dollar = opt.get('expected_move_dollar')
                exp_up = opt.get('expected_move_up')
                exp_down = opt.get('expected_move_down')
                
                if iv_percentile or exp_move_pct:
                    text += "\nOptions Analysis:\n"
                    
                    if iv_percentile:
                        text += f"  IV Percentile:    {iv_percentile:.1f}%\n"
                    
                    if exp_move_pct:
                        text += f"  Expected Move:    ±{exp_move_pct:.1f}%"
                        if exp_move_dollar:
                            text += f" (±${exp_move_dollar:.2f})\n"
                        else:
                            text += "\n"
                    
                    if exp_up and exp_down:
                        text += f"  Price Range:      ${exp_down:.2f} - ${exp_up:.2f}\n"
            
            text += "\n"
        
        text += f"""
================================================================================
DISCLAIMER: This report is for informational purposes only. Not financial advice.
(c) 2025 Earnings Bot
================================================================================
"""
        
        return text
