from django.core.management.base import BaseCommand
from django.db import connection
import time
import json
from bson import ObjectId
from pathlib import Path


class Command(BaseCommand):
    help = "DEBUG expired premium users (timestamp-based) -> write to JSON file"

    def handle(self, *args, **options):
        now_ts = int(time.time())

        db = connection.cursor().db_conn
        collection = db["api_user"]

        debug = {
            "now_ts": now_ts,
            "collections": [],
            "total_users": 0,
            "premium_users_count": 0,
            "users": [],
            "expired_ids": [],
            "note": "DEBUG MODE ONLY – NO UPDATE EXECUTED"
        }

        # 1️⃣ List collections
        debug["collections"] = db.list_collection_names()

        # 2️⃣ Count users
        debug["total_users"] = collection.count_documents({})

        premium_users = list(collection.find({"is_premium": True}))
        debug["premium_users_count"] = len(premium_users)

        # 3️⃣ Per-user debug
        for user in premium_users:
            user_debug = {}

            user_id = user.get("_id")
            username = user.get("username")
            expires_ts = user.get("premium_expires_at_ts")

            user_debug["_id"] = str(user_id) if isinstance(user_id, ObjectId) else user_id
            user_debug["username"] = username
            user_debug["premium_expires_at_ts"] = expires_ts
            user_debug["expires_ts_type"] = str(type(expires_ts))

            if expires_ts is None:
                user_debug["error"] = "premium_expires_at_ts is None"
                debug["users"].append(user_debug)
                continue

            try:
                expires_ts_int = int(expires_ts)
                user_debug["expires_ts_int"] = expires_ts_int
                user_debug["is_expired"] = expires_ts_int < now_ts
            except Exception as e:
                user_debug["error"] = f"Cannot cast expires_ts to int: {str(e)}"
                debug["users"].append(user_debug)
                continue

            if expires_ts_int < now_ts:
                debug["expired_ids"].append(user_debug["_id"])

            debug["users"].append(user_debug)

        # 4️⃣ Write to backend/checkexpire.json
        output_path = Path("backend/checkexpire.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(debug, f, indent=2, ensure_ascii=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Debug written to {output_path} (NO DATABASE UPDATE)"
            )
        )
