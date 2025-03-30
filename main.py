
import telebot
from flask import Flask, request

TOKEN = "ТВОЙ_ТОКЕН_БОТА"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/', methods=['GET', 'HEAD'])
def index():
    return 'Bot is running!'

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! 😎 Для заявки на выплату отправь сумму и код, например:\n50 CODE-50-1711769000348-KD8Q")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    bot.reply_to(message, "⛔️ Код не подтвержден или устарел.")

if __name__ == '__main__':
    import os
    import sys
    port = int(os.environ.get("PORT", 8080))
    bot.remove_webhook()
    bot.set_webhook(url=f"https://vk-cash-bot.onrender.com/{TOKEN}")
    app.run(host="0.0.0.0", port=port)
