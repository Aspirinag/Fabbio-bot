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

# 🎖️ Achievement personalizzati
ACHIEVEMENTS = [
    ((i+1) * 100, title, desc) for i, (title, desc) in enumerate([
        ("👶 Neofabbio", "Hai raggiunto 100 evocazioni. Il tuo viaggio inizia ora."),
        ("✨ Risvegliato", "200 Fabbii scritti: percepisci il segnale."),
        ("🔀 Discepolo della Fabbiosofia", "300 Fabbii: studi i testi antichi."),
        ("📱 Portatore di Fabbio", "400 Fabbii: diffondi la parola in ogni chat."),
        ("🐮 Mistico del Meme", "500 Fabbii: vedi oltre le emoji."),
        ("🤠 Evocatore di Caos", "600 Fabbii: l'entropia ti segue."),
        ("🌌 Oracolo di Fabbiolandia", "700 Fabbii: le visioni iniziano."),
        ("📣 Trombettiere del Fabbio", "800 Fabbii: annunci la verità."),
        ("🧄 Cavalcatore del Meme", "900 Fabbii: domini l'onda dell'assurdo."),
        ("🏆 Campione del Fabbio", "1000 Fabbii: entri nella leggenda."),
        ("🔮 Guardiano del Fabbio", "1100 Fabbii: proteggi il verbo."),
        ("💰 Archivista del Fabbio", "1200 Fabbii: conosci ogni incarnazione."),
        ("📣 Meditante del Fabbiadosso", "1300 Fabbii: respiri ironia."),
        ("🗓️ Scriba della Fabbiostoria", "1400 Fabbii: narri l'evoluzione."),
        ("🚀 Esploratore del Fabbiospazio", "1500 Fabbii: spingi oltre il cosmo."),
        ("👑 Fabbio Supremo", "1600 Fabbii: regni sul nonsense."),
        ("🤖 Fabbio Robot", "1700 Fabbii: scrivi per riflesso sacro."),
        ("💡 Illuminato dal Fabbio", "1800 Fabbii: capisci tutto, e nulla."),
        ("🚁 Fabbionauta", "1900 Fabbii: navighi nel vuoto sacro."),
        ("🌟 Fabbio", "2000 Fabbii: sei uno col Fabbio.")
    ])
]

# 🧠 Quiz Fabbioso
QUIZ = [
    {"question": "🌍 *Dove nasce il Fabbio?*", "options": ["Nel codice sorgente", "Nel buco del culo", "Da un uovo", "Nel caos"]},
    {"question": "🌈 *Cosa accade quando scrivi Fabbio sotto la luna piena?*", "options": ["Muori, bestia", "Diventi un lupo man mano", "Crasha Telegram", "Nessuno lo sa"]},
    {"question": "📱 *Chi riceve il segnale del Fabbio?*", "options": ["Solo i degni", "Chi ha scritto 1000 volte", "Chi è online alle 3", "Tutti, ma solo una volta"]},
    {"question": "🪴 *Cosa accade se pronunci Fabbio 3 volte allo specchio?*", "options": ["Me lo fai in mano", "Crash del cervello", "Nulla, solo tristezza", "Ti insulti da solo"]},
    {"question": "🧬 *Come purificarsi da un Fabbio scritto male?*", "options": ["Scriverne 10 giusti", "Chiedere perdono", "Ammazzarsi", "Non si può"]},
    {"question": "📦 *Cosa contiene il Sacro Archivio Fabbioso?*", "options": ["Tutti i messaggi cringe", "Le gif bannate", "Verità taciute", "Sticker dimenticati"]},
    {"question": "🪙 *Quanto vale un Fabbio?*", "options": ["1 BTC", "0", "Tutto", "Non ha prezzo"]},
    {"question": "🕳 *Cosa c’è nel buco nero Fabbioso?*", "options": ["Contro-meme", "Boomer", "Ironia concentrata", "Nulla"]},
    {"question": "⚖ *Cosa pesa più: un Fabbio o mille parole?*", "options": ["Un Fabbio", "Le parole", "Uguali", "Dipende"]},
    {"question": "🧘 *Chi raggiunge il Nirvana del Fabbio?*", "options": ["Chi è coglione", "Jjolas", "Tua madre", "Solo tu"]}
]

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    domanda = random.choice(QUIZ)
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"quiz|{opt}")] for opt in domanda["options"]]
    await update.message.reply_text(domanda["question"], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🌀 Fabbio ti prego, Fabbio.")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = int(r.get("fabbio_count") or 0)
    await update.message.reply_text(f"📊 Abbiamo scritto {count} volte Fabbio. Fabbio ti amiamo.")

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = [key for key in r.scan_iter("user:*")]
    classifica = []
    for key in users:
        try:
            data = json.loads(r.get(key))
            classifica.append((data.get("count", 0), data.get("username", "Sconosciuto")))
        except Exception as e:
            logging.warning(f"Errore nel parsing del dato Redis per {key}: {e}")
    classifica.sort(reverse=True)
    if not classifica:
        await update.message.reply_text("⛔️ Nessun evocatore trovato nella classifica.")
        return
    testo = "👑 *Classifica dei Fabbionauti:*\n"
    for i, (count, name) in enumerate(classifica[:10], 1):
        testo += f"{i}. {name} — {count} Fabbii\n"
    await update.message.reply_text(testo, parse_mode="Markdown")

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = json.loads(r.get(f"user:{user_id}") or json.dumps({"count": 0, "username": "Sconosciuto", "unlocked": []}))
    count = data.get("count", 0)
    unlocked = data.get("unlocked", [])
    testo = f"📍 Hai evocato Fabbio {count} volte.\n"
    if unlocked:
        testo += "🏅 Traguardi raggiunti:\n"
        for ach in unlocked:
            for threshold, title, desc in ACHIEVEMENTS:
                if str(threshold) == str(ach):
                    testo += f"— {title}: {desc}\n"
    else:
        testo += "(Nessun traguardo sbloccato ancora)"
    await update.message.reply_text(testo)

async def telegram_webhook_handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.process_update(update)
        return web.Response(text="OK")
    except Exception as e:
        logging.exception("Errore nel webhook handler:")
        return web.Response(status=500, text="Errore")

async def main():
    global app
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("me", me))
    app.add_handler(CommandHandler("fabbioquiz", quiz))
    app.add_handler(CallbackQueryHandler(quiz_callback, pattern=r"^quiz\\|"))

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
