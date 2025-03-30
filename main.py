import telebot
from flask import Flask, request
import re
import time

TOKEN = '8135081615:AAFHaG7cgRaNlBAAEk_ALEP0-wHYzOniYbU'
ADMIN_ID = 6180147473

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Проверка валидности кода
def validate_code(code, expected_amount):
    pattern = fr'^CODE-{expected_amount}-(\d+)-[A-Z0-9]{{4}}$'
    match = re.match(pattern, code)
    if not match:
        return False
    timestamp = int(match.group(1))
    now = int(time.time() * 1000)
    return now - timestamp < 5 * 60 * 1000  # 5 минут

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "🚀 Нажми кнопку 'Запустить', чтобы начать!\n\nИли отправь сумму и код:\nПример: `50 CODE-50-1711769000348-KD8Q`", parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.strip()
    parts = text.split()

    if len(parts) != 2:
        bot.send_message(message.chat.id, "❌ Формат неверный. Пример:\n`50 CODE-50-1711769000348-KD8Q`", parse_mode="Markdown")
        return

    amount, code = parts
    if not amount.isdigit():
        bot.send_message(message.chat.id, "❌ Сумма должна быть числом.")
        return

    if not validate_code(code, amount):
        bot.send_message(message.chat.id, "❌ Неверный или просроченный код.")
        return

    user = message.from_user
    confirm_text = f"""✅ Подтверждена заявка на выплату:

👤 Пользователь: @{user.username or user.first_name}
🆔 ID: {user.id}
📦 Сумма: {amount}₽
🔐 Код: {code}"""

    bot.send_message(ADMIN_ID, confirm_text)
    bot.send_message(message.chat.id, "✅ Код подтверждён! Заявка отправлена. Ожидай выплату.")

# Flask Webhook
@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bot is running!', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
