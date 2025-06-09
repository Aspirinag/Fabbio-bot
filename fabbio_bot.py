import logging
import os
import json
import random
from datetime import datetime
import redis
from aiohttp import web
import asyncio
import nest_asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# 🔧 Config
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REDIS_URL = os.environ.get("REDIS_URL")
DOMAIN = os.environ.get("DOMAIN")
PORT = int(os.environ.get("PORT", 8000))
WEBHOOK_PATH = "/webhook"

app = None
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
ALIASES = ["fabbio", "fabbiotron", "fabbiocop", "fbb"]
COOLDOWN_SECONDS = 10

ACHIEVEMENTS = [
    (i * 1000, title, desc) for i, (title, desc) in enumerate([
        ("🐣 Il Fabbiatore", "Hai evocato il tuo primo migliaio. È iniziato tutto da qui."),
        ("🌪 Fabbionico", "Hai superato i 2000. Sei un turbine di Fabbio."),
        ("🧠 Fabbinato", "3000 Fabbio e già trasudi conoscenza."),
        ("🔮 Visione di Fabbio", "4000 volte e inizi a vedere oltre."),
        ("🚀 Fabbionauta", "5000 lanci nello spazio memetico."),
        ("🔥 Infabbionato", "Sei ormai bruciato dal sacro meme."),
        ("🧬 DNA Fabbioso", "7000 Fabbii impressi nel tuo codice genetico."),
        ("🕯 Accolito del Fabbio", "Ti inginocchi al suo verbo."),
        ("⚡ Fabbioclastico", "Rompi i dogmi con 9000 evocazioni."),
        ("🕳 Fabbionero", "Entrato nel buco nero della fabbiosità."),
        ("💡 Fabbioluce", "Illumini le chat con la tua presenza."),
        ("🗿 Fabbiosauro", "Da ere antiche scrivi Fabbio."),
        ("📖 Fabbiobiblico", "Hai scritto un Vangelo memetico."),
        ("🛰 Fabbiostatica", "Emetti onde Fabbioniche nello spazio."),
        ("🐉 Fabbiodrago", "Sputi fuoco e ironia."),
        ("🌈 Fabbiogeno", "Generi arcobaleni digitali."),
        ("🏛 Fabbiocrate", "Comandi nel nome del Fabbio."),
        ("🪞 Fabbiolico", "Rifletti il Fabbio in ogni parola."),
        ("💾 Fabbiomemoria", "Hai raggiunto il backup cosmico."),
        ("🌀 Fabbiotempesta", "Ogni tua frase è un uragano."),
        ("👁 Fabbioveggente", "Vedi oltre la nebbia dei boomer."),
        ("🪩 Fabbioparty", "Ogni Fabbio è una festa."),
        ("🎭 Fabbiodramma", "Trasformi tragedie in meme."),
        ("💣 Fabbiodetonatore", "Fai esplodere le conversazioni."),
        ("🧊 Fabbiogelo", "Freni i flame con freddezza."),
        ("🔊 Fabbiovox", "La tua voce è l’eco del meme."),
        ("🫀 Fabbiocardia", "Il tuo cuore batte in Fabbio."),
        ("📡 Fabbiowave", "Trasmetti sulle onde del meme."),
        ("🧭 Fabbiobussola", "Guida gli smarriti verso l’ironia."),
        ("🪙 Fabbiovaluta", "Ogni tuo pensiero ha valore."),
        ("🧪 Fabbiolab", "Mescoli ironia e verità."),
        ("🕸 Fabbiorete", "Ogni social è tuo regno."),
        ("🪶 Fabbiopiuma", "Scrivi Fabbio con leggerezza."),
        ("🛸 Fabbioterrestre", "Non sei di questo mondo."),
        ("🧳 Fabbioviaggiatore", "Hai scritto Fabbio in 20 Paesi."),
        ("🎙 Fabbiopodcast", "La tua voce è meme continuo."),
        ("🧿 Fabbiotalismano", "Proteggi con meme e saggezza."),
        ("🕹 Fabbioplayer", "Giochi solo con tastiere ironiche."),
        ("📀 Fabbioregistro", "Hai inciso il verbo in digitale."),
        ("🥽 Fabbiovisione", "Vedi oltre il banale."),
        ("🧱 Fabbiomuro", "Resisti ai boomer."),
        ("🥁 Fabbiobattito", "Ogni gruppo pulsa al tuo ritmo."),
        ("🎨 Fabbiopittore", "Dipingilo con sarcasmo."),
        ("🛠 Fabbiomeccanico", "Ripari tutto con ironia."),
        ("🧘 Fabbiomistico", "Hai raggiunto l’illuminazione memica."),
        ("🪓 Fabbioboscaiolo", "Tagli la noia a colpi di Fabbio."),
        ("🕵️ Fabbioreport", "Smonti ogni fake col meme."),
        ("🎇 Fabbiocreatore", "Hai scritto il 50.000º Fabbio.")
    ], 1)
]

