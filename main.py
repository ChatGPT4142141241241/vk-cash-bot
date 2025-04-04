
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
import re
import time
import random

API_TOKEN = '8135081615:AAFHaG7cgRaNlBAAEk_ALEP0-wHYzOniYbU'
ADMIN_ID = 6180147473

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_states = {}
first_spin_done = {}

def generate_code(amount):
    timestamp = int(time.time() * 1000)
    random_part = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=4))
    return f"CODE-{amount}-{timestamp}-{random_part}"

@bot.message_handler(commands=['start'])
def send_start(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🎁 Крутить бесплатно", callback_data="free_spin"),
        InlineKeyboardButton("📜 Правила", callback_data="rules"),
        InlineKeyboardButton("❓ FAQ", callback_data="faq"),
        InlineKeyboardButton("📋 Политика", callback_data="policy")
    )
    bot.send_message(message.chat.id, "🎰 Добро пожаловать в VK Cash!\nВыбирай действие ниже:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["free_spin", "paid_spin"])
def handle_spin(call):
    uid = call.from_user.id
    if call.data == "free_spin" and first_spin_done.get(uid):
        bot.answer_callback_query(call.id, "Бесплатная попытка уже использована.")
        return
    elif call.data == "free_spin":
        amount = 50
        first_spin_done[uid] = True
    else:
        amount = random.choice([0, 0, 100, 250, 500])

    bot.send_message(call.message.chat.id, "🔄 Крутим колесо...\n🎯 [ 🍋 🍉 🍒 💰 🎲 ]\n🎯 [ 💣 🍒 💣 🍀 💰 ]")
    time.sleep(2)

    if amount == 0:
        bot.send_message(call.message.chat.id, "❌ Увы, ничего не выпало. Попробуй снова!")
    else:
        code = generate_code(amount)
        user_states[uid] = { "amount": amount, "code": code }
        bot.send_message(call.message.chat.id, f"🎉 Ты получил {amount}₽!\n🎫 Код: `{code}`\n\nОтправь свои реквизиты для выплаты.", parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    uid = message.from_user.id
    if uid in user_states:
        state = user_states.pop(uid)
        payout_info = f"💰 Новая заявка:\n👤 @{message.from_user.username or message.from_user.first_name}\n🆔 {uid}\n📦 Сумма: {state['amount']}₽\n🔐 Код: {state['code']}\n💳 Реквизиты: {message.text}"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💸 Выплатить", callback_data=f"pay_{uid}"))
        bot.send_message(ADMIN_ID, payout_info, reply_markup=markup)
        bot.reply_to(message, "✅ Заявка отправлена! Ожидай выплату.")
    else:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("💳 Попробовать снова за 50₽", callback_data="paid_spin")
        )
        bot.send_message(message.chat.id, "❌ Сначала получи код. Крути колесо!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def handle_payment(call):
    user_id = call.data.split("_")[1]
    bot.send_message(user_id, "💸 Выплата отправлена! Спасибо за участие 🙌")
    bot.answer_callback_query(call.id, "Выплата отмечена!")

@bot.callback_query_handler(func=lambda call: call.data in ["rules", "faq", "policy"])
def handle_info(call):
    info = {
        "rules": "📜 *Правила участия:*\n- Первая прокрутка — бесплатная\n- Повторная — 50₽\n- Суммы бонусов — от 50₽ до 500₽\n- После оплаты — случайный результат",
        "faq": "❓ *FAQ:*\n- *Как сыграть?* Нажми 'Крутить'\n- *Как снова сыграть?* Нажми 'Попробовать снова за 50₽'\n- *Как получить бонус?* Забери код и отправь реквизиты",
        "policy": "📋 *Политика:*\n- Проект — развлекательный\n- Результаты случайны\n- Возврата нет\n- Участие добровольное"
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
