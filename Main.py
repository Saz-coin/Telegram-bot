import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- الإعدادات ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = '@Soomcoin1' 
CHANNEL_URL = 'https://t.me/Soomcoin1'
COIN_NAME = 'Soom'
POINTS_PER_REFERRAL = 100 

DB_FILE = 'database.json'

# --- إدارة البيانات ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except: return {}
    return {}

def save_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

user_data = load_data()

# --- الأوامر ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    
    if user_id not in user_data:
        user_data[user_id] = {'points': 0, 'referred_by': None, 'credited': False}
        if args and args[0].isdigit():
            referrer_id = args[0]
            if referrer_id != user_id:
                user_data[user_id]['referred_by'] = referrer_id
        save_data(user_data)

    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ Verify Subscription", callback_data='check_sub')],
        [InlineKeyboardButton("💰 Balance", callback_data='get_balance')],
        [InlineKeyboardButton("🔗 Referral Link", callback_data='get_link')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🚀 Welcome to **{COIN_NAME}** Bot!\n\n"
        f"Please join our channel first, then click verify to start earning {COIN_NAME}.",
        reply_markup=reply_markup
    )

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=int(user_id))
        if member.status in ['member', 'administrator', 'creator']:
            referrer_id = user_data[user_id].get('referred_by')
            if referrer_id and not user_data[user_id].get('credited'):
                if referrer_id in user_data:
                    user_data[referrer_id]['points'] += POINTS_PER_REFERRAL
                    user_data[user_id]['credited'] = True
                    save_data(user_data)
                    try:
                        await context.bot.send_message(chat_id=int(referrer_id), text=f"🎉 Success! +{POINTS_PER_REFERRAL} {COIN_NAME}")
                    except: pass

            await query.answer("✅ Verified!")
            await query.edit_message_text(f"Status: Verified! ✅\nShare your link to earn more **{COIN_NAME}**.")
        else:
            await query.answer("❌ Join the channel first!", show_alert=True)
    except:
        await query.answer("⚠️ Admin error! Make sure the bot is Admin in the channel.", show_alert=True)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if query.data == 'get_balance':
        points = user_data.get(user_id, {}).get('points', 0)
        await query.answer()
        await query.message.reply_text(f"📊 Your Balance: **{points}** {COIN_NAME}")
        
    elif query.data == 'get_link':
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={user_id}"
        await query.answer()
        await query.message.reply_text(f"🔗 Your Link: {link}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern='check_sub'))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == '__main__':
    main()
    
