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


@method_decorator(login_required(login_url='users/login'), name='dispatch')
class CheckOutView(CartMixin, View):
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
            'cart_items': cart.items.select_related('product').order_by('_added_at'),
            'total_price': total_price,
        }

        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'orders/checkout_content.html', context)
        return render(request, 'orders/checkout.html', context)
    
    def post(self, request):
        cart = self.get_cart(request)
        payment_provider = request.POST.get('payment_provider')

        if cart.total_items == 0:
            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/empty_cart.html', {'message': 'Ваша корзина пуста'})
            return redirect('cart:cart_modal')
        
        if not payment_provider or payment_provider not in ['stripe', 'heleket']:
            context = {
                'form': OrderForm(user=request.user),
                'cart': cart,
                'cart_items': cart.items.select_related('product').order_by('_added_at'),
                'total_price': cart.subtotal,
                'error_message': 'Пожалуйста выберите метод оплаты',
            }
            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/checkout_context.html', context)
            return render(request, 'orders/checkout.html', context)
        total_price = cart.subtotal
        form_data = request.POST.copy()
        if not form_data.get('email'):
            form_data['email'] = request.user.email
        form = OrderForm(form_data, user=request.user)

        if form.is_valid():
            order = Order.objects.create(
                user=request.user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                address1=form.cleaned_data['address1'],
                address2=form.cleaned_data['address2'],
                city=form.cleaned_data['city'],
                country=form.cleaned_data['country'],
                province=form.cleaned_data['province'],
                postal_code=form.cleaned_data['postal_code'],
                phone=form.cleaned_data['phone'],
                special_instructions='',
                total_price=total_price,
                payment_provider=payment_provider,
            )

            for item in cart.items.select_related('product'):
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price or Decimal('0.00')
                )

            # try:
            #     if payment_provider == '__stripe':
            #         checkout_session = 