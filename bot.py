import sqlite3
import os
import requests  # 🔥 NOVO
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ===== CONFIG =====
TOKEN = "SEU_TOKEN_AQUI"  # ⚠️ TROQUE ISSO IMEDIATAMENTE

GROUP_ID = -1002312326448
ADMINS = [7966376623]

SUPORTE = "https://t.me/teus_67"

PAYPAL = "susanesantos4@gmail.com"
CASHAPP = "$BassBaddict"

# ===== PAYPAL API (NOVO) =====
PAYPAL_CLIENT_ID = "AVgKcL-ogJwwEfzeCko0IjaZrpbvSXs72gKlHSdI8-JsD30I_WU05ga2Ti2Z_lAkfh9gevq9qPxJTrGY"
PAYPAL_SECRET = "EHc2ffBa76xUNLFpyd6LDoxtVOg6EyXJdORKZzNMhY6x6SXivEy95Ul5laGS6Pg9R--3Y2agt8bUrr-J"
PAYPAL_API = "https://api-m.sandbox.paypal.com"

PLANOS = {
    "1m": (30, "1 Month — $25"),
    "3m": (90, "3 Months — $55"),
    "6m": (180, "6 Months — $85"),
    "12m": (365, "🔥 BEST VALUE — 1 Year $120")
}

# ===== DATABASE =====
conn = sqlite3.connect("db.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, expire_date TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS all_users (user_id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS avisos (user_id INTEGER, tipo TEXT)")

# 🔥 NOVO
cursor.execute("""
CREATE TABLE IF NOT EXISTS payments (
    order_id TEXT PRIMARY KEY,
    user_id INTEGER,
    plano TEXT,
    status TEXT
)
""")

conn.commit()

def salvar_usuario(user_id):
    cursor.execute("INSERT OR IGNORE INTO all_users VALUES (?)", (user_id,))
    conn.commit()

def get_user(user_id):
    cursor.execute("SELECT expire_date FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone()

# ===== PAYPAL TOKEN =====
def get_paypal_token():
    r = requests.post(
        f"{PAYPAL_API}/v1/oauth2/token",
        auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET),
        data={"grant_type": "client_credentials"}
    )
    return r.json()["access_token"]

# ===== CRIAR PAGAMENTO =====
def criar_pagamento_paypal(user_id, plano):
    valores = {
        "1m": "25",
        "3m": "55",
        "6m": "85",
        "12m": "120"
    }

    token = get_paypal_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    data = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "USD",
                "value": valores[plano]
            }
        }]
    }

    r = requests.post(f"{PAYPAL_API}/v2/checkout/orders", json=data, headers=headers)
    res = r.json()

    order_id = res["id"]

    approval_url = next(
        link["href"] for link in res["links"] if link["rel"] == "approve"
    )

    cursor.execute(
        "INSERT INTO payments VALUES (?, ?, ?, ?)",
        (order_id, user_id, plano, "pending")
    )
    conn.commit()

    return approval_url

async def safe_answer(query):
    try:
        await query.answer()
    except:
        pass

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    salvar_usuario(update.message.from_user.id)

    user = get_user(update.message.from_user.id)

    if user:
        text = "✅ You already have an active subscription.\n\nUse the options below."
        keyboard = [
            [InlineKeyboardButton("🔄 Renew Subscription", callback_data="unlock")],
            [InlineKeyboardButton("📅 My Subscription", callback_data="sub")],
            [InlineKeyboardButton("💬 Support", url=SUPORTE)]
        ]
    else:
        text = """Hi 😊

Welcome! The VIP Farts Wardrobe group is a paid group with full access to exclusive content. We currently have over 40,000 videos and more than 100 models, all well organized and constantly updated.

You’ll get full access to everything, and you can also make requests if you’re looking for something specific 👀

We focus on keeping the group active, organized, and always bringing new content.

Let me know if you’d like to join and I’ll guide you through everything 👍"""

        keyboard = [
            [InlineKeyboardButton("🔓 Become a Member", callback_data="unlock")],
            [InlineKeyboardButton("💬 Support", url=SUPORTE)]
        ]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ===== PLANOS =====
async def unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)

    salvar_usuario(query.from_user.id)

    keyboard = []
    for key, value in PLANOS.items():
        keyboard.append([InlineKeyboardButton(value[1], callback_data=f"plan_{key}")])

    await query.message.reply_text("Choose your plan 👇", reply_markup=InlineKeyboardMarkup(keyboard))

# ===== ESCOLHA =====
async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)

    plano = query.data.split("_")[1]
    context.user_data["plano"] = plano

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 PayPal (Auto)", callback_data=f"paypal_{plano}")],
        [InlineKeyboardButton("💵 CashApp (Manual)", callback_data=f"cash_{plano}")]
    ])

    await query.message.reply_text(
        f"Selected:\n{PLANOS[plano][1]}\n\nChoose payment method 👇",
        reply_markup=keyboard
    )

# ===== PAYPAL =====
async def paypal_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)

    plano = query.data.split("_")[1]

    link = criar_pagamento_paypal(query.from_user.id, plano)

    await query.message.reply_text(f"""
💳 Pay with PayPal:

{link}

⚡ Access will be granted automatically after payment.
""")

# ===== CASH =====
async def cash_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)

    plano = query.data.split("_")[1]

    await query.message.reply_text(f"""
💵 CashApp

Send to:
{CASHAPP}

Selected:
{PLANOS[plano][1]}

After payment click below 👇
""",
    reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Send Proof", callback_data="proof")]
    ]))

# ===== RESTO DO CÓDIGO (INALTERADO) =====
# (tudo continua igual daqui pra baixo)