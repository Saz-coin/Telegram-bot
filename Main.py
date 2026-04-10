const { Telegraf, Markup } = require('telegraf');
const fs = require('fs');
const http = require('http');

// --- الإعدادات الخاصة بك ---
const BOT_TOKEN = '8467862987:AAGnQyQ0nURo3Kn8-9ZtNYE8I0Y-jyeFaV8';
const CHANNEL_ID = '@Soomcoin1'; 
const CHANNEL_LINK = 'https://t.me/Soomcoin1';

const bot = new Telegraf(BOT_TOKEN);

// --- منع البوت من النوم (Render Keep-Alive) ---
// هذا السيرفر مهم جداً ليعمل البوت على Render بدون توقف
http.createServer((req, res) => {
    res.write("Soom Coin Bot is Running!");
    res.end();
}).listen(process.env.PORT || 8080);

// --- نظام حفظ البيانات (Database) ---
const DB_FILE = './users_data.json';
let db = {};
if (fs.existsSync(DB_FILE)) {
    try {
        db = JSON.parse(fs.readFileSync(DB_FILE));
    } catch (e) { db = {}; }
}

function saveDB() {
    fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2));
}

// --- نظام الحماية من الانهيار (Anti-Crash) ---
process.on('uncaughtException', (err) => console.error('خطأ تم تفاديه:', err));
process.on('unhandledRejection', (reason) => console.error('فشل تم تفاديه:', reason));

// --- وظيفة التحقق من الاشتراك الإجباري ---
async function checkSub(ctx) {
    try {
        const member = await ctx.telegram.getChatMember(CHANNEL_ID, ctx.from.id);
        return ['member', 'administrator', 'creator'].includes(member.status);
    } catch (e) { return false; }
}

// --- أمر البداية مع نظام الإحالات ---
bot.start(async (ctx) => {
    const userId = ctx.from.id;
    const refId = ctx.payload;

    if (!db[userId]) {
        db[userId] = { points: 0, referrals: 0 };
        if (refId && db[refId] && refId != userId) {
            db[refId].points += 10;
            db[refId].referrals += 1;
            saveDB();
            try { bot.telegram.sendMessage(refId, "✅ انضم شخص جديد برابطك وحصلت على 10 نقاط!"); } catch(e){}
        }
        saveDB();
    }

    const isSubbed = await checkSub(ctx);
    if (!isSubbed) {
        return ctx.reply(`⚠️ يجب عليك الاشتراك في قناة المشروع أولاً:\n${CHANNEL_LINK}`, 
            Markup.inlineKeyboard([
                [Markup.button.url('انضم للقناة', CHANNEL_LINK)],
                [Markup.button.callback('تم الاشتراك ✅', 'verify')]
            ])
        );
    }
    showMenu(ctx);
});

function showMenu(ctx) {
    ctx.replyWithMarkdown(`🚀 *مرحباً بك في مشروع SOOM*\n\nابدأ بجمع النقاط الآن!`, 
        Markup.keyboard([['💰 رصيدي', '👥 دعوة الأصدقاء'], ['📢 قناة المشروع']]).resize());
}

bot.action('verify', async (ctx) => {
    if (await checkSub(ctx)) {
        await ctx.answerCbQuery('تم التحقق! ✨');
        showMenu(ctx);
    } else {
        await ctx.answerCbQuery('❌ لم تشترك بعد!', { show_alert: true });
    }
});

bot.hears('💰 رصيدي', (ctx) => {
    const user = db[ctx.from.id] || { points: 0, referrals: 0 };
    ctx.reply(`💎 رصيدك: ${user.points} نقطة\n👥 الإحالات: ${user.referrals}`);
});

bot.hears('👥 دعوة الأصدقاء', (ctx) => {
    ctx.reply(`رابط دعوتك الخاص:\nhttps://t.me/${ctx.botInfo.username}?start=${ctx.from.id}`);
});

// تشغيل البوت
bot.launch().then(() => console.log('Soom Bot is Online!'));
