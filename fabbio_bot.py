import logging
import os
import json
import random
from datetime import datetime
import redis
from aiohttp import web
import asyncio
import nest_asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# 🔧 Config
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REDIS_URL = os.environ.get("REDIS_URL")
DOMAIN = os.environ.get("DOMAIN")
PORT = int(os.environ.get("PORT", 8000))
WEBHOOK_PATH = "/webhook"

app = None
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
ALIASES = ["fabbio", "fabbiotron", "fabbiocop", "fbb"]
COOLDOWN_SECONDS = 10

ACHIEVEMENTS = [
    (i * 1000, title, desc) for i, (title, desc) in enumerate([
        ("🐣 Il Fabbiatore", "Hai evocato il tuo primo migliaio. È iniziato tutto da qui."),
        ("🌪 Fabbionico", "Hai superato i 2000. Sei un turbine di Fabbio."),
        ("🧠 Fabbinato", "3000 Fabbio e già trasudi conoscenza."),
        ("🚀 Fabbionauta", "5000 lanci nello spazio memetico."),
        ("🔥 Infabbionato", "Sei ormai bruciato dal sacro meme."),
        ("🧬 DNA Fabbioso", "7000 Fabbii impressi nel tuo codice genetico."),
        ("🕯 Accolito del Fabbio", "Ti inginocchi al suo verbo."),
        ("⚡ Fabbioclastico", "Rompi i dogmi con 9000 evocazioni."),
        ("🕳 Fabbionero", "Entrato nel buco nero della fabbiosità."),
        ("🎇 Fabbiocreatore", "Hai scritto il 50.000º Fabbio.")
    ], 1)
]

QUIZ = [
    {"question": "🌍 *Dove nasce il Fabbio?*", "options": ["Nel codice sorgente", "Nel cuore degli utenti", "Nel cloud", "Nel caos"]},
    {"question": "🌈 *Cosa accade quando scrivi Fabbio sotto la luna piena?*", "options": ["Appare un admin", "Si risveglia l’antico meme", "Crasha Telegram", "Nessuno lo sa"]},
    {"question": "📡 *Chi riceve il segnale del Fabbio?*", "options": ["Solo i degni", "Chi ha scritto 1000 volte", "Chi è online alle 3", "Tutti, ma solo una volta"]},
    {"question": "🧤 *Cosa accade se pronunci Fabbio 3 volte allo specchio?*", "options": ["Compare un meme", "Crash del cervello", "Nulla, solo tristezza", "Ti insulti da solo"]},
    {"question": "🧼 *Come purificarsi da un Fabbio scritto male?*", "options": ["Scriverne 10 giusti", "Chiedere perdono", "Autoironizzarsi", "Non si può"]},
    {"question": "📦 *Cosa contiene il Sacro Archivio Fabbioso?*", "options": ["Tutti i messaggi cringe", "Le gif bannate", "Verità taciute", "Sticker dimenticati"]},
    {"question": "🪙 *Quanto vale un Fabbio?*", "options": ["1 BTC", "0", "Tutto", "Non ha prezzo"]},
    {"question": "🕳 *Cosa c’è nel buco nero Fabbioso?*", "options": ["Contro-meme", "Boomer", "Ironia concentrata", "Nulla"]},
    {"question": "⚖ *Cosa pesa più: un Fabbio o mille parole?*", "options": ["Un Fabbio", "Le parole", "Uguali", "Dipende"]},
    {"question": "🧘 *Chi raggiunge il Nirvana del Fabbio?*", "options": ["Chi non spammi", "Chi meme bene", "Chi ignora", "Solo tu"]}
]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.lower()
    count = sum(text.count(alias) for alias in ALIASES)
    if count == 0:
        return
    fabbio_count = int(r.get("fabbio_count") or 0) + count
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
            await update.message.reply_text(f"\U0001F3C6 *{title}* — {desc}", parse_mode="Markdown")
    current["unlocked"] = list(unlocked)
    r.set(f"user:{user_id}", json.dumps(current))

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = int(r.get("fabbio_count") or 0)
    await update.message.reply_text(f"\U0001F4CA Abbiamo scritto {count} volte Fabbio. Fabbio ti amiamo.")

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = [key for key in r.scan_iter("user:*")]
    classifica = []
    for key in users:
        data = json.loads(r.get(key))
        classifica.append((data.get("count", 0), data.get("username", "Sconosciuto")))
    classifica.sort(reverse=True)
    testo = "\U0001F451 *Classifica dei Fabbionauti:*\n"
    for i, (count, name) in enumerate(classifica[:10], 1):
        testo += f"{i}. {name} — {count} Fabbii\n"
    await update.message.reply_text(testo, parse_mode="Markdown")

async def fabbioquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quiz = random.choice(QUIZ)
    keyboard = [[InlineKeyboardButton(opt, callback_data="quiz_none")] for opt in quiz["options"]]
    await update.message.reply_text(quiz["question"], parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    testo = (
        "📜 *Comandi disponibili:*\n"
        "/stats — Totale Fabbii globali\n"
        "/top — Classifica dei Fabbionauti\n"
        "/fabbioquiz — Quiz mistico-comico\n"
        "Scrivi 'Fabbio' (o i suoi alias) per evocare la potenza e sbloccare traguardi!"
    )
    await update.message.reply_text(testo, parse_mode="Markdown")

async def telegram_webhook_handler(request):
    global app
    try:
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.update_queue.put(update)
        return web.Response(text="OK")
    except Exception as e:
        logging.exception("❌ Errore nel webhook handler:")
        return web.Response(status=500, text="Errore")

async def main():
    global app
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("fabbioquiz", fabbioquiz))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app.initialize()
    web_app = web.Application()
    web_app.router.add_post(WEBHOOK_PATH, telegram_webhook_handler)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.bot.set_webhook(url=f"{DOMAIN}{WEBHOOK_PATH}")
    await app.start()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
