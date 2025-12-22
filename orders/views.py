from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.views.generic import View
from .forms import OrderForm
from .models import Order, OrderItem
from cart.views import CartMixin
from django.shortcuts import get_object_or_404
from decimal import Decimal
from django.db import transaction
from .utils import send_telegram_order_notification


@method_decorator(login_required(login_url='users/login'), name='dispatch')
class CheckoutView(CartMixin, View):
    def get(self, request):
        cart = self.get_cart(request)

        if cart.total_items == 0:
            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/empty_cart.html', {'message': 'Ваша корзина пуста'})
            return redirect('cart:cart_modal')
        
        total_price = cart.subtotal

        form = OrderForm(user=request.user)
        context = {
            'form': form,
            'cart': cart,
            'cart_items': cart.items.select_related('product').order_by('added_at'),
            'total_price': total_price,
        }

        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'orders/checkout_content.html', context)
        return render(request, 'orders/checkout.html', context)
    
    @method_decorator(login_required(login_url='users/login'), name='dispatch')
    @transaction.atomic
    def post(self, request):
        cart = self.get_cart(request)

        if cart.total_items == 0:
            return redirect('cart:cart_modal')

        form = OrderForm(request.POST, user=request.user)

        if not form.is_valid():
            return render(request, 'orders/checkout.html', {
                'form': form,
                'cart': cart,
                'cart_items': cart.items.select_related('product'),
                'total_price': cart.subtotal,
            })

        order = Order.objects.create(
            user=request.user,
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            email=request.user.email,
            address1=form.cleaned_data['address1'],
            address2=form.cleaned_data['address2'],
            city=form.cleaned_data['city'],
            country=form.cleaned_data['country'],
            province=form.cleaned_data['province'],
            postal_code=form.cleaned_data['postal_code'],
            phone=form.cleaned_data['phone'],
            total_price=cart.subtotal,
        )

        for item in cart.items.select_related('product'):
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            )

        cart.items.all().delete()

        send_telegram_order_notification(order)

        return redirect('orders:success')