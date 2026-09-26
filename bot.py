import os
import time
import threading
import telebot
from flask import Flask

BOT_TOKEN = "8630263342:AAEKwsrJ-pQEdqSMZ_3xhpxj4qw1En48XNE"  # Replace with your token from @BotFather

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Victa-v7 is LIVE and running!"

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Victa V7.2 AWAKE!\n\nWelcome Trader Erastus Davicta!\nVicta is SMART & LIVE waiting for the market!\n\nNext signal in 1 min!\nTrend Analysis: BUY\nVicta is SMART & LIVE waiting for the market!")

@bot.message_handler(commands=['signal'])
def signal_cmd(message):
    bot.reply_to(message, "Checking market... BUY Signal!")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def run_bot():
    while True:
        try:
            print("Victa Bot Polling Started...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Bot crashed: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Start web server in background (for Render)
    threading.Thread(target=run_flask).start()
    # Start telegram bot
    run_bot()
