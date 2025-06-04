import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import Update

# ✅ Prende il token dall’ambiente
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# 📁 File per il contatore
COUNTER_FILE = 'counter.txt'

# 🔁 Carica il contatore
def load_counter() -> int:
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'r') as f:
            return int(f.read())
    return 0

# 💾 Salva il contatore
def save_counter(count: int):
    with open(COUNTER_FILE, 'w') as f:
        f.write(str(count))

# 📊 Contatore globale
fabbio_count = load_counter()

# 📥 Gestione messaggi
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global fabbio_count
    text = update.message.text.lower()
    count = text.count("fabbio")
    if count > 0:
        fabbio_count += count
        save_counter(fabbio_count)
        if fabbio_count % 1000 == 0:
            await update.message.reply_text(f"🎉 'Fabbio' è stato scritto {fabbio_count} volte!")

# 📈 Comando /stats
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📊 'Fabbio' è stato scritto {fabbio_count} volte!")

# ▶️ Avvio del bot
def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("stats", show_stats))
    logging.info("✅ Application started")
    app.run_polling()

if __name__ == "__main__":
    main()
