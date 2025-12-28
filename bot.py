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

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def is_owner(user_id: int) -> bool:
    return user_id in get_owners()


def owner_filter(_, __, message: Message):
    if not message.from_user:
        return False
    return is_owner(message.from_user.id)


OWNER = filters.create(owner_filter)


async def alert_owners(text: str):
    for owner in get_owners():
        try:
            await app.send_message(owner, f"⚠️ **Chmasta Alert**\n{text}")
        except:
            pass


# -------------------------------------------------
# START
# -------------------------------------------------
@app.on_message(filters.private & filters.command("start"))
async def start(_, m):
    await app.send_photo(
        m.chat.id,
        START_IMAGE,
        caption=(
            "✨ **Welcome to Chmasta** ✨\n\n"
            "I auto-delete messages from selected admins "
            "in your channels after a custom delay ⏱\n\n"
            "📌 Configure everything from private chat\n"
            "📘 Use /help to get started\n\n"
            "🚀 Bot is running smoothly!"
        )
    )


# -------------------------------------------------
# HELP
# -------------------------------------------------
@app.on_message(filters.private & filters.command("help"))
async def help_cmd(_, m):
    await m.reply(
        "📘 **Chmasta Commands**\n\n"
        "/settime `<channel_id> <seconds>` ⏱\n"
        "/whitelist `<channel_id> <user_id>` ✅\n"
        "/unwhitelist `<channel_id> <user_id>` ❌\n"
        "/owners 👑\n"
        "/addowner `<user_id>` ➕ (main owner)\n"
        "/removeowner `<user_id>` ➖ (main owner)\n"
        "/logs 📊\n\n"
        "⚠ Bot must be admin with delete permission"
    )


# -------------------------------------------------
# SET TIMER (PER CHANNEL)
# -------------------------------------------------
@app.on_message(filters.private & filters.command("settime") & OWNER)
async def settime(_, m):
    if len(m.command) < 3:
        return await m.reply(
            "❌ **Usage:**\n"
            "`/settime <channel_id> <seconds>`\n\n"
            "Example:\n"
            "`/settime -1001234567890 3600`"
        )

    channel_id = int(m.command[1])
    seconds = int(m.command[2])

    set_timer(channel_id, seconds)
    log_action("SET_TIMER", m.from_user.id, channel_id, str(seconds))

    await m.reply(f"⏱ Auto-delete set to `{seconds}` seconds")


# -------------------------------------------------
# WHITELIST ADMIN
# -------------------------------------------------
@app.on_message(filters.private & filters.command("whitelist") & OWNER)
async def whitelist(_, m):
    if len(m.command) < 3:
        return await m.reply(
            "❌ **Usage:**\n"
            "`/whitelist <channel_id> <user_id>`\n\n"
            "Example:\n"
            "`/whitelist -1001234567890 123456789`"
        )

    channel_id = int(m.command[1])
    user_id = int(m.command[2])

    add_admin(channel_id, user_id)
    log_action("ADMIN_ADD", m.from_user.id, channel_id, str(user_id))

    await m.reply("✅ Admin whitelisted for this channel")


@app.on_message(filters.private & filters.command("unwhitelist") & OWNER)
async def unwhitelist(_, m):
    if len(m.command) < 3:
        return await m.reply(
            "❌ **Usage:**\n"
            "`/unwhitelist <channel_id> <user_id>`"
        )

    channel_id = int(m.command[1])
    user_id = int(m.command[2])

    remove_admin(channel_id, user_id)
    log_action("ADMIN_REMOVE", m.from_user.id, channel_id, str(user_id))

    await m.reply("❌ Admin removed from this channel")


# -------------------------------------------------
# OWNERS
# -------------------------------------------------
@app.on_message(filters.private & filters.command("owners") & OWNER)
async def owners_cmd(_, m):
    text = "👑 **Bot Owners**\n\n"
    for o in get_owners():
        badge = "⭐" if o == MAIN_OWNER_ID else ""
        text += f"• `{o}` {badge}\n"
    await m.reply(text)


@app.on_message(filters.private & filters.command("addowner") & OWNER)
async def addowner(_, m):
    if m.from_user.id != MAIN_OWNER_ID:
        return await m.reply("🚫 Only MAIN OWNER can add owners")

    if len(m.command) < 2:
        return await m.reply("❌ Usage: `/addowner <user_id>`")

    uid = int(m.command[1])
    add_owner(uid)
    log_action("OWNER_ADD", m.from_user.id, details=str(uid))

    await m.reply("➕ Owner added")


@app.on_message(filters.private & filters.command("removeowner") & OWNER)
async def removeowner(_, m):
    if m.from_user.id != MAIN_OWNER_ID:
        return await m.reply("🚫 Only MAIN OWNER can remove owners")

    if len(m.command) < 2:
        return await m.reply("❌ Usage: `/removeowner <user_id>`")

    uid = int(m.command[1])
    if not remove_owner(uid):
        return await m.reply("❌ Cannot remove MAIN OWNER")

    log_action("OWNER_REMOVE", m.from_user.id, details=str(uid))
    await m.reply("➖ Owner removed")


# -------------------------------------------------
# LOGS
# -------------------------------------------------
@app.on_message(filters.private & filters.command("logs") & OWNER)
async def logs_cmd(_, m):
    data = logs.find().sort("time", -1).limit(10)
    text = "📊 **Recent Logs**\n\n"
    for d in data:
        text += f"• `{d['action']}` → `{d.get('details','')}`\n"
    await m.reply(text)


# -------------------------------------------------
# AUTO DELETE (CHANNEL SILENT HANDLER)
# -------------------------------------------------
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
        await alert_owners(f"Failed to delete message `{m.id}` in `{m.chat.id}`")


print("✅ Chmasta deployed successfully — running 24/7 🚀")
app.run()
