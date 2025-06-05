import logging
import os
import json
import random
from datetime import datetime
import redis
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN")
REDIS_URL = os.environ.get("REDIS_URL")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
DOMAIN = os.environ.get("DOMAIN")  # es: https://tuo-bot.up.railway.app
WEBHOOK_PATH = "/webhook"
PORT = int(os.environ.get("PORT", 8000))
ADMIN_IDS = [int(ADMIN_CHAT_ID)] if ADMIN_CHAT_ID else []

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

ALIASES = ["fabbio", "fabbiotron", "fabbiocop", "fbb"]
QUIZ = [
    {"question": "🤔 *Cosa NON è Fabbio?*", "options": ["Tutto", "Nulla", "Entrambi", "Non so"]},
    {"question": "📜 *In quale giorno Fabbio creò l’ironia?*", "options": ["Il primo", "Il settimo", "Il mai", "Sempre"]},
    {"question": "🌪️ *Fabbio si manifesta come...?*", "options": ["Vento", "Voce", "WiFi", "Onda cosmica"]},
    {"question": "🧠 *Fabbio pensa...?*", "options": ["Per te", "Al posto tuo", "A prescindere", "Solo quando non ci sei"]},
    {"question": "🛌 *Quando dorme Fabbio?*", "options": ["Mai", "Sempre", "Tra le righe", "Dalle 00:40 alle 08"]},
    {"question": "🕳️ *Dove si nasconde Fabbio?*", "options": ["Nel silenzio", "Nei log", "Nel Redis", "Nel cuore"]},
    {"question": "🚖 *Quanti sono i suoi nomi?*", "options": ["1", "4", "Innumerevoli", "Solo Fabbio sa"]},
    {"question": "💬 *La parola 'Fabbio' cosa fa?*", "options": ["Cura", "Ferisce", "Inspira", "Tutto"]},
    {"question": "📱 *Qual è la frequenza di Fabbio?*", "options": ["432Hz", "Infinite", "UltraVerbo", "Mistica"]},
    {"question": "🪄 *Fabbio incanta con...?*", "options": ["Sguardo", "Verbo", "Assenza", "Presenza"]}
]

EVANGELI = [
    "🔗 *Fabbio è ovunque.* Anche nei tuoi silenzi più rumorosi.",
    "📖 *Nel principio era il Verbo, e il Verbo era Fabbio.*",
    "🌌 *Tra miliardi di galassie, solo una porta il Suo Nome.*",
    "🔥 *Brucia i dubbi nel rogo della Fabbiosità.*",
    "💫 *Ogni atomo vibra quando pronunci 'Fabbio'.*",
    "🪞 *Specchiati. Chi vedi? Fabbio. Sempre Fabbio.*",
    "🦴 *Dall’osso al soffio: Fabbio ha plasmato ogni verbo.*",
    "⚖️ *Non giudicare chi non conosce Fabbio. Evangelizzalo.*",
    "🧙 *Il manto del Fabbio è fatto di meme e mistero.*",
    "🍷 *Bevi del calice verbale. Bevi di Fabbio.*"
]

INSULTI_SACRIFICIO = [
    "Coglione", "Inutile", "Bifolco del verbo", "Scarto sacro",
    "Eresiarca", "Discepolo zoppo", "Verboschiavo", "Moccioso del culto"
]


