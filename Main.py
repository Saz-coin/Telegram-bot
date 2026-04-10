const { Telegraf, Markup } = require('telegraf');
const fs = require('fs');
const http = require('http');

const BOT_TOKEN = '8467862987:AAGnQyQ0nURo3Kn8-9ZtNYE8I0Y-jyeFaV8';
const CHANNEL_ID = '@Soomcoin1';
const CHANNEL_LINK = 'https://t.me/Soomcoin1';

const bot = new Telegraf(BOT_TOKEN);

http.createServer((req, res) => {
    res.write("Bot is running");
    res.end();
}).listen(process.env.PORT || 8080);

const DB_FILE = './users.json';
let db = {};
if (fs.existsSync(DB_FILE)) {
    try { db = JSON.parse(fs.readFileSync(DB_FILE)); } catch (e) { db = {}; }
}

function saveDB() {
    fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2));
}

async function checkSub(ctx) {
    try {
        const member = await ctx.telegram.getChatMember(CHANNEL_ID, ctx.from.id);
        return ['member', 'administrator', 'creator'].includes(member.status);
    } catch (e) { return false; }
}

bot.start(async (ctx) => {
    const userId = ctx.from.id;
    const refId = ctx.payload;
    if (!db[userId]) {
        db[userId] = { points: 0, referrals: 0 };
        if (refId && db[refId] && refId != userId) {
            db[refId].points += 10;
            db[refId].referrals += 1;
            saveDB();
        }
        saveDB();
    }
    const isSub = await checkSub(ctx);
    if (!isSub) {
        return ctx.reply(`Welcome! Join: ${CHANNEL_LINK}`, Markup.inlineKeyboard([
            [Markup.button.url('Join', CHANNEL_LINK)],
            [Markup.button.callback('Verified ✅', 'check')]
        ]));
    }
    ctx.reply('Main Menu', Markup.keyboard([['Balance', 'Invite']]).resize());
});

bot.action('check', async (ctx) => {
    if (await checkSub(ctx)) { showMenu(ctx); } 
    else { ctx.answerCbQuery('Not joined!', { show_alert: true }); }
});

bot.hears('Balance', (ctx) => {
    const u = db[ctx.from.id] || { points: 0 };
    ctx.reply(`Points: ${u.points}`);
});

bot.hears('Invite', (ctx) => {
    ctx.reply(`Link: https://t.me/${ctx.botInfo.username}?start=${ctx.from.id}`);
});

bot.launch();
