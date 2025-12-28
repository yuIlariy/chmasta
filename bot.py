import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import Message

from config import *
from database import *

logging.basicConfig(level=logging.INFO)

# 🤖 Bot client (commands only)
bot = Client(
    "chmasta_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# 👤 User client (deletion engine)
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
def is_owner(user_id: int) -> bool:
    return user_id in get_owners()


def owner_filter(_, __, message: Message):
    return message.from_user and is_owner(message.from_user.id)


OWNER = filters.create(owner_filter)

# -------------------------------------------------
# START
# -------------------------------------------------
@bot.on_message(filters.private & filters.command("start"))
async def start_handler(_, m: Message):
    await m.reply_photo(
        START_IMAGE,
        caption=(
            "✨ **Welcome to Chmasta** ✨\n\n"
            "I auto-delete messages from selected admins "
            "in verified channels after a delay ⏱\n\n"
            "Use /help to configure me.\n"
            "All commands are used in **private chat**."
        )
    )

# -------------------------------------------------
# HELP
# -------------------------------------------------
@bot.on_message(filters.private & filters.command("help"))
async def help_handler(_, m: Message):
    await m.reply(
        "📘 **Chmasta Commands**\n\n"
        "/channel <channel_id>\n"
        "/channels\n"
        "/settime <channel_id> <seconds>\n"
        "/whitelist <channel_id> <user_id>\n"
        "/unwhitelist <channel_id> <user_id>\n\n"
        "⚠ Bot deletes messages using a user account.\n"
        "The user account must be admin in the channel."
    )

# -------------------------------------------------
# CHANNEL VERIFICATION
# -------------------------------------------------
@bot.on_message(filters.private & filters.command("channel") & OWNER)
async def channel_verify(_, m: Message):
    if len(m.command) < 2:
        return await m.reply(
            "❌ **Usage:**\n"
            "`/channel <channel_id>`"
        )

    channel_id = int(m.command[1])

    # Force peer resolution using user session
    try:
        await user.get_chat(channel_id)
    except Exception:
        return await m.reply(
            "❌ Unable to verify channel.\n"
            "Make sure the user account has joined the channel."
        )

    verify_channel(channel_id)
    log_action("CHANNEL_VERIFY", m.from_user.id, channel_id)

    await m.reply("✅ Channel verified and synced")

# -------------------------------------------------
# CHANNEL LIST
# -------------------------------------------------
@bot.on_message(filters.private & filters.command("channels") & OWNER)
async def channels_list(_, m: Message):
    chs = get_channels()
    if not chs:
        return await m.reply("📭 No channels verified yet.")

    text = "📡 **Verified Channels**\n\n"
    for c in chs:
        text += f"• `{c['channel_id']}`\n"

    await m.reply(text)

# -------------------------------------------------
# SET TIMER
# -------------------------------------------------
@bot.on_message(filters.private & filters.command("settime") & OWNER)
async def settime(_, m: Message):
    if len(m.command) < 3:
        return await m.reply(
            "❌ **Usage:**\n"
            "`/settime <channel_id> <seconds>`"
        )

    channel_id = int(m.command[1])
    seconds = int(m.command[2])

    set_timer(channel_id, seconds)
    log_action("SET_TIMER", m.from_user.id, channel_id, seconds)

    await m.reply(f"⏱ Auto-delete set to `{seconds}` seconds")

# -------------------------------------------------
# WHITELIST
# -------------------------------------------------
@bot.on_message(filters.private & filters.command("whitelist") & OWNER)
async def whitelist(_, m: Message):
    if len(m.command) < 3:
        return await m.reply(
            "❌ **Usage:**\n"
            "`/whitelist <channel_id> <user_id>`"
        )

    channel_id = int(m.command[1])
    user_id = int(m.command[2])

    add_admin(channel_id, user_id)
    log_action("ADMIN_ADD", m.from_user.id, channel_id, user_id)

    await m.reply("✅ Admin whitelisted for this channel")


@bot.on_message(filters.private & filters.command("unwhitelist") & OWNER)
async def unwhitelist(_, m: Message):
    if len(m.command) < 3:
        return await m.reply(
            "❌ **Usage:**\n"
            "`/unwhitelist <channel_id> <user_id>`"
        )

    channel_id = int(m.command[1])
    user_id = int(m.command[2])

    remove_admin(channel_id, user_id)
    log_action("ADMIN_REMOVE", m.from_user.id, channel_id, user_id)

    await m.reply("❌ Admin removed from this channel")

# -------------------------------------------------
# AUTO DELETE (USER SESSION)
# -------------------------------------------------
@user.on_message(filters.channel)
async def auto_delete(_, m: Message):
    if not m.from_user:
        return

    channel_id = m.chat.id
    admins = get_admins(channel_id)

    if m.from_user.id not in admins:
        return

    delay = get_timer(channel_id, DEFAULT_DELETE_TIME)
    await asyncio.sleep(delay)

    try:
        await user.delete_messages(channel_id, m.id)
        log_action("MESSAGE_DELETED", m.from_user.id, channel_id, m.id)
    except Exception as e:
        log_action("DELETE_FAILED", m.from_user.id, channel_id, str(e))

# -------------------------------------------------
# RUN
# -------------------------------------------------
print("✅ Chmasta fully operational 🚀")

bot.start()
user.start()

print("🤖 Chmasta is running — press Ctrl+C to stop")
idle()

bot.stop()
user.stop()