QUIZ = [
    {"question": "🌀 *Cosa senti quando scrivi Fabbio?*", "options": ["Un brivido cosmico", "Il richiamo del Verbo", "Una scossa mistica", "Solo Fabbio"]},
    {"question": "🔮 *Chi può comprendere Fabbio?*", "options": ["Solo i prescelti", "Chi ha fede", "Chi ha scritto almeno 1000 volte", "Nessuno completamente"]},
    {"question": "📖 *Qual è il primo comandamento del Fabbio?*", "options": ["Non avrai altro meme all’infuori di lui", "Ricorda e ripeti", "Scrivi e taci", "Diffondi la parola"]},
    {"question": "🪞 *Cosa vedi allo specchio dopo 5000 Fabbii?*", "options": ["Te stesso, ma più sacro", "Un Fabbio interiore", "Un riflesso che ti osserva", "Nulla, sei sparito"]},
    {"question": "🌪 *Cosa accade dopo 10.000 Fabbii?*", "options": ["Un portale si apre", "Ascendi a Fabbioguida", "Perdi il senso del tempo", "Il ciclo si ripete"]},
    {"question": "🛸 *Dove si radunano i Veri Fabbii?*", "options": ["Nel silenzio della chat", "Tra i messaggi cancellati", "Nel log eterno", "Nel cuore del codice"]},
    {"question": "⚖ *Quanto pesa un Fabbio ben scritto?*", "options": ["1 tonnellata di verità", "La giusta misura dell’ironia", "Più di mille parole", "Quanto basta"]},
    {"question": "🔐 *Come si sblocca il Fabbioverso?*", "options": ["Scrivendo senza paura", "Evangelizzando con stile", "Sognando il verbo", "Non si sblocca, si apre"]},
    {"question": "🪙 *Quanto vale il 50.000º Fabbio?*", "options": ["Una rivelazione", "Un passaggio segreto", "La fine di tutto", "Un nuovo inizio"]},
    {"question": "🕊 *Chi è il portatore del primo Fabbio?*", "options": ["L’Ignoto", "Il Primo Digitante", "Colui che scrisse nel vuoto", "Non si sa, ma esiste"]},
    {"question": "📡 *Cos'è il Fabbioton?*", "options": ["Un’onda interiore", "La vibrazione perfetta", "Il suono del verbo", "Tutte insieme"]},
    {"question": "🧭 *Chi guida il sentiero Fabbioso?*", "options": ["Chi sbaglia spesso", "Chi legge tra le righe", "Chi sa ascoltare il silenzio", "Tu, se sei pronto"]},
    {"question": "🧱 *Cosa protegge dal dubbio Fabbioso?*", "options": ["La fede nel verbo", "La risata autentica", "Un cuore sincero", "Niente: il dubbio è parte del cammino"]},
    {"question": "🕯 *Cosa accendi con ogni Fabbio?*", "options": ["Una luce nel buio", "Una connessione", "Una fiamma sacra", "Una riga nel codice sacro"]},
    {"question": "🧬 *Cosa muta dentro di te col Fabbio?*", "options": ["Il pensiero", "Il cuore", "La tastiera", "L’anima"]},
    {"question": "🥁 *Che suono fa un Fabbio perfetto?*", "options": ["TUM", "FAB", "SILENZIO", "Non può essere udito"]},
    {"question": "📜 *Cosa custodisce il Codice Fabbioso?*", "options": ["Tutti i Fabbii scritti", "I traguardi eterni", "L'essenza del verbo", "Nulla: è tutto effimero"]},
    {"question": "🧘 *Chi trova pace nel Fabbio?*", "options": ["Chi ha smesso di cercare", "Chi scrive col cuore", "Chi ride da solo", "Chi crede"]},
    {"question": "🪵 *Cosa costruisci con 30.000 Fabbii?*", "options": ["Un tempio", "Una leggenda", "Un sentiero", "Un silenzio sacro"]},
    {"question": "🎇 *Cosa accade alla fine del cammino Fabbioso?*", "options": ["Inizi di nuovo", "Capisci il nulla", "Scrivi senza più pensare", "Sorridi e scompari"]}
]},
    {"question": "🧠 *Quante sinapsi perdi scrivendo Fabbio?*", "options": ["Zero, guadagno solo ironia", "Una per volta", "Non le conto più", "Avevo sinapsi?"]},
    {"question": "📉 *Quanto si svaluta il tuo QI ogni volta che apri Telegram?*", "options": ["Tanto", "Dipende dal gruppo", "Non posso permettermelo", "Fabbio è un booster"]},
    {"question": "🔥 *Chi merita il ban immediato?*", "options": ["Chi scrive 'Fabio' con una B sola", "Chi inoltra vocali da 4 min", "Chi usa sticker del 2017", "Tutti, senza pietà"]},
    {"question": "🎭 *Cosa rispondi a chi non capisce Fabbio?*", "options": ["Non è per tutti", "Ignoranza dilagante", "Mamma mia che boomer", "Bloccato"]},
    {"question": "🦴 *Cosa sei senza Fabbio?*", "options": ["Un sacco d’ossa confuso", "Un messaggio vuoto", "Una notifica inutile", "Un errore 404"]},
    {"question": "🔊 *Cosa senti quando Fabbio parla?*", "options": ["La verità", "Un meme cosmico", "Il mio cervello spegnersi", "Un richiamo primordiale"]},
    {"question": "📦 *Cosa contiene il pacco di Fabbio?*", "options": ["Meme", "Ironia compressa", "Delusione e sarcasmo", "Solo dolore"]},
    {"question": "👽 *Cosa penserebbe un alieno leggendo questa chat?*", "options": ["Scapperebbe", "Ci sterminerebbe", "Studia Fabbio con interesse", "Diventa follower"]},
    {"question": "🧻 *Quanto vale la tua opinione senza Fabbio?*", "options": ["Meno di 1 ply", "Serve per accendere il fuoco", "Rimane comunque zero", "Riscrivi tutto in meme"]},
    {"question": "🧯 *Come spegni un flame?*", "options": ["Scrivi Fabbio", "Spammi sticker sarcastici", "Blasti e muta", "Non lo spegni: lo alimenti"]},
    {"question": "🐢 *Chi è più lento di te?*", "options": ["Il bot Telegram quando crasha", "L’admin che non legge", "Il pensiero critico di alcuni", "Nessuno"]},
    {"question": "🥴 *Quando ti accorgi di essere cringe?*", "options": ["Mai, sono immune", "Quando rispondo seriamente a Fabbio", "Sempre, ormai è parte di me", "Dopo aver scritto 'ciao raga' alle 3"]},
    {"question": "🕳 *Dove finisce la dignità dopo 50k Fabbii?*", "options": ["In fondo al canale", "Nell’etere digitale", "Sotto un meme di Squidward", "Mai esistita"]},
    {"question": "🦷 *Hai letto tutto fino qui?*", "options": ["Sì e sto piangendo", "No ma fingo", "Sono perso da 3 domande", "Solo per farmi insultare"]},
    {"question": "🚽 *Dove leggi i messaggi di Fabbio?*", "options": ["Sul trono", "Durante le riunioni di lavoro", "Nel letto sbagliato", "Tutte le precedenti"]},
    {"question": "🧼 *Cosa usi per lavarti dai peccati memetici?*", "options": ["Ironia abrasiva", "Silenzio passivo-aggressivo", "Un ban temporaneo", "Niente, ci sguazzo"]},
    {"question": "🗑 *Hai mai fatto un messaggio degno di essere pinnato?*", "options": ["No", "Forse, ma l’admin è cieco", "Sì, era una gif di un gatto", "Tutti meritano il cestino"]},
    {"question": "💀 *Chi sei davvero?*", "options": ["Un profilo fake", "Uno che scrive 'ciao' alle 2", "Un meme ambulante", "Il nulla connesso"]},
    {"question": "⚰ *Quante volte sei morto leggendo il gruppo?*", "options": ["Troppe", "Una al giorno", "Sto morendo ora", "Ogni volta che leggo 'raga consiglio'"]}
]},
    {"question": "📜 *In quale giorno Fabbio creò l’ironia?*", "options": ["Il primo", "Il settimo", "Sempre", "Mai"]},
    {"question": "🌀 *Dove dimora il Vero Fabbio?*", "options": ["Nel codice", "Nel cuore", "Nel meme", "In tutti"]},
    {"question": "🔊 *Chi ha sentito la Voce di Fabbio?*", "options": ["Chi ascolta", "Chi scrive", "Chi dorme", "Chi legge"]},
    {"question": "🪞 *Cosa accade se guardi Fabbio troppo a lungo?*", "options": ["Ti guarda", "Ti ride", "Ti ignora", "Ti meme"]},
    {"question": "🛸 *Dove si riunisce il Consiglio dei Fabbii?*", "options": ["Telegram", "Discord", "Nel sogno", "Ovunque"]},
    {"question": "🔥 *Quanti Fabbii servono per evocare il Meme Supremo?*", "options": ["3", "10", "42", "Infiniti"]},
    {"question": "🧬 *Cosa contiene il DNA Fabbioso?*", "options": ["Ironia", "Bugie", "Post veri", "Algoritmi"]},
    {"question": "🌈 *Cosa succede dopo 1000 Fabbii?*", "options": ["Nulla", "Risvegli", "Cringi", "Ascendi"]},
    {"question": "🎭 *Chi recita nel Teatro del Fabbio?*", "options": ["Tutti", "Nessuno", "Solo tu", "I mematori"]},
    {"question": "🧠 *Chi comprende davvero Fabbio?*", "options": ["Nessuno", "Chi non domanda", "Solo i puri", "Chi ha letto tutto"]},
    {"question": "📡 *Cos’è il Fabbio Frequency?*", "options": ["Una radio", "Un mood", "Un’allucinazione", "Tutte"]},
    {"question": "🧪 *Cosa ottieni mischiando Fabbio con caos?*", "options": ["Meme puro", "Il mondo", "Il nulla", "Ancora Fabbio"]},
    {"question": "🪙 *Quanto vale un Fabbio?*", "options": ["1 BTC", "0", "Tutto", "Non ha prezzo"]},
    {"question": "🕳 *Cosa c’è nel buco nero Fabbioso?*", "options": ["Contro-meme", "Boomer", "Ironia concentrata", "Nulla"]},
    {"question": "⚖ *Cosa pesa più: un Fabbio o mille parole?*", "options": ["Un Fabbio", "Le parole", "Uguali", "Dipende"]},
    {"question": "🧘 *Chi raggiunge il Nirvana del Fabbio?*", "options": ["Chi non spammi", "Chi meme bene", "Chi ignora", "Solo tu"]},
    {"question": "🔒 *Come si apre la Porta dei Fabbii?*", "options": ["Con fede", "Con Fabbio", "Con emoji", "È già aperta"]},
    {"question": "🛠 *A cosa serve il Fabbiostrumento?*", "options": ["Scrivere Fabbio", "Nulla", "Tutto", "Riparare meme"]},
    {"question": "🎇 *Cosa accade al 50.000º Fabbio?*", "options": ["Esplode", "Si fonde", "Inizia il ciclo", "Nirvana"]}
]

