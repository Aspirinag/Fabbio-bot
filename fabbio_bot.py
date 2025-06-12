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
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, filters
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
        ("🧄 Cavalcatore del Meme", "900 Fabbii: domini l'onda dell'assurdo."),
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
        await update.message.reply_text("😴 Sto dormendo. Riprova dalle 8 in poi.")
        return True
    return False

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    key = f"user:{user_id}"
    data = r.get(key)

    if not data:
        await update.message.reply_text("🙈 Nessuna evocazione trovata per te.")
        return

    user_data = json.loads(data)
    count = user_data.get("count", 0)
    username = user_data.get("username") or update.effective_user.first_name

    total_key = "global:total"
    total_count = r.get(total_key)
    if total_count is None:
        total_count = 19752
        r.set(total_key, total_count)
    else:
        total_count = int(total_count)

    reply = (
        f"📊 Statistiche di {username}\n"
        f"🔢 Evocazioni personali: {count}\n"
        f"🌍 Evocazioni totali: {total_count}"
    )

    await update.message.reply_text(reply)

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    key = f"user:{user_id}"
    data = r.get(key)

    if not data:
        await update.message.reply_text("🙈 Nessuna evocazione trovata per te.")
        return

    user_data = json.loads(data)
    count = user_data.get("count", 0)
    username = user_data.get("username") or update.effective_user.first_name

    best_title = None
    for threshold, title, _ in reversed(ACHIEVEMENTS):
        if count >= threshold:
            best_title = title
            break

    reply = f"👤 Nome: {username}\n📈 Fabbii evocati: {count}"
    if best_title:
        reply += f"\n🏅 Achievement: {best_title}"

    await update.message.reply_text(reply)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ Comandi disponibili: /stats, /top, /me, /fabbioquiz, /ripulisci, /help")

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = random.choice(QUIZ_QUESTIONS)
    keyboard = [
        [InlineKeyboardButton(opt, callback_data=f"quiz|{i}|{question['answer']}")]
        for i, opt in enumerate(question["options"])
    ]
    await update.message.reply_text(
        question["question"],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    selected = int(parts[1])
    correct = int(parts[2])
    if selected == correct:
        await query.edit_message_text("✅ Corretto! Sei un vero conoscitore di Fabbio.")
    else:
        await query.edit_message_text("❌ Risposta sbagliata. Il Fabbio ti osserva.")

# ✅ TOP con MarkdownV2 + escape
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await blocked_if_sleeping(update):
        return

    try:
        user_keys = list(r.scan_iter(match="user:*"))
        classifica = []

        for key in user_keys:
            value = r.get(key)
            if not value:
                continue

            try:
                user_data = json.loads(value)
                count = user_data.get("count", 0)
                username = user_data.get("username") or key.split(":", 1)[-1]
                classifica.append((count, username))
            except Exception as e:
                logging.warning(f"[TOP] Errore parsing JSON per {key}: {e} (valore: {value})")
                continue

        if not classifica:
            await update.message.reply_text("⛔️ Nessun evocatore trovato nella classifica.")
            return

        classifica.sort(reverse=True)

        testo = "🏆 *Classifica dei Fabbionauti:*\n"
        for i, (count, name) in enumerate(classifica[:10], 1):
            safe_name = escape_markdown(name, version=2)
            testo += f"{i}. {safe_name} — {count} Fabbii\n"

        if len(testo) > 4000:
            testo = testo[:3990] + "\n[...]"

        await update.message.reply_text(testo, parse_mode="MarkdownV2")

    except Exception as e:
        logging.exception("[TOP] Errore durante il recupero della classifica")
        await update.message.reply_text("⚠️ Errore durante il recupero della classifica.")

# ✅ RIPULISCI
async def ripulisci(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔️ Solo gli amministratori possono usare questo comando.")
        return

    chiavi_eliminate = 0
    chiavi_controllate = 0

    for key in r.scan_iter("user:*"):
        chiavi_controllate += 1
        value = r.get(key)
        try:
            json.loads(value)
        except Exception as e:
            r.delete(key)
            chiavi_eliminate += 1
            logging.warning(f"[RIPULISCI] Rimossa chiave corrotta: {key} (valore: {value})")

    await update.message.reply_text(
        f"🧹 Pulizia completata!\n"
        f"🔍 Chiavi controllate: {chiavi_controllate}\n"
        f"🗑️ Chiavi eliminate: {chiavi_eliminate}"
    )

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
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ripulisci", ripulisci))
    app.add_handler(CallbackQueryHandler(quiz_callback, pattern=r"^quiz\|"))

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
