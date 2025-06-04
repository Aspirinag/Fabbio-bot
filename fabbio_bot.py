import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import Update
from tinydb import TinyDB, Query

# ✅ Prende il token dall’ambiente
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# 📁 TinyDB setup
db = TinyDB("fabbio_db.json")
meta_table = db.table("meta")
user_table = db.table("users")

# 🔁 Carica il contatore globale
def load_counter() -> int:
    data = meta_table.get(doc_id=1)
    return data["count"] if data else 18510  # partenza da 18.510 se non esiste

# 💾 Salva il contatore globale
def save_counter(count: int):
    meta_table.upsert({"count": count}, doc_ids=[1])

# 📊 Contatore globale
fabbio_count = load_counter()

# 📥 Gestione messaggi
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global fabbio_count
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    count = text.count("fabbio")

    if count > 0:
        fabbio_count += count
        save_counter(fabbio_count)

        # 🧑‍💻 Aggiorna conteggio per utente
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Sconosciuto"
        existing = user_table.get(Query().user_id == user_id)
        if existing:
            user_table.update(
                {"count": existing["count"] + count, "username": username},
                Query().user_id == user_id
            )
        else:
            user_table.insert({"user_id": user_id, "username": username, "count": count})

        if fabbio_count % 1000 == 0:
            await update.message.reply_text(f"🎉 Abbiamo scritto {fabbio_count} volte Fabbio. Fabbio ti amiamo.")

# 📈 Comando /stats
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = sorted(user_table.all(), key=lambda x: x["count"], reverse=True)[:3]
    leaderboard = "\n".join(
        [f"🥇 {u['username']}: {u['count']} volte" if i == 0 else
         f"🥈 {u['username']}: {u['count']} volte" if i == 1 else
         f"🥉 {u['username']}: {u['count']} volte"
         for i, u in enumerate(top_users)]
    )
    await update.message.reply_text(
        f"📊 Abbiamo scritto {fabbio_count} volte Fabbio. Fabbio ti amiamo.\n\n🏆 Classifica:\n{leaderboard}"
    )

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

