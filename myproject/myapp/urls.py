from django.urls import path
from . import views

urlpatterns = [
    # Store
    path('', views.home, name='home'),
    path('category/<slug:category_slug>/', views.category_products, name='category_products'),
    path('product/<str:pk>/', views.product_detail, name='product_detail'),

    # Cart & Checkout
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name="checkout"),
    path('history/', views.order_history, name="order_history"),
    path('update_item/', views.update_item, name="update_item"),
    path('process_order/', views.process_order, name='process_order'),
    path('my-orders/', views.customer_orders, name='customer_orders'),

    # Custom Admin
    path('custom-admin/', views.admin_login_view, name='admin_login'),
    path('custom-admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('custom-admin/products/', views.admin_products, name='admin_products'),
    path('custom-admin/products/add/', views.add_product, name='add_product'),
    path('custom-admin/products/edit/<str:pk>/', views.edit_product, name='edit_product'),
    path('custom-admin/products/delete/<str:pk>/', views.delete_product, name='delete_product'),
    path('custom-admin/orders/', views.admin_orders, name='admin_orders'),
    path('custom-admin/orders/update/<str:pk>/', views.update_order_status, name='update_order_status'),
    path('custom-admin/customers/', views.admin_customers, name='admin_customers'),
    
    # Categories
    path('custom-admin/categories/', views.admin_categories, name='admin_categories'),
    path('custom-admin/categories/add/', views.add_category, name='add_category'),
    path('custom-admin/categories/edit/<int:pk>/', views.edit_category, name='edit_category'),
    path('custom-admin/categories/delete/<int:pk>/', views.delete_category, name='delete_category'),

    # Auth
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]