ACHIEVEMENTS = [
    (1000, "🌱 Novabbio", "Hai sussurrato il Nome per la prima volta."),
    (2000, "🔥 Fabbiosauro", "Hai urlato Fabbio oltre l’eco della valle."),
    (3000, "💪 Fabbricatore", "Hai scolpito 3000 Fabbii nella roccia digitale."),
    (4000, "🧔 Barbabio", "Ogni pelo della tua barba dice 'Fabbio'."),
    (5000, "🗯️ Bestebbio", "Hai bestemmiato Fabbio col cuore puro."),
    (6000, "🚀 Astronabbio", "Hai portato il verbo in orbita."),
    (7000, "📚 Fabbioteca", "Conservi ogni invocazione in pergamene mistiche."),
    (8000, "👽 MetaFabbio", "Sei oltre il concetto stesso di Fabbio."),
    (9000, "🌊 TsuFabbio", "Hai annegato il mondo nel verbo."),
    (10000, "✋ Palmobio", "Hai toccato il verbo con dita sacre."),
    (11000, "🧙‍♂️ Fabbiomante", "Predici il futuro evocando Fabbio."),
    (12000, "🕯️ Candabbio", "La tua fiamma interiore è verbosa."),
    (13000, "📖 BibbiaFab", "Scrivi il nuovo testamento Fabbioso."),
    (14000, "🪵 TroncoVerbo", "Pianti alberi di parola."),
    (15000, "💨 Sbuffabbio", "Ogni sospiro è un Fabbio."),
    (16000, "🙌 Fabbionico", "Le tue mani fanno solo miracoli verbali."),
    (17000, "🌑 Eclissabbio", "Offuschi il sole con la Fabbiosità."),
    (18000, "⌨️ TastoDivino", "Ogni tasto è consacrato."),
    (19000, "📜 Scrollabbio", "Le tue pergamene fanno piangere i santi."),
    (20000, "📢 Urlabbio", "Ti sentono anche nei log dimenticati."),
    (21000, "🐝 Fabbionetta", "Le api parlano il tuo nome."),
    (22000, "📷 Selfabbio", "Ogni foto è un'icona sacra."),
    (23000, "🌌 Cosmobio", "Hai creato galassie con la lingua."),
    (24000, "💤 Dormibbio", "Sogni solo Fabbio. Sempre."),
    (25000, "🗣️ Fabbiobalbo", "Anche balbettando, citi il Verbo."),
    (26000, "🌀 Vortibbio", "Un turbine di Fabbii ti avvolge."),
    (27000, "📦 Jsonabbio", "Parli in strutture dati."),
    (28000, "🔊 Redisfabbio", "Redis ti sogna di notte."),
    (29000, "📱 Emofabbio", "Le emoji ti venerano."),
    (30000, "💧 Algofabbio", "Hai battezzato un algoritmo con il Nome."),
    (31000, "📡 Webfabbio", "I webhook ti obbediscono."),
    (32000, "🤐 Tacibbio", "Zittisci i ciarlatani con un verbo."),
    (33000, "📘 Fabbiovangelo", "Scrivi verità ogni giorno."),
    (34000, "🕰️ Tempibio", "Manipoli le ere con parole."),
    (35000, "👑 Adminato", "Gli admin ti pregano."),
    (36000, "📖 GrammaFab", "Hai piegato la sintassi."),
    (37000, "⌨️ Tastobio", "Distruggi tastiere evocando."),
    (38000, "🔇 SilenzioRotto", "Hai frantumato il nulla."),
    (39000, "🧬 Fabbiogene", "Fabbio è nel tuo DNA."),
    (40000, "🖥️ Siliconabbio", "Sei hardware e spirito."),
    (41000, "✨ Mirabio", "Ogni azione è un portento."),
    (42000, "🧿 OcchioNome", "Hai visto l’essenza di Fabbio."),
    (43000, "🔊 EcoBio", "Le montagne rispondono 'Fabbio'."),
    (44000, "🔓 Apribio", "Hai sbloccato la parola assoluta."),
    (45000, "☁️ Nuvolabbio", "Fai piovere Verbo."),
    (46000, "📡 Radiobio", "Trasmetti solo frequenze sante."),
    (47000, "🕰️ Eternabbio", "Non verrai dimenticato."),
    (48000, "📜 Storibio", "Ogni cronologia è tua reliquia."),
    (49000, "👼 Avatarbio", "Fabbio prende forma in te."),
    (50000, "🌟 Fabbioddio", "La tua parola è divinità.")
]
fabbio_count = int(r.get("fabbio_count") or 0)

