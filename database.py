from pymongo import MongoClient
from datetime import datetime
from config import MONGO_URI, DB_NAME, MAIN_OWNER_ID

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

owners = db.owners
channels = db.channels
admins = db.admins
logs = db.logs


# ---------- OWNERS ----------
def init_main_owner():
    owners.update_one(
        {"_id": "owners"},
        {"$addToSet": {"users": MAIN_OWNER_ID}},
        upsert=True
    )


def get_owners():
    data = owners.find_one({"_id": "owners"})
    return data["users"] if data else []


def add_owner(user_id: int):
    owners.update_one(
        {"_id": "owners"},
        {"$addToSet": {"users": user_id}},
        upsert=True
    )


def remove_owner(user_id: int):
    if user_id == MAIN_OWNER_ID:
        return False
    owners.update_one(
        {"_id": "owners"},
        {"$pull": {"users": user_id}}
    )
    return True


# ---------- CHANNEL TIMERS ----------
def set_timer(channel_id: int, seconds: int):
    channels.update_one(
        {"channel_id": channel_id},
        {"$set": {"timer": seconds}},
        upsert=True
    )


def get_timer(channel_id: int, default: int):
    data = channels.find_one({"channel_id": channel_id})
    return data["timer"] if data else default


# ---------- ADMIN WHITELIST ----------
def add_admin(channel_id: int, user_id: int):
    admins.update_one(
        {"channel_id": channel_id},
        {"$addToSet": {"admins": user_id}},
        upsert=True
    )


def remove_admin(channel_id: int, user_id: int):
    admins.update_one(
        {"channel_id": channel_id},
        {"$pull": {"admins": user_id}}
    )


def get_admins(channel_id: int):
    data = admins.find_one({"channel_id": channel_id})
    return data["admins"] if data else []


# ---------- LOGS ----------
def log_action(action, by, channel_id=None, details=None):
    logs.insert_one({
        "action": action,
        "by": by,
        "channel_id": channel_id,
        "details": details,
        "time": datetime.utcnow()
    })
