from django.shortcuts import render, redirect, get_object_or_404
from shop.models import Order, Product, OfflineSale, Category
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDay, TruncMonth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
import json
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone

def is_staff(user):
    return user.is_authenticated and user.is_staff

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            error = 'Invalid username or password'
    return render(request, 'login.html', {'error': error})

def admin_logout(request):
    logout(request)
    return redirect('admin_login')

@login_required(login_url='admin_login')
@user_passes_test(is_staff, login_url='admin_login')
def admin_dashboard(request):
    # ==========================================
    # 1. POST HANDLERS
    # ==========================================
    if request.method == 'POST':
        
        # --- DELETE OFFLINE SALE ---
        if 'delete_offline_sale' in request.POST:
            sale_id = request.POST.get('offline_sale_id')
            try:
                sale = OfflineSale.objects.get(id=sale_id)
                sale.product.stock += sale.quantity
                sale.product.save()
                sale.delete()
                messages.success(request, '✅ Offline sale deleted! Stock restored.')
            except OfflineSale.DoesNotExist:
                messages.error(request, '❌ Sale not found.')
            return redirect('admin_dashboard')

        # --- EDIT OFFLINE SALE ---
        elif 'edit_offline_sale' in request.POST:
            sale_id = request.POST.get('offline_sale_id')
            new_product_id = request.POST.get('product_id')
            new_qty = int(request.POST.get('quantity') or 0)
            new_received = Decimal(str(request.POST.get('received_amount') or 0))
            new_shop_name = request.POST.get('shop_name', '')
            new_comments = request.POST.get('comments', '')
            
            try:
                sale = OfflineSale.objects.get(id=sale_id)
                old_product = sale.product
                old_qty = sale.quantity
                
                new_product = Product.objects.get(id=new_product_id)
                
                new_total = Decimal(str(new_qty)) * new_product.price
                new_balance = new_total - new_received
                
                old_product.stock += old_qty
                old_product.save()
                
                if new_product.stock >= new_qty:
                    new_product.stock -= new_qty
                    new_product.save()
                    
                    sale.product = new_product
                    sale.quantity = new_qty
                    sale.price = new_product.price
                    sale.received_amount = new_received
                    sale.balance_amount = new_balance
                    sale.shop_name = new_shop_name
                    sale.comments = new_comments
                    sale.save()
                    
                    messages.success(request, f'✅ Sale #{sale_id} updated successfully!')
                else:
                    old_product.stock -= old_qty
                    old_product.save()
                    messages.error(request, f'❌ Not enough stock for {new_product.name}!')
                    
            except Exception as e:
                messages.error(request, f'❌ Error: {str(e)}')
            
            return redirect('admin_dashboard')

        # --- ADD PRODUCT ---
        elif 'add_product' in request.POST:
            name = request.POST.get('name')
            part_number = request.POST.get('part_number')
            description = request.POST.get('description')
            category_id = request.POST.get('category_id')
            barcode = request.POST.get('barcode')
            cost_price = request.POST.get('cost_price')
            price = request.POST.get('price')
            stock = request.POST.get('stock')
            image = request.FILES.get('image')
            
            if name and price and stock:
                Product.objects.create(
                    name=name,
                    part_number=part_number,
                    description=description,
                    category_id=category_id if category_id else None,
                    barcode=barcode,
                    cost_price=cost_price,
                    price=price,
                    stock=stock,
                    image=image
                )
                messages.success(request, '✅ Product added successfully')
            return redirect('admin_dashboard')

        # --- ADD CATEGORY ---
        elif 'add_category' in request.POST:
            name = request.POST.get('name')
            description = request.POST.get('description')
            image = request.FILES.get('image')
            if name:
                Category.objects.create(name=name, description=description, image=image)
                messages.success(request, '✅ Category added successfully')
            return redirect('admin_dashboard')

        # --- ADD OFFLINE SALE --- 
        elif 'record_sale' in request.POST:
            product_id = request.POST.get('product_id')
            qty = int(request.POST.get('quantity') or 0)
            price = float(request.POST.get('custom_price') or 0)
            received = float(request.POST.get('received') or 0)
            shop_name = request.POST.get('shop_name', '')
            note = request.POST.get('comments', '')

            product = get_object_or_404(Product, id=product_id)
            cost_price = float(product.cost_price) if product.cost_price else product.price * 0.7

            total = qty * price
            balance = total - received

            OfflineSale.objects.create(
                product=product,
                quantity=qty,
                cost_price=cost_price,
                price=price,
                received_amount=received,
                balance_amount=balance,
                shop_name=shop_name,
                comments=note,
                date=timezone.now()
            )

            product.stock -= qty
            product.save()
            messages.success(request, '✅ Offline sale recorded successfully!')
            return redirect('admin_dashboard')

        # --- CHANGE ORDER STATUS ---
        elif 'change_status' in request.POST:
            Order.objects.filter(id=request.POST.get('order_id')).update(status=request.POST.get('status'))
            messages.success(request, '✅ Order status updated')
            return redirect('admin_dashboard')

        # --- DELETE PRODUCT ---
        elif 'delete_product' in request.POST:
            Product.objects.filter(id=request.POST.get('product_id')).delete()
            messages.success(request, '✅ Product deleted successfully')
            return redirect('admin_dashboard')

        # --- DELETE CATEGORY ---
        elif 'delete_category' in request.POST:
            Category.objects.filter(id=request.POST.get('category_id')).delete()
            messages.success(request, '✅ Category deleted successfully')
            return redirect('admin_dashboard')

        # --- EDIT PRODUCT ---
        elif 'edit_product' in request.POST:
            pid = request.POST.get('product_id')
            product = Product.objects.get(id=pid)
            product.name = request.POST.get('name')
            product.part_number = request.POST.get('part_number')
            product.description = request.POST.get('description')
            product.category_id = request.POST.get('category_id')
            product.barcode = request.POST.get('barcode')
            product.cost_price = request.POST.get('cost_price')
            product.price = request.POST.get('price')
            product.stock = request.POST.get('stock')
            product.save()
            messages.success(request, '✅ Product updated')
            return redirect('admin_dashboard')

    # ==========================================
    # 2. DATA FETCHING
    # ==========================================
    
    # Basic Stats
    delivered_orders = Order.objects.filter(status='Delivered')
    total_revenue = delivered_orders.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0')
    total_revenue_float = float(total_revenue)
    orders_completed = delivered_orders.count()
    pending_orders = Order.objects.filter(status='Pending').count()
    avg_order_value = total_revenue_float / orders_completed if orders_completed > 0 else 0
    
    # Daily Data (Last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Daily Online Revenue
    daily_online_data = {}
    current_date = start_date
    while current_date <= end_date:
        daily_online_data[current_date.strftime('%Y-%m-%d')] = {
            'revenue': 0, 'orders': 0, 'day_name': current_date.strftime('%d %b')
        }
        current_date += timedelta(days=1)
    
    for order in delivered_orders:
        order_date = order.order_date.date()
        date_key = order_date.strftime('%Y-%m-%d')
        if date_key in daily_online_data:
            daily_online_data[date_key]['revenue'] += float(order.total_price)
            daily_online_data[date_key]['orders'] += 1
    
    online_daily_dates = [data['day_name'] for data in daily_online_data.values()]
    online_daily_revenues = [data['revenue'] for data in daily_online_data.values()]
    online_daily_orders = [data['orders'] for data in daily_online_data.values()]
    
    # Daily Offline Data
    daily_offline_data = {}
    current_date = start_date
    while current_date <= end_date:
        daily_offline_data[current_date.strftime('%Y-%m-%d')] = {
            'revenue': 0, 'quantity': 0, 'transactions': 0, 'day_name': current_date.strftime('%d %b')
        }
        current_date += timedelta(days=1)
    
    offline_sales = OfflineSale.objects.all()
    for sale in offline_sales:
        sale_date = sale.date.date()
        date_key = sale_date.strftime('%Y-%m-%d')
        if date_key in daily_offline_data:
            daily_offline_data[date_key]['revenue'] += float(sale.quantity * sale.price)
            daily_offline_data[date_key]['quantity'] += sale.quantity
            daily_offline_data[date_key]['transactions'] += 1
    
    offline_daily_dates = [data['day_name'] for data in daily_offline_data.values()]
    offline_daily_revenues = [data['revenue'] for data in daily_offline_data.values()]
    offline_daily_quantities = [data['quantity'] for data in daily_offline_data.values()]
    
    # Daily Profit Data
    daily_profit_data = {}
    current_date = start_date
    while current_date <= end_date:
        daily_profit_data[current_date.strftime('%Y-%m-%d')] = {'profit': 0, 'day_name': current_date.strftime('%d %b')}
        current_date += timedelta(days=1)
    
    for sale in offline_sales:
        sale_date = sale.date.date()
        date_key = sale_date.strftime('%Y-%m-%d')
        if date_key in daily_profit_data:
            daily_profit_data[date_key]['profit'] += sale.profit()
    
    for order in delivered_orders:
        order_date = order.order_date.date()
        date_key = order_date.strftime('%Y-%m-%d')
        if date_key in daily_profit_data:
            daily_profit_data[date_key]['profit'] += order.profit()
    
    profit_daily_dates = [data['day_name'] for data in daily_profit_data.values()]
    profit_daily_values = [data['profit'] for data in daily_profit_data.values()]
    
    # Top Selling Parts
    top_parts = (
        delivered_orders.values('product__name', 'product__part_number')
        .annotate(revenue=Sum('total_price'))
        .order_by('-revenue')[:6]
    )
    max_rev = float(top_parts[0]['revenue']) if top_parts else 1
    for p in top_parts:
        p['revenue_val'] = float(p['revenue'] or 0)
        p['share'] = int((p['revenue_val'] / max_rev) * 100) if max_rev > 0 else 0
    
    # Forecast
    daily_avg_revenue = total_revenue_float / 30 if total_revenue_float > 0 else 1000
    forecast = [
        {'month': 'Next 7 Days', 'value': int(daily_avg_revenue * 7), 'confidence': 85, 'growth': 5.0},
        {'month': 'Next 14 Days', 'value': int(daily_avg_revenue * 14), 'confidence': 80, 'growth': 5.5},
        {'month': 'Next 30 Days', 'value': int(daily_avg_revenue * 30), 'confidence': 75, 'growth': 6.0},
    ]
    
    # Orders
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    all_orders = Order.objects.all().order_by('-order_date')
    
    for order in all_orders:
        order.profit = order.profit()
    
    if search_query:
        all_orders = all_orders.filter(Q(customer_name__icontains=search_query) | Q(id__icontains=search_query))
    if status_filter:
        all_orders = all_orders.filter(status=status_filter)
    
    # Offline Sales Summary
    offline_revenue = sum((s.quantity * s.price) for s in offline_sales) if offline_sales else 0
    offline_total_qty = sum(s.quantity for s in offline_sales) if offline_sales else 0
    grand_total = offline_revenue
    
    # Products
    total_cost_value = 0
    total_sale_value = 0
    all_products = Product.objects.all().order_by('-id')
    
    for product in all_products:
        if product.cost_price and product.cost_price > 0:
            product.profit = float(product.price) - float(product.cost_price)
            product.profit_margin = ((float(product.price) - float(product.cost_price)) / float(product.cost_price)) * 100
        else:
            product.profit = float(product.price) * 0.3
            product.profit_margin = 30.0
        
        product.cost_value = float(product.cost_price or 0) * product.stock
        product.sale_value = float(product.price) * product.stock
        total_cost_value += product.cost_value
        total_sale_value += product.sale_value
    
    # Stock Alerts
    low_stock_products = Product.objects.filter(stock__lte=5, stock__gt=0)
    out_of_stock_products = Product.objects.filter(stock=0)
    
    # Profit Analytics
    total_online_profit = sum(order.profit() for order in delivered_orders)
    total_offline_profit = sum(sale.profit() for sale in offline_sales)
    total_profit = total_online_profit + total_offline_profit
    
    # Top Profitable Products
    profitable_products = {}
    for sale in offline_sales:
        product_name = sale.product.name
        profit = sale.profit()
        if product_name not in profitable_products:
            profitable_products[product_name] = {'profit': 0, 'quantity': 0}
        profitable_products[product_name]['profit'] += profit
        profitable_products[product_name]['quantity'] += sale.quantity
    
    top_profit_products = sorted(profitable_products.items(), key=lambda x: x[1]['profit'], reverse=True)[:5]
    
    # High/Low Margin Products
    high_margin_products = []
    low_margin_products = []
    for prod in all_products:
        if prod.cost_price and prod.cost_price > 0:
            margin = prod.profit_margin
            if margin > 30:
                high_margin_products.append({'name': prod.name, 'margin': margin, 'profit_per_unit': prod.profit})
            elif margin < 10:
                low_margin_products.append({'name': prod.name, 'margin': margin, 'profit_per_unit': prod.profit})
    
    # Most Demanding Shops
    shop_sales = {}
    for sale in offline_sales:
        shop_name = sale.shop_name if sale.shop_name else "Walk-in Customer"
        if shop_name not in shop_sales:
            shop_sales[shop_name] = {'revenue': 0, 'quantity': 0}
        shop_sales[shop_name]['revenue'] += (sale.quantity * sale.price)
        shop_sales[shop_name]['quantity'] += sale.quantity
    
    top_shops = sorted(shop_sales.items(), key=lambda x: x[1]['revenue'], reverse=True)[:5]
    top_shops_names = [shop[0] for shop in top_shops]
    top_shops_revenue = [float(shop[1]['revenue']) for shop in top_shops]
    top_shops_quantity = [shop[1]['quantity'] for shop in top_shops]
    
    # Most Demanding Products
    product_sales = {}
    for sale in offline_sales:
        product_name = sale.product.name
        if product_name not in product_sales:
            product_sales[product_name] = {'quantity': 0, 'revenue': 0}
        product_sales[product_name]['quantity'] += sale.quantity
        product_sales[product_name]['revenue'] += (sale.quantity * sale.price)
    
    top_products = sorted(product_sales.items(), key=lambda x: x[1]['quantity'], reverse=True)[:5]
    top_products_names = [product[0] for product in top_products]
    top_products_quantity = [product[1]['quantity'] for product in top_products]
    
    # Categories
    categories = Category.objects.all()
    
    # ==========================================
    # 3. RENDER
    # ==========================================
    context = {
        'total_revenue': int(total_revenue_float),
        'orders_completed': orders_completed,
        'pending_orders': pending_orders,
        'avg_order_value': round(avg_order_value, 2),
        
        'online_daily_dates': json.dumps(online_daily_dates),
        'online_daily_revenues': json.dumps(online_daily_revenues),
        'online_daily_orders': json.dumps(online_daily_orders),
        
        'offline_daily_dates': json.dumps(offline_daily_dates),
        'offline_daily_revenues': json.dumps(offline_daily_revenues),
        'offline_daily_quantities': json.dumps(offline_daily_quantities),
        
        'profit_daily_dates': json.dumps(profit_daily_dates),
        'profit_daily_values': json.dumps(profit_daily_values),
        
        'top_parts': top_parts,
        'forecast': forecast,
        
        'all_orders': all_orders[:20],
        'search_query': search_query,
        'status_filter': status_filter,
        
        'offline_sales': offline_sales,
        'offline_revenue': offline_revenue,
        'offline_total_qty': offline_total_qty,
        'total_sales_amount': grand_total,
        
        'all_products': all_products,
        'products': Product.objects.all().order_by('-id'),
        'categories': categories,
        
        'total_cost_value': total_cost_value,
        'total_sale_value': total_sale_value,
        'total_products': all_products.count(),
        
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        
        'total_online_profit': int(total_online_profit),
        'total_offline_profit': int(total_offline_profit),
        'total_profit': int(total_profit),
        'top_profit_products': top_profit_products,
        'high_margin_products': high_margin_products[:5],
        'low_margin_products': low_margin_products[:5],
        
        'top_shops_names': json.dumps(top_shops_names),
        'top_shops_revenue': json.dumps(top_shops_revenue),
        'top_shops_quantity': json.dumps(top_shops_quantity),
        'top_products_names': json.dumps(top_products_names),
        'top_products_quantity': json.dumps(top_products_quantity),
        
        'current_time': datetime.now().strftime("%A, %d %b %Y | %I:%M %p"),
    }
    return render(request, 'dashboard.html', context)


def order_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        quantity = int(request.POST.get('quantity', 1))
        
        order = Order.objects.create(
            product=product,
            customer_name=name,
            phone=phone,
            address=address,
            quantity=quantity,
            total_price=product.price * quantity,
            status='Pending'
        )
        product.stock -= quantity
        product.save()
        
        return render(request, 'invoice.html', {'order': order})
    
    return render(request, 'order.html', {'product': product})


def admin_order_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'invoice.html', {'order': order})


def offline_invoice(request, sale_id):
    sale = get_object_or_404(OfflineSale, id=sale_id)
    total = sale.quantity * sale.price
    balance = total - sale.received_amount
    return render(request, 'offline_invoice_template.html', {
        'sale': sale,
        'total': total,
        'balance': balance
    })