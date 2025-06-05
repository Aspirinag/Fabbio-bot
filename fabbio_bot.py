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

# Config
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REDIS_URL = os.environ.get("REDIS_URL")
DOMAIN = os.environ.get("DOMAIN")  # es: https://fabbio-bot-production.up.railway.app
WEBHOOK_PATH = "/webhook"
PORT = int(os.environ.get("PORT", 8000))

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

ALIASES = ["fabbio", "fabbiotron", "fabbiocop", "fbb"]

# Stato globale
fabbio_count = int(r.get("fabbio_count") or 0)

def is_bot_sleeping():
    now = datetime.utcnow()
    hour = (now.hour + 2) % 24  # UTC+2
    minute = now.minute
    return (hour == 0 and minute >= 40) or (0 < hour < 8)

# Handlers
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
        await update.message.reply_text(f"✨ Hai evocato Fabbio {count} volte. Totale: {fabbio_count}")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = int(r.get("fabbio_count") or 0)
    await update.message.reply_text(f"📊 Abbiamo scritto {count} volte Fabbio. Fabbio ti amiamo.")

# Webhook handler per aiohttp
async def telegram_webhook_handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.update_queue.put(update)
        return web.Response(text="OK")
    except Exception as e:
        print("Errore nel webhook:", e)
        return web.Response(status=500, text="Errore nel webhook")

# Main
async def main():
    global app
    logging.basicConfig(level=logging.INFO)

    # Inizializza app Telegram
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Server AIOHTTP
    web_app = web.Application()
    web_app.add_routes([web.post(WEBHOOK_PATH, telegram_webhook_handler)])
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"🌐 Webhook attivo su {DOMAIN}{WEBHOOK_PATH}")

    # Registra il webhook
    await app.initialize()
    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.bot.set_webhook(url=f"{DOMAIN}{WEBHOOK_PATH}")
    await app.start()

    # Mantieni attivo
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