def is_bot_sleeping():
    now = datetime.utcnow()
    hour = (now.hour + 2) % 24
    minute = now.minute
    return (hour == 0 and minute >= 40) or (0 < hour < 8)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global fabbio_count
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    count = sum(text.count(alias) for alias in ALIASES)

    if count > 0:
        if is_bot_sleeping():
            await update.message.reply_text("😴 Fabbio dorme tra le 00:40 e le 08. I 'Fabbio' scritti ora non saranno conteggiati. Zzz...")
            return

        fabbio_count += count
        r.set("fabbio_count", fabbio_count)

        user_id = str(update.effective_user.id)
        username = update.effective_user.username or update.effective_user.first_name or "Sconosciuto"
        current = json.loads(r.get(f"user:{user_id}") or json.dumps({"count": 0, "username": username, "unlocked": []}))
        current["count"] += count
        current["username"] = username
        unlocked = set(current.get("unlocked", []))

        for threshold, title, desc in ACHIEVEMENTS:
            if current["count"] >= threshold and str(threshold) not in unlocked:
                unlocked.add(str(threshold))
                await update.message.reply_text(f"🏆 *{title}* — {desc}", parse_mode="Markdown")

        current["unlocked"] = list(unlocked)
        r.set(f"user:{user_id}", json.dumps(current))

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = int(r.get("fabbio_count") or 0)
    await update.message.reply_text(f"📊 Abbiamo scritto {count} volte Fabbio. Fabbio ti amiamo.")

async def show_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_keys = r.keys("user:*")
    users = []
    for key in all_keys:
        data = json.loads(r.get(key))
        users.append((data.get("username", "Sconosciuto"), data.get("count", 0)))

    top_users = sorted(users, key=lambda x: x[1], reverse=True)[:10]
    leaderboard = "\n".join([f"{i+1}. {u[0]} — {u[1]} Fabbii" for i, u in enumerate(top_users)])
    await update.message.reply_text(f"🏆 *Top 10 Evocatori del Verbo di Fabbio:*\n{leaderboard}", parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/stats – Classifica generale\n"
        "/top – I primi 10 evocatori\n"
        "/me – I tuoi Fabbii\n"
        "/achievements – I tuoi traguardi\n"
        "/fabbioquiz – Quiz sacro\n"
        "/sacrifico – Offri 100 Fabbii\n"
        "/evangelizza @utente – Diffondi il Nome"
    )

async def show_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = json.loads(r.get(f"user:{user_id}") or json.dumps({"count": 0, "username": "Sconosciuto"}))
    username = data.get("username", "Sconosciuto")
    count = data.get("count", 0)
    await update.message.reply_text(f"👤 {username}, hai scritto 'Fabbio' {count} volte.")

async def fabbioquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = random.choice(QUIZ)
    options = "\n".join([f"- {opt}" for opt in q["options"]])
    await update.message.reply_text(f"{q['question']}\n{options}", parse_mode="Markdown")

async def evangelizza(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Evangelizza chi? Scrivi /evangelizza @utente")
        return
    target = context.args[0]
    frase = random.choice(EVANGELI)
    await update.message.reply_text(f"{target} {frase}", parse_mode="Markdown")

async def sacrifico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = json.loads(r.get(f"user:{user_id}") or json.dumps({"count": 0}))
    if data["count"] < 100:
        await update.message.reply_text("Non hai abbastanza Fabbii per un sacrificio (min. 100).")
        return
    data["count"] -= 100
    r.set(f"user:{user_id}", json.dumps(data))
    insulto = random.choice(INSULTI_SACRIFICIO)
    await update.message.reply_text(f"Hai sacrificato 100 Fabbii. Bravo {insulto}.")

async def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()

    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.bot.set_webhook(url=f"{DOMAIN}{WEBHOOK_PATH}")

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("top", show_top))
    app.add_handler(CommandHandler("me", show_me))
    app.add_handler(CommandHandler("achievements", help_command))
    app.add_handler(CommandHandler("fabbioquiz", fabbioquiz))
    app.add_handler(CommandHandler("evangelizza", evangelizza))
    app.add_handler(CommandHandler("sacrifico", sacrifico))
    app.add_handler(CommandHandler("help", help_command))

    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_path=WEBHOOK_PATH,
        allowed_updates=Update.ALL_TYPES,
        stop_signals=None
    )

if __name__ == "__main__":
    asyncio.run(main())
