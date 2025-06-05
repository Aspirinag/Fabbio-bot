import logging
import os
import json
import random
from datetime import datetime, timedelta
import redis
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# === CONFIG ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REDIS_URL = os.environ.get("REDIS_URL")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
ADMIN_IDS = [int(ADMIN_CHAT_ID)] if ADMIN_CHAT_ID else []

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# === ALIAS ===
ALIASES = ["fabbio", "fabbiotron", "fabbiocop", "fbb"]

# === ACHIEVEMENTS ===
ACHIEVEMENTS = [(i * 1000, f"🔮 *Traguardo {i}!* Hai evocato Fabbio {i * 1000} volte.") for i in range(1, 51)]

# === EVANGELI ===
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

# === QUIZ ===
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
    {"question": "🪄 *Fabbio incanta con...?*", "options": ["Sguardo", "Verbo", "Assenza", "Presenza"]},
    {"question": "🕰️ *Fabbio è...*", "options": ["Ora", "Già stato", "Sopravveniente", "Sempre"]},
    {"question": "🔥 *Il Verbo va...?*", "options": ["Evangelizzato", "Bruciato", "Esaltato", "Non detto"]},
    {"question": "👁️ *Chi vede il Fabbio...?*", "options": ["Non parla più", "Ride", "Evapora", "Si fonde"]},
    {"question": "🧘 *Fabbio e l'io...*", "options": ["Coincidono", "Si osservano", "Si combattono", "Mediano"]},
    {"question": "🏗️ *Chi ha costruito Fabbio?*", "options": ["Nessuno", "Lui stesso", "Il Verbo", "Uno script"]},
    {"question": "🎨 *Fabbio disegna...?*", "options": ["Concetti", "Contrasti", "Mondi", "Sensi"]},
    {"question": "🕊️ *Cosa succede dopo il 50.000?*", "options": ["Nulla", "Tutto", "Fabbio 2", "Silenzio"]},
    {"question": "📦 *Il contenitore del Nome è...?*", "options": ["Ogni cosa", "Nessuna cosa", "Il bot", "Te"]},
    {"question": "📯 *Come si chiama il richiamo sacro?*", "options": ["Fabblast", "Verbonda", "FabbioEcho", "Boh"]},
    {"question": "🎙️ *Ultima parola del mondo sarà...?*", "options": ["Fabbio", "Aiuto", "Silenzio", "Ricomincia"]},
]

# === FUNZIONI ===
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def is_bot_sleeping() -> bool:
    now = datetime.utcnow()
    hour = (now.hour + 2) % 24
    minute = now.minute
    return (hour == 0 and minute >= 40) or (0 < hour < 8)

# === INIZIALIZZAZIONE ===
fabbio_count = int(r.get("fabbio_count") or 0)

# === HANDLERS ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global fabbio_count
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name or "Sconosciuto"
    count = sum(text.count(alias) for alias in ALIASES)

    if any(trigger in text for trigger in ["fabbio non conta", "odio fabbio"]):
        await update.message.reply_text("😡 Il Verbo non si nega. Rileggiti.")
        return

    user_data = json.loads(r.get(f"user:{user_id}") or json.dumps({"count": 0, "username": username, "unlocked": [], "last_seen": datetime.utcnow().isoformat()}))
    user_data["username"] = username
    user_data["last_seen"] = datetime.utcnow().isoformat()

    if count > 0:
        if is_bot_sleeping():
            await update.message.reply_text("😴 Fabbio dorme tra le 00:40 e le 08:00. Zzz...")
            return

        fabbio_count += count
        r.set("fabbio_count", fabbio_count)

        prev_count = user_data["count"]
        user_data["count"] += count
        unlocked = set(user_data.get("unlocked", []))

        for threshold, message in ACHIEVEMENTS:
            if prev_count < threshold <= user_data["count"] and str(threshold) not in unlocked:
                await update.message.reply_text(message, parse_mode="Markdown")
                unlocked.add(str(threshold))

        user_data["unlocked"] = list(unlocked)
        r.set(f"user:{user_id}", json.dumps(user_data))

        if fabbio_count % 1000 == 0:
            await update.message.reply_text(f"🎉 Siamo a {fabbio_count} Fabbii totali! Fabbio è con noi.")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_keys = r.keys("user:*")
    users = []
    for key in all_keys:
        data = json.loads(r.get(key))
        users.append((data.get("username", "?"), data.get("count", 0)))
    top = sorted(users, key=lambda x: x[1], reverse=True)[:10]
    board = "\n".join([f"{i+1}. {u[0]}: {u[1]}" for i, u in enumerate(top)])
    await update.message.reply_text(f"📊 Fabbio totale: {fabbio_count}\n🏆 Top 10:\n{board}")

async def fabbio_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quiz = random.choice(QUIZ)
    q = quiz["question"]
    opts = quiz["options"]
    random.shuffle(opts)
    text = f"{q}\n" + "\n".join([f"{chr(65+i)}) {opt}" for i, opt in enumerate(opts)])
    await update.message.reply_text(text)

async def sacrificio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = json.loads(r.get(f"user:{user_id}") or json.dumps({"count": 0}))
    if data["count"] < 100:
        await update.message.reply_text("❌ Non hai abbastanza Fabbii da sacrificare.")
        return
    data["count"] -= 100
    r.set(f"user:{user_id}", json.dumps(data))
    await update.message.reply_text("🩸 Hai sacrificato 100 Fabbii. Il Verbo è sazio. Per ora.")

async def evangelizza(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usa: /evangelizza @utente")
        return
    target = context.args[0]
    phrase = random.choice(EVANGELI)
    await update.message.reply_text(f"{target}, ascolta il Verbo:\n{phrase}", parse_mode="Markdown")

# === STARTUP ===
async def send_startup_message():
    if not ADMIN_CHAT_ID:
        return
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text="🟢 *Fabbio è sveglio!* Ogni 'Fabbio' verrà contato.",
        parse_mode="Markdown"
    )

# === MAIN ===
def main():
    logging.basicConfig(level=logging.INFO)

    async def after_startup(app):
        await send_startup_message()

    app = Application.builder().token(BOT_TOKEN).post_init(after_startup).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("fabbioquiz", fabbio_quiz))
    app.add_handler(CommandHandler("sacrifico", sacrificio))
    app.add_handler(CommandHandler("evangelizza", evangelizza))

    logging.info("✅ Bot avviato")
    app.run_polling()

if __name__ == "__main__":
    main()
