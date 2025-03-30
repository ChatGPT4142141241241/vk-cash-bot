
import telebot
from flask import Flask, request
import re
import time

API_TOKEN = '8135081615:AAFHaG7cgRaNlBAAEk_ALEP0-wHYzOniYbU'
ADMIN_ID = 6180147473

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

def validate_code(code, expected_amount):
    pattern = fr'^CODE-{expected_amount}-(\d+)-[A-Z0-9]{{4}}$'
    match = re.match(pattern, code)
    if not match:
        return False
    timestamp = int(match.group(1))
    now = int(time.time() * 1000)
    return now - timestamp < 5 * 60 * 1000

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "Привет! 🤑 Для заявки на выплату отправь сумму и код, например:\n50 CODE-50-1711769000348-KD8Q"
    )

@bot.message_handler(func=lambda m: True)
def handle_submission(message):
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

    user = message.from_user
    result = f"💰 Подтвержденная заявка:\n👤 Пользователь: @{user.username or user.first_name}\n🆔 ID: {user.id}\n📦 Сумма: {amount}₽\n🔐 Код: {code}"
    bot.send_message(ADMIN_ID, result)
    bot.reply_to(message, "✅ Код подтвержден! Заявка отправлена, ожидай выплату.")

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bot is running!', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
