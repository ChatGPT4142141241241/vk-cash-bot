
import telebot
from flask import Flask, request
import re
import time

API_TOKEN = '8135081615:AAFHaG7cgRaNlBAAEk_ALEP0-wHYzOniYbU'
ADMIN_ID = 6180147473

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# Генератор стартовой клавиатуры
def start_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("🚀 Запустить"))
    return markup

# Проверка кода
def validate_code(code, expected_amount):
    pattern = fr'^CODE-{expected_amount}-(\d+)-[A-Z0-9]{{4}}$'
    match = re.match(pattern, code)
    if not match:
        return False
    timestamp = int(match.group(1))
    now = int(time.time() * 1000)
    return now - timestamp < 5 * 60 * 1000

# Обработка команды /start и кнопки
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "Добро пожаловать! Нажми кнопку ниже, чтобы начать 👇", reply_markup=start_keyboard())

@bot.message_handler(func=lambda m: m.text == "🚀 Запустить")
def handle_start_button(message):
    bot.reply_to(message, "Привет! 🤑 Для заявки на выплату отправь сумму и код, например:
50 CODE-50-1711769000348-KD8Q")

@bot.message_handler(func=lambda m: True)
def handle_code_submission(message):
    text = message.text.strip()
    parts = text.split()

    if len(parts) != 2:
        bot.reply_to(message, "❌ Формат неверный. Пример: 50 CODE-50-1711769000348-ABCD")
        return

    amount, code = parts
    if not amount.isdigit():
        bot.reply_to(message, "❌ Сумма должна быть числом.")
        return

    if not validate_code(code, amount):
        bot.reply_to(message, "❌ Неверный или просроченный код.")
        return

    user = message.from_user
    msg = (
        f"💰 Подтвержденная заявка:
"
        f"👤 Пользователь: @{user.username or user.first_name}
"
        f"🆔 ID: {user.id}
"
        f"📦 Сумма: {amount}₽
"
        f"🔐 Код: {code}"
    )

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("💸 Выплатить", callback_data=f"pay_{user.id}"))

    bot.send_message(ADMIN_ID, msg, reply_markup=markup)
    bot.reply_to(message, "✅ Код подтверждён. Ожидай выплату!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def handle_payment(call):
    target_id = call.data.split("_")[1]
    bot.send_message(target_id, "💸 Ваша выплата подтверждена! Спасибо за участие 🙌")
    bot.answer_callback_query(call.id, "Выплата отправлена игроку.")

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bot is running!', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
