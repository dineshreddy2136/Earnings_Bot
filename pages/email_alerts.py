"""Email Alerts Page - Send Earnings Reports via Email"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.config_loader import config
from utils.data_access import get_weekly_earnings_data, init_database
from utils.formatters import format_market_cap, format_revenue_estimate


def email_alerts():
    """Email alerts page - send earnings reports via email"""
    st.header("📧 Email Earnings Alerts")
    st.markdown("**Send earnings reports directly to your inbox**")
    
    # Check email configuration
    if not _is_email_configured():
        _show_configuration_warning()
        return
    
    # Email configuration section
    with st.expander("⚙️ Email Configuration", expanded=False):
        _display_email_config()
    
    st.markdown("---")
    
    # Time period selection
    st.subheader("📅 Select Time Period")
    time_period = st.radio(
        "Send earnings data for:",
        ["Tomorrow", "This Week", "Next Week", "Custom Date Range"],
        horizontal=True
    )
    
    # Get date range based on selection
    start_date, end_date = _get_date_range(time_period)
    
    # Display selected date range
    st.info(f"📅 Selected Period: **{start_date.strftime('%B %d, %Y')}** to **{end_date.strftime('%B %d, %Y')}**")
    
    # Get earnings data for the period
    earnings_df = get_weekly_earnings_data(start_date, end_date)
    
    if earnings_df.empty:
        st.warning(f"No earnings data found for the selected period.")
        return
    
    # Display preview of data
    st.markdown("---")
    st.subheader(f"📊 Preview: {len(earnings_df)} Companies")
    
    # Preview table
    preview_df = earnings_df[['symbol', 'company_name', 'earnings_date', 'earnings_time', 'sector', 'current_price', 'eps_estimate']].head(10)
    st.dataframe(preview_df, use_container_width=True)
    
    if len(earnings_df) > 10:
        st.caption(f"Showing 10 of {len(earnings_df)} companies. Full list will be sent via email.")
    
    # Email options
    st.markdown("---")
    st.subheader("📧 Email Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_options_data = st.checkbox(
            "Include Options IV Data",
            value=True,
            help="Include IV Rank, IV Percentile, and Expected Move data if available"
        )
    
    with col2:
        email_format = st.radio(
            "Email Format:",
            ["HTML (Rich Format)", "Plain Text"],
            horizontal=True
        )
    
    # Recipients
    recipients = config.get('email', 'recipients', default=[])
    st.info(f"📬 Email will be sent to {len(recipients)} recipient(s): {', '.join(recipients)}")
    
    # Send button
    st.markdown("---")
    if st.button("📨 Send Email Report", type="primary", use_container_width=True):
        _send_earnings_report(
            earnings_df,
            start_date,
            end_date,
            time_period,
            include_options_data,
            email_format == "HTML (Rich Format)"
        )


def _is_email_configured():
    """Check if email is properly configured"""
    sender_email = config.get('email', 'sender_email', default='')
    sender_password = config.get('email', 'sender_password', default='')
    recipients = config.get('email', 'recipients', default=[])
    
    if not sender_email or 'your_email' in sender_email:
        return False
    if not sender_password or 'your_app' in sender_password or 'your_password' in sender_password:
        return False
    if not recipients or 'recipient' in recipients[0]:
        return False
    
    return True


def _show_configuration_warning():
    """Show warning about email configuration"""
    st.warning("⚠️ Email not configured. Please update config.yaml with your email settings.")
    
    with st.expander("📝 How to Configure Email", expanded=True):
        st.markdown("""
        ### Setup Instructions:
        
        1. **Open `config.yaml`** in the root directory
        
        2. **Update the email section:**
        ```yaml
        email:
          sender_email: "your_email@gmail.com"
          sender_password: "your_16_char_app_password"
          recipients:
            - "recipient1@example.com"
            - "recipient2@example.com"
        ```
        
        3. **For Gmail users:**
           - Enable 2-Factor Authentication
           - Generate App Password: https://myaccount.google.com/apppasswords
           - Use the 16-character password (remove spaces)
        
        4. **Save and restart the app**
        """)


def _display_email_config():
    """Display current email configuration"""
    sender_email = config.get('email', 'sender_email', default='Not configured')
    recipients = config.get('email', 'recipients', default=[])
    smtp_server = config.get('email', 'smtp_server', default='smtp.gmail.com')
    smtp_port = config.get('email', 'smtp_port', default=587)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("From", sender_email)
        st.metric("SMTP Server", f"{smtp_server}:{smtp_port}")
    
    with col2:
        st.metric("Recipients", len(recipients))
        for i, recipient in enumerate(recipients, 1):
            st.caption(f"{i}. {recipient}")


def _get_date_range(time_period):
    """Get start and end dates based on time period selection"""
    today = date.today()
    
    if time_period == "Tomorrow":
        tomorrow = today + timedelta(days=1)
        return tomorrow, tomorrow
    
    elif time_period == "This Week":
        # Get Monday and Sunday of current week
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        sunday = monday + timedelta(days=6)
        return monday, sunday
    
    elif time_period == "Next Week":
        # Get Monday and Sunday of next week
        days_since_monday = today.weekday()
        this_monday = today - timedelta(days=days_since_monday)
        next_monday = this_monday + timedelta(days=7)
        next_sunday = next_monday + timedelta(days=6)
        return next_monday, next_sunday
    
    else:  # Custom Date Range
        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("Start Date", today)
        with col2:
            end = st.date_input("End Date", today + timedelta(days=7))
        return start, end


def _send_earnings_report(earnings_df, start_date, end_date, time_period, include_options, use_html):
    """Send earnings report via email"""
    
    # Get email settings
    sender_email = config.get('email', 'sender_email')
    sender_password = config.get('email', 'sender_password')
    recipients = config.get('email', 'recipients')
    smtp_server = config.get('email', 'smtp_server', default='smtp.gmail.com')
    smtp_port = config.get('email', 'smtp_port', default=587)
    
    try:
        with st.spinner("📧 Sending email..."):
            # Get options data if requested
            options_data = {}
            if include_options:
                options_data = _get_options_data_for_symbols(earnings_df['symbol'].tolist())
            
            # Create email content
            subject = f"📊 Earnings Report: {time_period} ({start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')})"
            
            if use_html:
                body = _create_html_email(earnings_df, start_date, end_date, time_period, options_data)
            else:
                body = _create_text_email(earnings_df, start_date, end_date, time_period, options_data)
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender_email
            msg["To"] = ", ".join(recipients)
            
            # Attach body
            if use_html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipients, msg.as_string())
            
            st.success(f"✅ Email sent successfully to {len(recipients)} recipient(s)!")
            
            # Show confirmation details
            with st.expander("📬 Email Details"):
                st.write(f"**Subject:** {subject}")
                st.write(f"**Recipients:** {', '.join(recipients)}")
                st.write(f"**Companies:** {len(earnings_df)}")
                st.write(f"**Format:** {'HTML' if use_html else 'Plain Text'}")
                st.write(f"**Options Data:** {'Included' if include_options else 'Not included'}")
    
    except Exception as e:
        st.error(f"❌ Failed to send email: {str(e)}")
        st.info("💡 Check your email configuration in config.yaml")


def _get_options_data_for_symbols(symbols):
    """Get options IV data for given symbols"""
    try:
        db = init_database()
        all_options = db.get_all_options_data()
        
        if all_options.empty:
            return {}
        
        # Create dictionary with symbol as key
        options_dict = {}
        for _, row in all_options.iterrows():
            if row['symbol'] in symbols:
                options_dict[row['symbol']] = {
                    'iv_rank': row.get('iv_rank_52week'),
                    'iv_percentile': row.get('iv_percentile'),
                    'expected_move_percent': row.get('expected_move_percent'),
                    'expected_move_up': row.get('expected_move_up'),
                    'expected_move_down': row.get('expected_move_down')
                }
        
        return options_dict
    
    except Exception as e:
        print(f"Error getting options data: {e}")
        return {}


def _create_html_email(earnings_df, start_date, end_date, time_period, options_data):
    """Create HTML formatted email"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          * {{ margin: 0; padding: 0; box-sizing: border-box; }}
          body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6; 
            color: #2c3e50;
            background-color: #f8f9fa;
            padding: 20px;
          }}
          .email-container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
          }}
          .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
          }}
          .header h1 {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
          }}
          .header .subtitle {{
            font-size: 18px;
            opacity: 0.95;
            font-weight: 300;
          }}
          .summary-section {{
            display: flex;
            justify-content: space-around;
            padding: 30px;
            background-color: #f8f9fa;
            border-bottom: 3px solid #e9ecef;
          }}
          .summary-card {{
            text-align: center;
            padding: 15px 25px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            min-width: 200px;
          }}
          .summary-card .label {{
            font-size: 12px;
            text-transform: uppercase;
            color: #6c757d;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
          }}
          .summary-card .value {{
            font-size: 24px;
            font-weight: 700;
            color: #667eea;
          }}
          .content {{
            padding: 30px;
          }}
          .section-title {{
            font-size: 20px;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            display: inline-block;
          }}
          table {{
            border-collapse: separate;
            border-spacing: 0;
            width: 100%;
            margin: 20px 0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
          }}
          thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          }}
          th {{
            color: white;
            padding: 16px 12px;
            text-align: left;
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }}
          tbody tr {{
            background-color: #ffffff;
            transition: all 0.3s ease;
          }}
          tbody tr:nth-child(even) {{
            background-color: #f8f9fa;
          }}
          tbody tr:hover {{
            background-color: #e7f1ff;
            transform: scale(1.01);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
          }}
          td {{
            padding: 14px 12px;
            border-bottom: 1px solid #e9ecef;
            font-size: 14px;
          }}
          .symbol {{
            font-weight: 700;
            color: #667eea;
            font-size: 15px;
          }}
          .company-name {{
            color: #495057;
            font-weight: 500;
          }}
          .price {{
            font-weight: 600;
            color: #28a745;
          }}
          .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
          }}
          .badge-bmo {{
            background-color: #fff3cd;
            color: #856404;
          }}
          .badge-amc {{
            background-color: #d1ecf1;
            color: #0c5460;
          }}
          .badge-other {{
            background-color: #e2e3e5;
            color: #383d41;
          }}
          .iv-high {{
            color: #dc3545;
            font-weight: 700;
            background-color: #f8d7da;
            padding: 4px 8px;
            border-radius: 4px;
          }}
          .iv-medium {{
            color: #fd7e14;
            font-weight: 700;
            background-color: #fff3cd;
            padding: 4px 8px;
            border-radius: 4px;
          }}
          .iv-low {{
            color: #28a745;
            font-weight: 700;
            background-color: #d4edda;
            padding: 4px 8px;
            border-radius: 4px;
          }}
          .expected-move {{
            font-weight: 600;
            color: #6f42c1;
          }}
          .footer {{
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 30px;
            text-align: center;
          }}
          .footer-content {{
            max-width: 600px;
            margin: 0 auto;
          }}
          .footer h3 {{
            color: #ecf0f1;
            margin-bottom: 15px;
            font-size: 18px;
          }}
          .footer p {{
            font-size: 13px;
            line-height: 1.8;
            color: #bdc3c7;
            margin: 8px 0;
          }}
          .footer .disclaimer {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #34495e;
            font-size: 11px;
            color: #95a5a6;
          }}
          .sector-badge {{
            display: inline-block;
            padding: 3px 8px;
            background-color: #e9ecef;
            color: #495057;
            border-radius: 4px;
            font-size: 12px;
          }}
          @media only screen and (max-width: 600px) {{
            .summary-section {{ flex-direction: column; }}
            .summary-card {{ margin-bottom: 15px; }}
            table {{ font-size: 12px; }}
            th, td {{ padding: 8px 6px; }}
          }}
        </style>
      </head>
      <body>
        <div class="email-container">
          <!-- Header -->
          <div class="header">
            <h1>📊 Earnings Report</h1>
            <div class="subtitle">{time_period} | {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}</div>
          </div>
          
          <!-- Summary Section -->
          <div class="summary-section">
            <div class="summary-card">
              <div class="label">📅 Period</div>
              <div class="value" style="font-size: 16px;">{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}</div>
            </div>
            <div class="summary-card">
              <div class="label">🏢 Companies</div>
              <div class="value">{len(earnings_df)}</div>
            </div>
            <div class="summary-card">
              <div class="label">🕐 Generated</div>
              <div class="value" style="font-size: 14px;">{datetime.now().strftime('%I:%M %p')}</div>
            </div>
          </div>
          
          <!-- Main Content -->
          <div class="content">
            <div class="section-title">Companies Reporting Earnings</div>
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Company</th>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Sector</th>
                  <th style="text-align: right;">Price</th>
                  <th style="text-align: right;">EPS Est.</th>
                  {'<th style="text-align: center;">IV Rank</th><th style="text-align: center;">Expected Move</th>' if options_data else ''}
                </tr>
              </thead>
              <tbody>
    """
    
    # Add rows
    for _, row in earnings_df.iterrows():
        symbol = row['symbol']
        price = f"${row['current_price']:.2f}" if pd.notna(row['current_price']) and row['current_price'] > 0 else 'N/A'
        eps = f"${row['eps_estimate']:.2f}" if pd.notna(row['eps_estimate']) and row['eps_estimate'] != 0 else 'N/A'
        
        # Determine time badge
        time_str = row.get('earnings_time', 'N/A')
        if 'BMO' in str(time_str) or 'Before' in str(time_str):
            time_badge = '<span class="badge badge-bmo">BMO</span>'
        elif 'AMC' in str(time_str) or 'After' in str(time_str):
            time_badge = '<span class="badge badge-amc">AMC</span>'
        else:
            time_badge = f'<span class="badge badge-other">{time_str}</span>'
        
        sector = row.get('sector', 'N/A')
        sector_display = f'<span class="sector-badge">{sector}</span>' if sector != 'N/A' else 'N/A'
        
        html += f"""
                <tr>
                  <td><span class="symbol">{symbol}</span></td>
                  <td><span class="company-name">{row['company_name'][:40]}{'...' if len(row['company_name']) > 40 else ''}</span></td>
                  <td>{row['earnings_date']}</td>
                  <td>{time_badge}</td>
                  <td>{sector_display}</td>
                  <td style="text-align: right;"><span class="price">{price}</span></td>
                  <td style="text-align: right;">{eps}</td>
        """
        
        if options_data and symbol in options_data:
            opt = options_data[symbol]
            iv_rank = opt.get('iv_rank')
            iv_class = 'iv-high' if iv_rank and iv_rank > 75 else 'iv-medium' if iv_rank and iv_rank > 50 else 'iv-low'
            iv_text = f"{iv_rank:.1f}%" if iv_rank else 'N/A'
            
            exp_move = opt.get('expected_move_percent')
            exp_text = f"±{exp_move:.1f}%" if exp_move else 'N/A'
            
            html += f"""
                  <td style="text-align: center;"><span class="{iv_class}">{iv_text}</span></td>
                  <td style="text-align: center;"><span class="expected-move">{exp_text}</span></td>
            """
        elif options_data:
            html += f"""
                  <td style="text-align: center;">N/A</td>
                  <td style="text-align: center;">N/A</td>
            """
        
        html += "</tr>"
    
    html += """
              </tbody>
            </table>
          </div>
          
          <!-- Footer -->
          <div class="footer">
            <div class="footer-content">
              <h3>📊 Earnings Bot v2.0</h3>
              <p><strong>Professional Earnings Intelligence Platform</strong></p>
              <p>Comprehensive earnings tracking with advanced volatility analysis</p>
              <div class="disclaimer">
                <p><strong>⚠️ DISCLAIMER:</strong> This report is for informational purposes only and does not constitute financial advice. 
                All data is sourced from public markets and may contain inaccuracies. Past performance does not guarantee future results. 
                Please conduct your own research and consult with a qualified financial advisor before making investment decisions.</p>
                <p style="margin-top: 10px;">© 2025 Earnings Bot. All rights reserved.</p>
              </div>
            </div>
          </div>
        </div>
      </body>
    </html>
    """
    
    return html


def _create_text_email(earnings_df, start_date, end_date, time_period, options_data):
    """Create plain text formatted email"""
    
    text = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                        📊 EARNINGS REPORT: {time_period.upper():^20}                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌─ REPORT SUMMARY ────────────────────────────────────────────────────────────┐
│                                                                              │
│  📅 Period:           {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}
│  🏢 Total Companies:  {len(earnings_df)}
│  🕐 Generated:        {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
│  📊 Data Source:      Live Market Data via yfinance
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

{'═' * 80}
COMPANIES REPORTING EARNINGS
{'═' * 80}

"""
    
    for idx, row in earnings_df.iterrows():
        symbol = row['symbol']
        price = f"${row['current_price']:.2f}" if pd.notna(row['current_price']) and row['current_price'] > 0 else 'N/A'
        eps = f"${row['eps_estimate']:.2f}" if pd.notna(row['eps_estimate']) and row['eps_estimate'] != 0 else 'N/A'
        
        text += f"""
┌─ {symbol} {'─' * (74 - len(symbol))}┐
│
│  Company:  {row['company_name'][:60]}
│  
│  📅 Earnings Date:     {row['earnings_date']}
│  🕐 Time:              {row.get('earnings_time', 'N/A')}
│  🏢 Sector:            {row.get('sector', 'N/A')}
│  
│  💵 Current Price:     {price}
│  💰 EPS Estimate:      {eps}
"""
        
        if options_data and symbol in options_data:
            opt = options_data[symbol]
            iv_rank = opt.get('iv_rank')
            exp_move = opt.get('expected_move_percent')
            exp_up = opt.get('expected_move_up')
            exp_down = opt.get('expected_move_down')
            iv_percentile = opt.get('iv_percentile')
            
            text += f"""│  
│  ━━━ OPTIONS ANALYSIS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
│  
"""
            
            if iv_rank:
                iv_status = "🔴 HIGH" if iv_rank > 75 else "🟡 MEDIUM" if iv_rank > 50 else "🟢 LOW"
                text += f"│  📊 IV Rank (52-week):  {iv_rank:.1f}%  [{iv_status}]\n"
            
            if iv_percentile:
                text += f"│  � IV Percentile:      {iv_percentile:.1f}%\n"
            
            if exp_move:
                text += f"""│  
│  🎯 Expected Move:      ±{exp_move:.1f}%
"""
            
            if exp_up and exp_down:
                move_range = exp_up - exp_down
                text += f"""│  📍 Price Range:        ${exp_down:.2f} ━━━━━ ${exp_up:.2f}
│     Range Width:        ${move_range:.2f}
"""
        
        text += f"""│
└{'─' * 78}┘

"""
    
    text += f"""
{'═' * 80}
FOOTER INFORMATION
{'═' * 80}

┌─ ABOUT THIS REPORT ──────────────────────────────────────────────────────────┐
│                                                                              │
│  📊 Earnings Bot v2.0 - Professional Earnings Intelligence Platform          │
│                                                                              │
│  This comprehensive earnings report includes:                               │
│  • Real-time earnings dates and times (BMO/AMC)                            │
│  • Current stock prices and EPS estimates                                  │
│  • Advanced implied volatility analysis (IV Rank & Percentile)             │
│  • Expected move calculations based on options pricing                      │
│                                                                              │
│  Data Sources:                                                              │
│  • Market Data: Yahoo Finance (yfinance API)                               │
│  • Options Data: Real-time options chains                                  │
│  • Calculations: Proprietary 52-week IV analysis algorithms                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ DISCLAIMER ─────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ⚠️  IMPORTANT NOTICE:                                                       │
│                                                                              │
│  This report is for INFORMATIONAL PURPOSES ONLY and does not constitute     │
│  financial, investment, or trading advice. All data is sourced from public  │
│  markets and may contain inaccuracies or delays.                            │
│                                                                              │
│  Past performance does NOT guarantee future results. Options trading        │
│  involves substantial risk and is not suitable for all investors.           │
│                                                                              │
│  ALWAYS conduct your own research and consult with a qualified financial    │
│  advisor before making any investment decisions.                            │
│                                                                              │
│  © 2025 Earnings Bot. All rights reserved.                                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

{'═' * 80}
End of Report
{'═' * 80}
"""
    
    return text


if __name__ == "__main__":
    email_alerts()
