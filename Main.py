import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- الإعدادات النهائية ---
# سيقوم الكود بسحب التوكن من إعدادات ريندر (Environment Variables)
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = '@Soomcoin1' 
CHANNEL_URL = 'https://t.me/Soomcoin1'
COIN_NAME = 'Soom'
POINTS_PER_REFERRAL = 100 

DB_FILE = 'database.json'

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
    
