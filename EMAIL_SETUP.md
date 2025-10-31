# 📧 Email Configuration Guide

## Overview
The Earnings Bot uses SMTP email to send earnings reports. Your email credentials are stored securely in a `.env` file that is **never committed to git**.

## Quick Setup

### 1. Copy the Example File
```bash
cp .env.example .env
```

### 2. Edit `.env` File
Open `.env` in a text editor and update with your credentials:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_16_char_app_password
RECIPIENT_EMAILS=recipient1@example.com,recipient2@example.com
```

### 3. Gmail App Password Setup

#### Enable 2-Factor Authentication
1. Go to: https://myaccount.google.com/security
2. Enable **2-Step Verification**

#### Generate App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select app: **Mail**
3. Select device: **Other (Custom name)** → Enter "Earnings Bot"
4. Click **Generate**
5. Copy the 16-character password (ignore spaces)
6. Paste into `.env` file as `SENDER_PASSWORD`

### 4. Test Your Configuration
```bash
python test_email_smtp.py
```

If successful, you'll see:
```
✅ TEST PASSED - Email sent successfully!
```

## File Structure

```
Earnings_Bot/
├── .env                 # Your credentials (NOT in git)
├── .env.example         # Template file (safe to commit)
├── .gitignore          # Includes .env
├── utils/
│   └── email_config.py  # Email configuration loader
└── test_email_smtp.py  # Test script
```

## Security Features

✅ **Never Committed**: `.env` file is in `.gitignore`  
✅ **Separate from Code**: Credentials isolated from source code  
✅ **Template Provided**: `.env.example` for easy setup  
✅ **Validation**: Built-in checks for proper configuration  

## Multiple Recipients

Add multiple recipients with comma separation:

```env
RECIPIENT_EMAILS=alice@example.com,bob@example.com,charlie@example.com
```

## Using Other Email Providers

### Outlook/Office365
```env
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
```

### Yahoo Mail
```env
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
```

### Custom SMTP
```env
SMTP_SERVER=mail.yourprovider.com
SMTP_PORT=587  # or 465 for SSL
```

## Troubleshooting

### Authentication Error
**Problem**: "535-5.7.8 Username and Password not accepted"

**Solutions**:
1. Regenerate Gmail App Password
2. Ensure 2FA is enabled
3. Check password has no spaces
4. Verify email address is correct

### Connection Error
**Problem**: "Connection refused" or "Timeout"

**Solutions**:
1. Check SMTP server address
2. Verify port number (587 for TLS, 465 for SSL)
3. Check firewall/network settings

### No Recipients
**Problem**: "Email not configured" warning

**Solutions**:
1. Check `.env` file exists
2. Verify `RECIPIENT_EMAILS` is filled
3. Ensure no example.com addresses remain

## Configuration Priority

The app checks for email configuration in this order:

1. **`.env` file** (Recommended)
   - Secure
   - Not in git
   - Easy to update

2. **`config.yaml`** (Fallback)
   - Can be used if needed
   - Less secure (might be committed)
   - Set `use_env_file: false` to use this

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SMTP_SERVER` | Yes | SMTP server address | smtp.gmail.com |
| `SMTP_PORT` | Yes | SMTP port number | 587 |
| `SENDER_EMAIL` | Yes | Your email address | you@gmail.com |
| `SENDER_PASSWORD` | Yes | App password (not regular password) | abcd efgh ijkl mnop |
| `RECIPIENT_EMAILS` | Yes | Comma-separated recipients | alice@ex.com,bob@ex.com |

## Testing in Streamlit App

1. Open the app:
   ```bash
   streamlit run streamlit_app.py
   ```

2. Navigate to **📧 Email Alerts**

3. If configured correctly, you'll see:
   - ✅ Email configuration section
   - List of recipients
   - Send button enabled

4. If not configured:
   - ⚠️ Configuration warning
   - Setup instructions

## Best Practices

✅ **DO**:
- Use App Passwords (not your main password)
- Keep `.env` file secure
- Add `.env` to `.gitignore`
- Test configuration before using
- Use multiple recipients for backup

❌ **DON'T**:
- Commit `.env` file to git
- Share `.env` file publicly
- Use your regular email password
- Hard-code credentials in code
- Include example values in production

## Support

### Gmail Specific Issues

**Less Secure Apps**:
- Gmail now requires App Passwords
- Regular passwords no longer work
- Must have 2FA enabled

**Daily Sending Limits**:
- New accounts: ~100-500 emails/day
- Established accounts: ~2000 emails/day
- Upgrade to Google Workspace for higher limits

### Additional Help

- Check `EMAIL_ALERTS_GUIDE.md` for usage instructions
- Run `python test_email_smtp.py` for diagnostics
- Review logs in Streamlit app for errors

---

## Quick Checklist

- [ ] Copied `.env.example` to `.env`
- [ ] Updated `SENDER_EMAIL` with your Gmail
- [ ] Enabled 2FA on Google account
- [ ] Generated App Password
- [ ] Added App Password to `.env`
- [ ] Added recipient emails (comma-separated)
- [ ] Ran `python test_email_smtp.py`
- [ ] Received test email successfully
- [ ] `.env` is in `.gitignore`
- [ ] Never committed `.env` to git

✅ **Ready to send earnings reports!**
