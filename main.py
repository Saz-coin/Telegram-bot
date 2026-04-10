import os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# --- الإعدادات ---
TOKEN = "8467862987:AAGnQyQ0nURo3Kn8-9ZtNYE8I0Y-jyeFaV8"
CHANNEL_ID = "@Soomcoin1"
CHANNEL_LINK = "https://t.me/Soomcoin1"

# --- سيرفر لمنع التوقف (Flask) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# --- قاعدة بيانات مؤقتة ---
db = {}

# --- الوظائف الأساسية ---
async def is_sub(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ref_id = context.args[0] if context.args else None

    if uid not in db:
        db[uid] = {"p": 0, "r": 0}
        if ref_id and int(ref_id) in db and int(ref_id) != uid:
            db[int(ref_id)]["p"] += 10
            db[int(ref_id)]["r"] += 1

    if not await is_sub(uid, context):
        btn = [[InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)],
               [InlineKeyboardButton("Verify ✅", callback_data='check')]]
        await update.message.reply_text("Join our channel to use the bot:", reply_markup=InlineKeyboardMarkup(btn))
    else:
        await show_menu(update)

async def show_menu(update):
    kb = [['Balance', 'Invite']]
    markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    msg = update.message if update.message else update.callback_query.message
    await msg.reply_text("Welcome to SOOM Project!", reply_markup=markup)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id
    data = db.get(uid, {"p": 0, "r": 0})

    if text == 'Balance':
        await update.message.reply_text(f"💎 Points: {data['p']}\n👥 Referrals: {data['r']}")
    elif text == 'Invite':
        bot_info = await context.bot.get_me()
        await update.message.reply_text(f"Your Link: https://t.me/{bot_info.username}?start={uid}")

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await is_sub(query.from_user.id, context):
        await show_menu(update)
    else:
        await query.message.reply_text("Please join first!")

# --- التشغيل ---
if __name__ == '__main__':
    Thread(target=run).start()
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app_tg.add_handler(CallbackQueryHandler(verify, pattern='check'))
    app_tg.run_polling()
                                     
