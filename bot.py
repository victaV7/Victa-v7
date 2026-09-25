from flask import Flask
import threading, requests, time, os
from datetime import datetime
import pytz

app = Flask(__name__)

@app.route('/')
def home():
    return "Victa V7 SMART LIVE"

threading.Thread(target=lambda: app.run(host='0.0.0.0',port=10000)).start()

BOT_TOKEN = os.environ.get("BOT_TOKEN") or "8630263342:AAEKwsrJ-pQEdqSMZ_3xhxpxj4qw1En48XNE"
API = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHAT_ID = None
price_history = []
last_price = 0
offset = 0

def send(chat_id, text):
    try:
        requests.post(f"{API}/sendMessage", data={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        print(e)

def get_eurusd():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/EUR", timeout=10).json()
        return float(r["rates"]["USD"])
    except:
        return None

def calc_rsi(prices, period=14):
    if len(prices) < period+1:
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
    rsi = 100 - (100/(1+rs))
    return rsi

def get_kampala_time():
    tz = pytz.timezone('Africa/Kampala')
    return datetime.now(tz).strftime("%H:%M:%S")

print("Victa V7 SMART Starting...")
while True:
    try:
        # Check Telegram messages
        r = requests.get(f"{API}/getUpdates", params={"offset": offset, "timeout": 10}, timeout=15).json()
        for u in r.get("result", []):
            offset = u["update_id"] + 1
            msg = u.get("message", {})
            chat_id = msg.get("chat", {}).get("id")
            text = msg.get("text", "")
            if chat_id:
                CHAT_ID = chat_id
                if "/start" in text:
                    send(chat_id, "🚀 Victa Bot V7 SMART is LIVE!\nI will only alert for strong BUY/SELL signals\nTrader: Erastus Davicta\n📍 Kampala")

        # Check EURUSD every 60s
        price = get_eurusd()
        if price:
            price_history.append(price)
            if len(price_history) > 50:
                price_history.pop(0)

            rsi = calc_rsi(price_history)
            ema_fast = sum(price_history[-9:]) / min(9, len(price_history))
            ema_slow = sum(price_history[-21:]) / min(21, len(price_history))

            signal = None
            if price > ema_fast > ema_slow and rsi > 60:
                signal = f"🟢 STRONG BUY Signal!\n📈 LIVE EURUSD: {price:.5f}\nRSI: {rsi:.1f} | EMA: Bullish\n⏰ Time: {get_kampala_time()}\n📍 Kampala\nTrader: Erastus Davicta"
            elif price < ema_fast < ema_slow and rsi < 40:
                signal = f"🔴 STRONG SELL Signal!\n📉 LIVE EURUSD: {price:.5f}\nRSI: {rsi:.1f} | EMA: Bearish\n⏰ Time: {get_kampala_time()}\n📍 Kampala\nTrader: Erastus Davicta"

            if signal and CHAT_ID and abs(price - last_price) > 0.00005:
                send(CHAT_ID, signal)
                last_price = price

        time.sleep(60)

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)
