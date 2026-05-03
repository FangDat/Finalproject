from django.core.management.base import BaseCommand
from django.db import connection
import time
import logging
logger = logging.getLogger("cron.expire_premium")

class Command(BaseCommand):
    help = "Deactivate expired premium users (timestamp-based)"

    def handle(self, *args, **options):
        now_ts = int(time.time())

        db = connection.cursor().db_conn

        # ✅ FIX: đúng collection name
        collection = db["api_user"]

        # 1️⃣ Đếm trước
        expired_count = collection.count_documents({
            "is_premium": True,
            "premium_expires_at_ts": {"$lt": now_ts}
        })
        
        msg = f"Expired users matched: {expired_count}"
        self.stdout.write(f"Expired users matched: {expired_count}")
        logger.info(msg)

        if expired_count == 0:
            self.stdout.write("No expired users found.")
            logger.info("No expired users found.")
            return

        # 2️⃣ Update
        result = collection.update_many(
            {
                "is_premium": True,
                "premium_expires_at_ts": {"$lt": now_ts}  # lt means "less than" 
            },
            {
                "$set": {"is_premium": False}
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
