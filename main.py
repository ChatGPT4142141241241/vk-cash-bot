import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from flask import Flask, request
import time
import random
import json
import os
import threading
import requests

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
    codes[code] = {"user_id": user_id, "amount": amount, "used": False}
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

@bot.message_handler(commands=['start'])
def send_start(message):
    bot.send_message(message.chat.id, "🎰 Добро пожаловать в VK Cash!", reply_markup=get_main_markup(message.from_user.id))

@bot.message_handler(commands=['rules'])
def command_rules(message):
    bot.send_message(message.chat.id, "📜 Правила:\n- Первая прокрутка бесплатна\n- Повторные прокрутки — после оплаты 50₽\n- Выигрыш случайный, шансы низкие\n- Скрин оплаты обязателен")

@bot.message_handler(commands=['leaderboard'])
def command_leaderboard(message):
    usernames = ["@lucky_fox", "@spinmaster22", "@richbee", "@coincrazy", "@vegasowl"]
    text = "🏆 Топ участников:\n"
    for i, user in enumerate(usernames, 1):
        text += f"{i}. {user} — {random.choice([50,100,150,200])}₽\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['faq'])
def command_faq(message):
    bot.send_message(message.chat.id, "❓ FAQ:\n- Как начать? Нажми 'Крутить бесплатно'\n- Как снова играть? Оплати 50₽ и отправь скрин\n- Когда будет выплата? В течение 1 часа после подтверждения")

@bot.message_handler(commands=['policy'])
def command_policy(message):
    bot.send_message(message.chat.id, "📋 Политика:\n- Проект развлекательный\n- Результаты случайны\n- Возвратов нет\n- Участие добровольное")

@bot.message_handler(commands=['admin'])
def command_admin(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Нет доступа.")
        return
    with open(CODES_FILE) as f:
        codes = json.load(f)
    text = "🗂️ Активные коды:\n"
    for code, data in codes.items():
        status = "✅" if data['used'] else "🕓"
        text += f"{status} {code} — {data['amount']}₽ — ID: {data['user_id']}\n"
    used = sum(1 for c in codes.values() if c['used'])
    pending = sum(1 for c in codes.values() if not c['used'])
    total = len(codes)
    stats = f"📊 Статистика:\nВсего кодов: {total}\nОжидают: {pending}\nВыплачено: {used}"
    bot.send_message(message.chat.id, stats + "\n\n" + text[:4000])

@bot.callback_query_handler(func=lambda call: call.data in ["rules", "leaderboard", "faq", "policy", "admin"])
def handle_common_callbacks(call):
    commands = {
        "rules": command_rules,
        "leaderboard": command_leaderboard,
        "faq": command_faq,
        "policy": command_policy,
        "admin": command_admin
    }
    commands[call.data](call.message)

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
    amount = random.choice([0, 10, 25, 50, 100, 200, 500])
    code = generate_code(amount, uid)
    user_states[uid] = {"amount": amount, "code": code}
    bot.send_message(uid, f"🎉 ПОБЕДА {amount}₽!\nКод: `{code}`\nОтправь свои реквизиты:", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "pay")
def handle_pay(call):
    uid = call.from_user.id
    payment_pending.add(uid)
    bot.send_message(uid, "💳 Переведи 50₽ на ЮMoney: `4100119077541618`\nПосле оплаты нажми кнопку ниже.", parse_mode="Markdown",
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
        code_info = user_states.get(uid, {})
        extra = f"Код: {code_info.get('code')}\nСумма: {code_info.get('amount')}₽" if code_info else "(нет данных)"
        bot.send_message(ADMIN_ID, f"Платёж от ID: {uid}\n{extra}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def confirm_payment(call):
    if call.from_user.id != ADMIN_ID:
        return
    uid = int(call.data.split("_")[1])
    if uid in payment_review:
        payment_pending.discard(uid)
        payment_review.pop(uid)
        first_spin_done[uid] = False
        with open(CODES_FILE) as f:
            codes = json.load(f)
        for code, data in codes.items():
            if data["user_id"] == uid and not data["used"]:
                data["used"] = True
                break
        with open(CODES_FILE, "w") as f:
            json.dump(codes, f, indent=4)
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
        if code in codes and not codes[code]['used']:
            bot.send_message(ADMIN_ID, f"Новая заявка от @{message.from_user.username or uid}:\nКод: {code}\nСумма: {state['amount']}₽\nРеквизиты: {message.text}")
            bot.send_message(uid, "✅ Заявка отправлена! Ожидай выплату.")

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bot is running!', 200

def check_webhook():
    try:
        response = requests.get(f"https://api.telegram.org/bot{API_TOKEN}/getWebhookInfo")
        if response.status_code == 200:
            result = response.json()
            current_url = result['result'].get('url', '')
            if current_url != "https://vk-cash-bot.onrender.com":
                print("🔄 Webhook не совпадает, восстанавливаю...")
                requests.get(f"https://api.telegram.org/bot{API_TOKEN}/setWebhook?url=https://vk-cash-bot.onrender.com")
            else:
                print("✅ Webhook активен.")
        else:
            print(f"⚠️ Ошибка запроса Webhook: {response.status_code}")
    except Exception as e:
        print(f"💥 Ошибка при проверке Webhook: {e}")
    threading.Timer(10, check_webhook).start()

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
    check_webhook()
    app.run(host='0.0.0.0', port=8080)
