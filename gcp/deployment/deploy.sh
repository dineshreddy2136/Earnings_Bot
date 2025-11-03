#!/bin/bash

##############################################################################
# GCP Deployment Script - Earnings Bot
# 
# This script helps you deploy the Earnings Bot to Google Cloud Platform
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           Earnings Bot - GCP Deployment Script              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print step headers
print_step() {
    echo -e "\n${GREEN}▶ $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${YELLOW}  ℹ $1${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}  ✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}  ✗ $1${NC}"
}

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI not found"
    echo -e "\nPlease install gcloud CLI:"
    echo "  macOS: brew install --cask google-cloud-sdk"
    echo "  or visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

print_success "gcloud CLI found"

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    print_error "No GCP project configured"
    echo ""
    read -p "Enter your GCP Project ID: " PROJECT_ID
    gcloud config set project "$PROJECT_ID"
fi

print_info "Using project: $PROJECT_ID"

# Parse command
COMMAND=${1:-help}

case "$COMMAND" in
    setup)
        print_step "Setting up GCP services..."
        
        print_info "Enabling required APIs..."
        gcloud services enable cloudfunctions.googleapis.com
        gcloud services enable cloudscheduler.googleapis.com
        gcloud services enable firestore.googleapis.com
        gcloud services enable secretmanager.googleapis.com
        gcloud services enable cloudbuild.googleapis.com
        
        print_success "APIs enabled"
        
        print_info "Initializing Firestore..."
        gcloud firestore databases create --region=us-central --project="$PROJECT_ID" || print_info "Firestore already exists"
        
        print_success "Setup complete!"
        print_info "Next step: Run ./setup_secrets.sh to configure secrets"
        ;;
    
    deploy)
        print_step "Deploying Cloud Function..."
        
        cd ..
        
        gcloud functions deploy earnings-bot-daily \
            --gen2 \
            --runtime=python311 \
            --region=us-central1 \
            --source=. \
            --entry-point=main \
            --trigger-http \
            --allow-unauthenticated \
            --memory=512MB \
            --timeout=540s \
            --set-env-vars=GCP_PROJECT="$PROJECT_ID"
        
        FUNCTION_URL=$(gcloud functions describe earnings-bot-daily --region=us-central1 --format='value(serviceConfig.uri)')
        
        print_success "Cloud Function deployed!"
        print_info "Function URL: $FUNCTION_URL"
        
        print_step "Setting up Cloud Scheduler..."
        
        # Delete existing job if it exists
        gcloud scheduler jobs delete earnings-bot-scheduler --location=us-central1 --quiet 2>/dev/null || true
        
        # Create new job
        gcloud scheduler jobs create http earnings-bot-scheduler \
            --location=us-central1 \
            --schedule="0 8 * * *" \
            --time-zone="America/New_York" \
            --uri="$FUNCTION_URL" \
            --http-method=GET \
            --attempt-deadline=540s
        
        print_success "Scheduler configured to run daily at 8:00 AM EST"
        ;;
    
    test)
        print_step "Testing Cloud Function..."
        
        FUNCTION_URL=$(gcloud functions describe earnings-bot-daily --region=us-central1 --format='value(serviceConfig.uri)')
        
        print_info "Invoking function at: $FUNCTION_URL"
        
        curl -X GET "$FUNCTION_URL" -H "Content-Type: application/json"
        
        print_success "Test complete - check output above"
        ;;
    
    logs)
        print_step "Fetching recent logs..."
        
        gcloud functions logs read earnings-bot-daily --region=us-central1 --limit=100
        ;;
    
    status)
        print_step "Checking deployment status..."
        
        print_info "Cloud Function:"
        gcloud functions describe earnings-bot-daily --region=us-central1 --format="table(name,state,runtime,availableMemory,timeout)" || print_error "Function not deployed"
        
        echo ""
        print_info "Scheduler Job:"
        gcloud scheduler jobs describe earnings-bot-scheduler --location=us-central1 --format="table(name,state,schedule,timeZone)" || print_error "Scheduler not configured"
        ;;
    
    cleanup)
        print_step "Cleaning up GCP resources..."
        
        read -p "Are you sure you want to delete all resources? (yes/no): " CONFIRM
        
        if [ "$CONFIRM" == "yes" ]; then
            print_info "Deleting Cloud Scheduler job..."
            gcloud scheduler jobs delete earnings-bot-scheduler --location=us-central1 --quiet || true
            
            print_info "Deleting Cloud Function..."
            gcloud functions delete earnings-bot-daily --region=us-central1 --quiet || true
            
            print_success "Resources deleted"
        else
            print_info "Cleanup cancelled"
        fi
        ;;
    
    *)
        echo -e "${BLUE}Usage:${NC} $0 {setup|deploy|test|logs|status|cleanup}"
        echo ""
        echo "Commands:"
        echo "  setup    - Enable required GCP APIs and services"
        echo "  deploy   - Deploy Cloud Function and Scheduler"
        echo "  test     - Test the deployed Cloud Function"
        echo "  logs     - View recent execution logs"
        echo "  status   - Check deployment status"
        echo "  cleanup  - Delete all GCP resources"
        echo ""
        echo "Example:"
        echo "  $0 setup      # First time setup"
        echo "  $0 deploy     # Deploy to GCP"
        echo "  $0 test       # Test deployment"
        ;;
esac
