from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
import json
import datetime
from .models import Product, Category, Customer, Order, OrderItem, ShippingAddress
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import ProductForm, CategoryForm

# ==============================================================================
#  HELPER & UTILS
# ==============================================================================
def get_cart_data(request):
    if request.user.is_authenticated:
        customer, created = Customer.objects.get_or_create(user=request.user, defaults={'name': request.user.username, 'email': request.user.email})
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        # For non-logged in users (cookie cart placeholder or empty)
        # For now, empty
        items = []
        order = {'get_cart_total': 0, 'get_cart_items': 0}
        cartItems = 0
    return {'cartItems': cartItems, 'order': order, 'items': items}

# ==============================================================================
#  MAIN VIEWS
# ==============================================================================

def home(request):
    data = get_cart_data(request)
    cartItems = data['cartItems']
    
    search_query = request.GET.get('search', '')
    products = Product.objects.all()
    categories = Category.objects.all()
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(category__name__icontains=search_query)
        ).distinct()

    
    pending_orders = []
    if request.user.is_authenticated:
        customer = request.user.customer
        # Show only pending orders on dashboard
        pending_orders = Order.objects.filter(customer=customer, complete=True, status='Pending').order_by('-date_ordered')

    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'cartItems': cartItems,
        'pending_orders': pending_orders
    }
    return render(request, 'home.html', context)

@login_required(login_url='login')
def order_history(request):
    data = get_cart_data(request)
    cartItems = data['cartItems']
    
    customer = request.user.customer
    orders = Order.objects.filter(customer=customer, complete=True).order_by('-date_ordered')
    
    context = {'orders': orders, 'cartItems': cartItems}
    return render(request, 'history.html', context)

def category_products(request, category_slug):
    data = get_cart_data(request)
    cartItems = data['cartItems']
    
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category)
    categories = Category.objects.all() 
    context = {
        'products': products, 'category': category, 'categories': categories,
        'cartItems': cartItems
    }
    return render(request, 'category_products.html', context)

@login_required(login_url='login')
def product_detail(request, pk):
    data = get_cart_data(request)
    cartItems = data['cartItems']
    
    product = get_object_or_404(Product, id=pk)
    context = {
        'product': product,
        'cartItems': cartItems
    }
    return render(request, 'product_detail.html', context)

def cart(request):
    data = get_cart_data(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'cart.html', context)

def checkout(request):
    data = get_cart_data(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'checkout.html', context)

def update_item(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    
    print('Action:', action)
    print('Product:', productId)

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)
    elif action == 'delete':
        orderItem.quantity = 0

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)

def process_order(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        
        # Check if we have specific selected items
        selected_product_ids = data.get('selected_product_ids')
        
        if selected_product_ids and isinstance(selected_product_ids, list):
            # Partial Checkout Logic
            main_order, created = Order.objects.get_or_create(customer=customer, complete=False)
            try:
                # Create a new separate order for selected items
                order = Order.objects.create(customer=customer, complete=False)
                
                for pid in selected_product_ids:
                    product_to_buy = Product.objects.get(id=pid)
                    # Find the item in the main cart
                    item_to_move = OrderItem.objects.get(order=main_order, product=product_to_buy)
                    # Move it to the new order
                    item_to_move.order = order
                    item_to_move.save()
                    
            except Exception as e:
                return JsonResponse(f'Error processing selected items: {str(e)}', safe=False, status=400)
        else:
            # Full Cart Checkout
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
        
        # Verify total (security check - backend calculation)
        
        order.transaction_id = transaction_id
        
        # Mark as complete
        order.complete = True
        order.status = 'Pending'
        order.save()

        # Save Shipping Address
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )
        
    return JsonResponse('Payment submitted..', safe=False)

