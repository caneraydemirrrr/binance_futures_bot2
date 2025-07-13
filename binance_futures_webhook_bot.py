
# binance_futures_webhook_bot.py
# TradingView Webhook ile Binance Futures botu (SSL Hybrid + QQE MOD sinyallerine göre)

from flask import Flask, request, jsonify
from binance.client import Client
from binance.enums import *
import requests
import threading
import time
import datetime

# === Binance API ===
API_KEY = "QdcqyZkVRwZZEmzQshtz1DUW54BHtlt0jSvlYMef961nHJj66OiDxmwSJw9mIKrz"
API_SECRET = "1JERKJqQAiISzve2lwHWQdbZOLaR5xwusQH0oLxxGgKMz0RrsYqYSlZcMcJPCrKR"
client = Client(API_KEY, API_SECRET)

# === Telegram ===
TELEGRAM_TOKEN = "7746642327:AAHxhpVGZyspdyfEHvkQLRrB-Tcsmi6DVzc"
TELEGRAM_CHAT_ID = "5691191198"

# === Flask ===
app = Flask(__name__)

# === Ayarlar ===
LEVERAGE = 10
RISK_PERCENT = 0.20
STOP_LOSS_PERCENT = 5

positions = {}  # symbol -> {"side": "LONG"/"SHORT", "entry": price}
last_action_time = time.time()

def send_telegram_message(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram mesaj hatası: {e}")

def get_balance():
    balance = client.futures_account_balance()
    usdt_balance = float([b["balance"] for b in balance if b["asset"] == "USDT"][0])
    return usdt_balance

def place_order(symbol, side, qty):
    client.futures_change_leverage(symbol=symbol, leverage=LEVERAGE)
    return client.futures_create_order(
        symbol=symbol,
        side=SIDE_BUY if side == "LONG" else SIDE_SELL,
        type=ORDER_TYPE_MARKET,
        quantity=qty
    )

def close_order(symbol, side, qty):
    close_side = SIDE_SELL if side == "LONG" else SIDE_BUY
    return client.futures_create_order(
        symbol=symbol,
        side=close_side,
        type=ORDER_TYPE_MARKET,
        quantity=qty
    )

@app.route('/webhook', methods=['POST'])
def webhook():
    global last_action_time
    data = request.json
    symbol = data.get("symbol")
    symbol = symbol.replace('.P', '')  # .P uzantısını kaldır
    action = data.get("action")  # "LONG" or "SHORT"

    if not symbol or not action:
        return jsonify({"error": "Eksik veri"}), 400

    try:
        mark_price = float(client.futures_mark_price(symbol=symbol)['markPrice'])
        balance = get_balance()
        qty = round((balance * RISK_PERCENT * LEVERAGE) / mark_price, 2)

        current_pos = positions.get(symbol)

        # Pozisyon ters sinyalse önce kapat, sonra yeni pozisyon aç
        if current_pos:
            if current_pos["side"] != action:
                close_order(symbol, current_pos["side"], qty)
                send_telegram_message(f"📤 {symbol} {current_pos['side']} kapatıldı (ters sinyal)")
                del positions[symbol]

        if symbol not in positions:
            place_order(symbol, action, qty)
            positions[symbol] = {"side": action, "entry": mark_price}
            last_action_time = time.time()
            send_telegram_message(f"📥 {symbol} {action} açıldı\nFiyat: {mark_price}, Miktar: {qty}")

    except Exception as e:
        send_telegram_message(f"🚨 HATA: {e}")
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "ok"})

# === Durum kontrolü ===
def periodic_status_check():
    global last_action_time
    while True:
        try:
            now = time.time()
            if now - last_action_time > 1800:
                send_telegram_message("ℹ️ Son 30 dakikada hiç işlem açılmadı. Bot çalışıyor ama sinyal gelmedi veya koşullar oluşmadı.")
                last_action_time = now
        except Exception as e:
            send_telegram_message(f"⛔ Durum kontrolü hatası: {e}")
        time.sleep(1800)

# === Bot başlatma ===
if __name__ == "__main__":
    send_telegram_message("✅ Bot başlatıldı ve çalışıyor.")
    threading.Thread(target=periodic_status_check, daemon=True).start()
    print("🚀 Bot çalışıyor... Flask sunucusu başlatılıyor.")
    app.run(host="0.0.0.0", port=5000)
