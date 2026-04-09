import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# إعداد السجلات لمراقبة الأخطاء في Render
logging.basicConfig(level=logging.INFO)

# الإعدادات
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = '@Soomcoin1'
CHANNEL_URL = 'https://t.me/Soomcoin1'

# قاعدة بيانات بسيطة
if not os.path.exists('db.json'):
    with open('db.json', 'w') as f: json.dump({}, f)

def get_data():
    with open('db.json', 'r') as f: return json.load(f)

def save_data(data):
    with open('db.json', 'w') as f: json.dump(data, f)

# دالة البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = get_data()
    
    if user_id not in data:
        data[user_id] = {'points': 0}
        save_data(data)

    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ Verify", callback_data='v')],
        [InlineKeyboardButton("💰 Balance", callback_data='b')]
    ]
    
    await update.message.reply_text(
        "Welcome to Soom Coin! 🚀\nJoin the channel and verify to start.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# دالة الأزرار
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()

    if query.data == 'v':
        try:
            member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=int(user_id))
            if member.status in ['member', 'administrator', 'creator']:
                await query.edit_message_text("✅ Verified! Use /start to see your menu.")
            else:
                await query.answer("❌ Join first!", show_alert=True)
        except:
            await query.answer("⚠️ Bot is not Admin in channel!", show_alert=True)
            
    elif query.data == 'b':
        points = get_data().get(user_id, {}).get('points', 0)
        await query.message.reply_text(f"Your Balance: {points} Soom")

# تشغيل البوت
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.run_polling()

if __name__ == '__main__':
    main()
    
