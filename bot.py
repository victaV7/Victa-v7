from flask import Flask
import threading, requests, time, os
from datetime import datetime
import pytz

app = Flask(__name__)
@app.route('/')
def home(): return "Victa V7 SMART LIVE - Secure"

threading.Thread(target=lambda: app.run(host='0.0.0.0',port=10000)).start()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN: raise Exception("BOT_TOKEN missing!")
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

CHAT_ID = None
price_history = []
last_price = 0
offset = 0

def send(c,t):
    try: requests.post(f"{API}/sendMessage", data={"chat_id":c,"text":t}, timeout=10)
    except: pass

def get_price():
    try: return float(requests.get("https://open.er-api.com/v6/latest/EUR",timeout=10).json()["rates"]["USD"])
    except: return None

def calc_rsi(p, period=14):
    if len(p) < period+1: return 50
    gains=[]; losses=[]
    for i in range(1,len(p)):
        d=p[i]-p[i-1]
        gains.append(d if d>0 else 0); losses.append(abs(d) if d<0 else 0)
    ag=sum(gains[-period:])/period; al=sum(losses[-period:])/period
    if al==0: return 70
    return 100-(100/(1+ag/al))

def time_ug(): return datetime.now(pytz.timezone('Africa/Kampala')).strftime("%H:%M:%S")

print("Victa V7 SMART SECURE Starting...")

while True:
    try:
        r=requests.get(f"{API}/getUpdates",params={"offset":offset,"timeout":10},timeout=15).json()
        for u in r.get("result",[]):
            offset=u["update_id"]+1
            m=u.get("message",{}); cid=m.get("chat",{}).get("id"); txt=m.get("text","")
            if cid:
                CHAT_ID=cid
                if "/start" in txt:
                    send(cid,"🚀 Victa V7 SMART SECURE LIVE!\n✅ No echo bug\n✅ Token hidden\n✅ Only STRONG signals\nTrader: Erastus Davicta\n📍 Kampala Time: "+time_ug())
        price=get_price()
        if price:
            price_history.append(price)
            if len(price_history)>50: price_history.pop(0)
            rsi=calc_rsi(price_history)
            fast=sum(price_history[-9:])/min(9,len(price_history))
            slow=sum(price_history[-21:])/min(21,len(price_history))
            sig=None
            if price>fast>slow and rsi>60:
                sig=f"🟢 STRONG BUY\n📈 EURUSD: {price:.5f}\nRSI: {rsi:.1f} Bullish\n⏰ {time_ug()} Kampala"
            elif price<fast<slow and rsi<40:
                sig=f"🔴 STRONG SELL\n📉 EURUSD: {price:.5f}\nRSI: {rsi:.1f} Bearish\n⏰ {time_ug()} Kampala"
            if sig and CHAT_ID and abs(price-last_price)>0.00005:
                send(CHAT_ID,sig); last_price=price
        time.sleep(60)
    except Exception as e:
        print(e); time.sleep(10)
