import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. إعداد السجلات (Logs) لمراقبة الأخطاء في Render
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. كود السيرفر الوهمي (لحل مشكلة إغلاق ريندر للبوت)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Soom Bot is Alive!")

def run_health_server():
    # ريندر يعطي بورت تلقائي، إذا لم يجده نستخدم 8080
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Health check server started on port {port}")
    server.serve_forever()

# 3. إعدادات البوت والقناة
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = '@Soomcoin1'
CHANNEL_URL = 'https://t.me/Soomcoin1'
COIN_NAME = 'Soom'
POINTS_PER_REFERRAL = 100
DB_FILE = 'db.json'

# 4. وظائف قاعدة البيانات (تخزين النقاط)
if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w') as f: json.dump({}, f)

def load_db():
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# 5. دوال البوت الأساسية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user_id = str(update.effective_user.id)
    data = load_db()
    
    if user_id not in data:
        data[user_id] = {'points': 0, 'referred_by': None, 'credited': False}
        if context.args and context.args[0].isdigit():
            ref = context.args[0]
            if ref != user_id: data[user_id]['referred_by'] = ref
        save_db(data)

    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ Verify Subscription", callback_data='v')],
        [InlineKeyboardButton("💰 Balance", callback_data='b')],
        [InlineKeyboardButton("🔗 Referral Link", callback_data='l')]
    ]
    await update.message.reply_text(
        f"🚀 Welcome to **{COIN_NAME}**!\n\nJoin the channel then click verify to activate your account.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = load_db()
    await query.answer()

    if query.data == 'v':
        try:
            member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=int(user_id))
            if member.status in ['member', 'administrator', 'creator']:
                # التحقق من الإحالة
                ref_id = data.get(user_id, {}).get('referred_by')
                if ref_id and not data[user_id].get('credited'):
                    if ref_id in data:
                        data[ref_id]['points'] += POINTS_PER_REFERRAL
                        data[user_id]['credited'] = True
                        save_db(data)
                        try: await context.bot.send_message(chat_id=int(ref_id), text=f"🎉 Someone joined! +{POINTS_PER_REFERRAL} {COIN_NAME}")
                        except: pass
                
                await query.edit_message_text("✅ Verified Successfully! Use the buttons below.")
            else:
                await query.answer("❌ You must join the channel first!", show_alert=True)
        except Exception as e:
            logger.error(f"Verification Error: {e}")
            await query.answer("⚠️ Bot is not Admin in the channel!", show_alert=True)
            
    elif query.data == 'b':
        pts = data.get(user_id, {}).get('points', 0)
        await query.message.reply_text(f"📊 Your Balance: **{pts}** {COIN_NAME}", parse_mode='Markdown')
        
    elif query.data == 'l':
        bot_info = await context.bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={user_id}"
        await query.message.reply_text(f"🔗 Your Link:\n`{link}`", parse_mode='Markdown')

# 6. تشغيل البوت والسيرفر
def main():
    if not BOT_TOKEN:
        print("CRITICAL: BOT_TOKEN is missing!")
        return

    # تشغيل السيرفر الوهمي في خيط (Thread) منفصل
    Thread(target=run_health_server, daemon=True).start()
    
    # بناء البوت ومسح أي أوامر قديمة معلقة
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    
    print("Bot is starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
