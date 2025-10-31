"""Email Alerts Page - Send Earnings Reports via Email"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.config_loader import config
from utils.email_config import get_email_config, is_email_configured
from utils.data_access import get_weekly_earnings_data, init_database
from utils.formatters import format_market_cap, format_revenue_estimate


def email_alerts():
    """Email alerts page - send earnings reports via email"""
    st.header("📧 Email Earnings Alerts")
    st.markdown("**Send earnings reports directly to your inbox**")
    
    # Check email configuration
    if not is_email_configured():
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
    email_config = get_email_config()
    recipients = email_config.get('recipients', [])
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


def _show_configuration_warning():
    """Show warning about email configuration"""
    st.warning("⚠️ Email not configured. Please configure your email settings.")
    
    with st.expander("📝 How to Configure Email", expanded=True):
        st.markdown("""
        ### Setup Instructions:
        
        #### Option 1: Using .env file (Recommended - Secure)
        
        1. **Copy the example file:**
        ```bash
        cp .env.example .env
        ```
        
        2. **Edit `.env` file** and update with your credentials:
        ```
        SMTP_SERVER=smtp.gmail.com
        SMTP_PORT=587
        SENDER_EMAIL=your_email@gmail.com
        SENDER_PASSWORD=your_16_char_app_password
        RECIPIENT_EMAILS=recipient1@example.com,recipient2@example.com
        ```
        
        3. **For Gmail users:**
           - Enable 2-Factor Authentication
           - Generate App Password: https://myaccount.google.com/apppasswords
           - Use the 16-character password (remove spaces)
        
        4. **Restart the app**
        
        #### Option 2: Using config.yaml (Not Recommended)
        
        You can also configure email in `config.yaml`, but this is less secure
        as you might accidentally commit credentials to git.
        
        ---
        
        **Note:** The `.env` file is automatically added to `.gitignore` to
        prevent accidentally committing your credentials.
        """)


def _display_email_config():
    """Display current email configuration"""
    email_config = get_email_config()
    
    sender_email = email_config.get('sender_email', 'Not configured')
    recipients = email_config.get('recipients', [])
    smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
    smtp_port = email_config.get('smtp_port', 587)
    
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
    
    # Get email settings from .env or config
    email_config = get_email_config()
    sender_email = email_config.get('sender_email')
    sender_password = email_config.get('sender_password')
    recipients = email_config.get('recipients')
    smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
    smtp_port = email_config.get('smtp_port', 587)
    
    try:
        with st.spinner("📧 Sending email..."):
            # Get options data if requested
            options_data = {}
            if include_options:
                options_data = _get_options_data_for_symbols(earnings_df['symbol'].tolist())
            
            # Create email content
            subject = f" ATTENTION: {len(earnings_df)} Earnings Ahead | {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
            
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
                    'iv_percentile': row.get('iv_percentile'),
                    'expected_move_percent': row.get('expected_move_percent'),
                    'expected_move_dollar': row.get('expected_move_dollar'),
                    'expected_move_up': row.get('expected_move_up'),
                    'expected_move_down': row.get('expected_move_down')
                }
        
        return options_dict
    
    except Exception as e:
        print(f"Error getting options data: {e}")
        return {}


def _create_html_email(earnings_df, start_date, end_date, time_period, options_data):
    """Create simple HTML formatted email"""
    
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 5px;">
          
          <h2 style="color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px;">
            Earnings Report: {time_period}
          </h2>
          
          <p style="color: #666; font-size: 14px;">
            <strong>Period:</strong> {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}<br>
            <strong>Total Companies:</strong> {len(earnings_df)}<br>
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
"""
    
    if options_data:
        html += """
                <th style="padding: 10px; text-align: right;">Exp. Move %</th>
                <th style="padding: 10px; text-align: right;">Exp. Move $</th>
"""
    
    html += """
              </tr>
            </thead>
            <tbody>
"""
    
    # Add company rows
    for idx, row in earnings_df.iterrows():
        symbol = row['symbol']
        company_name = row['company_name']
        earnings_date = row['earnings_date']
        earnings_time = row.get('earnings_time', 'N/A')
        
        price = f"${row['current_price']:.2f}" if pd.notna(row['current_price']) and row['current_price'] > 0 else 'N/A'
        eps = f"${row['eps_estimate']:.2f}" if pd.notna(row['eps_estimate']) and row['eps_estimate'] != 0 else 'N/A'
        
        # Alternate row colors
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
        
        if options_data:
            if symbol in options_data:
                opt = options_data[symbol]
                exp_move_pct = opt.get('expected_move_percent')
                exp_move_dollar = opt.get('expected_move_dollar')
                
                move_pct_display = f"±{exp_move_pct:.1f}%" if exp_move_pct else '-'
                move_dollar_display = f"±${exp_move_dollar:.2f}" if exp_move_dollar else '-'
            else:
                move_pct_display = '-'
                move_dollar_display = '-'
            
            html += f"""
                <td style="padding: 10px; text-align: right;">{move_pct_display}</td>
                <td style="padding: 10px; text-align: right;">{move_dollar_display}</td>
"""
        
        html += """
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


def _create_text_email(earnings_df, start_date, end_date, time_period, options_data):
    """Create simple plain text formatted email"""
    
    text = f"""
================================================================================
                    EARNINGS REPORT: {time_period.upper()}
================================================================================

Period:       {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}
Companies:    {len(earnings_df)}
Generated:    {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

================================================================================

"""
    
    for idx, row in earnings_df.iterrows():
        symbol = row['symbol']
        company_name = row['company_name']
        earnings_date = row['earnings_date']
        earnings_time = row.get('earnings_time', 'N/A')
        sector = row.get('sector', 'N/A')
        
        price = f"${row['current_price']:.2f}" if pd.notna(row['current_price']) and row['current_price'] > 0 else 'N/A'
        eps = f"${row['eps_estimate']:.2f}" if pd.notna(row['eps_estimate']) and row['eps_estimate'] != 0 else 'N/A'
        
        text += f"""
{symbol} - {company_name}
{'-' * 80}
Earnings Date:    {earnings_date}
Time:             {earnings_time}
Sector:           {sector}
Current Price:    {price}
EPS Estimate:     {eps}
"""
        
        if options_data and symbol in options_data:
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


if __name__ == "__main__":
    email_alerts()
