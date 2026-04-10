const { Telegraf, Markup } = require('telegraf');
const fs = require('fs');
const http = require('http');

// --- Settings ---
const BOT_TOKEN = '8467862987:AAGnQyQ0nURo3Kn8-9ZtNYE8I0Y-jyeFaV8';
const CHANNEL_ID = '@Soomcoin1'; 
const CHANNEL_LINK = 'https://t.me/Soomcoin1';

const bot = new Telegraf(BOT_TOKEN);

// --- Render Keep-Alive Server ---
http.createServer((req, res) => {
    res.write("Soom Coin Bot is Running!");
    res.end();
}).listen(process.env.PORT || 8080);

// --- Database Logic ---
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

// --- Anti-Crash Logic ---
process.on('uncaughtException', (err) => console.error('Error caught:', err));
process.on('unhandledRejection', (reason) => console.error('Rejection caught:', reason));

// --- Subscription Check ---
async function checkSub(ctx) {
    try {
        const member = await ctx.telegram.getChatMember(CHANNEL_ID, ctx.from.id);
        return ['member', 'administrator', 'creator'].includes(member.status);
    } catch (e) { return false; }
}

// --- Commands ---
bot.start(async (ctx) => {
    const userId = ctx.from.id;
    const refId = ctx.payload;

    if (!db[userId]) {
        db[userId] = { points: 0, referrals: 0 };
        if (refId && db[refId] && refId != userId) {
            db[refId].points += 10;
            db[refId].referrals += 1;
            saveDB();
            try { bot.telegram.sendMessage(refId, "New referral joined! +10 points."); } catch(e){}
        }
        saveDB();
    }

    const isSubbed = await checkSub(ctx);
    if (!isSubbed) {
        return ctx.reply(`Welcome to SOOM Project. Please join our channel to start: \n${CHANNEL_LINK}`, 
            Markup.inlineKeyboard([
                [Markup.button.url('Join Channel', CHANNEL_LINK)],
                [Markup.button.callback('I joined ✅', 'verify')]
            ])
        );
    }
    showMenu(ctx);
});

function showMenu(ctx) {
    ctx.reply("Welcome to SOOM! Start collecting points now.", 
        Markup.keyboard([['My Balance', 'Invite Friends'], ['Our Channel']]).resize());
}

bot.action('verify', async (ctx) => {
    if (await checkSub(ctx)) {
        await ctx.answerCbQuery('Verified! ✨');
        showMenu(ctx);
    } else {
        await ctx.answerCbQuery('Not subscribed yet!', { show_alert: true });
    }
});

bot.hears('My Balance', (ctx) => {
    const user = db[ctx.from.id] || { points: 0, referrals: 0 };
    ctx.reply(`Balance: ${user.points} points\nReferrals: ${user.referrals}`);
});

bot.hears('Invite Friends', (ctx) => {
    ctx.reply(`Your invite link:\nhttps://t.me/${ctx.botInfo.username}?start=${ctx.from.id}`);
});

bot.launch().then(() => console.log('Bot is Online!'));
