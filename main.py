import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
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
payment_pending = set()
payment_review = {}
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
        "status": "pending"
    }
    with open(CODES_FILE, "w") as f:
        json.dump(codes, f, indent=4)
    return code

def get_main_markup(user_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎁 Крутить бесплатно", callback_data="free_spin"))
    markup.add(InlineKeyboardButton("💸 Оплатить 50₽", callback_data="pay"))
    markup.add(InlineKeyboardButton("🏆 Топ", callback_data="leaderboard"))
    markup.add(InlineKeyboardButton("📜 Правила", callback_data="rules"),
               InlineKeyboardButton("❓ FAQ", callback_data="faq"))
    markup.add(InlineKeyboardButton("📋 Политика", callback_data="policy"))
    if user_id == ADMIN_ID:
        markup.add(InlineKeyboardButton("👑 Админ-панель", callback_data="admin"))
    return markup

def get_random_win():
    roll = random.randint(1, 100)
    if roll <= 70:
        return 0
    elif roll <= 90:
        return random.choice([50, 70, 100])
    else:
        return random.choice([150, 200, 300, 500])

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
    msg = bot.send_message(uid, "🔄 Крутим колесо...\n[ 🎰 🎰 🎰 ]")
    time.sleep(1)
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text="[ 🍒 💣 🍋 ]")
    time.sleep(1)
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text="[ 🍀 💰 🍉 ]")
    time.sleep(1)
    amount = get_random_win()
    if amount == 0:
        bot.send_message(uid, "😢 Увы, ничего не выиграно на этот раз.")
        return
    code = generate_code(amount, uid)
    user_states[uid] = {"amount": amount, "code": code}
    bot.send_message(uid, f"🎉 ПОБЕДА {amount}₽!\nКод: `{code}`\nОтправь свои реквизиты:", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "pay")
def handle_pay(call):
    uid = call.from_user.id
    payment_pending.add(uid)
    bot.send_message(uid, "💳 Переведи 50₽ на ЮMoney: `4100119077541618`\nПосле оплаты нажми кнопку ниже.",
                     parse_mode="Markdown",
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
        payment_review[uid] = message.message_id
        bot.send_message(uid, "📩 Скрин отправлен на проверку. Ожидай подтверждение от администратора.")
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{uid}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{uid}")
        )
        bot.forward_message(ADMIN_ID, uid, message.message_id)
        bot.send_message(ADMIN_ID, f"Платёж от ID: {uid}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def confirm_payment(call):
    if call.from_user.id != ADMIN_ID:
        return
    uid = int(call.data.split("_")[1])
    if uid in payment_review:
        payment_pending.discard(uid)
        payment_review.pop(uid)
        first_spin_done[uid] = False
        bot.send_message(uid, "✅ Оплата подтверждена! Можешь снова крутить колесо.")
        bot.edit_message_text("✅ Подтверждено.", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject_payment(call):
    if call.from_user.id != ADMIN_ID:
        return
    uid = int(call.data.split("_")[1])
    if uid in payment_review:
        payment_pending.discard(uid)
        payment_review.pop(uid)
        bot.send_message(uid, "❌ Оплата отклонена. Повтори попытку или свяжись с админом.")
        bot.edit_message_text("❌ Отклонено.", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.message_handler(func=lambda m: True)
def handle_requisites(message):
    uid = message.from_user.id
    if uid in user_states:
        state = user_states.pop(uid)
        code = state['code']
        with open(CODES_FILE) as f:
            codes = json.load(f)
        if code in codes and codes[code]['status'] == "pending":
            codes[code]['requisites'] = message.text
            codes[code]['status'] = "waiting_payment"
            with open(CODES_FILE, "w") as f:
                json.dump(codes, f, indent=4)
            bot.send_message(ADMIN_ID, f"🧾 Заявка от @{message.from_user.username or uid}\nКод: {code}\nСумма: {state['amount']}₽\nРеквизиты: {message.text}")
            bot.send_message(uid, "✅ Заявка отправлена! Ожидай выплату.")

@bot.callback_query_handler(func=lambda call: call.data == "admin")
def handle_admin_panel(call):
    if call.from_user.id != ADMIN_ID:
        return
    with open(CODES_FILE, "r") as f:
        codes = json.load(f)
    total = len(codes)
    waiting = sum(1 for c in codes.values() if c['status'] == "waiting_payment")
    paid = sum(1 for c in codes.values() if c['status'] == "paid")
    pending = sum(1 for c in codes.values() if c['status'] == "pending")
    text = f"📊 Всего: {total} | Ожидают: {waiting} | Выплачено: {paid}\n\n🗂️ Активные коды:\n"
    for code, info in codes.items():
        text += f"{code} — {info['amount']}₽ — {info['status']} — ID: {info['user_id']}\n"
    bot.send_message(call.message.chat.id, text[:4000])

@bot.callback_query_handler(func=lambda call: call.data in ["rules", "faq", "policy", "leaderboard"])
def handle_info_buttons(call):
    texts = {
        "rules": "📜 Правила:\n- Первая прокрутка бесплатна\n- Повторные — после оплаты 50₽\n- Шансы случайные\n- Скрин оплаты обязателен",
        "faq": "❓ FAQ:\n- Как начать? Жми 'Крутить бесплатно'\n- Как снова играть? Оплати и пришли скрин\n- Когда выплата? До 1 часа",
        "policy": "📋 Политика:\n- Проект развлекательный\n- Возвратов нет\n- Участие добровольное",
        "leaderboard": "🏆 Топ участников:\n" + '\n'.join(
            [f"{i+1}. @{random.choice(['winnerX', 'luckyY', 'spinZ'])}{random.randint(1000,9999)} — {random.choice([50, 100, 150, 200])}₽"
             for i in range(5)])
    }
    bot.send_message(call.message.chat.id, texts[call.data])

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
        BotCommand("rules", "Посмотреть правила"),
        BotCommand("leaderboard", "Топ участников"),
        BotCommand("faq", "FAQ по игре"),
        BotCommand("policy", "Политика"),
        BotCommand("admin", "Админ-панель")
    ])
    app.run(host='0.0.0.0', port=8080)
