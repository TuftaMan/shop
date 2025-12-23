import requests
from django.conf import settings


def send_telegram_order_notification(order):
    message_lines = [
        "🛒 *Новый заказ!*",
        "",
        f"🆔 Заказ №{order.id}",
        f"👤 Имя: {order.first_name} {order.last_name}",
        f"📧 Email: {order.email}",
        f"📞 Телефон: {order.phone or '—'}",
        "",
        "📦 Товары:",
    ]

    for item in order.items.select_related('product'):
        message_lines.append(
            f"• {item.product.name} × {item.quantity} = {item.get_total_price()} ₽"
        )

    message_lines.extend([
        "",
        f"💰 Итого: *{order.total_price} ₽*",
    ])

    message = "\n".join(message_lines)

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        # ❗️Никогда не ломаем заказ из-за Telegram
        pass
