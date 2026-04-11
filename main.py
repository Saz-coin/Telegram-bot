import os
from flask import Flask
from threading import Thread
from supabase import create_client, Client
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# --- الإعدادات الخاصة بك ---
TOKEN = "8467862987:AAGnQyQ0nURo3Kn8-9ZtNYE8I0Y-jyeFaV8"
SUPABASE_URL = "https://bbqbgoyxtblelvxcmfyp.supabase.co"
SUPABASE_KEY = "EyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJicWJnb3l4dGJsZWx2eGNtZnlwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU4NTEyNTEsImV4cCI6MjA5MTQyNzI1MX0.t727rSWSifnRe_M89MipEj7Q3nXJEhO-WWIVIsu4oTs"
CHANNEL_ID = "@Soomcoin1"
CHANNEL_LINK = "https://t.me/Soomcoin1"

# --- الربط بـ Supabase ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- سيرفر Render لمنع التوقف ---
app = Flask('')
@app.route('/')
def home(): return "Soom Bot is Live on Supabase"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

async def is_sub(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name
    args = context.args
    
    # التحقق من وجود المستخدم
    res = supabase.table("users").select("*").eq("id", uid).execute()
    
    if not res.data:
        # تسجيل جديد في الجدول
        supabase.table("users").insert({"id": uid, "name": name, "points": 0, "referrals": 0, "is_verified": False}).execute()
        
        # نظام الإحالة (زيادة نقاط الداعي)
        if args and args[0].isdigit():
            ref_id = int(args[0])
            if ref_id != uid:
                # نستخدم RPC لزيادة النقاط بشكل آمن
                supabase.rpc('increment_points', {'row_id': ref_id, 'p_inc': 100, 'r_inc': 1}).execute()
                try: await context.bot.send_message(chat_id=ref_id, text="🎁 حصلت على +100 نقطة لدعوة صديق جديد!")
                except: pass

    bot_info = await context.bot.get_me()
    invite_link = f"https://t.me/{bot_info.username}?start={uid}"
    
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Verify & Claim 50 Pts", callback_data='v')],
        [InlineKeyboardButton("👥 My Invite Link", callback_data='l')]
    ]
    
    await update.message.reply_text(
        f"🚀 *Welcome to SOOM Project*\n\n"
        f"1️⃣ Join channel for **50 Pts**.\n"
        f"2️⃣ Invite friends for **100 Pts**.\n\n"
        f"🔗 *Your Link:* `{invite_link}`",
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id
    
    # كلمة السر لرؤية كل المستخدمين ونقاطهم من تلجرام
    if text == 'adminnh':
        res = supabase.table("users").select("*").execute()
        report = "📊 *قائمة مستخدمي SOOM:*\n"
        for u in res.data:
            report += f"👤 {u['name']} | Pts: {u['points']}\n"
        await update.message.reply_text(report, parse_mode='Markdown')
        return

    if text == '💰 Balance':
        res = supabase.table("users").select("points").eq("id", uid).single().execute()
        await update.message.reply_text(f"💎 *Your Balance:* {res.data['points']} Pts", parse_mode='Markdown')

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()
    
    if query.data == 'v':
        if await is_sub(uid, context):
            res = supabase.table("users").select("is_verified", "points").eq("id", uid).single().execute()
            if not res.data['is_verified']:
                # تحديث النقاط وحالة التحقق
                new_pts = res.data['points'] + 50
                supabase.table("users").update({"is_verified": True, "points": new_pts}).eq("id", uid).execute()
                await query.message.reply_text("🎉 Verified! +50 Points added.")
            
            await query.message.delete()
            kb = [['💰 Balance', '👥 Invite']]
            await query.message.reply_text("💎 *Main Menu Active*", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode='Markdown')
        else:
            await query.message.reply_text("❌ Please join @Soomcoin1 first!")
            
    elif query.data == 'l':
        bot = await context.bot.get_me()
        await query.message.reply_text(f"🎁 *Invite Link:* \n`https://t.me/{bot.username}?start={uid}`", parse_mode='Markdown')

if __name__ == '__main__':
    Thread(target=run).start()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(verify_callback))
    application.run_polling(drop_pending_updates=True)
    
