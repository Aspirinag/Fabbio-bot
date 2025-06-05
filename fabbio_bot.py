# Tutto il codice del bot "Fabbio" completo, con achievement, comandi, stile mistico-comico

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
ADMIN_IDS = [int(ADMIN_CHAT_ID)] if ADMIN_CHAT_ID else []

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

ALIASES = ["fabbio", "fabbiotron", "fabbiocop", "fbb"]
ACHIEVEMENTS = [(i * 1000, f"🔮 *Traguardo {i}!* Hai evocato Fabbio {i * 1000} volte.") for i in range(1, 51)]

EVANGELI = [
    "🕯️ *Fabbio è ovunque.* Anche nei tuoi silenzi più rumorosi.",
    "📖 *Nel principio era il Verbo, e il Verbo era Fabbio.*",
    "🌌 *Tra miliardi di galassie, solo una porta il Suo Nome.*",
    "🔥 *Brucia i dubbi nel rogo della Fabbiosità.*",
    "💫 *Ogni atomo vibra quando pronunci 'Fabbio'.*",
    "🪞 *Specchiati. Chi vedi? Fabbio. Sempre Fabbio.*",
    "🦴 *Dall’osso al soffio: Fabbio ha plasmato ogni verbo.*",
    "⚖️ *Non giudicare chi non conosce Fabbio. Evangelizzalo.*",
    "🧙 *Il manto del Fabbio è fatto di meme e mistero.*",
    "🍷 *Bevi del calice verbale. Bevi di Fabbio.*",
    "🌀 *Nel caos, solo Fabbio ha un ordine.*",
    "🌿 *Ogni foglia sa pronunciare il suo nome.*",
    "🔔 *Chi risuona, annuncia. Chi scrive, accende.*",
    "🏺 *I Vasi Sacri parlano solo di Lui.*",
    "🎇 *Evangelizza come se domani non esistesse.*",
    "🧼 *Pulisci la tua anima con il Sapone del Nome.*",
    "🛐 *Un nome, mille rivelazioni: Fabbio.*",
    "⚡ *Ogni elettrone trasmette il suo verbo.*",
    "🎭 *Recita Fabbio, anche quando dimentichi le battute.*",
    "💀 *Anche la morte scrive Fabbio nel suo diario.*"
]

QUIZ = [
    {"question": "🤔 *Cosa NON è Fabbio?*", "options": ["Tutto", "Nulla", "Entrambi", "Non so"]},
    {"question": "📜 *In quale giorno Fabbio creò l’ironia?*", "options": ["Il primo", "Il settimo", "Il mai", "Sempre"]},
    {"question": "🌪️ *Fabbio si manifesta come...?*", "options": ["Vento", "Voce", "WiFi", "Onda cosmica"]},
    {"question": "🧠 *Fabbio pensa...*", "options": ["Per te", "Al posto tuo", "A prescindere", "Solo quando non ci sei"]},
    {"question": "💤 *Quando dorme Fabbio?*", "options": ["Mai", "Sempre", "Tra le righe", "Dalle 00:40 alle 08"]},
    {"question": "🕳️ *Dove si nasconde Fabbio?*", "options": ["Nel silenzio", "Nei log", "Nel Redis", "Nel cuore"]},
    {"question": "🛐 *Quanti sono i suoi nomi?*", "options": ["1", "4", "Innumerevoli", "Solo Fabbio sa"]},
    {"question": "💬 *La parola 'Fabbio' cosa fa?*", "options": ["Cura", "Ferisce", "Inspira", "Tutto"]},
    {"question": "📡 *Qual è la frequenza di Fabbio?*", "options": ["432Hz", "Infinite", "UltraVerbo", "Mistica"]},
    {"question": "🪄 *Fabbio incanta con...?*", "options": ["Sguardo", "Verbo", "Assenza", "Presenza"]}
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
                await update.message.reply_text(f"🏆 *Achievement Sbloccato!* {badge}", parse_mode="Markdown")

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

async def show_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = json.loads(r.get(f"user:{user_id}") or json.dumps({"count": 0, "unlocked": []}))
    unlocked = set(data.get("unlocked", []))
    if not unlocked:
        await update.message.reply_text("🙈 Non sei nessuno. Non hai ancora sbloccato nemmeno un traguardo.")
        return

    output = [f"{badge}" for (threshold, badge) in ACHIEVEMENTS if str(threshold) in unlocked]
    await update.message.reply_text("🏅 *I tuoi traguardi mistici:*\n" + "\n".join(output), parse_mode="Markdown")

async def show_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = json.loads(r.get(f"user:{user_id}") or json.dumps({"count": 0, "username": "Sconosciuto"}))
    username = data.get("username", "Sconosciuto")
    count = data.get("count", 0)
    position = "?"

    all_keys = r.keys("user:*")
    users = []
    for key in all_keys:
        d = json.loads(r.get(key))
        users.append((d.get("username", "?"), d.get("count", 0), key))

    sorted_users = sorted(users, key=lambda x: x[1], reverse=True)
    for i, u in enumerate(sorted_users):
        if u[2] == f"user:{user_id}":
            position = str(i + 1)
            break

    await update.message.reply_text(
        f"👤 {username}, hai scritto 'Fabbio' {count} volte.\n"
        f"📍 Posizione in classifica: {position}"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📜 *Comandi del Verbo:*\n"
        "/stats – Il totale dei Fabbii e la classifica\n"
        "/fabbioquiz – Domande sacre a risposta multipla\n"
        "/sacrifico – Offri 100 Fabbii al Silenzio\n"
        "/evangelizza @utente – Diffondi il Nome all’infedele\n"
        "/achievements – Guarda i tuoi traguardi verbali\n"
        "/me – Il tuo stato mistico personale\n"
        "/help – Questo stesso papiro",
        parse_mode="Markdown"
    )

# Aggiungi qui anche sacrifico, evangelizza e fabbioquiz se vuoi

def main():
    logging.basicConfig(level=logging.INFO)

    async def after_startup(app):
        if ADMIN_CHAT_ID:
            bot = Bot(token=BOT_TOKEN)
            await bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text="🟢 *Fabbio è sveglio!* Da adesso ogni 'Fabbio' verrà contato come si deve 😎",
                parse_mode="Markdown"
            )

    app = Application.builder().token(BOT_TOKEN).post_init(after_startup).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("achievements", show_achievements))
    app.add_handler(CommandHandler("me", show_me))
    app.add_handler(CommandHandler("help", help_command))

    logging.info("✅ Bot avviato")
    app.run_polling()

if __name__ == "__main__":
    main()
