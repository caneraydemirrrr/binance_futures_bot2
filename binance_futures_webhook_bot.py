import os
import time
import threading
from flask import Flask, request
from binance.client import Client
from binance.exceptions import BinanceAPIException
import requests

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = Flask(__name__)
client = Client(API_KEY, API_SECRET)

@app.route("/")
def index():
    return "Binance Futures Webhook Bot Çalışıyor"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    symbol = data.get("symbol")
    side = data.get("side")

    if not symbol or not side:
        return {"error": "Eksik veri"}, 400

    try:
        quantity = 1  # Buraya pozisyon büyüklüğünü ayarlayabilirsiniz
        client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_BUY if side.lower() == "buy" else Client.SIDE_SELL,
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity
        )
        send_telegram_message(f"✅ İşlem açıldı: {side.upper()} - {symbol}")
        return {"success": True}, 200
    except BinanceAPIException as e:
        send_telegram_message(f"❌ Binance API hatası: {e.message}")
        return {"error": str(e)}, 500

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }
        requests.post(url, json=payload)
    except Exception as e:
        print("Telegram mesaj hatası:", str(e))

def durum_kontrol():
    while True:
        send_telegram_message("🟢 Bot çalışıyor (durum kontrol)")
        time.sleep(1800)

if __name__ == "__main__":
    threading.Thread(target=durum_kontrol, daemon=True).start()
    send_telegram_message("🚀 Bot başlatıldı ve çalışıyor.")
    app.run(host="0.0.0.0", port=5000)
