import os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# --- الإعدادات ---
TOKEN = "8467862987:AAGnQyQ0nURo3Kn8-9ZtNYE8I0Y-jyeFaV8"
CHANNEL_ID = "@Soomcoin1"
CHANNEL_LINK = "https://t.me/Soomcoin1"

# --- سيرفر Render لمنع التوقف ---
app = Flask('')
@app.route('/')
def home(): return "Soom Bot is Active"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# --- قاعدة بيانات مؤقتة ---
db = {}

async def is_sub(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    args = context.args
    if uid not in db:
        db[uid] = {"p": 0, "r": 0, "s": False, "name": update.effective_user.first_name}
        if args and args[0].isdigit():
            ref_id = int(args[0])
            if ref_id in db and ref_id != uid:
                db[ref_id]["p"] += 100
                db[ref_id]["r"] += 1

    bot_info = await context.bot.get_me()
    invite_link = f"https://t.me/{bot_info.username}?start={uid}"
    keyboard = [
        [InlineKeyboardButton("📢 1. Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ 2. Verify & Claim 50 Pts", callback_data='verify_now')],
        [InlineKeyboardButton("👥 My Invite Link", callback_data='show_invite')]
    ]
    await update.message.reply_text(
        f"🚀 *Welcome to SOOM Project*\n\n1️⃣ Join channel for **50 Pts**.\n2️⃣ Invite for **100 Pts**!\n\n🔗 *Your Link:* `{invite_link}`",
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
    )

async def show_menu(update):
    kb = [['💰 Balance', '👥 Invite'], ['📢 Official Channel']]
    markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    text = "💎 *SOOM Dashboard*\nYour account is active!"
    if update.message: await update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')
    else: await update.callback_query.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id
    
    # --- الكلمة السرية للإدارة ---
    if text == 'adminnh':
        if not db:
            await update.message.reply_text("لا يوجد مستخدمين بعد.")
            return
        report = "📊 *قائمة النقاط السرية:*\n\n"
        for user_id, data in db.items():
            report += f"👤 {data.get('name', 'Unknown')} | ID: `{user_id}`\n💎 Pts: {data['p']} | 👥 Ref: {data['r']}\n"
            report += "-------------------\n"
        await update.message.reply_text(report, parse_mode='Markdown')
        return

    # باقي الأزرار العادية
    data = db.get(uid, {"p": 0, "r": 0})
    if text == '💰 Balance':
        await update.message.reply_text(f"💎 Balance: {data['p']} Pts")
    elif text == '👥 Invite':
        bot = await context.bot.get_me()
        await update.message.reply_text(f"🎁 Earn 100 Pts:\n`https://t.me/{bot.username}?start={uid}`", parse_mode='Markdown')
    elif text == '📢 Official Channel':
        await update.message.reply_text(f"Join: {CHANNEL_LINK}")

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()
    if query.data == 'verify_now':
        if await is_sub(uid, context):
            if not db[uid].get("s", False):
                db[uid]["p"] += 50
                db[uid]["s"] = True
                await query.message.reply_text("🎉 Verified! +50 Points added.")
            await query.message.delete()
            await show_menu(update)
        else: await query.message.reply_text("❌ Join @Soomcoin1 first!")
    elif query.data == 'show_invite':
        bot = await context.bot.get_me()
        await query.message.reply_text(f"🎁 *Link:* `https://t.me/{bot.username}?start={uid}`", parse_mode='Markdown')

async def post_init(app: Application):
    await app.bot.set_my_commands([BotCommand("start", "Restart Bot")])

if __name__ == '__main__':
    Thread(target=run).start()
    application = Application.builder().token(TOKEN).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(verify_callback))
    application.run_polling(drop_pending_updates=True)
