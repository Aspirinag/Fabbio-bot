# FabbioBot - Codice completo

import logging
import os
import json
import random
from datetime import datetime
import redis
from aiohttp import web
import asyncio
import nest_asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# 🔧 Config
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REDIS_URL = os.environ.get("REDIS_URL")
DOMAIN = os.environ.get("DOMAIN")
PORT = int(os.environ.get("PORT", 8000))
WEBHOOK_PATH = "/webhook"
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
ADMIN_IDS = [int(ADMIN_CHAT_ID)] if ADMIN_CHAT_ID else []

app = None
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
ALIASES = ["fabbio", "fabbiotron", "fabbiocop", "fbb"]

# 🎖️ Achievements ogni 100 Fabbii
ACHIEVEMENTS = [
    ((i + 1) * 100, title, desc) for i, (title, desc) in enumerate([
        ("👶 Neofabbio", "Hai raggiunto 100 evocazioni. Il tuo viaggio inizia ora."),
        ("✨ Risvegliato", "200 Fabbii scritti: percepisci il segnale."),
        ("🌀 Discepolo della Fabbiosofia", "300 Fabbii: studi i testi antichi."),
        ("📱 Portatore di Fabbio", "400 Fabbii: diffondi la parola in ogni chat."),
        ("🤮 Mistico del Meme", "500 Fabbii: vedi oltre le emoji."),
        ("🤠 Evocatore di Caos", "600 Fabbii: l'entropia ti segue."),
        ("🌌 Oracolo di Fabbiolandia", "700 Fabbii: le visioni iniziano."),
        ("📣 Trombettiere del Fabbio", "800 Fabbii: annunci la verità."),
        ("🦄 Cavalcatore del Meme", "900 Fabbii: domini l'onda dell'assurdo."),
        ("🏆 Campione del Fabbio", "1000 Fabbii: entri nella leggenda."),
        ("🔮 Guardiano del Fabbio", "1100 Fabbii: proteggi il verbo."),
        ("📀 Archivista del Meme", "1200 Fabbii: conosci ogni incarnazione."),
        ("🛏️ Meditante del Paradosso", "1300 Fabbii: respiri ironia."),
        ("📅 Scriba della Fabbiostoria", "1400 Fabbii: narri l'evoluzione."),
        ("🚀 Esploratore del Fabbiospazio", "1500 Fabbii: spingi oltre il cosmo."),
        ("👑 Fabbio Supremo", "1600 Fabbii: regni sul nonsense."),
        ("🤖 Automa del Meme", "1700 Fabbii: scrivi per riflesso sacro."),
        ("💡 Illuminato dal Fabbio", "1800 Fabbii: capisci tutto, e nulla."),
        ("🛰 Fabbinauta", "1900 Fabbii: navighi nel vuoto sacro."),
        ("🌟 Entità Fabbiosa", "2000 Fabbii: sei uno col Fabbio.")
    ])
]

# 🧠 Quiz
QUIZ = [
    {"question": "🌍 *Dove nasce il Fabbio?*", "options": ["Nel codice sorgente", "Nel cuore degli utenti", "Nel cloud", "Nel caos"]},
    {"question": "🌈 *Cosa accade quando scrivi Fabbio sotto la luna piena?*", "options": ["Appare un admin", "Si risveglia l’antico meme", "Crasha Telegram", "Nessuno lo sa"]},
    {"question": "📱 *Chi riceve il segnale del Fabbio?*", "options": ["Solo i degni", "Chi ha scritto 1000 volte", "Chi è online alle 3", "Tutti, ma solo una volta"]},
    {"question": "🧤 *Cosa accade se pronunci Fabbio 3 volte allo specchio?*", "options": ["Compare un meme", "Crash del cervello", "Nulla, solo tristezza", "Ti insulti da solo"]},
    {"question": "🪜 *Come purificarsi da un Fabbio scritto male?*", "options": ["Scriverne 10 giusti", "Chiedere perdono", "Autoironizzarsi", "Non si può"]},
    {"question": "📦 *Cosa contiene il Sacro Archivio Fabbioso?*", "options": ["Tutti i messaggi cringe", "Le gif bannate", "Verità taciute", "Sticker dimenticati"]},
    {"question": "🪙 *Quanto vale un Fabbio?*", "options": ["1 BTC", "0", "Tutto", "Non ha prezzo"]},
    {"question": "🕳 *Cosa c’è nel buco nero Fabbioso?*", "options": ["Contro-meme", "Boomer", "Ironia concentrata", "Nulla"]},
    {"question": "⚖ *Cosa pesa più: un Fabbio o mille parole?*", "options": ["Un Fabbio", "Le parole", "Uguali", "Dipende"]},
    {"question": "🧘 *Chi raggiunge il Nirvana del Fabbio?*", "options": ["Chi non spammi", "Chi meme bene", "Chi ignora", "Solo tu"]}
]

