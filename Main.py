const { Telegraf, Markup } = require('telegraf');
const fs = require('fs');
const http = require('http');

const BOT_TOKEN = '8467862987:AAGnQyQ0nURo3Kn8-9ZtNYE8I0Y-jyeFaV8';
const CHANNEL_ID = '@Soomcoin1';
const CHANNEL_LINK = 'https://t.me/Soomcoin1';

const bot = new Telegraf(BOT_TOKEN);

// Server for Render to prevent sleeping
http.createServer((req, res) => {
  res.write("Bot is Live");
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

async function isSubscribed(ctx) {
  try {
    const res = await ctx.telegram.getChatMember(CHANNEL_ID, ctx.from.id);
    return ['member', 'administrator', 'creator'].includes(res.status);
  } catch (e) { return false; }
}

bot.start(async (ctx) => {
  const uid = ctx.from.id;
  const ref = ctx.payload;

  if (!db[uid]) {
    db[uid] = { points: 0, referrals: 0 };
    if (ref && db[ref] && ref != uid) {
      db[ref].points += 10;
      db[ref].referrals += 1;
      saveDB();
    }
    saveDB();
  }

  const sub = await isSubscribed(ctx);
  if (!sub) {
    return ctx.reply(`Welcome! Please join our channel first:\n${CHANNEL_LINK}`, 
      Markup.inlineKeyboard([
        [Markup.button.url('Join Channel', CHANNEL_LINK)],
        [Markup.button.callback('I have joined ✅', 'verify')]
      ])
    );
  }
  ctx.reply('Welcome to SOOM Project!', Markup.keyboard([['Balance', 'Invite Friends']]).resize());
});

bot.action('verify', async (ctx) => {
  if (await isSubscribed(ctx)) {
    ctx.reply('Verified! Use the menu below:', Markup.keyboard([['Balance', 'Invite Friends']]).resize());
  } else {
    ctx.answerCbQuery('Join the channel first!', { show_alert: true });
  }
});

bot.hears('Balance', (ctx) => {
  const u = db[ctx.from.id] || { points: 0, referrals: 0 };
  ctx.reply(`💎 Balance: ${u.points} points\n👥 Referrals: ${u.referrals}`);
});

bot.hears('Invite Friends', (ctx) => {
  ctx.reply(`Invite link:\nhttps://t.me/${ctx.botInfo.username}?start=${ctx.from.id}`);
});

bot.launch();
