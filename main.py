import os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# --- Settings ---
TOKEN = "8467862987:AAGnQyQ0nURo3Kn8-9ZtNYE8I0Y-jyeFaV8"
CHANNEL_ID = "@Soomcoin1"
CHANNEL_LINK = "https://t.me/Soomcoin1"

# --- Keep-Alive Server ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# --- Temporary DB ---
db = {}

# --- Logic ---
async def is_sub(user_id, context):
    try:
        # هذه الوظيفة تتطلب أن يكون البوت Admin في القناة
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Error checking sub: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    args = context.args
    
    if uid not in db:
        db[uid] = {"p": 0, "r": 0}
        if args and args[0].isdigit():
            ref_id = int(args[0])
            if ref_id in db and ref_id != uid:
                db[ref_id]["p"] += 10
                db[ref_id]["r"] += 1
                try: await context.bot.send_message(chat_id=ref_id, text="🎁 Someone joined via your link! +10 Points.")
                except: pass

    # فحص الاشتراك فوراً عند الضغط على Start
    if not await is_sub(uid, context):
        # هنا تم تعديل الكود لتظهر الكبسة بشكل صحيح
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel (اضغط هنا)", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ I have Joined (تم الاشتراك)", callback_data='check')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ Access Denied!\n\nYou must join our official channel to use the bot and earn points.",
            reply_markup=reply_markup
        )
    else:
        await show_menu(update)

async def show_menu(update):
    kb = [['💰 Balance', '👥 Invite'], ['📢 Official Channel']]
    markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    
    # تحديد مكان الرسالة سواء كانت ضغطة زر أو أمر start
    if update.message:
        await update.message.reply_text("🚀 Main Menu - Start earning SOOM!", reply_markup=markup)
    else:
        await update.callback_query.message.reply_text("🚀 Welcome! Menu unlocked:", reply_markup=markup)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id
    data = db.get(uid, {"p": 0, "r": 0})

    if text == '💰 Balance':
        await update.message.reply_text(f"💎 Balance: {data['p']} Points\n👥 Referrals: {data['r']}")
    elif text == '👥 Invite':
        bot_info = await context.bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={uid}"
        await update.message.reply_text(f"Share this link:\n{link}")
    elif text == '📢 Official Channel':
        await update.message.reply_text(f"Join here: {CHANNEL_LINK}")

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if await is_sub(query.from_user.id, context):
        await query.message.delete() # حذف رسالة الاشتراك بعد النجاح
        await show_menu(update)
    else:
        await query.message.reply_text("❌ Not joined yet! Please join @Soomcoin1 first.")

# --- Start ---
if __name__ == '__main__':
    Thread(target=run).start()
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(verify_callback, pattern='check'))
    
    application.run_polling()
