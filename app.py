import asyncio
import json
import os
import aiohttp
import random
import string
from datetime import datetime
from pytz import timezone
from pyrogram.types import Message, PreCheckoutQuery
from pyrogram.handlers import PreCheckoutQueryHandler, MessageHandler
from pyrogram import Client, filters, types

class Config:
    API_ID = "26850449"
    API_HASH = "72a730c380e68095a8549ad7341b0608"
    BOT_TOKEN = "8087895028:AAEbGcnvo48_-5EbmhXw_3-WTNeLZhY6zvM"
    REFERRAL_CODE = "_tgr_SPS-LQYzMjll"
    ADMIN_IDS = [6505111743]

class Pyro:
    Soumo = Client(
        name="Soumo",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        in_memory=True
    )
app = Pyro.Soumo

DATABASE_FILE = "database.json"
REMOVED_USERS_FILE = "removedUsers.json"

def load_data(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

database = load_data(DATABASE_FILE)
removed_users = load_data(REMOVED_USERS_FILE)

def generate_transaction_hash():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

async def startHandler(app: Client, message: Message):
    user_id = str(message.from_user.id)
    args = message.command[1] if len(message.command) > 1 else None

    if user_id in removed_users:
        await message.reply("❌ You are permanently blocked from using this bot.")
        return

    if user_id in database:
        await message.reply("✅ You are already approved to use the bot.")
        return

    if args == Config.REFERRAL_CODE:
        database[user_id] = {"approved": True, "transactions": []}
        save_data(DATABASE_FILE, database)
        await message.reply("✅ You have been approved to use the Stars Farming Bot!")
    else:
        removed_users[user_id] = {"blocked": True}
        save_data(REMOVED_USERS_FILE, removed_users)
        await message.reply("❌ You must start the bot using the special referral link.\n\nYou are now permanently blocked from using this bot.")
        return

async def farmHandler(app: Client, message: Message):     
    user_id = str(message.from_user.id)

    if user_id not in database:
        await message.reply("❌ You are not approved to use this bot.")
        return

    amount = 100
    if len(message.command) > 1:
        try:
            amount = int(message.command[1])
            if amount <= 0:
                return await message.reply("Amount must be positive.")
            if amount > 100000:
                return await message.reply("The maximum amount is 100000.")
        except ValueError:
            return await message.reply("Invalid amount !")

    transaction_hash = generate_transaction_hash()
    ist_time = datetime.now(timezone("Asia/Kolkata")).strftime("%d %B %Y, %I:%M %p IST")

    transaction = {
        "hash": transaction_hash,
        "amount": amount,
        "time": ist_time
    }

    database[user_id]["transactions"].append(transaction)
    save_data(DATABASE_FILE, database)

    await app.send_invoice(
        chat_id=message.chat.id,
        title="FARMING",
        description="Let's farm Telegram stars together!",
        currency="XTR",
        prices=[types.LabeledPrice(label="Star", amount=amount)],
        payload="stars",
        photo_url="https://i.ibb.co/7XqgFQt/Telegram-Stars.png"
    )

async def mylogsHandler(app: Client, message: Message):
    user_id = str(message.from_user.id)

    if user_id not in database:
        await message.reply("❌ You are not approved to use this bot.")
        return

    transactions = database[user_id].get("transactions", [])
    if not transactions:
        await message.reply("You have no transactions yet.")
        return

    logs = f"{message.from_user.mention}'s Transaction Details:\n\n"
    
    for i, tx in enumerate(transactions, start=1):
        hash_short = f"{tx['hash'][:4]}...{tx['hash'][-5:]}"
        logs += f"{i}. Hash: `{hash_short}`\n   Amount: {tx['amount']} Stars\n   Time: {tx['time']}\n\n"

    await message.reply(logs)

async def approveHandler(app: Client, message: Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.reply("❌ You are not authorized to approve users.")
        return

    if len(message.command) < 2:
        await message.reply("⚠️ Please provide a user ID to approve.\nExample: `/approve 123456789`")
        return

    user_id = message.command[1]

    if user_id in database:
        await message.reply(f"✅ User `{user_id}` is already approved.")
        return

    if user_id in removed_users:
        await message.reply(f"❌ User `{user_id}` is permanently blocked and cannot be approved.")
        return

    database[user_id] = {"approved": True, "transactions": []}
    save_data(DATABASE_FILE, database)

    await message.reply(f"✅ User `{user_id}` has been approved.")

async def cleardbHandler(app: Client, message: Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.reply("❌ You are not authorized to clear the database.")
        return

    if os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)
    if os.path.exists(REMOVED_USERS_FILE):
        os.remove(REMOVED_USERS_FILE)

    save_data(DATABASE_FILE, {})
    save_data(REMOVED_USERS_FILE, {})

    await message.reply("✅ Both databases have been cleared successfully!")

async def preCheckout_queryHandler(app: Client, query: PreCheckoutQuery) -> None:
    await query.answer(True)

async def successPays(app: Client, message: Message):
    if message.successful_payment:
        await message.reply("Payment Received!")

app.add_handler(MessageHandler(startHandler, filters.command("start")))
app.add_handler(MessageHandler(farmHandler, filters.command("farm")))
app.add_handler(MessageHandler(mylogsHandler, filters.command("mylogs")))
app.add_handler(MessageHandler(approveHandler, filters.command("approve")))
app.add_handler(MessageHandler(cleardbHandler, filters.command("cleardb")))
app.add_handler(PreCheckoutQueryHandler(preCheckout_queryHandler))
app.add_handler(MessageHandler(successPays, filters.successful_payment))

app.run()