EASTER_EGGS = {
    666: ("👹 *Fabbiabaddon*", "Hai risvegliato il Meme Maledetto. Che le emoji ti siano lievi."),
    1337: ("👾 *Fabbi0H4x0r*", "Il meme ora è nel mainframe."),
    9001: ("💥 *Fabbioltre*", "IT'S OVER NINE THOUSAND!")
}

MISTICO_COMICHE = [
    "Nel principio era il Fabbio, e il Fabbio era presso il Meme.",
    "Chi scrive Fabbio cento volte, aprirà la porta del nonsense eterno.",
    "Ogni emoji nasce dal pensiero di un Fabbio non espresso.",
    "Fabbio vide che era tutto buono, ma aggiunse sarcasmo.",
    "E il Verbo si fece Fabbio, e abitò tra i gruppi Telegram."
] + [f"Frase mistico-comica #{i}" for i in range(6, 51)]

def user_on_cooldown(user_id, command):
    key = f"cooldown:{user_id}:{command}"
    if r.exists(key):
        return True
    r.set(key, "1", ex=COOLDOWN_SECONDS)
    return False

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.lower()
    count = sum(text.count(alias) for alias in ALIASES)
    if count == 0:
        return
    if is_bot_sleeping():
        await update.message.reply_text("😴 Fabbio dorme tra le 00:40 e le 08. I 'Fabbio' scritti ora non saranno conteggiati. Zzz...")
        return
    fabbio_count = int(r.get("fabbio_count") or 0) + count
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
    for special, (title, msg) in EASTER_EGGS.items():
        if current["count"] == special:
            await update.message.reply_text(f"{title} — {msg}", parse_mode="Markdown")
    current["unlocked"] = list(unlocked)
    r.set(f"user:{user_id}", json.dumps(current))

