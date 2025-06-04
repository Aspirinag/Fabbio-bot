import logging
import os
import json
import redis
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import Update, Bot

# ✅ Variabili d’ambiente
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REDIS_URL = os.environ.get("REDIS_URL")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")  # inserisci il tuo chat_id nei secrets

# 🔌 Connessione a Redis
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# 🔁 Carica il contatore globale
def load_counter() -> int:
    return int(r.get("fabbio_count") or 18510)

# 💾 Salva il contatore globale
def save_counter(count: int):
    r.set("fabbio_count", count)

# 📊 Contatore globale
fabbio_count = load_counter()

# 🕑 Controllo orario attivo (2–8)
def is_bot_sleeping() -> bool:
    from datetime import datetime
    hour = datetime.utcnow().hour + 2  # UTC → ora italiana
    return 2 <= hour < 8

# 📥 Gestione messaggi
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global fabbio_count
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    count = text.count("fabbio")

    if count > 0:
        if is_bot_sleeping():
            await update.message.reply_text(
                "😴 Fabbio dorme tra le 2 e le 8. I 'Fabbio' scritti ora non saranno conteggiati. Zzz..."
            )
            return

        fabbio_count += count
        save_counter(fabbio_count)

user_id = str(update.effective_user.id)