# 📬 Gestione messaggi
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
            await update.message.reply_text(f"🏆 *{title}* — {desc}", parse_mode="Markdown")
    current["unlocked"] = list(unlocked)
    r.set(f"user:{user_id}", json.dumps(current))

# 📊 Comandi
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = int(r.get("fabbio_count") or 0)
    await update.message.reply_text(f"📊 Abbiamo scritto {count} volte Fabbio. Fabbio ti amiamo.")

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = [key for key in r.scan_iter("user:*")]
    classifica = []
    for key in users:
        data = json.loads(r.get(key))
        classifica.append((data.get("count", 0), data.get("username", "Sconosciuto")))
    classifica.sort(reverse=True)
    testo = "👑 *Classifica dei Fabbionauti:*\n"
    for i, (count, name) in enumerate(classifica[:10], 1):
        testo += f"{i}. {name} — {count} Fabbii\n"
    await update.message.reply_text(testo, parse_mode="Markdown")

async def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = json.loads(r.get(f"user:{user_id}") or json.dumps({"count": 0, "username": "Sconosciuto", "unlocked": []}))
    count = data.get("count", 0)
    unlocked = data.get("unlocked", [])
    response = f"📈 Hai scritto 'Fabbio' {count} volte.\n"
    if unlocked:
        response += "\n🏅 *Achievement sbloccati:*\n"
        for threshold, title, _ in ACHIEVEMENTS:
            if str(threshold) in unlocked:
                response += f"- {title} ({threshold} Fabbii)\n"
    else:
        response += "Non hai ancora sbloccato nessun traguardo... ma il cammino è lungo!"
    await update.message.reply_text(response, parse_mode="Markdown")

async def fabbioquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quiz = random.choice(QUIZ)
    keyboard = [[InlineKeyboardButton(opt, callback_data="quiz_fabbio")] for opt in quiz["options"]]
    await update.message.reply_text(quiz["question"], parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ *Risposta esatta!* Hai evocato Fabbio.", parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    testo = (
        "📜 *Comandi disponibili:*\n"
        "/stats — Totale Fabbii globali\n"
        "/top — Classifica dei Fabbionauti\n"
        "/me — I tuoi Fabbii e traguardi\n"
        "/fabbioquiz — Quiz mistico-comico\n"
        "/help — Elenco comandi\n"
        "/resetclassifica — (admin only)"
    )
    await update.message.reply_text(testo, parse_mode="Markdown")

async def reset_classifica(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in [str(i) for i in ADMIN_IDS]:
        await update.message.reply_text("🔒 Non sei degno di brandire il potere del reset.")
        return
    deleted = 0
    for key in r.scan_iter("user:*"):
        r.delete(key)
        deleted += 1
    await update.message.reply_text(f"⚡ Classifica resettata. {deleted} anime purificate. ✨")

# 🌐 Webhook
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

# 🚀 Main
async def main():
    global app
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("me", me_command))
    app.add_handler(CommandHandler("fabbioquiz", fabbioquiz))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("resetclassifica", reset_classifica))
    app.add_handler(CallbackQueryHandler(quiz_callback, pattern="^quiz_fabbio$"))
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
