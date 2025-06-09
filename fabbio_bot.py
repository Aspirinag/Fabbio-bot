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
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")  # tuo user_id telegram
ADMIN_IDS = [int(ADMIN_CHAT_ID)] if ADMIN_CHAT_ID else []

app = None
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
ALIASES = ["fabbio", "fabbiotron", "fabbiocop", "fbb"]

# 🎖️ Achievement personalizzati
ACHIEVEMENTS = [
    (i * 1000, title, desc) for i, (title, desc) in enumerate([
        ("🍼 Neofabbio", "Hai emesso il primo vagito mistico."),
        ("✨ Risvegliato", "Hai aperto l'occhio interiore fabbioso."),
        ("🌀 Discepolo del Meme", "Inizi a comprendere la spirale."),
        ("📡 Ricettore Fabbionico", "Captazioni cosmiche riuscite."),
        ("🧠 Illuminato da Fabbio", "Ora comprendi la vera ironia."),
        ("🎯 Invocatore del Caso", "Ogni Fabbio è una freccia nel caos."),
        ("🔊 Ascoltatore dell'Eco", "Risuoni di fabbiovibrazioni."),
        ("💥 Scintilla Sacra", "Hai acceso la fiamma dell’assurdo."),
        ("🛸 Viaggiatore dell’Ironia", "Esplori galassie memetiche."),
        ("🎩 Apostolo del Cappello", "Indossi la stoffa del paradosso."),
        ("🔮 Veggente Fabbiotico", "Prevedi le curve dell’ironico."),
        ("📘 Lettore del Fabbiolibro", "Sai cosa non cercare."),
        ("🧙 Adepto dell'Oscuro Fabbio", "Segui l’ombra sacra."),
        ("🕳️ Abitante del Meme", "Ti sei perso nel buco fabbioso."),
        ("🦴 Collezionista di Frammenti", "Ogni Fabbio è un reperto."),
        ("🗿 Statua Vivente", "Rimani fermo nella gloria."),
        ("⚙️ Meccanico dell’Assurdo", "Hai oliato l’impossibile."),
        ("🌙 Confidente della Luna", "Hai bisbigliato all'ignoto."),
        ("🎭 Maschera della Parodia", "Rappresenti l’inafferrabile."),
        ("🏹 Arciere del Non-senso", "Miri al meme eterno."),
        ("💬 Coniugatore di Verbi Fabbiosi", "Parli in terza assurda."),
        ("🎮 Giocatore dell’Improbabile", "Hai superato l’endgame."),
        ("🌩️ Fulminato da Fabbio", "Un lampo ti ha segnato."),
        ("🚿 Purificato nel Meme", "Hai lavato ogni dubbio."),
        ("🚀 Esploratore del Fabbiospazio", "Hai varcato l’infinitià."),
        ("🌌 Messaggero dell’Infinito", "Porti la novella ironica."),
        ("📿 Monaco del Paradosso", "Ti sei ritirato nel meme."),
        ("🕰️ Viaggiatore Temporale", "Scrivi Fabbio ieri e domani."),
        ("🥽 Visionario del Meme", "Hai visto ciò che non c’è."),
        ("💡 Lampadina Mistica", "Hai avuto l’idea fabbiosa."),
        ("👁️ Testimone del Terzo Occhio", "Vedi oltre le righe."),
        ("🧩 Decifratore del Caos", "Hai ordinato l’impossibile."),
        ("📺 Guardiano dei Reels", "Controlli il loop eterno."),
        ("🪞 Specchio dell’Assurdo", "Riflessi di Fabbio ti scrutano."),
        ("⚖️ Bilanciatore di Meme", "Giudichi l’ironia con equità."),
        ("🧃 Bevitore del Succo Sacro", "Ti sei dissetato nel Fabbio."),
        ("🧤 Portatore del Guanto", "Hai maneggiato la potenza."),
        ("🪄 Stregone di Terzo Livello", "Incanti con le sillabe."),
        ("🫧 Soffiatore del Vuoto", "Hai fatto bolle di senso."),
        ("🐢 Cavalcatore di Tartarughe", "Hai tempo. E Fabbio."),
        ("👾 Entità Glitchata", "Esisti tra i pacchetti."),
        ("🐦 Oracolo del Tweet", "Profetizzi in 280 caratteri."),
        ("🛐 Sacerdote del Meme Antico", "Custodisci il verbo perduto."),
        ("💽 Incisore del .fab", "Hai scritto sulla pietra binaria."),
        ("🔗 Saldatore di Reazioni", "Colleghi ogni risposta."),
        ("🎓 Laureato in Fabbiologia", "Conosci. Sai. Ironizzi."),
        ("🏛️ Architetto del Ridicolo", "Costruisci sogni assurdi."),
        ("🧼 Detergente Spirituale", "Hai pulito l’oscuro."),
        ("💿 Collezionista di Silenzi", "Ogni non detto è tuo."),
        ("👑 Fabbio in Persona", "Tu sei ciò che evochi.")
    ], 1)
]

# 🤯 Quiz Fabbioso
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

# 📬 Messaggi & gestione
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
        "/fabbioquiz — Quiz mistico-comico\n"
        "Scrivi 'Fabbio' (o i suoi alias) per evocare la potenza e sbloccare traguardi!"
    )
    await update.message.reply_text(testo, parse_mode="Markdown")

# 🔄 Reset classifica (admin only)
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
    app.add_handler(CommandHandler("fabbioquiz", fabbioquiz))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("top", top))
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
