import telebot
import qrcode
import io

TOKEN = "8135081615:AAFHaG7cgRaNlBAAEk_ALEP0-wHYzOniYbU"
bot = telebot.TeleBot(TOKEN)

# Конфиг для подключения через v2rayNG
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
    markup.row("🔑 Получить конфиг", "❓ FAQ")
    markup.row("💳 Купить доступ")
    bot.send_message(message.chat.id,
                     "Добро пожаловать в SokolVPN 🦅\n"
                     "Защити свой трафик и облети блокировки!\n"
                     "Выбери действие ниже:",
                     reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🔑 Получить конфиг")
def send_config(message):
    bot.send_message(message.chat.id, "Вот твой конфиг VLESS для v2rayNG:")
    bot.send_message(message.chat.id, f"`{VPN_CONFIG}`", parse_mode="Markdown")

    img = qrcode.make(VPN_CONFIG)
    bio = io.BytesIO()
    bio.name = 'qrcode.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    bot.send_photo(message.chat.id, photo=bio, caption="Сканируй QR в v2rayNG")

@bot.message_handler(func=lambda message: message.text == "❓ FAQ")
def send_faq(message):
    bot.send_message(message.chat.id,
                     "❓ *Что такое SokolVPN?*\n"
                     "- Это надёжный VPN на базе протокола VLESS с шифрованием Reality.\n\n"
                     "📲 *Как пользоваться?*\n"
                     "1. Скачай приложение v2rayNG\n"
                     "2. Нажми на +, выбери импорт по QR или вставь конфиг вручную\n"
                     "3. Подключайся и летай 🛡️",
                     parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "💳 Купить доступ")
def send_payment(message):
    bot.send_message(message.chat.id,
                     "💳 Оплати через DonatPay: https://donatepay.ru/d/SokolVPN\n"
                     "После оплаты нажми /start и получи конфиг.\n"
                     "_(оплата временно работает в ручном режиме)_",
                     parse_mode="Markdown")

bot.polling()