# ==============================================================================
#  AUTHENTICATION VIEWS
# ==============================================================================

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('signup')

        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name
        )
        Customer.objects.create(
            user=user, name=f"{user.first_name} {user.last_name}", email=user.email
        )
        messages.success(request, "Account created successfully. Please log in.")
        return redirect('login')

    return render(request, 'signup.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        username_or_email = request.POST.get('username_or_email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username_or_email, password=password)
        if user is None:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
                
        if user is not None:
            login(request, user)
            # Ensure customer profile exists
            Customer.objects.get_or_create(user=user, defaults={'name': user.username, 'email': user.email})
            return redirect('home')
        else:
            messages.error(request, "Invalid username/email or password.")
            return redirect('login')
            
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('login')

# ==============================================================================
#  CUSTOM ADMIN VIEWS
# ==============================================================================

def is_admin(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(is_admin, login_url='admin_login')
def admin_dashboard(request):
    total_orders = Order.objects.filter(complete=True).count()
    total_products = Product.objects.all().count()
    total_customers = Customer.objects.all().count()
    
    # Recent orders
    recent_orders = Order.objects.filter(complete=True).order_by('-date_ordered')[:5]

    context = {
        'total_orders': total_orders,
        'total_products': total_products,
        'total_customers': total_customers,
        'recent_orders': recent_orders
    }
    return render(request, 'admin/dashboard.html', context)

def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid admin credentials.")
            
    return render(request, 'admin/admin_login.html')

@user_passes_test(is_admin, login_url='admin_login')
def admin_products(request):
    products = Product.objects.all()
    return render(request, 'admin/product_list.html', {'products': products})

@user_passes_test(is_admin, login_url='admin_login')
def add_product(request):
    form = ProductForm()
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Product added successfully")
            return redirect('admin_products')
            
    return render(request, 'admin/product_form.html', {'form': form, 'title': 'Add Product'})

@user_passes_test(is_admin, login_url='admin_login')
def edit_product(request, pk):
    product = get_object_or_404(Product, id=pk)
    form = ProductForm(instance=product)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully")
            return redirect('admin_products')

    return render(request, 'admin/product_form.html', {'form': form, 'title': 'Edit Product'})

@user_passes_test(is_admin, login_url='admin_login')
def delete_product(request, pk):
    product = get_object_or_404(Product, id=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Product deleted successfully")
        return redirect('admin_products')
    return render(request, 'admin/delete_confirm.html', {'item': product})

@user_passes_test(is_admin, login_url='admin_login')
def admin_orders(request):
    orders = Order.objects.filter(complete=True).order_by('-date_ordered')
    return render(request, 'admin/order_list.html', {'orders': orders})

@user_passes_test(is_admin, login_url='admin_login')
def update_order_status(request, pk):
    order = get_object_or_404(Order, id=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        order.status = status
        order.save()
        messages.success(request, f"Order #{order.id} updated to {status}")
    return redirect('admin_orders')

@user_passes_test(is_admin, login_url='admin_login')
def admin_customers(request):
    customers = Customer.objects.all()
    return render(request, 'admin/customer_list.html', {'customers': customers})

@login_required(login_url='login')
def customer_orders(request):
    customer = request.user.customer
    orders = Order.objects.filter(customer=customer, complete=True).order_by('-date_ordered')
    context = {'orders': orders}
    return render(request, 'customer_orders.html', context)

# Admin: Category Management
@login_required(login_url='admin_login')
def admin_categories(request):
    categories = Category.objects.all()
    return render(request, 'admin/category_list.html', {'categories': categories})

@login_required(login_url='admin_login')
def add_category(request):
    form = CategoryForm()
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_categories')
    return render(request, 'admin/category_form.html', {'form': form, 'title': 'Add Category'})

@login_required(login_url='admin_login')
def edit_category(request, pk):
    category = get_object_or_404(Category, id=pk)
    form = CategoryForm(instance=category)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('admin_categories')
    return render(request, 'admin/category_form.html', {'form': form, 'title': 'Edit Category'})

@login_required(login_url='admin_login')
def delete_category(request, pk):
    category = get_object_or_404(Category, id=pk)
    if request.method == "POST":
        category.delete()
        return redirect('admin_categories')
    return render(request, 'admin/delete_confirm.html', {'item': category, 'type': 'Category', 'cancel_url': 'admin_categories'})