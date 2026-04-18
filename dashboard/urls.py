from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('order/<int:product_id>/', views.order_now, name='order_now'),
    path('admin/invoice/<int:order_id>/', views.admin_order_invoice, name='admin_order_invoice'),
    path('admin/offline-invoice/<int:sale_id>/', views.offline_invoice, name='offline_invoice'),
]