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
POINTS_PER_
