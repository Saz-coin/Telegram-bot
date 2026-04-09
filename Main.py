import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# تفعيل السجلات لمعرفة مكان الخطأ بالضبط
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# الإعدادات
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = '@Soomcoin1'
CHANNEL_URL = 'https://t.me/Soomcoin1'

# قاعدة بيانات بسيطة جداً
DB_FILE = 'db.json'
if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w') as f: json.dump({}, f)

def load_db():
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user_id = str(update.effective_user.id)
    data = load_db()
    
    if user_id not in data:
        data[user_id] = {'points': 0}
        save_db(data)

    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ Verify", callback_data='verify')],
        [InlineKeyboardButton("💰 Balance", callback_data='balance')]
    ]
    await update.message.reply_text(
        "Welcome! 🚀\nJoin our channel then click verify.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()

    if query.data == 'verify':
        try:
            member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=int(user_id))
            if member.status in ['member', 'administrator', 'creator']:
                await query.edit_message_text("✅ Verified! Use /start to see your balance.")
            else:
                await query.answer("❌ You are not in the channel!", show_alert=True)
        except Exception as e:
            logger.error(f"Error: {e}")
            await query.answer("⚠️ Bot is not Admin in channel!", show_alert=True)
            
    elif query.data == 'balance':
        pts = load_db().get(user_id, {}).get('points', 0)
        await query.message.reply_text(f"Your Balance: {pts} Soom")

def main():
    if not BOT_TOKEN:
        logger.error("No BOT_TOKEN found!")
        return
    
    # بناء البوت
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    logger.info("Starting bot...")
    application.run_polling(drop_pending_updates=True) # هذه الإضافة تمسح الأوامر القديمة المعلقة

if __name__ == '__main__':
    main()
                
