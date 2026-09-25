import requests, time
BOT_TOKEN="8630263342:AAEXZlPraPxjTzDuoF5312ziQdb5_jyyuNs"
CHAT_ID="6753218887"
prices=[]
def get_price():
    try:
        r=requests.get("https://api.exchangerate-api.com/v4/latest/EUR",timeout=10)
        return r.json()["rates"]["USD"]
    except: return None
def ema(data,p):
    if len(data)<p: return None
    k=2/(p+1); e=sum(data[:p])/p
    for x in data[p:]: e=x*k+e*(1-k)
    return e
def rsi(data,per=14):
    if len(data)<per+1: return 50
    g=l=0
    for i in range(1,per+1):
        ch=data[-i]-data[-i-1]
        if ch>0: g+=ch
        else: l+=abs(ch)
    if l==0: return 70
    return 100-(100/(1+g/l))
def send(m):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",data={"chat_id":CHAT_ID,"text":m},timeout=15)
send("Victa V7 RENDER LIVE - Real EURUSD")
last=""
while True:
    price=get_price()
    if price:
        prices.append(price)
        if len(prices)>50: prices.pop(0)
        if len(prices)>=21:
            e9=ema(prices,9); e21=ema(prices,21); r=rsi(prices,14)
            sig=""
            if e9>e21 and 55<r<75: sig="BUY"
            elif e9<e21 and 25<r<45: sig="SELL"
            if sig and sig!=last:
                last=sig
                send(f"{sig} EURUSD {price:.5f} RSI {r:.1f}")
    time.sleep(60)
