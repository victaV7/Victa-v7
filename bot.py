from flask import Flask
import threading, requests, time, os
from datetime import datetime
import pytz

app = Flask(__name__)
@app.route('/')
def home():
    return "Victa V7 SMART SECURE LIVE - Fixed"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask, daemon=True).start()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
print(f"Token exists: {bool(BOT_TOKEN)}")

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN missing in Environment!")
    # Keep app alive so Render doesn't crash
    while True:
        time.sleep(60)

API = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHAT_ID = None
price_history = []
last_price = 0
offset = 0

def send(cid, txt):
    try:
        requests.post(f"{API}/sendMessage", data={"chat_id":cid, "text":txt}, timeout=10)
    except Exception as e:
        print(e)

def get_price():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/EUR", timeout=10).json()
        return float(r["rates"]["USD"])
    except:
        return None

def calc_rsi(prices, period=14):
    if len(prices) < period+1:
        return 50
    gains=[];losses=[]
    for i in range(1,len(prices)):
        d=prices[i]-prices[i-1]
        gains.append(d if d>0 else 0)
        losses.append(abs(d) if d<0 else 0)
    ag=sum(gains[-period:])/period
    al=sum(losses[-period:])/period
    if al==0:
        return 70
    return 100-(100/(1+ag/al))

def ug_time():
    return datetime.now(pytz.timezone('Africa/Kampala')).strftime("%H:%M:%S")

print("Victa V7 SMART STARTING - SAFE MODE")

while True:
    try:
        resp = requests.get(f"{API}/getUpdates", params={"offset":offset,"timeout":10}, timeout=15).json()
        for u in resp.get("result", []):
            offset = u["update_id"]+1
            msg = u.get("message",{})
            cid = msg.get("chat",{}).get("id")
            txt = msg.get("text","")
            if cid:
                CHAT_ID = cid
                if txt.strip() == "/start":
                    send(cid, f"🚀 Victa V7 SMART FIXED!\n✅ No echo\n✅ Secure\n⏰ {ug_time()} Kampala\nTrader: Erastus Davicta")

        price = get_price()
        if price:
            price_history.append(price)
            if len(price_history)>50:
                price_history.pop(0)
            rsi = calc_rsi(price_history)
            fast = sum(price_history[-9:])/min(9,len(price_history))
            slow = sum(price_history[-21:])/min(21,len(price_history))
            sig=None
            if price>fast>slow and rsi>60:
                sig=f"🟢 STRONG BUY\nEURUSD {price:.5f}\nRSI {rsi:.1f}\n{ug_time()}"
            elif price<fast<slow and rsi<40:
                sig=f"🔴 STRONG SELL\nEURUSD {price:.5f}\nRSI {rsi:.1f}\n{ug_time()}"
            if sig and CHAT_ID and abs(price-last_price)>0.00005:
                send(CHAT_ID,sig)
                last_price=price
        time.sleep(60)
    except Exception as e:
        print(f"Loop error: {e}")
        time.sleep(10)