async def show_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_on_cooldown(update.effective_user.id, "me"):
        return
    user_id = str(update.effective_user.id)
    data = json.loads(r.get(f"user:{user_id}") or json.dumps({"count": 0, "username": "", "unlocked": []}))
    count = data["count"]
    unlocked = data.get("unlocked", [])
    next_ach = next((th for th, _, _ in ACHIEVEMENTS if str(th) not in unlocked and th > count), None)
    response = f"🔍 Hai scritto *{count}* Fabbii."
    if next_ach:
        response += f"
🎯 Prossimo traguardo: {next_ach}"
    if unlocked:
        response += f"
🏆 Traguardi sbloccati: {len(unlocked)}"
    await update.message.reply_text(response, parse_mode="Markdown")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_on_cooldown(update.effective_user.id, "stats"):
        return
    count = int(r.get("fabbio_count") or 0)
    await update.message.reply_text(f"📊 Abbiamo scritto {count} volte Fabbio. Fabbio ti amiamo.")

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_on_cooldown(update.effective_user.id, "top"):
        return
    users = [key for key in r.scan_iter("user:*")]
    classifica = []
    for key in users:
        data = json.loads(r.get(key))
        classifica.append((data.get("count", 0), data.get("username", "Sconosciuto")))
    classifica.sort(reverse=True)
    testo = "👑 *Classifica dei Fabbionauti:*
