from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View
from django.http import JsonResponse, HttpResponse
from django.template.response import TemplateResponse
from django.contrib import messages
from django.db import transaction
from main.models import Product
from .models import Cart, CartItem
from .forms import AddToCartForm
import json


class CartMixin():
    def get_cart(self, request):
        if hasattr(request, 'cart'):
            return request.cart
        
        if not request.session.session_key:
            request.session.create()    

        cart, created = Cart.objects.get_or_create(
            session_key = request.session.session_key
        )

        request.session['cart_id'] = cart.id
        request.session.modified = True
        return cart
    

class CartModalView(CartMixin, View):
    def get(self, request):
        cart = self.get_cart(request)
        context = {
            'cart': cart,
            'cart_items': cart.items.select_related(
                'product', 
            ).order_by('-added_at')
        }
        return TemplateResponse(request, 'cart/cart_modal.html', context)

        

class AddToCartView(CartMixin, View):
    @transaction.atomic
    def post(self, request, slug):
        cart = self.get_cart(request)
        product = get_object_or_404(Product, slug=slug)

        form = AddToCartForm(request.POST, product=product)

        if not form.is_valid():
            return JsonResponse({
                'error': 'Invalid form data',
                'errors': form.errors,
            }, status=400)
        
        quantity = form.cleaned_data['quantity']
        if product.stock < quantity:
            return JsonResponse({
                'error': f'Товара нет в наличии'
            }, status=400)
        
        existing_item = cart.items.filter(
            product=product
        ).first()

        if existing_item:
            total_quantity = existing_item.quantity + quantity
            if total_quantity > product.stock:
                return JsonResponse({
                'error': f'В наличии есть только {product.stock} предметов'
                }, status=400)
            
        cart_item = cart.add_product(product, quantity)

        request.session['cart_id'] = cart.id
        request.session.modified = True

        if request.headers.get('HX-Request'):
            return HttpResponse(f"""
                <div class="p-3 bg-green-600 text-white rounded shadow mb-2">
                    {product.name.capitalize()} добавлен в корзину
                </div>
                <script>
                    setTimeout(() => {{
                        document.querySelector('#notification-container div')?.remove();
                    }}, 2500);
                </script>
            """)
        else:
            return JsonResponse({
                'success': True,
                'total_items': cart.total_items,
                'message': f'{product.name} добавлен в корзину',
                'cart_item_id': cart_item.id
            })
        

class UpdateCartItemView(CartMixin, View):
    @transaction.atomic
    def post(self, request, item_id):
        cart = self.get_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

        quantity = int(request.POST.get('quantity', 1))

        if quantity < 0:
            return JsonResponse({'error': 'Invalid quantity'}, status=400)
        
        # Если количество = 0, удаляем элемент
        if quantity == 0:
            cart_item.delete()
            # Возвращаем пустую строку - элемент исчезнет со страницы
            return HttpResponse('')
        else:
            if quantity > cart_item.product.stock:
                return JsonResponse({
                    'error': f'В наличии {cart_item.product.stock}'
                }, status=400)
            
            cart_item.quantity = quantity
            cart_item.save()

        request.session['cart_id'] = cart.id
        request.session.modified = True

        # Возвращаем только обновленный элемент
        context = {
            'item': cart_item
        }
        return TemplateResponse(request, 'cart/cart_item.html', context)
    

class RemoveCartItemView(CartMixin, View):
    def post(self, request, item_id):
        cart = self.get_cart(request)

        try:
            cart_item = cart.items.get(id=item_id)
            cart_item.delete()

            request.session['cart_id'] = cart.id
            request.session.modified = True

            # Возвращаем пустую строку - элемент исчезнет
            return HttpResponse('')
            
        except CartItem.DoesNotExist:
            return JsonResponse({'error': 'Предмет не найден'}, status=400)
        

class CartCountView(CartMixin, View):
    def get(self, request):
        cart = self.get_cart(request)
        return JsonResponse({
            'total_items': cart.total_items,
            'subtotal': float(cart.subtotal)
        })
    

class ClearCartView(CartMixin, View):
    def post(self, request):
        cart = self.get_cart(request)
        cart.clear()

        request.session['cart_id'] = cart.id
        request.session.modified = True

        if request.headers.get('HX-Request'):
            # Теперь возвращаем полный cart_modal с пустой корзиной
            return TemplateResponse(request, 'cart/cart_modal.html', {
                'cart': cart,
                'cart_items': []
            })
        return JsonResponse({
            'success': True,
            'message': 'Корзина очищена'
        })
    

class CartSummaryView(CartMixin, View):
    def get(self, request):
        cart = self.get_cart(request)
        context = {
            'cart': cart
        }
        return TemplateResponse(request, 'cart/cart_summary.html', context)