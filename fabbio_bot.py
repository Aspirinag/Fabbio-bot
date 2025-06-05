import logging
import os
import json
import redis
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime

# ✅ Variabili d’ambiente
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REDIS_URL = os.environ.get("REDIS_URL")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")

# 🔌 Connessione a Redis
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# 🔁 Carica il contatore globale
def load_counter() -> int:
    return int(r.get("fabbio_count") or 0)

# 💾 Salva il contatore globale
def save_counter(count: int):
    r.set("fabbio_count", count)

# 📊 Contatore globale
fabbio_count = load_counter()

# 🕑 Controllo orario (00:40–08:00 italiane)
def is_bot_sleeping() -> bool:
    now = datetime.utcnow()
    hour = (now.hour + 2) % 24
    minute = now.minute
    return (hour == 0 and minute >= 40) or (0 < hour < 8)

# 🏆 Achievement
ACHIEVEMENTS = [
    (1000, "🐾 *Iniziato!* Hai appena evocato Fabbio."),
    (2000, "🎈 *Curioso!* Fabbio ti ha notato."),
    (3000, "🎯 *Ripetente!* Hai una missione nella vita."),
    (4000, "👶 *Bimbo di Fabbio!* I tuoi primi passi."),
    (5000, "📢 *Annunciatore!* Il verbo si propaga."),
    (6000, "🔔 *Campanaro!* Fabbio rintocca in te."),
    (7000, "📚 *Studioso!* Conosci i testi sacri."),
    (8000, "🧱 *Costruttore!* Un mattone alla volta."),
    (9000, "🧼 *Puro!* Nessuna bestemmia, solo Fabbio."),
    (10000, "🐣 *Neofita!* Sei dei nostri."),
    (11000, "🍝 *Fabbiolo Italiano!* Pasta e Fabbio."),
    (12000, "🤳 *Selfabbio!* La tua immagine è Fabbio."),
    (13000, "🕵️ *Indagatore!* Cercavi altro, hai trovato Fabbio."),
    (14000, "🎭 *Mimo di Fabbio!* Lo rappresenti."),
    (15000, "🐸 *Anfibio!* Gridi Fabbio in ogni habitat."),
    (16000, "💬 *Chiacchierone!* Ti sentono ovunque."),
    (17000, "📣 *Predicatore!* Ti seguono in tanti."),
    (18000, "🔄 *Ricorsivo!* Fabbio chiama Fabbio."),
    (19000, "🧠 *Devoto Mentale!* Hai cancellato il resto."),
    (20000, "🎤 *Fabbiocantante!* Hai trovato la nota giusta."),
    (21000, "🧭 *Esploratore!* Porti Fabbio ovunque."),
    (22000, "🚀 *Fabbionauta!* Sei fuori orbita."),
    (23000, "⚔️ *Crociato!* In battaglia col Verbo."),
    (24000, "🎢 *FabbioVibes!* È un sali-scendi mistico."),
    (25000, "💎 *Discepolo!* Riconosci solo un Maestro."),
    (26000, "🛡️ *Guardiano!* Proteggi il nome."),
    (27000, "🤖 *Automaton!* Un bot? Forse."),
    (28000, "💣 *Fabbiobomba!* Esplosione verbale."),
    (29000, "🐉 *Profeta!* Vedi lontano."),
    (30000, "🔮 *Visionario!* Sai che verrà."),
    (31000, "📡 *Trasmettitore!* Diffondi a distanza."),
    (32000, "🧙 *Stregone!* Hai il Verbo magico."),
    (33000, "👑 *FabbioMaster!* Nessuno sopra di te."),
    (34000, "🌋 *Vulcano!* Ribolli di fede."),
    (35000, "📈 *Scalatore!* Vertiginoso."),
    (36000, "🦾 *Cyborg!* Umana macchina fabbiosa."),
    (37000, "🕹️ *Giocatore Sacro!* Vinci con Fabbio."),
    (38000, "🧬 *DNA Fabbio!* Lo porti dentro."),
    (39000, "⚡ *Scintilla!* Accendi la fiamma."),
    (40000, "🧠🧠 *Ultrapensante!* Non puoi più tornare indietro."),
    (41000, "🗿 *Testimone di Pietra!* Immutabile."),
    (42000, "🧊 *Fabbio Glaciale!* Freddo ma fedele."),
    (43000, "🌌 *Fabbioverso!* Sei ovunque."),
    (44000, "🪐 *Apostolo Galattico!* Oltre il tempo."),
    (45000, "🎇 *Esplosione!* Un urlo nell’etere."),
    (46000, "🏛️ *Sacerdote!* Celebrante ufficiale."),
    (47000, "🔥🔥 *Bruciatore!* Consumi ogni dubbio."),
    (48000, "📿 *Fabbiosanto!* Illuminato dagli altri."),
    (49000, "✨ *Entità!* Puro spirito verbale."),
    (50000, "🕊️ *Illuminato!* Hai raggiunto la vetta. Il silenzio ti basta.")
]

# 📥 Gestione dei messaggi
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global fabbio_count
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    count = sum(text.count(alias) for alias in ["fabbio", "fbb", "fabbiotron", "fabbiocop"])

    if count > 0:
        if is_bot_sleeping():
            await update.message.reply_text(
                "😴 Fabbio dorme tra le 00:40 e le 08:00. I 'Fabbio' scritti ora non saranno conteggiati. Zzz..."
            )
            return

        fabbio_count += count
        save_counter(fabbio_count)

        user_id = str(update.effective_user.id)
        username = update.effective_user.username or update.effective_user.first_name or "Sconosciuto"

        user_data = json.loads(r.get(f"user:{user_id}") or '{"count": 0, "username": "", "unlocked": []}')
        previous_count = user_data["count"]
        user_data["count"] += count
        user_data["username"] = username
        unlocked = set(user_data.get("unlocked", []))

        for threshold, message in ACHIEVEMENTS:
            if previous_count < threshold <= user_data["count"] and str(threshold) not in unlocked:
                await update.message.reply_text(message, parse_mode="Markdown")
                unlocked.add(str(threshold))

        user_data["unlocked"] = list(unlocked)
        r.set(f"user:{user_id}", json.dumps(user_data))

        if fabbio_count % 1000 == 0:
            await update.message.reply_text(f"🎉 Abbiamo scritto {fabbio_count} volte Fabbio. Fabbio ti amiamo.")

# 📈 Comando /stats
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_keys = r.keys("user:*")
    users = []

    for key in all_keys:
        data = json.loads(r.get(key))
        users.append((data["username"], data["count"]))

    top_users = sorted(users, key=lambda x: x[1], reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    leaderboard = "\n".join(
        [f"{medals[i]} {u[0]}: {u[1]} volte" for i, u in enumerate(top_users)]
    )

    await update.message.reply_text(
        f"📊 Abbiamo scritto {fabbio_count} volte Fabbio. Fabbio ti amiamo.\n\n🏆 Classifica:\n{leaderboard}"
    )

# 📬 Messaggio all'avvio
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

    async def after_startup(app):
        await send_startup_message()

    app = Application.builder().token(BOT_TOKEN).post_init(after_startup).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("stats", show_stats))

    logging.info("✅ Bot avviato")
    app.run_polling()

if __name__ == "__main__":
    main()
