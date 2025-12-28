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

def add_owner(user_id):
    owners.update_one(
        {"_id": "owners"},
        {"$addToSet": {"users": user_id}},
        upsert=True
    )

def remove_owner(user_id):
    if user_id == MAIN_OWNER_ID:
        return False
    owners.update_one(
        {"_id": "owners"},
        {"$pull": {"users": user_id}}
    )
    return True


# ---------- CHANNELS ----------
def set_timer(chat_id, timer):
    channels.update_one(
        {"chat_id": chat_id},
        {"$set": {"timer": timer}},
        upsert=True
    )

def get_timer(chat_id, default):
    data = channels.find_one({"chat_id": chat_id})
    return data["timer"] if data else default


# ---------- ADMINS ----------
def add_admin(chat_id, user_id):
    admins.update_one(
        {"chat_id": chat_id},
        {"$addToSet": {"admins": user_id}},
        upsert=True
    )

def remove_admin(chat_id, user_id):
    admins.update_one(
        {"chat_id": chat_id},
        {"$pull": {"admins": user_id}}
    )

def get_admins(chat_id):
    data = admins.find_one({"chat_id": chat_id})
    return data["admins"] if data else []


# ---------- LOGS ----------
def log_action(action, by, chat_id=None, details=None):
    logs.insert_one({
        "action": action,
        "by": by,
        "chat_id": chat_id,
        "details": details,
        "time": datetime.utcnow()
    })
