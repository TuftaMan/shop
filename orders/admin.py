from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('image_preview', 'product', 'quantity',
              'price', 'get_total_price')
    readonly_fields = ('image_preview', 'get_total_price')
    can_delete = False


    def image_preview(self, obj):
        if obj.product.main_image:
            return mark_safe(f'<img src="{obj.product.main_image.url}" style="max-heigh: 100px; "max-width: 100px; object-fit: cover;" />')
        return mark_safe('<span style="color: gray;"> No image</span>')
    image_preview.short_description = 'Image'


    def get_total_price(self, obj):
        try:
            return obj.get_total_price()
        except TypeError:
            return mark_safe('<span style="color: red;">Invalid Data</span>')
    get_total_price.short_description = 'Total Price'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'email',
        'total_price',
        'status',
        'created_at',
    )

    list_filter = ('status',)
    search_fields = ('email', 'first_name', 'last_name')
    date_hierarchy = 'created_at'

    readonly_fields = (
        'created_at',
        'total_price',
    )

    inlines = [OrderItemInline]

    fieldsets = (
        ('Order Information', {
            'fields': (
                'user',
                'first_name',
                'last_name',
                'email',
                'phone',
                'total_price',
            )
        }),
        ('Delivery', {
            'fields': (
                'address1',
                'address2',
                'country',
                'city',
                'province',
                'postal_code',
            )
        }),
        ('Status', {
            'fields': ('status',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + (
                'user',
                'first_name',
                'last_name',
                'email',
                'phone',
                'address1',
                'address2',
                'country',
                'city',
                'province',
                'postal_code',
            )
        return self.readonly_fields