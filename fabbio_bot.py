import logging
import os
import json
import random
from datetime import datetime, time
import redis
from aiohttp import web
import asyncio
import nest_asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from telegram.helpers import escape_markdown

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

# 🏆 Achievements
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
        ("🫔 Cavalcatore del Meme", "900 Fabbii: domini l'onda dell'assurdo."),
        ("🏆 Campione del Fabbio", "1000 Fabbii: entri nella leggenda."),
        ("🔮 Guardiano del Fabbio", "1100 Fabbii: proteggi il verbo."),
        ("💰 Archivista del Fabbio", "1200 Fabbii: conosci ogni incarnazione."),
        ("🔔 Meditante del Fabbiadosso", "1300 Fabbii: respiri ironia."),
        ("🗓️ Scriba della Fabbiostoria", "1400 Fabbii: narri l'evoluzione."),
        ("🚀 Esploratore del Fabbiospazio", "1500 Fabbii: spingi oltre il cosmo."),
        ("👑 Fabbio Supremo", "1600 Fabbii: regni sul nonsense."),
        ("🤖 Fabbio Robot", "1700 Fabbii: scrivi per riflesso sacro."),
        ("💡 Illuminato dal Fabbio", "1800 Fabbii: capisci tutto, e nulla."),
        ("🚁 Fabbionauta", "1900 Fabbii: navighi nel vuoto sacro."),
        ("🌟 Fabbio", "2000 Fabbii: sei uno col Fabbio.")
    ])
]

QUIZ_QUESTIONS = [
    {
        "question": "Chi è Fabbio?",
        "options": ["Un meme", "Un salvatore", "Una leggenda", "Tutte le precedenti"],
        "answer": 3
    },
    {
        "question": "Cosa si ottiene evocando Fabbio?",
        "options": ["Pace", "Caos", "Luce eterna", "Dipende dal giorno"],
        "answer": 3
    },
    {
        "question": "Dove abita Fabbio?",
        "options": ["Nel codice", "Nel cuore degli utenti", "Nel cloud", "Ovunque"],
        "answer": 3
    }
]

def is_bot_sleeping():
    now = datetime.now().time()
    return time(0, 40) <= now < time(8, 0)

async def blocked_if_sleeping(update: Update):
    if is_bot_sleeping():
        await update.message.reply_text("📌 Sto dormendo. Riprova dalle 8 in poi.")
        return True
    return False

# 🚀 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Ciao! Il bot è attivo. Usa /ripulisci_avanzato se sei admin.")

# 🧹 /ripulisci_avanzato
async def ripulisci_avanzato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Solo gli amministratori possono usare questo comando.")
        return

    chiavi_eliminate = 0
    chiavi_controllate = 0

    for key in r.scan_iter("user:*"):
        chiavi_controllate += 1
        value = r.get(key)
        try:
            user_data = json.loads(value)
            count = user_data.get("count")
            username = user_data.get("username") or key.split(":", 1)[-1]

            if not isinstance(count, int) or not isinstance(username, str) or not username.strip():
                r.delete(key)
                chiavi_eliminate += 1
                logging.warning(f"[RIPULISCI_ADV] Rimossa chiave non valida: {key} — count: {count}, username: {username}")
        except Exception as e:
            r.delete(key)
            chiavi_eliminate += 1
            logging.warning(f"[RIPULISCI_ADV] Rimossa chiave JSON corrotto: {key} (valore: {value}) — Errore: {e}")

    report = (
        f"🚹 Pulizia avanzata completata!\n"
        f"🔍 Chiavi controllate: {chiavi_controllate}\n"
        f"🗑️ Chiavi eliminate: {chiavi_eliminate}"
    )

    await update.message.reply_text(
        escape_markdown(report, version=2),
        parse_mode="MarkdownV2"
    )

# 🔝 /top
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = []
    for key in r.scan_iter("user:*"):
        data = json.loads(r.get(key))
        users.append((data.get("count", 0), data.get("username") or key.split(":", 1)[-1]))
    top_users = sorted(users, reverse=True)[:10]
    text = "\n".join([f"{i+1}. {u} — {c}" for i, (c, u) in enumerate(top_users)]) or "Nessun evocatore registrato."
    await update.message.reply_text(f"🏆 *Classifica degli evocatori*\n{text}", parse_mode="Markdown")

# ❓ /fabbioquiz
async def fabbioquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = random.choice(QUIZ_QUESTIONS)
    keyboard = [
        [InlineKeyboardButton(opt, callback_data=f"quiz|{i}|{q['answer']}")]
        for i, opt in enumerate(q["options"])
    ]
    await update.message.reply_text(q["question"], reply_markup=InlineKeyboardMarkup(keyboard))

async def quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, selected, correct = query.data.split("|")
    selected, correct = int(selected), int(correct)
    result = "✅ Giusto!" if selected == correct else "❌ Sbagliato!"
    await query.edit_message_text(f"{result} La risposta corretta era: {correct+1}.")

# 📦 /me
async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    key = f"user:{user_id}"
    user_data = json.loads(r.get(key) or '{}')
    count = user_data.get("count", 0)
    username = user_data.get("username", update.effective_user.username or "?")
    await update.message.reply_text(f"📦 {username}, hai evocato Fabbio {count} volte.")

# 🙌 /evangelizza
async def evangelizza(update: Update, context: ContextTypes.DEFAULT_TYPE):
    frasi = [
        "📣 Portate il verbo del Fabbio a ogni angolo della terra!",
        "✨ Ogni Fabbio conta. Anche questo.",
        "🧿 Solo chi evoca, capisce.",
        "🌠 Un Fabbio al giorno toglie il logorio di torno."
    ]
    await update.message.reply_text(random.choice(frasi))

# 📈 Conteggio evocazioni
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    if any(alias in text for alias in ALIASES):
        if await blocked_if_sleeping(update):
            return
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "?"
        key = f"user:{user_id}"
        user_data = json.loads(r.get(key) or '{}')
        user_data["count"] = user_data.get("count", 0) + 1
        user_data["username"] = username
        r.set(key, json.dumps(user_data))

# 🗵️ Webhook handler
async def telegram_webhook_handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.process_update(update)
        return web.Response(text="OK")
    except Exception as e:
        logging.exception("Errore nel webhook handler:")
        return web.Response(status=500, text="Errore")

# ▶️ main
async def main():
    global app
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ripulisci_avanzato", ripulisci_avanzato))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("fabbioquiz", fabbioquiz))
    app.add_handler(CallbackQueryHandler(quiz_callback, pattern=r"^quiz\\|"))
    app.add_handler(CommandHandler("me", me))
    app.add_handler(CommandHandler("evangelizza", evangelizza))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

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
