from flask import Flask
import threading, requests, time, os
from datetime import datetime
import pytz

app = Flask(__name__)
@app.route('/')
def home():
    return "Victa V7 SMART SECURE LIVE"

threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not set in Render!")

API = f"https://api.telegram.org/bot{BOT_TOKEN}"

CHAT_ID = None
price_history = []
last_price = 0
offset = 0

def send(chat_id, text):
    try:
        requests.post(f"{API}/sendMessage", data={"chat_id": chat_id, "text": text}, timeout=10)
    except:
        pass

def get_price():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/EUR", timeout=10).json()
        return float(r["rates"]["USD"])
    except:
        return None

def calc_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    gains = []
    losses = []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 70
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def kampala_time():
    return datetime.now(pytz.timezone('Africa/Kampala')).strftime("%H:%M:%S")

print("Victa V7 SMART SECURE Starting...")

while True:
    try:
        # Get Telegram messages
        resp = requests.get(f"{API}/getUpdates", params={"offset": offset, "timeout":
