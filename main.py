import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from flask import Flask, request
import re
import time
import random
import json
import os

API_TOKEN = '8135081615:AAFHaG7cgRaNlBAAEk_ALEP0-wHYzOniYbU'
ADMIN_ID = 6180147473  # <-- ЗАМЕНИ на свой Telegram user ID

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_states = {}
payment_pending = set()
first_spin_done = {}

CODES_FILE = "codes.json"

if not os.path.exists(CODES_FILE):
    with open(CODES_FILE, "w") as f:
        json.dump({}, f)

def generate_code(amount, user_id):
    timestamp = int(time.time() * 1000)
    random_part = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=4))
    code = f"CODE-{amount}-{timestamp}-{random_part}"
    with open(CODES_FILE, "r") as f:
        codes = json.load(f)
    codes[code] = {"user_id": user_id, "amount": amount, "used": False}
    with open(CODES_FILE, "w") as f:
        json.dump(codes, f, indent=4)
    return code

def get_main_markup(user_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎁 Крутить бесплатно", callback_data="free_spin"))
    markup.add(InlineKeyboardButton("💸 Оплатить 50₽", callback_data="pay"))
    markup.add(InlineKeyboardButton("🏆 Топ", callback_data="leaderboard"))
    markup.add(InlineKeyboardButton("📜 Правила", callback_data="rules"))
    if user_id == ADMIN_ID:
        markup.add(InlineKeyboardButton("👑 Админ-панель", callback_data="admin"))
    return markup

@bot.message_handler(commands=['start'])
def send_start(message):
    bot.send_message(message.chat.id, "🎰 Добро пожаловать в VK Cash!", reply_markup=get_main_markup(message.from_user.id))

@bot.callback_query_handler(func=lambda call: call.data == "free_spin")
def handle_free_spin(call):
    uid = call.from_user.id
    if first_spin_done.get(uid):
        bot.answer_callback_query(call.id, "❌ Бесплатная попытка уже использована.")
        return
    first_spin_done[uid] = True
    bot.send_message(uid, "🔄 Крутим колесо...")
    time.sleep(1)
    amount = 50
    code = generate_code(amount, uid)
    user_states[uid] = {"amount": amount, "code": code}
    bot.send_message(uid, f"🎉 ПОБЕДА {amount}₽!\nКод: `{code}`\nОтправь свои реквизиты:", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "pay")
def handle_pay(call):
    uid = call.from_user.id
    payment_pending.add(uid)
    bot.send_message(uid, "💳 Переведи 50₽ на ЮMoney: `4100119077541618`\nПосле оплаты нажми кнопку ниже.", parse_mode="Markdown",
                     reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Я оплатил", callback_data="paid")))

@bot.callback_query_handler(func=lambda call: call.data == "paid")
def handle_paid(call):
    uid = call.from_user.id
    if uid in payment_pending:
        bot.send_message(uid, "📸 Пришли скриншот оплаты.")
    else:
        bot.send_message(uid, "⚠️ Сначала нажми кнопку \"Оплатить\".")

@bot.message_handler(content_types=['photo'])
def handle_payment_proof(message):
    uid = message.from_user.id
    if uid in payment_pending:
        payment_pending.remove(uid)
        first_spin_done[uid] = False
        bot.send_message(uid, "✅ Оплата принята! Можешь снова крутить колесо.")
        # optionally, forward the proof to admin:
        bot.forward_message(ADMIN_ID, uid, message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "leaderboard")
def handle_leaderboard(call):
    fake_users = [f"@winner{random.randint(1000,9999)}" for _ in range(5)]
    text = "🏆 Топ участников:\n"
    for i, user in enumerate(fake_users, 1):
        text += f"{i}. {user} — {random.choice([50,100,150,200])}₽\n"
    bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def handle_rules(call):
    text = "📜 Правила:\n- Первая прокрутка бесплатна и всегда даёт 50₽\n- Повторные прокрутки — после оплаты 50₽\n- Выигрыш случайный, шансы низкие\n- Скрин оплаты обязателен"
    bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data == "admin")
def handle_admin(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ Нет доступа.")
        return
    with open(CODES_FILE) as f:
        codes = json.load(f)
    used = sum(1 for c in codes.values() if c['used'])
    pending = sum(1 for c in codes.values() if not c['used'])
    total = len(codes)
    text = f"📊 Статистика:\nВсего кодов: {total}\nОжидают: {pending}\nВыплачено: {used}"
    bot.send_message(call.message.chat.id, text)

@bot.message_handler(func=lambda m: True)
def handle_requisites(message):
    uid = message.from_user.id
    if uid in user_states:
        state = user_states.pop(uid)
        code = state['code']
        with open(CODES_FILE) as f:
            codes = json.load(f)
        if code in codes and not codes[code]['used']:
            codes[code]['used'] = True
            with open(CODES_FILE, "w") as f:
                json.dump(codes, f, indent=4)
            bot.send_message(ADMIN_ID, f"Новая заявка от @{message.from_user.username or uid}:\nКод: {code}\nСумма: {state['amount']}₽\nРеквизиты: {message.text}")
            bot.send_message(uid, "✅ Заявка отправлена! Ожидай выплату.")

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bot is running!', 200

if __name__ == '__main__':
    bot.set_my_commands([
        BotCommand("start", "Запустить бота"),
        BotCommand("pay", "Оплатить 50₽"),
        BotCommand("rules", "Посмотреть правила")
    ])
    app.run(host='0.0.0.0', port=8080)
