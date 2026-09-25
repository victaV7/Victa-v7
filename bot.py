from flask import Flask
import threading, requests, time, os
from datetime import datetime
import pytz

app = Flask(__name__)
@app.route('/')
def home():
    return "Victa V7.2 ALWAYS AWAKE"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask, daemon=True).start()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
print(f"Token OK: {bool(BOT_TOKEN)}")
if not BOT_TOKEN:
    while True:
        print("NO TOKEN")
        time.sleep(60)

API = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHAT_ID = None
offset = 0

def send(cid, txt):
    try:
        requests.post(f"{API}/sendMessage", data={"chat_id":cid,"text":txt}, timeout=10)
        print(f"Sent to {cid}")
    except Exception as e:
        print(e)

def get_price():
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/EUR", timeout=10).json()
        return float(r["rates"]["USD"])
    except:
        return 1.1396

def ug_time():
    return datetime.now(pytz.timezone('Africa/Kampala')).strftime("%H:%M:%S")

print("V7.2 STARTED - WAITING FOR /start")

while True:
    try:
        resp = requests.get(f"{API}/getUpdates", params={"offset":offset,"timeout":20}, timeout=25).json()
        for u in resp.get("result", []):
            offset = u["update_id"]+1
            msg = u.get("message",{})
            cid = msg.get("chat",{}).get("id")
            txt = msg.get("text","").strip()
            print(f"Got: {txt} from {cid}")
            if cid and txt:
                CHAT_ID = cid
                if "/start" in txt.lower() or "start" in txt.lower():
                    send(cid, f"🚀 Victa V7.2 AWAKE!\n✅ I hear you Erastus!\n⏰ {ug_time()} Kampala\nEURUSD {get_price():.5f}\nTrader: Erastus Davicta\n\nNext signal in 1 min!")
                else:
                    # No echo anymore - just acknowledge
                    send(cid, f"👍 Got it: {txt}\nBot is awake! {ug_time()}")
        time.sleep(2)
    except Exception as e:
        print(f"Loop error {e}")
        time.sleep(5)
