import telebot
from flask import Flask, request
import re
import time

TOKEN = '8135081615:AAFHaG7cgRaNlBAAEk_ALEP0-wHYzOniYbU'
ADMIN_ID = 6180147473

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
user_requests = {}

# Проверка формата кода
def validate_code(code, expected_amount):
    pattern = fr'^CODE-{expected_amount}-(\d+)-[A-Z0-9]{{4}}$'
    match = re.match(pattern, code)
    if not match:
        return False
    timestamp = int(match.group(1))
    now = int(time.time() * 1000)
    return now - timestamp < 10 * 60 * 1000  # 10 минут

# Кнопка "Запустить"
@bot.message_handler(func=lambda message: message.text == '🚀 Запустить')
def handle_start_button(message):
    bot.send_message(
        message.chat.id,
        "Привет! 🤑 Чтобы получить выплату, отправь сумму и код. Пример:\n\n50 CODE-50-1711769000348-KD8Q"
    )

# Обработка текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.chat.id == ADMIN_ID and message.text.startswith("💸 Выплатить"):
        parts = message.text.split("\n")
        user_id = int(parts[1].split(":")[1].strip())
        bot.send_message(user_id, "✅ Деньги отправлены. Спасибо за участие!")
        return

    text = message.text.strip()
    parts = text.split()
    if len(parts) != 2:
        bot.reply_to(message, "❌ Формат неверный. Пример: 50 CODE-50-1711769000348-KD8Q")
        return

    amount, code = parts
    if not amount.isdigit():
        bot.reply_to(message, "❌ Сумма должна быть числом.")
        return

    if not validate_code(code, amount):
        bot.reply_to(message, "❌ Неверный или просроченный код.")
        return

    user_id = message.from_user.id
    user_requests[user_id] = {
        "amount": amount,
        "code": code,
        "username": message.from_user.username or message.from_user.first_name
    }

    bot.send_message(message.chat.id, "💳 Введи номер кошелька или карты для получения выплаты:")

# Получение реквизитов от игрока
@bot.message_handler(func=lambda message: message.from_user.id in user_requests)
def handle_wallet(message):
    user_id = message.from_user.id
    wallet = message.text.strip()
    data = user_requests.pop(user_id)

    text = (
        f"💰 Подтвержденная заявка:\n"
        f"👤 Пользователь: @{data['username']}\n"
        f"🆔 ID: {user_id}\n"
        f"📦 Сумма: {data['amount']}₽\n"
        f"🔐 Код: {data['code']}\n"
        f"💳 Реквизиты: {wallet}"
    )

    markup = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton("💸 Выплатить", callback_data="pay_user")
    markup.add(button)

    bot.send_message(ADMIN_ID, text, reply_markup=markup)
    bot.send_message(message.chat.id, "✅ Заявка отправлена. Ожидай выплату.")

# Flask сервер для вебхука
@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bot is running!', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
