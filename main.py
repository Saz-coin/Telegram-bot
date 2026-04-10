import os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# --- الإعدادات ---
TOKEN = "8467862987:AAGnQyQ0nURo3Kn8-9ZtNYE8I0Y-jyeFaV8"
CHANNEL_ID = "@Soomcoin1"
CHANNEL_LINK = "https://t.me/Soomcoin1"

# --- Keep-Alive Server ---
app = Flask('')
@app.route('/')
def home(): return "Soom Bot is Active"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# --- قاعدة البيانات المؤقتة ---
db = {}

# --- الوظائف المنطقية ---
async def is_sub(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    args = context.args
    
    # تعريف المستخدم الجديد
    if uid not in db:
        # p = points, r = referrals, s = subscription_bonus_claimed
        db[uid] = {"p": 0, "r": 0, "s": False}
        
        # نظام الإحالة (100 نقطة للمُحيل)
        if args and args[0].isdigit():
            ref_id = int(args[0])
            if ref_id in db and ref_id != uid:
                db[ref_id]["p"] += 100
                db[ref_id]["r"] += 1
                try: 
                    await context.bot.send_message(
                        chat_id=ref_id, 
                        text=f"🎊 New referral joined! You earned +100 Points."
                    )
                except: pass

    if not await is_sub(uid, context):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ Verify & Claim 50 Points", callback_data='check')]
        ]
        await update.message.reply_text(
            "🚀 *Welcome to SOOM Project*\n\nTo start earning, please join our official channel and verify your subscription to get your first **50 Points**!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await show_menu(update)

async def show_menu(update):
    kb = [['💰 My Balance', '👥 Invite Friends'], ['📢 Official Channel']]
    markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    text = "💎 *SOOM Dashboard*\n\nKeep collecting points to qualify for the Airdrop!"
    
    if update.message:
        await update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')
    else:
        await update.callback_query.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id
    data = db.get(uid, {"p": 0, "r": 0})

    if text == '💰 My Balance':
        await update.message.reply_text(f"📊 *Your Stats*\n\n💎 Points: {data['p']}\n👥 Referrals: {data['r']}", parse_mode='Markdown')
    
    elif text == '👥 Invite Friends':
        bot_info = await context.bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={uid}"
        await update.message.reply_text(
            f"🎁 *Invite & Earn*\n\nShare your link and get **100 Points** for every friend you invite!\n\n🔗 `{link}`",
            parse_mode='Markdown'
        )
    
    elif text == '📢 Official Channel':
        await update.message.reply_text(f"🔗 Join our community: {CHANNEL_LINK}")

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()
    
    if await is_sub(uid, context):
        # منح مكافأة الاشتراك (50 نقطة) لمرة واحدة فقط
        if not db[uid].get("s", False):
            db[uid]["p"] += 50
            db[uid]["s"] = True
            await query.message.reply_text("✅ Verified! You've received **50 Points** as a welcome bonus.", parse_mode='Markdown')
        
        await query.message.delete()
        await show_menu(update)
    else:
        await query.message.reply_text("❌ Please join @Soomcoin1 first to claim your points!")

# --- Execution ---
if __name__ == '__main__':
    Thread(target=run).start()
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(verify_callback, pattern='check'))
    
    # حل مشكلة الـ Conflict
    application.run_polling(drop_pending_updates=True)
    
