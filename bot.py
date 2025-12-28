import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

from pyrogram import idle
from config import *
from database import *

logging.basicConfig(level=logging.INFO)

# 🤖 Bot client (commands)
bot = Client(
    "chmasta_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# 👤 User client (DELETION ENGINE)
user = Client(
    "chmasta_user",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION
)

init_main_owner()


# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def is_owner(user_id):
    return user_id in get_owners()


def owner_filter(_, __, m):
    return m.from_user and is_owner(m.from_user.id)


OWNER = filters.create(owner_filter)


# -------------------------------------------------
# START / HELP
# -------------------------------------------------
@bot.on_message(filters.private & filters.command("start"))
async def start(_, m):
    await m.reply_photo(
        START_IMAGE,
        caption="✨ **Chmasta is live!**\n\nUse /help to configure channels."
    )

@bot.on_message(filters.private & filters.command("help"))
async def help_cmd(_, m):
    await m.reply(
        "📘 **Commands**\n\n"
        "/channel <channel_id> – verify channel\n"
        "/channels – list channels\n"
        "/settime <channel_id> <seconds>\n"
        "/whitelist <channel_id> <user_id>\n"
    )


# -------------------------------------------------
# CHANNEL VERIFICATION
# -------------------------------------------------
@bot.on_message(filters.private & filters.command("channel") & OWNER)
async def channel_verify(_, m):
    if len(m.command) < 2:
        return await m.reply("❌ Usage: /channel <channel_id>")

    cid = int(m.command[1])
    verify_channel(cid)
    log_action("CHANNEL_VERIFY", m.from_user.id, cid)

    await m.reply("✅ Channel verified & synced")


@bot.on_message(filters.private & filters.command("channels") & OWNER)
async def channels_cmd(_, m):
    chs = get_channels()
    if not chs:
        return await m.reply("📭 No channels added")

    text = "📡 **Managed Channels**\n\n"
    for c in chs:
        text += f"• `{c['channel_id']}`\n"
    await m.reply(text)


# -------------------------------------------------
# TIMER / WHITELIST
# -------------------------------------------------
@bot.on_message(filters.private & filters.command("settime") & OWNER)
async def settime(_, m):
    if len(m.command) < 3:
        return await m.reply("❌ /settime <channel_id> <seconds>")

    cid = int(m.command[1])
    sec = int(m.command[2])

    set_timer(cid, sec)
    log_action("SET_TIMER", m.from_user.id, cid, sec)

    await m.reply(f"⏱ Timer set to {sec}s")


@bot.on_message(filters.private & filters.command("whitelist") & OWNER)
async def whitelist(_, m):
    if len(m.command) < 3:
        return await m.reply("❌ /whitelist <channel_id> <user_id>")

    cid = int(m.command[1])
    uid = int(m.command[2])

    add_admin(cid, uid)
    log_action("ADMIN_ADD", m.from_user.id, cid, uid)

    await m.reply("✅ Admin whitelisted")


# -------------------------------------------------
# AUTO DELETE (USER SESSION – WORKS)
# -------------------------------------------------
@user.on_message(filters.channel)
async def auto_delete(_, m: Message):
    cid = m.chat.id
    admins = get_admins(cid)

    if m.from_user and m.from_user.id in admins:
        timer = get_timer(cid, DEFAULT_DELETE_TIME)
        await asyncio.sleep(timer)

        try:
            await user.delete_messages(cid, m.id)
            log_action("MESSAGE_DELETED", m.from_user.id, cid, m.id)
        except Exception as e:
            log_action("DELETE_FAILED", None, cid, str(e))


# -------------------------------------------------
# RUN BOTH
# -------------------------------------------------
print("✅ Chmasta fully operational 🚀")

bot.start()
user.start()

print("🤖 Chmasta is running — press Ctrl+C to stop")
idle()

bot.stop()
user.stop()
