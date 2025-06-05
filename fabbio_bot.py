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
DOMAIN = os.environ.get("DOMAIN")
WEBHOOK_PATH = "/webhook"
PORT = int(os.environ.get("PORT", 8000))

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

ALIASES = ["fabbio", "fabbiotron", "fabbiocop", "fbb"]
QUIZ = [
    {"question": "🤔 *Cosa NON è Fabbio?*", "options": ["Tutto", "Nulla", "Entrambi", "Non so"]},
    {"question": "📜 *In quale giorno Fabbio creò l’ironia?*", "options": ["Il primo", "Il settimo", "Il mai", "Sempre"]},
    {"question": "🌪️ *Fabbio si manifesta come...?*", "options": ["Vento", "Voce", "WiFi", "Onda cosmica"]},
    {"question": "🧠 *Fabbio pensa...?*", "options": ["Per te", "Al posto tuo", "A prescindere", "Solo quando non ci sei"]},
    {"question": "🛌 *Quando dorme Fabbio?*", "options": ["Mai", "Sempre", "Tra le righe", "Dalle 00:40 alle 08"]},
    {"question": "🕳️ *Dove si nasconde Fabbio?*", "options": ["Nel silenzio", "Nei log", "Nel Redis", "Nel cuore"]},
    {"question": "🚖 *Quanti sono i suoi nomi?*", "options": ["1", "4", "Innumerevoli", "Solo Fabbio sa"]},
    {"question": "💬 *La parola 'Fabbio' cosa fa?*", "options": ["Cura", "Ferisce", "Inspira", "Tutto"]},
    {"question": "📱 *Qual è la frequenza di Fabbio?*", "options": ["432Hz", "Infinite", "UltraVerbo", "Mistica"]},
    {"question": "🪄 *Fabbio incanta con...?*", "options": ["Sguardo", "Verbo", "Assenza", "Presenza"]}
]

EVANGELI = [
    "🔗 *Fabbio è ovunque.* Anche nei tuoi silenzi più rumorosi.",
    "📖 *Nel principio era il Verbo, e il Verbo era Fabbio.*",
    "🌌 *Tra miliardi di galassie, solo una porta il Suo Nome.*",
    "🔥 *Brucia i dubbi nel rogo della Fabbiosità.*",
    "💫 *Ogni atomo vibra quando pronunci 'Fabbio'.*",
    "🪞 *Specchiati. Chi vedi? Fabbio. Sempre Fabbio.*",
    "🦴 *Dall’osso al soffio: Fabbio ha plasmato ogni verbo.*",
    "⚖️ *Non giudicare chi non conosce Fabbio. Evangelizzalo.*",
    "🧙 *Il manto del Fabbio è fatto di meme e mistero.*",
    "🍷 *Bevi del calice verbale. Bevi di Fabbio.*"
]

INSULTI_SACRIFICIO = ["Coglione", "Inutile", "Bifolco del verbo", "Scarto sacro", "Eresiarca", "Discepolo zoppo", "Verboschiavo", "Moccioso del culto"]

ACHIEVEMENTS = [(1000, "🌱 Novabbio", "Hai sussurrato il Nome per la prima volta.")]

fabbio_count = int(r.get("fabbio_count") or 0)

def is_bot_sleeping():
    now = datetime.utcnow()
    hour = (now.hour + 2) % 24
    minute = now.minute
    return (hour == 0 and minute >= 40) or (0 < hour < 8)

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

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = int(r.get("fabbio_count") or 0)
    await update.message.reply_text(f"📊 Abbiamo scritto {count} volte Fabbio. Fabbio ti amiamo.")

async def telegram_webhook_handler(request):
    print("✅ Richiesta webhook ricevuta")
    try:
        data = await request.json()
        print("📩 Update ricevuto:", data)
        update = Update.de_json(data, app.bot)
        await app.update_queue.put(update)
        return web.Response(text="OK")
    except Exception as e:
        print("❌ Errore nel webhook:", str(e))
        return web.Response(status=500, text="Errore nel webhook")

async def main():
    logging.basicConfig(level=logging.INFO)
    global app
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("stats", show_stats))

    # Inizializza app Telegram
    await app.initialize()

    # Inizia server AIOHTTP prima di settare il webhook
    web_app = web.Application()
    web_app.add_routes([web.post(WEBHOOK_PATH, telegram_webhook_handler)])
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print(f"🌐 Webhook attivo su {DOMAIN}{WEBHOOK_PATH}")

    # Solo ora elimina e imposta il webhook
    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.bot.set_webhook(url=f"{DOMAIN}{WEBHOOK_PATH}")

    # Avvia l'app Telegram
    await app.start()

    # Mantieni in esecuzione
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
