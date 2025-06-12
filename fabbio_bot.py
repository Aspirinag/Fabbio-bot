import logging
import os
import json
import random
from datetime import datetime, time
import redis
from aiohttp import web
import asyncio
import nest_asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# 🔧 Config
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REDIS_URL = os.environ.get("REDIS_URL")
DOMAIN = os.environ.get("DOMAIN")
PORT = int(os.environ.get("PORT", 8000))
WEBHOOK_PATH = "/webhook"
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
ADMIN_IDS = [int(ADMIN_CHAT_ID)] if ADMIN_CHAT_ID else []

app = None
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
ALIASES = ["fabbio", "fabbiotron", "fabbiocop", "fbb"]

# 🏆 Achievement personalizzati
ACHIEVEMENTS = [
    ((i+1) * 100, title, desc) for i, (title, desc) in enumerate([
        ("👶 Neofabbio", "Hai raggiunto 100 evocazioni. Il tuo viaggio inizia ora."),
        ("✨ Risvegliato", "200 Fabbii scritti: percepisci il segnale."),
        ("🔀 Discepolo della Fabbiosofia", "300 Fabbii: studi i testi antichi."),
        ("📱 Portatore di Fabbio", "400 Fabbii: diffondi la parola in ogni chat."),
        ("🐮 Mistico del Meme", "500 Fabbii: vedi oltre le emoji."),
        ("🤠 Evocatore di Caos", "600 Fabbii: l'entropia ti segue."),
        ("🌌 Oracolo di Fabbiolandia", "700 Fabbii: le visioni iniziano."),
        ("📣 Trombettiere del Fabbio", "800 Fabbii: annunci la verità."),
        ("🧄 Cavalcatore del Meme", "900 Fabbii: domini l'onda dell'assurdo."),
        ("🏆 Campione del Fabbio", "1000 Fabbii: entri nella leggenda."),
        ("🔮 Guardiano del Fabbio", "1100 Fabbii: proteggi il verbo."),
        ("💰 Archivista del Fabbio", "1200 Fabbii: conosci ogni incarnazione."),
        ("🔔 Meditante del Fabbiadosso", "1300 Fabbii: respiri ironia."),
        ("🗓️ Scriba della Fabbiostoria", "1400 Fabbii: narri l'evoluzione."),
        ("🚀 Esploratore del Fabbiospazio", "1500 Fabbii: spingi oltre il cosmo."),
        ("👑 Fabbio Supremo", "1600 Fabbii: regni sul nonsense."),
        ("🤖 Fabbio Robot", "1700 Fabbii: scrivi per riflesso sacro."),
        ("💡 Illuminato dal Fabbio", "1800 Fabbii: capisci tutto, e nulla."),
        ("🚁 Fabbionauta", "1900 Fabbii: navighi nel vuoto sacro."),
        ("🌟 Fabbio", "2000 Fabbii: sei uno col Fabbio.")
    ])
]

QUIZ_QUESTIONS = [
    {
        "question": "Chi è Fabbio?",
        "options": ["Un meme", "Un salvatore", "Una leggenda", "Tutte le precedenti"],
        "answer": 3
    },
    {
        "question": "Cosa si ottiene evocando Fabbio?",
        "options": ["Pace", "Caos", "Luce eterna", "Dipende dal giorno"],
        "answer": 3
    },
    {
        "question": "Dove abita Fabbio?",
        "options": ["Nel codice", "Nel cuore degli utenti", "Nel cloud", "Ovunque"],
        "answer": 3
    }
]

# 😴 Funzione sonno
def is_bot_sleeping():
    now = datetime.now().time()
    return time(0, 40) <= now < time(8, 0)

async def blocked_if_sleeping(update: Update):
    if is_bot_sleeping():
        await update.message.reply_text("😴 Sto dormendo. Riprova dalle 8 in poi.")
        return True
    return False

# ✅ Funzione corretta show_stats
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    key = f"user:{user_id}"
    data = r.get(key)

    if not data:
        await update.message.reply_text("🙈 Nessuna evocazione trovata per te.")
        return

    user_data = json.loads(data)
    count = user_data.get("count", 0)
    username = user_data.get("username") or update.effective_user.first_name

    total_key = "global:total"
    total_count = r.get(total_key)
    if total_count is None:
        total_count = 19752
        r.set(total_key, total_count)
    else:
        total_count = int(total_count)

    reply = (
        f"📊 Statistiche di {username}\n"
        f"🔢 Evocazioni personali: {count}\n"
        f"🌍 Evocazioni totali: {total_count}"
    )

    await update.message.reply_text(reply)

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    key = f"user:{user_id}"
    data = r.get(key)

    if not data:
        await update.message.reply_text("🙈 Nessuna evocazione trovata per te.")
        return

    user_data = json.loads(data)
    count = user_data.get("count", 0)
    username = user_data.get("username") or update.effective_user.first_name

    best_title = None
    for threshold, title, _ in reversed(ACHIEVEMENTS):
        if count >= threshold:
            best_title = title
            break

    reply = f"👤 Nome: {username}\n📈 Fabbii evocati: {count}"
    if best_title:
        reply += f"\n🏅 Achievement: {best_title}"

    await update.message.reply_text(reply)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ Comandi disponibili: /stats, /top, /me, /fabbioquiz, /help")

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = random.choice(QUIZ_QUESTIONS)
    keyboard = [
        [InlineKeyboardButton(opt, callback_data=f"quiz|{i}|{question['answer']}")]
        for i, opt in enumerate(question["options"])
    ]
    await update.message.reply_text(
        question["question"],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    selected = int(parts[1])
    correct = int(parts[2])
    if selected == correct:
        await query.edit_message_text("✅ Corretto! Sei un vero conoscitore di Fabbio.")
    else:
        await query.edit_message_text("❌ Risposta sbagliata. Il Fabbio ti osserva.")

async def top(update: Update, context: ContextTypes
