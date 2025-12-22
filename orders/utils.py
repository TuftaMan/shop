import requests
from django.conf import settings

def send_telegram_order_notification(order):
    message = (
        f"🛒 НОВЫЙ ЗАКАЗ\n\n"
        f"Имя: {order.name}\n"
        f"Телефон: {order.phone}\n"
        f"Email: {order.email}\n"
        f"Адрес: {order.address}\n\n"
        f"Сумма: {order.total_price} ₽"
    )

    url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TG_CHAT_ID,
        "text": message
    }

    requests.post(url, data=payload)
