# Binance Futures Webhook Bot

TradingView'den gelen webhook sinyalleriyle Binance Futures işlemleri yapar.

## Özellikler

- SSL Hybrid + QQE MOD sinyaline göre işlem açar
- Telegram bildirimleri gönderir
- Her 30 dakikada bir çalıştığını kontrol eder

## Kurulum

```bash
pip install -r requirements.txt
python binance_futures_webhook_bot.py
```

## Webhook URL

Ngrok ile örnek:
```
https://1234abcd.ngrok-free.app/webhook
```

## Telegram

Bot başlatıldığında ve hata oluştuğunda Telegram mesajı gönderir.
