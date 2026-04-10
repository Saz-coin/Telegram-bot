import os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# --- الإعدادات ---
TOKEN = "8467862987:AAGnQyQ0nURo3Kn8-9ZtNYE8I0Y-jyeFaV8"
CHANNEL_ID = "@Soomcoin1" # تأكد أن البوت "أدمن" في هذه القناة
CHANNEL_LINK = "https://t.me/Soomcoin1"

# --- سيرفر لمنع توقف Render ---
app = Flask('')
@app.route('/')
def home(): return "Soom Bot is Active"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# --- قاعدة بيانات مؤقتة في الذاكرة ---
db = {}

# --- وظيفة فحص الاشتراك ---
async def is_sub(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        # التحقق إذا كان العضو مشتركاً أو مديراً أو صاحب القناة
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- أمر البداية /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    args = context.args
    
    # تعريف المستخدم الجديد في النظام
    if uid not in db:
        db[uid] = {"p": 0, "r": 0, "s": False}
        # نظام الإحالة (100 نقطة للدعوة)
        if args and args[0].isdigit():
            ref_id = int(args[0])
            if ref_id in db and ref_id != uid:
                db[ref_id]["p"] += 100
                db[ref_id]["r"] += 1
                try: await context.bot.send_message(chat_id=ref_id, text="🎊 New Referral! You earned +100 Points.")
                except: pass

    # التحقق من الاشتراك لإظهار زر التأكيد
    if not await is_sub(uid, context):
        keyboard = [
            [InlineKeyboardButton("📢 Step 1: Join Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ Step 2: Verify & Claim 50 Pts", callback_data='verify_sub')]
        ]
        await update.message.reply_text(
            "🚀 *Welcome to SOOM Project*\n\nYou must join our official channel to start earning points.\n\n1️⃣ Join the channel using the button below.\n2️⃣ Press 'Verify' to claim your **50 Points**!",
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='Markdown'
        )
    else:
        # إذا كان مشتركاً بالفعل تظهر له القائمة الرئيسية
        await show_menu(update)

# --- عرض القائمة الرئيسية ---
async def show_menu(update):
    kb = [['💰 Balance', '👥 Invite'], ['📢 Official Channel']]
    markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    text = "💎 *SOOM Dashboard*\n\nYour account is verified. Start collecting points now!"
    
    if update.message:
        await update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')
    else:
        # في حال كان النداء من زر التأكيد (Callback)
        await update.callback_query.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')

# --- التعامل مع كبسة "تأكيد الاشتراك" ---
async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()
    
    if await is_sub(uid, context):
        # منح مكافأة الاشتراك مرة واحدة فقط
        if not db[uid].get("s", False):
            db[uid]["p"] += 50
            db[uid]["s"] = True
            await query.message.reply_text("🎉 Verified! You received **50 Points** welcome bonus.")
        
        # حذف رسالة الاشتراك والانتقال للقائمة
        await query.message.delete()
        await show_menu(update)
    else:
        # رسالة تنبيه إذا لم يشترك بعد
        await query.message.reply_text("⚠️ You haven't joined the channel yet! Please join @Soomcoin1 and try again.")

# --- التعامل مع أزرار القائمة (نصوص) ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id
    data = db.get(uid, {"p": 0, "r": 0})

    if text == '💰 Balance':
        await update.message.reply_text(f"💎 *Your Balance:* {data['p']} Points\n👥 *Referrals:* {data['r']}", parse_mode='Markdown')
    elif text == '👥 Invite':
        bot_info = await context.bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={uid}"
        await update.message.reply_text(f"🎁 *Invite & Earn 100 Pts:*\n\nShare this link with your friends:\n`{link}`", parse_mode='Markdown')
    elif text == '📢 Official Channel':
        await update.message.reply_text(f"🔗 Our Official Channel:\n{CHANNEL_LINK}")

# --- إعداد زر Start الجانبي ---
async def post_init(application: Application):
    await application.bot.set_my_commands([BotCommand("start", "♻️ Restart / Refresh Bot")])

# --- التشغيل الرئيسي ---
if __name__ == '__main__':
    # تشغيل سيرفر Flask في Thread منفصل
    Thread(target=run).start()
    
    # بناء تطبيق البوت
    application = Application.builder().token(TOKEN).post_init(post_init).build()
    
    # إضافة الأوامر والمعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(verify_callback, pattern='verify_sub'))
    
    print("Bot is Starting...")
    # drop_pending_updates=True يحل مشكلة التضارب (Conflict) فوراً
    application.run_polling(drop_pending_updates=True)
