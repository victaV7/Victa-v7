from flask import Flask
import threading
import requests, time

app = Flask(__name__)
@app.route('/')
def home():
    return "Victa V7 LIVE - Bot is Running!"

threading.Thread(target=lambda: app.run(host='0.0.0.0',port=10000)).start()

BOT_TOKEN = "8466153743:AAHv2lV5yQKcQ8YQ8YQ8YQ8YQ8YQ8YQ8"  # <-- REPLACE WITH YOUR REAL TOKEN FROM BOTFATHER
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def get_updates(offset=0):
    try:
        r = requests.get(f"{API}/getUpdates", params={"offset":offset,"timeout":25}, timeout=30)
        return r.json()
    except:
        return {}

def send(chat_id, text):
    try:
        requests.post(f"{API}/sendMessage", data={"chat_id":chat_id,"text":text})
    except:
        pass

print("Victa V7 Started...")
offset = 0
while True:
    try:
        data = get_updates(offset)
        for u in data.get("result", []):
            offset = u["update_id"]+1
            msg = u.get("message",{})
            chat_id = msg.get("chat",{}).get("id")
            text = msg.get("text","")
            if chat_id:
                if text == "/start":
                    send(chat_id, "🔥 Victa V7 is LIVE on RENDER 24/7! ✅")
                else:
                    send(chat_id, f"You said: {text}\nVicta V7 is working!")
    except Exception as e:
        print(e)
    time.sleep(1)
