from django.contrib import admin
from .models import Customer, Product, Order, Tag, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    # Sirf wohi fields rakhein jo model mein hain
    list_display = ('name', 'email', 'user') 
    search_fields = ('name', 'email', 'user__username')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price')
    search_fields = ('name', 'category__name')
    list_filter = ('category',)
    

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'date_ordered', 'complete', 'transaction_id', 'status')
    list_filter = ('status', 'date_ordered', 'complete')
    search_fields = ('customer__name', 'transaction_id')
    list_editable = ('status',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ('name',)

from .models import OrderItem, ShippingAddress
admin.site.register(OrderItem)
admin.site.register(ShippingAddress)