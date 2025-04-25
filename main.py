import telebot
import qrcode
import io
from flask import Flask, request

TOKEN = "8135081615:AAFHaG7cgRaNlBAAEk_ALEP0-wHYzOniYbU"
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

VPN_CONFIG = (
    "vless://3f32f673-f64b-4fd5-92b4-94d534ebe5c9@80.74.26.34:54633"
    "?type=tcp&security=reality"
    "&pbk=gGHVqhxR3Atr80tzgp5wHHnYjHaNKfvNJ_oOEbfMsEsE"
    "&fp=chrome&sni=yahoo.com"
    "&sid=4d0b91eee892b6&spx=%2F"
    "#SokolVPN"
)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🔑 Получить VPN", "📦 Инструкция")
    markup.row("💳 Оплатить доступ")
    bot.send_message(
        message.chat.id,
        "🦅 Добро пожаловать в *SokolVPN!*\n"
        "Твой зашифрованный туннель готов.\n"
        "Выбери действие ниже:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text == "🔑 Получить VPN")
def send_config(message):
    bot.send_message(message.chat.id, "Вот твой конфиг VLESS для v2rayNG:")
    bot.send_message(message.chat.id, f"`{VPN_CONFIG}`", parse_mode="Markdown")
    img = qrcode.make(VPN_CONFIG)
    bio = io.BytesIO()
    bio.name = 'sokolvpn_qr.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    bot.send_photo(message.chat.id, photo=bio, caption="Сканируй QR в v2rayNG")

@bot.message_handler(func=lambda message: message.text == "📦 Инструкция")
def send_faq(message):
    bot.send_message(
        message.chat.id,
        "📦 *Инструкция по подключению:*\n"
        "1. Скачай `v2rayNG` в Google Play\n"
        "2. Нажми ➕, выбери 'Импорт из QR' или 'Импорт из буфера'\n"
        "3. Подключайся и шифруйся 🔒",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text == "💳 Оплатить доступ")
def send_payment(message):
    bot.send_message(
        message.chat.id,
        "💳 *Оплата доступа:*\n"
        "Перейди по ссылке и оплати 99₽:\n"
        "https://donate.stream/SokolVPN2025_67f21aae98f41\n\n"
        "После оплаты нажми /start, чтобы получить конфиг.",
        parse_mode="Markdown"
    )

@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://sokolvpn.onrender.com/' + TOKEN)
    return "Webhook установлен", 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)