
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
import re
import time

API_TOKEN = '8135081615:AAFHaG7cgRaNlBAAEk_ALEP0-wHYzOniYbU'
ADMIN_ID = 6180147473

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_states = {}

def validate_code(code, expected_amount):
    pattern = fr'^CODE-{expected_amount}-(\d+)-[A-Z0-9]{{4}}$'
    match = re.match(pattern, code)
    if not match:
        return False
    timestamp = int(match.group(1))
    now = int(time.time() * 1000)
    return now - timestamp < 5 * 60 * 1000

@bot.message_handler(commands=['start'])
def send_start(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🚀 Запустить", callback_data="launch"))
    bot.send_message(message.chat.id, "Нажми кнопку ниже, чтобы запустить бота:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "launch")
def handle_launch(call):
    bot.send_message(call.message.chat.id, "🤑 Введите сумму и код, пример:
50 CODE-50-1711769000348-KD8Q")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.strip()
    parts = text.split()

    if len(parts) == 2 and parts[0].isdigit():
        amount, code = parts
        if not validate_code(code, amount):
            bot.reply_to(message, "❌ Неверный или просроченный код.")
            return
        user_states[message.from_user.id] = {
            "amount": amount,
            "code": code
        }
        bot.reply_to(message, "✅ Код подтвержден! Теперь отправь свои реквизиты для выплаты:")
    elif message.from_user.id in user_states:
        state = user_states.pop(message.from_user.id)
        payout_info = f"💰 Новая заявка:
👤 @{message.from_user.username or message.from_user.first_name}
🆔 {message.from_user.id}
📦 Сумма: {state['amount']}₽
🔐 Код: {state['code']}
💳 Реквизиты: {text}"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💸 Выплатить", callback_data=f"pay_{message.from_user.id}"))
        bot.send_message(ADMIN_ID, payout_info, reply_markup=markup)
        bot.reply_to(message, "✅ Заявка отправлена! Ожидай выплату.")
    else:
        bot.reply_to(message, "❌ Сначала отправь сумму и код выигрыша.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def handle_payment(call):
    user_id = call.data.split("_")[1]
    bot.send_message(user_id, "💸 Выплата отправлена! Спасибо за участие 🙌")
    bot.answer_callback_query(call.id, "Выплата отмечена!")

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bot is running!', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
