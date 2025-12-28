import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

from config import *
from database import *
from permissions import OWNER_PERMISSIONS

logging.basicConfig(level=logging.INFO)

app = Client(
    "chmasta",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

init_main_owner()


# ---------- HELPERS ----------
def is_owner(user_id):
    return user_id in get_owners()

def owner_filter(_, __, message):
    return is_owner(message.from_user.id)

OWNER = filters.create(owner_filter)


async def alert_owners(text):
    for owner in get_owners():
        try:
            await app.send_message(owner, f"⚠️ **Chmasta Alert**\n{text}")
        except:
            pass


# ---------- START ----------
@app.on_message(filters.private & filters.command("start"))
async def start(_, m):
    await app.send_photo(
        m.chat.id,
        START_IMAGE,
        caption=(
            "✨ **Welcome to Chmasta** ✨\n\n"
            "I automatically delete messages sent by selected admins "
            "after a custom delay — per channel ⏱\n\n"
            "➕ Add me as **admin** to your channel\n"
            "⚙ Configure with /help\n\n"
            "🚀 Running smooth & strong!"
        )
    )


# ---------- HELP ----------
@app.on_message(filters.private & filters.command("help"))
async def help_cmd(_, m):
    await m.reply(
        "📘 **Chmasta Commands**\n\n"
        "/settime `<seconds>` ⏱\n"
        "/whitelist `<user_id>` ✅\n"
        "/unwhitelist `<user_id>` ❌\n"
        "/owners 👑\n"
        "/addowner `<user_id>` ➕ (main owner)\n"
        "/removeowner `<user_id>` ➖ (main owner)\n"
        "/logs 📊\n\n"
        "⚠ Bot must have delete permission"
    )


# ---------- SET TIME ----------
@app.on_message(filters.command("settime") & OWNER)
async def settime(_, m):
    if not OWNER_PERMISSIONS["set_time"]:
        return

    timer = int(m.command[1])
    set_timer(m.chat.id, timer)
    log_action("SET_TIMER", m.from_user.id, m.chat.id, str(timer))
    await m.reply(f"⏱ Timer set to `{timer}` seconds")


# ---------- ADMIN WHITELIST ----------
@app.on_message(filters.command("whitelist") & OWNER)
async def whitelist(_, m):
    uid = int(m.command[1])
    add_admin(m.chat.id, uid)
    log_action("ADMIN_ADD", m.from_user.id, m.chat.id, str(uid))
    await m.reply("✅ Admin whitelisted")

@app.on_message(filters.command("unwhitelist") & OWNER)
async def unwhitelist(_, m):
    uid = int(m.command[1])
    remove_admin(m.chat.id, uid)
    log_action("ADMIN_REMOVE", m.from_user.id, m.chat.id, str(uid))
    await m.reply("❌ Admin removed")


# ---------- OWNERS ----------
@app.on_message(filters.command("owners") & OWNER)
async def owners_cmd(_, m):
    text = "👑 **Owners**\n\n"
    for o in get_owners():
        badge = "⭐" if o == MAIN_OWNER_ID else ""
        text += f"• `{o}` {badge}\n"
    await m.reply(text)

@app.on_message(filters.command("addowner") & OWNER)
async def addowner(_, m):
    if m.from_user.id != MAIN_OWNER_ID:
        return await m.reply("🚫 Only MAIN OWNER")

    uid = int(m.command[1])
    add_owner(uid)
    log_action("OWNER_ADD", m.from_user.id, details=str(uid))
    await m.reply("➕ Owner added")

@app.on_message(filters.command("removeowner") & OWNER)
async def removeowner(_, m):
    if m.from_user.id != MAIN_OWNER_ID:
        return await m.reply("🚫 Only MAIN OWNER")

    uid = int(m.command[1])
    if not remove_owner(uid):
        return await m.reply("❌ Cannot remove MAIN OWNER")

    log_action("OWNER_REMOVE", m.from_user.id, details=str(uid))
    await m.reply("➖ Owner removed")


# ---------- LOGS ----------
@app.on_message(filters.command("logs") & OWNER)
async def logs_cmd(_, m):
    data = logs.find().sort("time", -1).limit(10)
    text = "📊 **Recent Logs**\n\n"
    for d in data:
        text += f"• `{d['action']}` → `{d.get('details','')}`\n"
    await m.reply(text)


# ---------- AUTO DELETE ----------
@app.on_message(filters.channel)
async def auto_delete(_, m: Message):
    if not m.from_user:
        return

    admins_list = get_admins(m.chat.id)
    if m.from_user.id not in admins_list:
        return

    timer = get_timer(m.chat.id, DEFAULT_DELETE_TIME)
    await asyncio.sleep(timer)

    try:
        await m.delete()
        log_action("MESSAGE_DELETED", m.from_user.id, m.chat.id, str(m.id))
    except Exception as e:
        log_action("DELETE_FAILED", m.from_user.id, m.chat.id, str(e))
        await alert_owners(f"Delete failed in `{m.chat.id}`")


print("✅ Chmasta deployed successfully — running 24/7 🚀")
app.run()
