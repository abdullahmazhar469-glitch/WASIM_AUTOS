from django.contrib import admin
from .models import Product, Order, Category, Customer, Cart, CartItem, Review, OfflineSale

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Category)
admin.site.register(Customer)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Review)
admin.site.register(OfflineSale)