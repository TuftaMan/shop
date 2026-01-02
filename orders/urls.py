from django.urls import path
from .views import CheckoutView, OrderSuccessView, order_history

app_name = 'orders'

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('success/', OrderSuccessView.as_view(), name='success'),
    path('order-history', order_history, name='order_history'),
]