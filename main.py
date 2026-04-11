import os
import json
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# --- الإعدادات الأساسية ---
TOKEN = "8467862987:AAGnQyQ0nURo3Kn8-9ZtNYE8I0Y-jyeFaV8"
CHANNEL_ID = "@Soomcoin1"
CHANNEL_LINK = "https://t.me/Soomcoin1"
DB_FILE = "database.json"

# --- سيرفر ويب لمنع توقف الخدمة على Render ---
app = Flask('')
@app.route('/')
def home(): return "Soom Bot is Online"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# --- نظام إدارة قاعدة البيانات (JSON) ---
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

def save_db(data):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# تحميل البيانات عند بدء التشغيل
db = load_db()

# --- التحقق من الاشتراك في القناة ---
async def is_sub(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Error checking sub: {e}")
        return False

# --- معالج أمر البداية /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    args = context.args
    user_name = update.effective_user.first_name
    
    # تسجيل المستخدم إذا كان جديداً
    if uid not in db:
        db[uid] = {"p": 0, "r": 0, "s": False, "name": user_name}
        # نظام الإحالة (100 نقطة)
        if args and args[0].isdigit():
            ref_id = str(args[0])
            if ref_id in db and ref_id != uid:
                db[ref_id]["p"] += 100
                db[ref_id]["r"] += 1
                try:
                    await context.bot.send_message(
                        chat_id=int(ref_id), 
                        text=f"🎁 حصلت على +100 نقطة! انضم صديق جديد عبر رابطك."
                    )
                except: pass
        save_db(db)

    bot_info = await context.bot.get_me()
    invite_link = f"https://t.me/{bot_info.username}?start={uid}"
    
    # أزرار الاشتراك والدعوة
    keyboard = [
        [InlineKeyboardButton("📢 1. Join Channel (اشترك هنا)", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ 2. Verify & Claim 50 Pts (تأكيد)", callback_data='verify_now')],
        [InlineKeyboardButton("👥 My Invite Link (رابط الدعوة)", callback_data='show_invite')]
    ]
    
    await update.message.reply_text(
        f"🚀 *Welcome to SOOM Project*\n\n"
        f"1️⃣ اشترك في القناة لتربح **50 نقطة**.\n"
        f"2️⃣ شارك رابطك لتربح **100 نقطة** عن كل صديق!\n\n"
        f"🔗 *رابطك الخاص:* `{invite_link}`",
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )

# --- عرض القائمة الرئيسية بعد التأكيد ---
async def show_menu(update):
    kb = [['💰 Balance', '👥 Invite'], ['📢 Official Channel']]
    markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    text = "💎 *SOOM Dashboard*\n\nتم تفعيل حسابك بنجاح! استمر في جمع النقاط."
    
    if update.message:
        await update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')
    else:
        await update.callback_query.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')

# --- معالج النصوص والكلمة السرية ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = str(update.effective_user.id)
    
    # الكلمة السرية للإدارة
    if text == 'adminnh':
        if not db:
            await update.message.reply_text("⚠️ القائمة فارغة حالياً.")
            return
        
        report = "📊 *قائمة النقاط (الإدارة):*\n"
        for user_id, data in db.items():
            report += f"\n👤 {data.get('name', 'Unknown')}\nID: `{user_id}`\n💎 Pts: {data['p']} | 👥 Ref: {data['r']}\n"
            report += "---"
        await update.message.reply_text(report, parse_mode='Markdown')
        return

    # الأزرار العادية
    data = db.get(uid, {"p": 0, "r": 0})
    if text == '💰 Balance':
        await update.message.reply_text(f"📊 *إحصائياتك:*\n\n💎 النقاط: {data['p']}\n👥 الإحالات: {data['r']}", parse_mode='Markdown')
    elif text == '👥 Invite':
        bot = await context.bot.get_me()
        link = f"https://t.me/{bot.username}?start={uid}"
        await update.message.reply_text(f"🎁 *اربح 100 نقطة عن كل دعوة:*\n\n🔗 `{link}`", parse_mode='Markdown')
    elif text == '📢 Official Channel':
        await update.message.reply_text(f"🔗 رابط القناة الرسمية: {CHANNEL_LINK}")

# --- معالج الضغط على الأزرار الشفافة ---
async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    await query.answer()
    
    if query.data == 'verify_now':
        if await is_sub(int(uid), context):
            if not db[uid].get("s", False):
                db[uid]["p"] += 50
                db[uid]["s"] = True
                save_db(db)
                await query.message.reply_text("✅ تم التأكيد! حصلت على **50 نقطة** مكافأة الاشتراك.")
            
            await query.message.delete()
            await show_menu(update)
        else:
            await query.message.reply_text("❌ لم تشترك بعد! يرجى الانضمام للقناة @Soomcoin1 أولاً.")
            
    elif query.data == 'show_invite':
        bot = await context.bot.get_me()
        link = f"https://t.me/{bot.username}?start={uid}"
        await query.message.reply_text(f"🎁 *رابط الدعوة الخاص بك:* \n`{link}`", parse_mode='Markdown')

# --- إعداد زر القائمة الجانبية ---
async def post_init(app: Application):
    await app.bot.set_my_commands([BotCommand("start", "♻️ إعادة تشغيل البوت")])

# --- التشغيل الرئيسي ---
if __name__ == '__main__':
    # تشغيل سيرفر Flask
    Thread(target=run).start()
    
    # إعداد تطبيق البوت
    application = Application.builder().token(TOKEN).post_init(post_init).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(verify_callback))
    
    print("Bot is Starting...")
    # مسح التحديثات المعلقة لحل مشكلة التضارب (Conflict)
    application.run_polling(drop_pending_updates=True)
              
