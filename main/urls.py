from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from main.views import  customer_dashboard , profile 
from main.views import FoodListView, FoodDetailView, AddFoodView, OrderListView, EmployeeDashboardView
from main.views import  TopSellingFoodsView ,SignUpView  , manager_dashboard,edit_food, delete_food,EmployeeUpdateView,EmployeeDeleteView ,  EmployeeListView,EmployeeCreateView,OrderDetailView, HomeView
from main.views import food_detail , food_list ,  cart_detail ,   add_to_cart ,  remove_from_cart ,checkout , order_list , order_detail
from main.views import edit_rating,delete_rating , OrderPendingListView ,  OrderCompleteView, OrderCompletedListView
from main.views import  food_comments,reply_to_comment , discount_list_create_view , discount_delete_view , manage_addresses ,add_address,cancel_order , rate_food

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    
    path('signup/', SignUpView.as_view(), name='signup'),  
    path('login/', auth_views.LoginView.as_view(), name='login'),  
    path('logout/', auth_views.LogoutView.as_view(), name='logout'), 
     
    
    path('food/', FoodListView.as_view(), name='food_list'),
    path('food/<int:food_id>/', FoodDetailView.as_view(), name='food_detail'),
    path('food/add/', AddFoodView.as_view(), name='add_food'),
    path('food/<int:pk>/edit/', edit_food, name='edit_food'), 
    path('food/<int:pk>/delete/', delete_food, name='delete_food'),  

    path('rating/edit/<int:pk>/', edit_rating, name='edit_rating'),
    path('rating/delete/<int:pk>/', delete_rating, name='delete_rating'),
    path('food/<int:food_id>/comments/', food_comments, name='food_comments'),
    path('rating/<int:rating_id>/reply/',reply_to_comment , name='reply_to_comment'),


    path('discounts/', discount_list_create_view, name='discount_list'),
    path('discounts/delete/<int:pk>/', discount_delete_view, name='discount_delete'),
    path('foods/top-selling/', TopSellingFoodsView.as_view(), name='top_selling_foods'),


    path('orders/', OrderListView.as_view(), name='order_list'),
    path('order/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    

    path('employee/add/', EmployeeCreateView.as_view(), name='add_employee'),
    path('employee/list/', EmployeeListView.as_view(), name='employee_list'),
    path('employee/edit/<int:pk>/', EmployeeUpdateView.as_view(), name='edit_employee'),
    path('employee/delete/<int:pk>/', EmployeeDeleteView.as_view(), name='delete_employee'),


    path('orders/pending/', OrderPendingListView.as_view(), name='order_pending_list'),
    path('orders/complete/<int:pk>/', OrderCompleteView.as_view(), name='order_complete'),
    path('orders/completed/', OrderCompletedListView.as_view(), name='order_completed_list'),


    
    path('customer/foods/',food_list, name='customer_food_list'),
    path('customer/food/<int:food_id>/', food_detail, name='customer_food_detail'),
    path('customer/cart/', cart_detail, name='customer_cart_detail'),
    path('customer/cart/add/<int:food_id>/',add_to_cart, name='customer_add_to_cart'),
    path('customer/cart/remove/<int:item_id>/',remove_from_cart, name='customer_remove_from_cart'),
    path('customer/checkout/',checkout, name='customer_checkout'),
    path('customer/orders/',order_list, name='customer_order_list'),
    path('customer/order/<int:order_id>/',order_detail, name='customer_order_detail'),
    path('manage-addresses/', manage_addresses, name='manage_addresses'),
    path('add-address/', add_address, name='customer_add_address'),
    path('order/cancel/<int:order_id>/', cancel_order, name='cancel_order'),
    path('food/rate/<int:food_id>/', rate_food, name='rate_food'),

    path('manager/dashboard/', manager_dashboard, name='manager_dashboard'),
    path('customer/dashboard/', customer_dashboard , name='customer_dashboard'),
    path('employee/dashboard/', EmployeeDashboardView.as_view(), name='employee_dashboard'),
    
    path('profile/', profile, name='profile'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)