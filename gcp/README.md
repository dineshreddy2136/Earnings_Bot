# GCP Deployment - Earnings Bot

This folder contains all GCP-related code and configurations for deploying the Earnings Bot to Google Cloud Platform.

## 📁 Folder Structure

```
gcp/
├── README.md                 # This file - deployment guide
├── main.py                   # Cloud Function entry point
├── requirements.txt          # Python dependencies for Cloud Function
├── firestore_db.py          # Firestore database operations
├── email_service.py         # Email sending service
├── earnings_sync.py         # Earnings data sync logic
├── config.yaml              # Configuration (non-sensitive)
├── .gcloudignore           # Files to ignore during deployment
└── deployment/
    ├── deploy.sh            # Deployment script
    ├── setup_secrets.sh     # Script to set up GCP secrets
    └── scheduler_config.yaml # Cloud Scheduler configuration
```

## 🚀 Architecture

```
Cloud Scheduler (Daily at 8 AM EST)
    ↓
Cloud Function (Python 3.11)
    ↓
├─> Firestore (Store earnings data)
├─> yfinance API (Fetch earnings data)
└─> Gmail SMTP (Send email)
```

## 📋 Prerequisites

1. **GCP Account** with billing enabled
2. **gcloud CLI** installed
3. **Python 3.11+** locally
4. **Gmail App Password** (already configured in .env)

## 🔧 Setup Instructions

### 1. Install gcloud CLI

```bash
# macOS
brew install --cask google-cloud-sdk

# Initialize and authenticate
gcloud init
gcloud auth login
```

### 2. Create GCP Project

```bash
# Set your project ID
export PROJECT_ID="earnings-bot-project"

# Create project
gcloud projects create $PROJECT_ID --name="Earnings Bot"

# Set as current project
gcloud config set project $PROJECT_ID

# Enable billing (do this via GCP Console)
# https://console.cloud.google.com/billing
```

### 3. Enable Required APIs

```bash
cd gcp/deployment
./deploy.sh setup
```

This will enable:
- Cloud Functions API
- Cloud Scheduler API
- Cloud Firestore API
- Secret Manager API
- Cloud Build API

### 4. Set Up Secrets

```bash
cd gcp/deployment
./setup_secrets.sh
```

This will prompt you for:
- SMTP password
- Recipient emails
- Any other sensitive config

### 5. Deploy Cloud Function

```bash
cd gcp
gcloud functions deploy earnings-bot-daily \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point main \
  --region us-central1 \
  --memory 512MB \
  --timeout 540s
```

### 6. Set Up Cloud Scheduler

```bash
cd gcp/deployment
gcloud scheduler jobs create http earnings-bot-scheduler \
  --location us-central1 \
  --schedule "0 8 * * *" \
  --time-zone "America/New_York" \
  --uri "https://us-central1-$PROJECT_ID.cloudfunctions.net/earnings-bot-daily" \
  --http-method GET
```

## 🎯 Daily Execution Flow

1. **8:00 AM EST** - Cloud Scheduler triggers Cloud Function
2. **Fetch Data** - Function pulls earnings data from yfinance
3. **Store in Firestore** - Data saved to Firestore database
4. **Sync Options Data** - IV Rank, Expected Move calculations
5. **Generate Email** - HTML + Plain text formats
6. **Send Email** - Via Gmail SMTP to configured recipients
7. **Log Results** - Execution logs in Cloud Logging

## 💰 Cost Estimate

Based on 1 execution per day:

| Service | Usage | Cost/Month |
|---------|-------|------------|
| Cloud Functions | 30 invocations, 512MB, ~30s each | **$0.00** (free tier) |
| Cloud Scheduler | 30 jobs/month | **$0.30** |
| Firestore | ~500 writes, ~1000 reads/month | **$0.00** (free tier) |
| Secret Manager | 30 accesses/month | **$0.00** (free tier) |
| **TOTAL** | | **~$0.30/month** |

## 🔐 Security

- ✅ **No credentials in code** - All stored in Secret Manager
- ✅ **Encrypted at rest** - Firestore and Secret Manager encryption
- ✅ **HTTPS only** - All communication encrypted
- ✅ **IAM roles** - Principle of least privilege
- ✅ **Audit logs** - Track all access

## 📊 Monitoring

### View Logs
```bash
gcloud functions logs read earnings-bot-daily --limit 50
```

### View Scheduler Jobs
```bash
gcloud scheduler jobs list
```

### Check Function Status
```bash
gcloud functions describe earnings-bot-daily --region us-central1
```

## 🧪 Testing

### Test Cloud Function Locally
```bash
cd gcp
python main.py
```

### Test Cloud Function on GCP
```bash
gcloud functions call earnings-bot-daily --region us-central1
```

### Trigger Scheduler Manually
```bash
gcloud scheduler jobs run earnings-bot-scheduler --location us-central1
```

## 🔄 Updates

### Deploy Updated Code
```bash
cd gcp
gcloud functions deploy earnings-bot-daily \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point main \
  --region us-central1
```

### Update Secrets
```bash
echo -n "new_password" | gcloud secrets versions add smtp-password --data-file=-
```

### Update Schedule
```bash
gcloud scheduler jobs update http earnings-bot-scheduler \
  --schedule "0 9 * * *" \
  --location us-central1
```

## 🐛 Troubleshooting

### Function Errors
```bash
# View recent errors
gcloud functions logs read earnings-bot-daily --limit 100 | grep ERROR

# View full execution trace
gcloud functions logs read earnings-bot-daily --limit 10
```

### Scheduler Not Running
```bash
# Check job status
gcloud scheduler jobs describe earnings-bot-scheduler --location us-central1

# Check recent executions
gcloud scheduler jobs run earnings-bot-scheduler --location us-central1
```

### Firestore Connection Issues
```bash
# Verify Firestore is enabled
gcloud services list | grep firestore

# Check IAM permissions
gcloud projects get-iam-policy $PROJECT_ID
```

## 📚 Resources

- [Cloud Functions Documentation](https://cloud.google.com/functions/docs)
- [Cloud Scheduler Documentation](https://cloud.google.com/scheduler/docs)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)

## 🆘 Support

If you encounter issues:
1. Check the logs first
2. Verify secrets are configured
3. Ensure APIs are enabled
4. Check billing is active
5. Review IAM permissions

---

**Note:** Keep your local Streamlit app as-is. It will continue to work with SQLite. The GCP deployment is separate for daily automation only.