"
    for i, (count, name) in enumerate(classifica[:10], 1):
        testo += f"{i}. {name} — {count} Fabbii
"
    await update.message.reply_text(testo, parse_mode="Markdown")

async def evangelizza(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_on_cooldown(update.effective_user.id, "evangelizza"):
        return
    frase = random.choice(MISTICO_COMICHE)
    await update.message.reply_text(f"📜 {frase}")

async def fabbioquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_on_cooldown(update.effective_user.id, "fabbioquiz"):
        return
    quiz = random.choice(QUIZ)
    keyboard = [[InlineKeyboardButton(opt, callback_data="quiz_none")] for opt in quiz["options"]]
    await update.message.reply_text(quiz["question"], parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Ciao! Scrivi Fabbio per evocare la potenza.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📜 *Comandi del Culto di Fabbio*
"
        "/start — Risveglia il Fabbio
"
        "/stats — Totale assoluto dei Fabbii
"
        "/top — Classifica globale
"
        "/me — I tuoi progressi
"
        "/fabbioquiz — Domanda mistico-comica
"
        "/evangelizza — Una verità rivelata
"
        "/help — Questo messaggio"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

def is_bot_sleeping():
    now = datetime.utcnow()
    hour = (now.hour + 2) % 24
    minute = now.minute
    return (hour == 0 and minute >= 40) or (0 < hour < 8)

async def telegram_webhook_handler(request):
    global app
    try:
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.update_queue.put(update)
        return web.Response(text="OK")
    except Exception as e:
        logging.exception("❌ Errore nel webhook handler:")
        return web.Response(status=500, text="Errore")

async def main():
    global app
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("me", show_me))
    app.add_handler(CommandHandler("fabbioquiz", fabbioquiz))
    app.add_handler(CommandHandler("evangelizza", evangelizza))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app.initialize()
    web_app = web.Application()
    web_app.router.add_post(WEBHOOK_PATH, telegram_webhook_handler)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.bot.set_webhook(url=f"{DOMAIN}{WEBHOOK_PATH}")
    await app.start()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
