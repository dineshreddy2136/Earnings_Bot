"""
Cloud Function Entry Point - Earnings Bot Daily Sync

This function is triggered by Cloud Scheduler daily to:
1. Fetch earnings data from yfinance
2. Store data in Firestore
3. Sync options IV data
4. Send email report to recipients
"""

import functions_framework
from datetime import datetime, timedelta, date
import logging
from earnings_sync import EarningsSync
from email_service import EmailService
from firestore_db import FirestoreDB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@functions_framework.http
def main(request):
    """
    Main Cloud Function entry point
    
    Triggered by: Cloud Scheduler (daily at 8 AM EST)
    
    Returns:
        dict: Execution summary
    """
    try:
        logger.info("=" * 80)
        logger.info("Starting Earnings Bot daily execution")
        logger.info(f"Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
        # Initialize services
        db = FirestoreDB()
        earnings_sync = EarningsSync(db)
        email_service = EmailService(db)
        
        # Step 1: Sync earnings data
        logger.info("\n📊 Step 1: Syncing earnings data...")
        sync_result = earnings_sync.sync_all_earnings()
        logger.info(f"✅ Synced {sync_result['total_synced']} companies")
        logger.info(f"   - New records: {sync_result['new_records']}")
        logger.info(f"   - Updated records: {sync_result['updated_records']}")
        logger.info(f"   - Errors: {sync_result['errors']}")
        
        # Step 2: Sync options data for upcoming earnings
        logger.info("\n📈 Step 2: Syncing options IV data...")
        options_result = earnings_sync.sync_options_data()
        logger.info(f"✅ Synced options data for {options_result['total_synced']} symbols")
        logger.info(f"   - Errors: {options_result['errors']}")
        
        # Step 3: Send email report for this week
        logger.info("\n📧 Step 3: Sending email report...")
        email_result = email_service.send_weekly_report()
        logger.info(f"✅ Email sent to {email_result['recipients_count']} recipient(s)")
        logger.info(f"   - Companies in report: {email_result['companies_count']}")
        logger.info(f"   - Format: {email_result['format']}")
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("✅ Earnings Bot execution completed successfully!")
        logger.info("=" * 80)
        
        return {
            'status': 'success',
            'execution_time': datetime.now().isoformat(),
            'earnings_synced': sync_result['total_synced'],
            'options_synced': options_result['total_synced'],
            'email_sent': True,
            'recipients': email_result['recipients_count']
        }, 200
        
    except Exception as e:
        logger.error(f"❌ Error in main execution: {str(e)}", exc_info=True)
        
        return {
            'status': 'error',
            'error': str(e),
            'execution_time': datetime.now().isoformat()
        }, 500


def test_locally():
    """
    Test function locally before deploying
    """
    class MockRequest:
        pass
    
    result, status = main(MockRequest())
    print(f"\n{'=' * 80}")
    print(f"Test Result: {status}")
    print(f"Response: {result}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    # Run locally for testing
    test_locally()
