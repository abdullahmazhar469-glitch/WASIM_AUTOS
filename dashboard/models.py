# dashboard/models.py
# This app uses models from shop app
# No separate models needed for dashboard

from shop.models import Product, Order, OfflineSale, Category, Customer, Cart, CartItem, Review

# All models are imported from shop app
# You can use them directly in dashboard views