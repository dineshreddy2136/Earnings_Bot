# 📧 Email Alerts Guide

## Overview
The Email Alerts feature allows you to send comprehensive earnings reports directly to your inbox. You can choose different time periods and include options IV data.

## Features

### ✅ What's Included
- **Flexible Date Ranges**: Tomorrow, This Week, Next Week, or Custom
- **Rich Email Formats**: HTML (with styling) or Plain Text
- **Options Data**: IV Rank, IV Percentile, Expected Move ±%
- **Company Details**: Price, EPS Estimate, Earnings Date/Time, Sector
- **Multiple Recipients**: Send to multiple email addresses
- **Preview Mode**: See what data will be sent before sending

### 📊 Data Included in Reports

#### Basic Information
- Symbol & Company Name
- Earnings Date & Time (BMO/AMC)
- Sector/Industry
- Current Stock Price
- EPS Estimate

#### Options Data (if available)
- **IV Rank (52-week)**: Percentile of current IV vs 52-week range
- **IV Percentile**: % of days IV was below current level
- **Expected Move**: Predicted price movement percentage
- **Price Range**: Expected move high/low prices

## Setup Instructions

### 1. Configure Email Settings in `config.yaml`

```yaml
email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "your_email@gmail.com"
  sender_password: "your_16_char_app_password"
  recipients:
    - "recipient1@example.com"
    - "recipient2@example.com"
    - "recipient3@example.com"
```

### 2. For Gmail Users (Recommended)

1. **Enable 2-Factor Authentication**
   - Go to: https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Select app: "Mail"
   - Select device: "Other (Custom name)" → Enter "Earnings Bot"
   - Copy the 16-character password (remove spaces)
   - Paste into `sender_password` field in config.yaml

3. **Update Recipients**
   - Add as many recipient email addresses as needed
   - Each on a new line with proper YAML list format

### 3. Test Configuration
Use the `test_email_smtp.py` file to verify your setup:
```bash
python test_email_smtp.py
```

## How to Use

### In the Streamlit App

1. **Navigate to Email Alerts**
   - Open the Streamlit app
   - Select "📧 Email Alerts" from the sidebar

2. **Select Time Period**
   - **Tomorrow**: Only companies reporting next day
   - **This Week**: Monday-Sunday of current week
   - **Next Week**: Monday-Sunday of next week
   - **Custom**: Choose your own date range

3. **Preview Data**
   - See how many companies will be included
   - Review first 10 companies in preview table
   - Check date range is correct

4. **Configure Email Options**
   - ✅ **Include Options IV Data**: Shows IV Rank, Expected Move
   - 📄 **Email Format**: HTML (styled) or Plain Text
   - View recipients list

5. **Send Email**
   - Click "📨 Send Email Report"
   - Wait for confirmation
   - Check your inbox!

## Email Format Examples

### HTML Email (Rich Format)
- ✅ Beautiful table layout
- ✅ Color-coded IV Rank (High/Medium/Low)
- ✅ Professional header and footer
- ✅ Hover effects on table rows
- ✅ Mobile-friendly design

### Plain Text Email
- ✅ Clean, readable text format
- ✅ Tree-style layout for each company
- ✅ Works in any email client
- ✅ Lightweight and fast

## Use Cases

### 1. Daily Morning Brief
**Time Period**: Tomorrow  
**Options**: Include IV Data, HTML Format  
**Use Case**: Get daily earnings preview the night before

### 2. Weekly Planning
**Time Period**: This Week  
**Options**: Include IV Data, HTML Format  
**Use Case**: Plan your week's trading strategy

### 3. Advanced Planning
**Time Period**: Next Week  
**Options**: Include IV Data, Plain Text  
**Use Case**: Look ahead for positioning opportunities

### 4. Custom Research
**Time Period**: Custom (e.g., Specific Event Week)  
**Options**: Include IV Data, HTML Format  
**Use Case**: Research specific periods around events

## Troubleshooting

### ❌ Email Configuration Error
**Problem**: "Email not configured" warning  
**Solution**: 
- Check config.yaml has correct values
- Ensure sender_email doesn't contain placeholder text
- Verify app password is 16 characters (no spaces)

### ❌ SMTP Authentication Failed
**Problem**: "535-5.7.8 Username and Password not accepted"  
**Solution**:
- Regenerate Gmail App Password
- Double-check password in config.yaml (no quotes, no spaces)
- Ensure 2FA is enabled on Gmail account

### ❌ No Data Found
**Problem**: "No earnings data found for the selected period"  
**Solution**:
- Sync data first (go to "🔄 Sync Data" page)
- Check if date range is correct
- Verify database has data for that period

### ❌ Options Data Not Showing
**Problem**: Email has "N/A" for IV data  
**Solution**:
- Sync options data (on Sync Data page)
- Some tickers may not have options available
- Ensure "Include Options IV Data" is checked

## Email Safety & Privacy

### ✅ Best Practices
- Use App Passwords (never use actual Gmail password)
- Review recipients list before sending
- Don't share config.yaml file (contains credentials)
- Add config.yaml to .gitignore

### 🔒 Security
- Emails sent via TLS encryption (port 587)
- No passwords stored in database
- Config file stays on your local machine
- Recipients can be easily managed

## Advanced Tips

### Multiple Recipient Groups
Create different config files for different groups:
```yaml
# config.personal.yaml
email:
  recipients:
    - personal1@example.com
    - personal2@example.com

# config.work.yaml  
email:
  recipients:
    - work1@company.com
    - work2@company.com
```

### Automation (Future)
You can schedule emails using cron (macOS/Linux) or Task Scheduler (Windows):
```bash
# Send daily report at 6 PM
0 18 * * * cd /path/to/Earnings_Bot && python send_daily_report.py
```

### Custom Email Templates
The HTML email template can be customized by editing `_create_html_email()` in `pages/email_alerts.py`.

## Support

### Common Questions

**Q: Can I send to Gmail, Outlook, and other providers?**  
A: Yes! Recipients can have any email provider. Only sender needs Gmail (or update SMTP settings).

**Q: Is there a limit on recipients?**  
A: Gmail has sending limits (~100-500/day depending on account age). For mass emails, consider SendGrid.

**Q: Can I schedule automatic sends?**  
A: Not built-in yet, but you can use cron/scheduler to automate.

**Q: Does it work with other email providers?**  
A: Yes! Update smtp_server and smtp_port in config.yaml:
- **Outlook**: smtp.office365.com, port 587
- **Yahoo**: smtp.mail.yahoo.com, port 587
- **Custom**: Your provider's SMTP settings

---

## Quick Start Checklist

- [ ] Update config.yaml with email settings
- [ ] Generate Gmail App Password
- [ ] Add recipient email addresses
- [ ] Test with `test_email_smtp.py`
- [ ] Open Streamlit app
- [ ] Navigate to "📧 Email Alerts"
- [ ] Select time period
- [ ] Review preview
- [ ] Click "Send Email Report"
- [ ] Check inbox for confirmation
- [ ] ✅ Done!

---

**Need Help?** Check the configuration warning messages in the app—they provide step-by-step setup guidance.
