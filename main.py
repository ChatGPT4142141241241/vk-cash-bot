import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
import time
import random
import json
import os
import requests

API_TOKEN = '8135081615:AAFHaG7cgRaNlBAAEk_ALEP0-wHYzOniYbU'
WEBHOOK_URL = 'https://vk-cash-bot.onrender.com'  # твой актуальный URL
ADMIN_ID = 6180147473
YOOMONEY_WALLET = "4100119077541618"

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_states = {}
first_spin_done = {}
paid_users = set()

CODES_FILE = "codes.json"

if not os.path.exists(CODES_FILE):
    with open(CODES_FILE, "w") as f:
        json.dump({}, f)

def generate_code(amount, user_id):
    timestamp = int(time.time() * 1000)
    rand = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=4))
    code = f"CODE-{amount}-{timestamp}-{rand}"
    with open(CODES_FILE, "r") as f:
        data = json.load(f)
    data[code] = {"user_id": user_id, "amount": amount, "used": False}
    with open(CODES_FILE, "w") as f:
        json.dump(data, f, indent=4)
    return code

def get_main_markup(user_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎁 Крутить бесплатно", callback_data="free_spin"))
    if user_id in paid_users:
        markup.add(InlineKeyboardButton("🎯 Повторно крутить!", callback_data="paid_spin"))
    else:
        markup.add(InlineKeyboardButton("💵 Оплатить 50₽ — ЮMoney", url=f"https://yoomoney.ru/to/{YOOMONEY_WALLET}"))
        markup.add(InlineKeyboardButton("✅ Я оплатил", callback_data="i_paid"))

    markup.add(InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
               InlineKeyboardButton("🏆 Топ", callback_data="leaderboard"))
    markup.add(InlineKeyboardButton("📜 Правила", callback_data="rules"),
               InlineKeyboardButton("❓ FAQ", callback_data="faq"))
    markup.add(InlineKeyboardButton("📋 Политика", callback_data="policy"))
    if user_id == ADMIN_ID:
        markup.add(InlineKeyboardButton("👑 Админ-панель", callback_data="admin"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, "🎰 Добро пожаловать в *VK Cash*!\nВыбирай действие ниже 👇", 
                     reply_markup=get_main_markup(user_id), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "free_spin")
def free_spin(call):
    uid = call.from_user.id
    if first_spin_done.get(uid):
        bot.answer_callback_query(call.id, "Уже использована бесплатная попытка.")
        return
    first_spin_done[uid] = True
    run_spin(call, 50)

@bot.callback_query_handler(func=lambda c: c.data == "i_paid")
def confirm_payment(call):
    uid = call.from_user.id
    paid_users.add(uid)
    bot.send_message(uid, "✅ Оплата подтверждена! Теперь вы можете крутить ещё раз!", reply_markup=get_main_markup(uid))

@bot.callback_query_handler(func=lambda c: c.data == "paid_spin")
def paid_spin(call):
    uid = call.from_user.id
    if uid not in paid_users:
        bot.answer_callback_query(call.id, "Сначала оплатите 50₽ и нажмите 'Я оплатил'")
        return
    paid_users.remove(uid)
    run_spin(call, random.choice([0, 0, 0, 50, 100, 0, 200, 0, 300]))

def run_spin(call, amount):
    msg = bot.send_message(call.message.chat.id, "🔄 Крутим колесо...\n[ 🎰 🎰 🎰 ]")
    time.sleep(1)
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text="[ 🍋 🍒 💣 ]")
    time.sleep(1)
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text="[ 🍉 💰 💣 ]")
    time.sleep(1)
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text="[ 🍀 💰 🍒 ]")
    if amount > 0:
        code = generate_code(amount, call.from_user.id)
        user_states[call.from_user.id] = {"amount": amount, "code": code}
        msg = f"🎉 *Вы выиграли {amount}₽!* 🎉\n🎫 Код: `{code}`\n\n💳 Отправьте свои реквизиты:"
        bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, "🙁 Увы, ничего не выпало. Попробуйте снова!")

@bot.callback_query_handler(func=lambda c: c.data in ["shop", "leaderboard", "admin", "rules", "faq", "policy"])
def info_handler(call):
    uid = call.from_user.id
    responses = {
        "shop": "🛍 *Магазин:*\nЗдесь скоро появятся бусты и бонусы! Следи за обновлениями!",
        "leaderboard": f"🏆 *Топ игроков:*\n1. @user1 — 500₽\n2. @user2 — 200₽\n3. @user3 — 100₽",
        "admin": "👑 *Админ-панель:*\n- Кол-во пользователей: [в разработке]\n- Управление кодами: [в разработке]",
        "rules": "📜 *Правила:*\n1. Один бесплатный шанс\n2. Деньги — реальные\n3. Не обманывать 😉",
        "faq": "❓ *FAQ:*\n- *Как получить VKC?*\nКрути колесо и жди свою удачу!",
        "policy": "📋 *Политика:*\nВсе данные защищены.\nVK Cash — развлекательный проект."
    }
    bot.send_message(call.message.chat.id, responses[call.data], parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def payout_handler(message):
    uid = message.from_user.id
    if uid in user_states:
        state = user_states.pop(uid)
        code = state["code"]
        with open(CODES_FILE, "r") as f:
            codes = json.load(f)
        if code not in codes or codes[code]["used"] or codes[code]["user_id"] != uid:
            bot.send_message(uid, "⚠️ Ошибка с кодом. Попробуйте снова.")
            return
        codes[code]["used"] = True
        with open(CODES_FILE, "w") as f:
            json.dump(codes, f, indent=4)
        payout = (
            f"💰 Новая заявка от @{message.from_user.username or message.from_user.first_name}:\n"
            f"🆔 ID: {uid}\n"
            f"🔐 Код: {code}\n"
            f"📦 Сумма: {state['amount']}₽\n"
            f"💳 Реквизиты: {message.text}"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💸 Выплатить вручную", url="https://yoomoney.ru/main"))
        bot.send_message(ADMIN_ID, payout, reply_markup=markup)
        bot.send_message(uid, "✅ Заявка отправлена! Ожидайте выплаты в течение часа.")

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
        bot.process_new_updates([update])
        return "OK", 200
    return "VK Cash работает", 200

# Установка webhook при старте
def set_webhook():
    requests.get(f'https://api.telegram.org/bot{API_TOKEN}/setWebhook?url={WEBHOOK_URL}')

if __name__ == '__main__':
    set_webhook()
    app.run(host='0.0.0.0', port=8080)
