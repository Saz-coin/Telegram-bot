import os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, Command_攻撃, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# --- CONFIGURATION ---
TOKEN = "8467862987:AAGnQyQ0nURo3Kn8-9ZtNYE8I0Y-jyeFaV8"
CHANNEL_ID = "@Soomcoin1"
CHANNEL_LINK = "https://t.me/Soomcoin1"

# --- RENDER KEEP-ALIVE (Flask) ---
app = Flask('')

@app.route('/')
def home():
    return "Soom Bot is Alive!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# --- DATABASE (In-memory for now) ---
db = {}

# --- FUNCTIONS ---
async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ref_id = context.args[0] if context.args else None

    if uid not in db:
        db[uid] = {"points": 0, "referrals": 0}
        if ref_id and int(ref_id) in db and int(ref_id) != uid:
            db[int(ref_id)]["points"] += 10
            db[int(ref_id)]["referrals"] += 1
            try:
                await context.bot.send_message(chat_id=ref_id, text="New Referral! +10 Points.")
            except: pass

    if not await is_subscribed(uid, context):
        keyboard = [[InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)],
                    [InlineKeyboardButton("I joined ✅", callback_data='verify')]]
        await update.message.reply_text(f"Welcome to SOOM! Please join our channel first:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    await show_menu(update)

async def show_menu(update: Update):
    keyboard = [['Balance', 'Invite Friends']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    msg = update.message if update.message else update.callback_query.message
    await msg.reply_text("Welcome back to SOOM Project!", reply_markup=reply_markup)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id
    user_data = db.get(uid, {"points": 0, "referrals": 0})

    if text == 'Balance':
        await update.message.reply_text(f"💎 Points: {user_data['points']}\n👥 Referrals: {user_data['referrals']}")
    elif text == 'Invite Friends':
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={uid}"
        await update.message.reply_text(f"Share your link and earn 10 points:\n{link}")

async def verify_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await is_subscribed(query.from_user.id, context):
        await show_menu(update)
    else:
        await query.message.reply_text("You haven't joined yet!")

# --- RUN BOT ---
def main():
    # Start Flask in a separate thread
    Thread(target=run_flask).start()

    # Start Telegram Bot
    application = Application.builder().token(TOKEN).build()
    application.add_handler(Command_handler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    application.add_handler(CallbackQueryHandler(verify_click, pattern='verify'))
    
    print("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
  
