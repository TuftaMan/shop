import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import OrderCounter


def send_telegram_order_notification(order):
    message_lines = [
        "🛒 *Новый заказ!*",
        "",
        f"🆔 Заказ №{order.id}",
        f"🆔 Номер заказа №{order.order_number}",
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

    for chat in settings.TELEGRAM_CHAT_IDS:

        payload = {
            "chat_id": chat,
            "text": message,
            "parse_mode": "Markdown",
        }

        try:
            requests.post(url, json=payload, timeout=5)
        except Exception:
            # ❗️Никогда не ломаем заказ из-за Telegram
            pass


def generate_order_number(prefix='DW'):
    year = timezone.now().year

    with transaction.atomic():
        counter, _ = OrderCounter.objects.select_for_update().get_or_create(
            year=year
        )
        counter.last_number += 1
        counter.save()

        number = f'{prefix}-{year}-{counter.last_number:04d}'
        return number