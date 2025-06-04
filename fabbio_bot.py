import logging
import os
import json
import redis
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import Update, Bot

# ✅ Variabili d’ambiente
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REDIS_URL = os.environ.get("REDIS_URL")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")  # Inserisci il tuo chat ID Telegram nei segreti

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

# 🕑 Controllo orario attivo (2:00–8:00 disattivo)
def is_bot_sleeping() -> bool:
    from datetime import datetime
    hour = datetime.utcnow().hour + 2  # Converti UTC → ora italiana
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
        username = update.effective_user.username or update.effective_user.first_name or "Sconosciuto"

        # 📈 Aggiorna classifica per utente
        current = json.loads(r.get(f"user:{user_id}") or '{"count": 0, "username": ""}')
        current["count"] += count
        current["username"] = username
        r.set(f"user:{user_id}", json.dumps(current))

        if fabbio_count % 1000 == 0:
            await update.message.reply_text(f"🎉 Abbiamo scritto {fabbio_count} volte Fabbio. Fabbio ti amiamo.")

# 📈 Comando /stats
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_keys = r.keys("user:*")
    users = []

    for key in all_keys:
        data = json.loads(r.get(key))
        users.append((data["username"], data["count"]))

    top_users = sorted(users, key=lambda x: x[1], reverse=True)[:3]
    leaderboard = "\n".join(
        [f"🥇 {u[0]}: {u[1]} volte" if i == 0 else
         f"🥈 {u[0]}: {u[1]} volte" if i == 1 else
         f"🥉 {u[0]}: {u[1]} volte"
         for i, u in enumerate(top_users)]
    )

    await update.message.reply_text(
        f"📊 Abbiamo scritto {fabbio_count} volte Fabbio. Fabbio ti amiamo.\n\n🏆 Classifica:\n{leaderboard}"
    )

# 📬 Messaggio all'avvio (solo se il bot si è appena riattivato)
async def send_startup_message():
    if not ADMIN_CHAT_ID:
        return
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text="🟢 *Fabbio è sveglio!* Da adesso ogni 'Fabbio' verrà contato come si deve 😎",
        parse_mode="Markdown"
    )

# ▶️ Avvio del bot
def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("stats", show_stats))
    app.create_task(send_startup_message())
    logging.info("✅ Bot avviato")
    app.run_polling()

if __name__ == "__main__":
    main()
