from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Convert premium datetime fields to timestamp"

    def handle(self, *args, **options):
        db = connection.cursor().db_conn
        col = db["backend_api_user"]

        count = 0

        for u in col.find({
            "premium_expires_at": {"$exists": True}
        }):
            started = u.get("premium_started_at")
            expires = u.get("premium_expires_at")

            update = {}

            if started:
                update["premium_started_at_ts"] = int(started.timestamp())
            if expires:
                update["premium_expires_at_ts"] = int(expires.timestamp())

            if update:
                col.update_one({"_id": u["_id"]}, {"$set": update})
                count += 1

        self.stdout.write(f"Converted {count} users.")
