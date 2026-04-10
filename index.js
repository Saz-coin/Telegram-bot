const { Telegraf, Markup } = require('telegraf');
const http = require('http');

const BOT_TOKEN = '8467862987:AAGnQyQ0nURo3Kn8-9ZtNYE8I0Y-jyeFaV8';
const CHANNEL_ID = '@Soomcoin1';
const CHANNEL_LINK = 'https://t.me/Soomcoin1';

const bot = new Telegraf(BOT_TOKEN);

// Server to keep the bot alive on Render
http.createServer((req, res) => {
  res.write("Bot is running");
  res.end();
}).listen(process.env.PORT || 8080);

// Simple Database in memory (for starting)
let db = {};

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
      try { ctx.telegram.sendMessage(ref, "New Referral! +10 points."); } catch(e){}
    }
  }

  const sub = await isSubscribed(ctx);
  if (!sub) {
    return ctx.reply(`Welcome to SOOM! Please join our channel to start:\n${CHANNEL_LINK}`, 
      Markup.inlineKeyboard([
        [Markup.button.url('Join Channel', CHANNEL_LINK)],
        [Markup.button.callback('I joined ✅', 'verify')]
      ])
    );
  }
  ctx.reply('Main Menu', Markup.keyboard([['Balance', 'Invite Friends']]).resize());
});

bot.action('verify', async (ctx) => {
  if (await isSubscribed(ctx)) {
    ctx.reply('Success! Use the buttons below:', Markup.keyboard([['Balance', 'Invite Friends']]).resize());
  } else {
    ctx.answerCbQuery('Please join the channel first!', { show_alert: true });
  }
});

bot.hears('Balance', (ctx) => {
  const u = db[ctx.from.id] || { points: 0, referrals: 0 };
  ctx.reply(`💎 Points: ${u.points}\n👥 Referrals: ${u.referrals}`);
});

bot.hears('Invite Friends', (ctx) => {
  ctx.reply(`Your link: https://t.me/${ctx.botInfo.username}?start=${ctx.from.id}`);
});

bot.launch();

// Anti-crash logic
process.on('uncaughtException', (err) => console.log(err));
process.on('unhandledRejection', (res) => console.log(res));
           
