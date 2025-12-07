from django.db import models
from django.conf import settings
from main.models import Product


class Order(models.Model):
    STATUS_CHOICES = (
        ('pedding', 'Ожидает обработки'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    )
    