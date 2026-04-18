from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('profile/', views.profile, name='profile'),
    
    # Products
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('search-barcode/', views.search_by_barcode, name='search_by_barcode'),
    path('add-review/<int:product_id>/', views.add_review, name='add_review'),
    
    # Cart
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('update-cart/<int:item_id>/', views.update_cart, name='update_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:product_id>/', views.order_form, name='order_form'),
    
    # Export
    path('export-orders/', views.export_orders_excel, name='export_orders'),
    path('export-products/', views.export_products_excel, name='export_products'),
]