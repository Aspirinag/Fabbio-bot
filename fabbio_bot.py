
import logging
import os
import json
import random
from datetime import datetime
import redis
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# === CONFIG ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REDIS_URL = os.environ.get("REDIS_URL")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

ALIASES = ["fabbio", "fabbiotron", "fabbiocop", "fbb"]
ACHIEVEMENTS = [(i * 1000, f"🏆 *Titolo Fabbioso {i}* — Hai scritto Fabbio {i * 1000} volte. Ti si riconosce nel Verbo.") for i in range(1, 51)]

EVANGELI = [
    "🕯️ *Fabbio è ovunque.* Anche nei tuoi silenzi più rumorosi.",
    "📖 *Nel principio era il Verbo, e il Verbo era Fabbio.*",
    "🌌 *Tra miliardi di galassie, solo una porta il Suo Nome.*",
    "🔥 *Brucia i dubbi nel rogo della Fabbiosità.*"
]

QUIZ = [
    {"question": "🤔 *Cosa NON è Fabbio?*", "options": ["Tutto", "Nulla", "Entrambi", "Non so"]},
    {"question": "📜 *In quale giorno Fabbio creò l’ironia?*", "options": ["Il primo", "Il settimo", "Il mai", "Sempre"]},
]

INSULTI_SACRIFICIO = [
    "Coglione cosmico.",
    "Apostata del ridicolo.",
    "Larva verbale.",
    "Immondizia del Verbo.",
    "Sventura ambulante."
]

def is_bot_sleeping():
    now = datetime.utcnow()
    hour = (now.hour + 2) % 24
    minute = now.minute
    return (hour == 0 and minute >= 40) or (0 < hour < 8)

fabbio_count = int(r.get("fabbio_count") or 18510)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global fabbio_count
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    count = sum(text.count(alias) for alias in ALIASES)

    if count > 0:
        if is_bot_sleeping():
            await update.message.reply_text(
                "😴 Fabbio dorme tra le 00:40 e le 08. I 'Fabbio' scritti ora non saranno conteggiati. Zzz..."
            )
            return

        fabbio_count += count
        r.set("fabbio_count", fabbio_count)

        user_id = str(update.effective_user.id)
        username = update.effective_user.username or update.effective_user.first_name or "Sconosciuto"
        current = json.loads(r.get(f"user:{user_id}") or '{"count": 0, "username": "", "unlocked": []}')
        current["count"] += count
        current["username"] = username
        unlocked = set(current.get("unlocked", []))

        for threshold, badge in ACHIEVEMENTS:
            if current["count"] >= threshold and str(threshold) not in unlocked:
                unlocked.add(str(threshold))
                await update.message.reply_text(f"{badge}", parse_mode="Markdown")

        current["unlocked"] = list(unlocked)
        r.set(f"user:{user_id}", json.dumps(current))

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

async def sacrifico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = json.loads(r.get(f"user:{user_id}") or json.dumps({"count": 0}))
    if data["count"] < 100:
        await update.message.reply_text("🙅‍♂️ Non hai abbastanza Fabbii per il sacrificio. Servono almeno 100.")
        return
    data["count"] -= 100
    insulto = random.choice(INSULTI_SACRIFICIO)
    r.set(f"user:{user_id}", json.dumps(data))
    await update.message.reply_text(f"💀 Hai sacrificato 100 Fabbii. {insulto}")

def main():
    logging.basicConfig(level=logging.INFO)

    async def after_startup(app):
        if ADMIN_CHAT_ID:
            bot = Bot(token=BOT_TOKEN)
            await bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text="🟢 *Fabbio è sveglio!*",
                parse_mode="Markdown"
            )

    app = Application.builder().token(BOT_TOKEN).post_init(after_startup).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("sacrifico", sacrifico))

    logging.info("✅ Bot avviato")
    app.run_polling()

if __name__ == "__main__":
    main()
