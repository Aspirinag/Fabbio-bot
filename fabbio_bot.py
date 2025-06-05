
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

fabbio_count = int(r.get("fabbio_count") or 0)

# === HANDLERS ===

# ... (gli handler verranno completati nei messaggi successivi se necessario per superare il limite di caratteri)
