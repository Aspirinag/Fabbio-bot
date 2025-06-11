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

# 🏆 Achievement personalizzati
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

# 😴 Funzione sonno

def is_bot_sleeping():
    now = datetime.now().time()
    return time(0, 40) <= now < time(8, 0)

async def blocked_if_sleeping(update: Update):
    if is_bot_sleeping():
        await update.message.reply_text("😴 Sto dormendo. Riprova dalle 8 in poi.")
        return True
    return False

# 🔝 Comando top

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
                logging.warning(f"Errore parsing Redis ({key}): {e}")

        classifica.sort(reverse=True)
        if not classifica:
            await update.message.reply_text("⛔️ Nessun evocatore trovato nella classifica.")
            return

        testo = "\U0001F451 *Classifica dei Fabbionauti:*\n"
        for i, (count, name) in enumerate(classifica[:10], 1):
            testo += f"{i}. {name} — {count} Fabbii\n"

        await update.message.reply_text(testo, parse_mode="Markdown")
    except Exception as e:
        logging.exception("Errore nella generazione della classifica")
        await update.message.reply_text("⚠️ Errore durante il recupero della classifica.")

# 🌐 Webhook e main

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
