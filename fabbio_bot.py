import logging
import os
import json
import random
from datetime import datetime
import redis
from aiohttp import web
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# 🔐 Config
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REDIS_URL = os.environ.get("REDIS_URL")
DOMAIN = os.environ.get("DOMAIN")  # Es: https://fabbio-bot-production.up.railway.app
PORT = int(os.environ.get("PORT", 8000))
WEBHOOK_PATH = "/webhook"

# 🔄 Variabili globali
app = None
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
ALIASES = ["fabbio", "fabbiotron", "fabbiocop", "fbb"]
ACHIEVEMENTS = [(1000, "🌱 Novabbio", "Hai sussurrato il Nome per la prima volta.")]
fabbio_count = int(r.get("fabbio_count") or 0)

# 💤 Orario notturno
def is_bot_sleeping():
    now = datetime.utcnow()
    hour = (now.hour + 2) % 24
    minute = now.minute
    return (hour == 0 and minute >= 40) or (0 < hour < 8)

# ✉️ Handler messaggi
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global fabbio_count
    if not update.message or not update.message.text:
        return
    text = update.message.text.lower()
    count = sum(text.count(alias) for alias in ALIASES)
    if count > 0:
        if is_bot_sleeping():
            await update.message.reply_text("😴 Fabbio dorme tra le 00:40 e le 08. I 'Fabbio' scritti ora non saranno conteggiati. Zzz...")
            return
        fabbio_count += count
        r.set("fabbio_count", fabbio_count)
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or update.effective_user.first_name or "Sconosciuto"
        current = json.loads(r.get(f"user:{user_id}") or json.dumps({"count": 0, "username": username, "unlocked": []}))
        current["count"] += count
        current["username"] = username
        unlocked = set(current.get("unlocked", []))
        for threshold, title, desc in ACHIEVEMENTS:
            if current["count"] >= threshold and str(threshold) not in unlocked:
                unlocked.add(str(threshold))
                await update.message.reply_text(f"🏆 *{title}* — {desc}", parse_mode="Markdown")
        current["unlocked"] = list(unlocked)
        r.set(f"user:{user_id}", json.dumps(current))

# 📊 Comando /stats
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = int(r.get("fabbio_count") or 0)
    await update.message.reply_text(f"📊 Abbiamo scritto {count} volte Fabbio. Fabbio ti amiamo.")

# 🟢 Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Ciao! Fabbio è all'ascolto. Scrivilo e vedrai.")

# 🌐 Webhook handler
async def telegram_webhook_handler(request):
    global app
    try:
        data = await request.json()
        logging.info("🔔 Webhook ricevuto: %s", json.dumps(data))
        update = Update.de_json(data, app.bot)
        await app.update_queue.put(update)
        return web.Response(text="OK")
    except Exception as e:
        logging.exception("❌ Errore nel webhook handler:")
        return web.Response(status=500, text="Errore")

# 🧠 Main loop
async def main():
    global app
    logging.basicConfig(level=logging.DEBUG)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app.initialize()

    # 🔧 Server aiohttp per il webhook
    web_app = web.Application()
    web_app.router.add_post(WEBHOOK_PATH, telegram_webhook_handler)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info(f"🌐 Webhook attivo su {DOMAIN}{WEBHOOK_PATH}")
    logging.info("🤖 Bot avviato, in attesa di messaggi...")

    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.bot.set_webhook(url=f"{DOMAIN}{WEBHOOK_PATH}")
    await app.start()

    while True:
        await asyncio.sleep(3600)

# 🚀 Avvio
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
