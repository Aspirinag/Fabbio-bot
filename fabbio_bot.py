
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

INSULTI_SACRIFICIO = [
    "Hai sacrificato 100 Fabbii e guadagnato... un vaffabbio, coglione.",
    "Oh discepolo del nulla, l’unico dono che ricevi è il disprezzo del Verbo.",
    "Hai bruciato il verbo per niente. Sei un fabbiofesso.",
    "Fabbio ti ignora. E anche noi.",
    "Hai ottenuto il rango di Fabbiostronzo.",
    "Hai dato 100 Fabbii e ricevuto solo sputi mistici.",
    "Il tuo sacrificio è stato inutile. Come te.",
    "Fabbio ti guarda... e scuote la testa.",
    "Coglione mistico. Questo sei.",
    "Hai offerto Fabbii e ricevuto il silenzio eterno. E uno schiaffo verbale."
]

def is_bot_sleeping():
    now = datetime.utcnow()
    hour = (now.hour + 2) % 24
    minute = now.minute
    return (hour == 0 and minute >= 40) or (0 < hour < 8)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fabbio_count = int(r.get("fabbio_count") or 18510)
    if not update.message or not update.message.text:
        return
    text = update.message.text.lower()
    count = sum(text.count(alias) for alias in ALIASES)
    if count > 0:
        if is_bot_sleeping():
            await update.message.reply_text("😴 Fabbio dorme tra le 00:40 e le 08. Zzz...")
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
    users = [(json.loads(r.get(k)).get("username", "?"), json.loads(r.get(k)).get("count", 0)) for k in all_keys]
    top_users = sorted(users, key=lambda x: x[1], reverse=True)[:3]
    leaderboard = "
".join([f"🥇 {u[0]}: {u[1]} volte" if i == 0 else f"🥈 {u[0]}: {u[1]} volte" if i == 1 else f"🥉 {u[0]}: {u[1]} volte" for i, u in enumerate(top_users)])
    fabbio_count = int(r.get("fabbio_count") or 18510)
    await update.message.reply_text(f"📊 Abbiamo scritto {fabbio_count} volte Fabbio.

🏆 Classifica:
{leaderboard}")

async def fabbio_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quiz = random.choice(QUIZ)
    options = "
".join([f"- {opt}" for opt in quiz["options"]])
    await update.message.reply_text(f"{quiz['question']}
{options}", parse_mode="Markdown")

async def evangelizza(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Evangelizza *chi*? Scrivi `/evangelizza @utente`", parse_mode="Markdown")
        return
    user = context.args[0]
    phrase = random.choice(EVANGELI)
    await update.message.reply_text(f"{user}!
{phrase}", parse_mode="Markdown")

async def sacrifico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    current = json.loads(r.get(f"user:{user_id}") or '{"count": 0, "username": ""}')
    if current.get("count", 0) < 100:
        await update.message.reply_text("Non hai abbastanza Fabbii da sacrificare, povero disgraziato.")
        return
    current["count"] -= 100
    r.set(f"user:{user_id}", json.dumps(current))
    await update.message.reply_text(random.choice(INSULTI_SACRIFICIO), parse_mode="Markdown")

def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("fabbioquiz", fabbio_quiz))
    app.add_handler(CommandHandler("evangelizza", evangelizza))
    app.add_handler(CommandHandler("sacrifico", sacrifico))
    app.run_polling()

if __name__ == "__main__":
    main()
