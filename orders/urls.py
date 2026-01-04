from django.urls import path
from .views import CheckoutView, OrderSuccessView, order_history, order_track, order_track_result

app_name = 'orders'

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('success/<str:order_number>/', OrderSuccessView.as_view(), name='success'),
    path('order-history', order_history, name='order_history'),
    path('track/', order_track, name='order_track'),
    path('track/result/', order_track_result, name='order_track_result'),
]