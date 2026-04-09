import json
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# إعداد السجلات (Logs) لمراقبة عمل البوت في ريندر
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- الإعدادات الأساسية ---
# يسحب التوكن من Environment Variables في ريندر للأمان
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = '@Soomcoin1' 
CHANNEL_URL = 'https://t.me/Soomcoin1'
COIN_NAME = 'Soom'
POINTS_PER_REFERRAL = 100 

DB_FILE = 'database.json'

# --- وظائف قاعدة البيانات ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading database: {e}")
            return {}
    return {}

def save_data(data):
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving database: {e}")

user_data = load_data()

# --- الأوامر البرمجية ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    
    user_id = str(update.effective_user.id)
    args = context.args
    
    # إذا كان المستخدم جديداً
    if user_id not in user_data:
        user_data[user_id] = {'points': 0, 'referred_by': None, 'credited': False}
        # نظام الإحالة
        if args and args[0].isdigit():
            referrer_id = args[0]
            if referrer_id != user_id:
                user_data[user_id]['referred_by'] = referrer_id
        save_data(user_data)

    # الأزرار الرئيسية
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ Verify Subscription", callback_data='check_sub')],
        [InlineKeyboardButton("💰 Balance", callback_data='get_balance')],
        [InlineKeyboardButton("🔗 Referral Link", callback_data='get_link')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🚀 Welcome to **{COIN_NAME}** Bot!\n\n"
        f"1. Join our channel: {CHANNEL_ID}\n"
        f"2. Click 'Verify' to activate your account.\n"
        f"3. Invite friends to earn {POINTS_PER_REFERRAL} {COIN_NAME}!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    # أزرار تبقى ظاهرة بعد التحقق
    after_verify_keyboard = [
        [InlineKeyboardButton("💰 Balance", callback_data='get_balance')],
        [InlineKeyboardButton("🔗 Referral Link", callback_data='get_link')]
    ]
    reply_markup = InlineKeyboardMarkup(after_verify_keyboard)
    
    try:
        # التحقق من وجود المستخدم في القناة
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=int(user_id))
        
        if member.status in ['member', 'administrator', 'creator']:
            # إذا كان هناك شخص دعاه ولم يحصل على مكافأته بعد
            referrer_id = user_data[user_id].get('referred_by')
            if referrer_id and not user_data[user_id].get('credited'):
                if referrer_id in user_data:
                    user_data[referrer_id]['points'] += POINTS_PER_REFERRAL
                    user_data[user_id]['credited'] = True
                    save_data(user_data)
                    # إشعار للشخص الداعي
                    try:
                        await context.bot.send_message(
                            chat_id=int(referrer_id), 
                            text=f"🎉 New Referral! You earned {POINTS_PER_REFERRAL} {COIN_NAME}."
                        )
                    except: pass

            await query.answer("✅ Verified Successfully!")
            await query.edit_message_text(
                f"Status: Verified! ✅\n\nYou are now eligible to earn **{COIN_NAME}**. Share your link with friends!",
                reply_markup=reply_markup
            )
        else:
            await query.answer("❌ You haven't joined the channel yet!", show_alert=True)
            
    except Exception as e:
        logging.error(f"Error in verification: {e}")
        await query.answer("⚠️ Admin Error: Make sure the bot is an Admin in @Soomcoin1", show_alert=True)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if query.data == 'get_balance':
        points = user_data.get(user_id, {}).get('points', 0)
        await query.answer()
        await query.message.reply_text(f"📊 Your Current Balance: **{points}** {COIN_NAME}", parse_mode='Markdown')
        
    elif query.data == 'get_link':
        bot_info = await context.bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={user_id}"
        await query.answer()
        await query.message.reply_text(
            f"🔗 **Your Referral Link:**\n`{link}`\n\nInvite 1 friend = {POINTS_PER_REFERRAL} {COIN_NAME}!",
            parse_mode='Markdown'
        )

def main():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is missing! Check Render Environment Variables.")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern='check_sub'))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    
    print("Bot is alive and running...")
    app.run_polling()

if __name__ == '__main__':
    main()
