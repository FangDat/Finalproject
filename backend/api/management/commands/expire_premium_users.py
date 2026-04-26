from django.core.management.base import BaseCommand
from django.db import connection
import time
import logging
logger = logging.getLogger("cron.expire_premium")

class Command(BaseCommand):  # Define custom command class
    help = "Deactivate expired premium users (timestamp-based)"

    def handle(self, *args, **options):  # Main function executed when command runs
        now_ts = int(time.time())   # Get current time as integer timestamp

        db = connection.cursor().db_conn    # Get raw database connection

        collection = db["api_user"] # Select the correct MongoDB collection


        expired_count = collection.count_documents({    # Count expired premium users
            "is_premium": True,  # Only users with premium status
            "premium_expires_at_ts": {"$lt": now_ts}    # Expired if timestamp is less than now
        })
        
        msg = f"Expired users matched: {expired_count}"
        self.stdout.write(f"Expired users matched: {expired_count}")
        logger.info(msg)

        if expired_count == 0:   # Check if no expired users found
            self.stdout.write("No expired users found.")
            logger.info("No expired users found.")
            return


        result = collection.update_many(    # Update multiple expired users
            {
                "is_premium": True, # Filter premium users
                "premium_expires_at_ts": {"$lt": now_ts}
            },
            {
                "$set": {"is_premium": False}   # Set premium status to false
            }   
        )
        success_msg = (
            f"Matched: {result.matched_count}, "
            f"Modified: {result.modified_count}"
        )
        
        logger.info(success_msg)

        self.stdout.write(
            self.style.SUCCESS(
                f"Matched: {result.matched_count}, Modified: {result.modified_count}"
            )
        )
