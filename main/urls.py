from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from main.views import (
    ProfileView, HomeView, SignUpView,
    ManagerDashboardView, DiscountListCreateView, DiscountDeleteView,
    FoodListView, FoodDetailView, AddFoodView, EditFoodView, DeleteFoodView,
    EditRatingView, DeleteRatingView, FoodCommentsView, ReplyToCommentView,
    TopSellingFoodsView,
    EmployeeCreateView, EmployeeListView, EmployeeUpdateView, EmployeeDeleteView, EmployeeDashboardView,
    OrderListView, OrderDetailView, OrderPendingListView, OrderCompleteView, OrderCompletedListView,
    CustomerDashboardView, CustomerFoodListView, CustomerFoodDetailView,
    CartDetailView, AddToCartView, RemoveFromCartView,
    CustomerOrderListView, CustomerOrderDetailView,
    CheckoutView, ManageAddressesView, AddAddressView, CancelOrderView,
    RateFoodView
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),

    # Auth
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Profile
    path('profile/', ProfileView.as_view(), name='profile'),

    # Manager
    path('manager/dashboard/', ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('discounts/', DiscountListCreateView.as_view(), name='discount_list'),
    path('discounts/delete/<int:pk>/', DiscountDeleteView.as_view(), name='discount_delete'),
    path('foods/top-selling/', TopSellingFoodsView.as_view(), name='top_selling_foods'),

    # Food management
    path('food/', FoodListView.as_view(), name='food_list'),
    path('food/<int:food_id>/', FoodDetailView.as_view(), name='food_detail'),
    path('food/add/', AddFoodView.as_view(), name='add_food'),
    path('food/<int:pk>/edit/', EditFoodView.as_view(), name='edit_food'),
    path('food/<int:pk>/delete/', DeleteFoodView.as_view(), name='delete_food'),

    # Ratings & Comments
    path('rating/edit/<int:pk>/', EditRatingView.as_view(), name='edit_rating'),
    path('rating/delete/<int:pk>/', DeleteRatingView.as_view(), name='delete_rating'),
    path('food/<int:food_id>/comments/', FoodCommentsView.as_view(), name='food_comments'),
    path('rating/<int:rating_id>/reply/', ReplyToCommentView.as_view(), name='reply_to_comment'),

    # Employee
    path('employee/add/', EmployeeCreateView.as_view(), name='add_employee'),
    path('employee/list/', EmployeeListView.as_view(), name='employee_list'),
    path('employee/edit/<int:pk>/', EmployeeUpdateView.as_view(), name='edit_employee'),
    path('employee/delete/<int:pk>/', EmployeeDeleteView.as_view(), name='delete_employee'),
    path('employee/dashboard/', EmployeeDashboardView.as_view(), name='employee_dashboard'),

    # Orders (manager/employee)
    path('orders/', OrderListView.as_view(), name='order_list'),
    path('order/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('orders/pending/', OrderPendingListView.as_view(), name='order_pending_list'),
    path('orders/complete/<int:pk>/', OrderCompleteView.as_view(), name='order_complete'),
    path('orders/completed/', OrderCompletedListView.as_view(), name='order_completed_list'),

    # Customer
    path('customer/dashboard/', CustomerDashboardView.as_view(), name='customer_dashboard'),
    path('customer/foods/', CustomerFoodListView.as_view(), name='customer_food_list'),
    path('customer/food/<int:food_id>/', CustomerFoodDetailView.as_view(), name='customer_food_detail'),
    path('customer/food/rate/<int:food_id>/', RateFoodView.as_view(), name='rate_food'),

    path('customer/cart/', CartDetailView.as_view(), name='customer_cart_detail'),
    path('customer/cart/add/<int:food_id>/', AddToCartView.as_view(), name='customer_add_to_cart'),
    path('customer/cart/remove/<int:item_id>/', RemoveFromCartView.as_view(), name='customer_remove_from_cart'),

    path('customer/orders/', CustomerOrderListView.as_view(), name='customer_order_list'),
    path('customer/order/<int:order_id>/', CustomerOrderDetailView.as_view(), name='customer_order_detail'),

    path('customer/checkout/', CheckoutView.as_view(), name='customer_checkout'),
    path('manage-addresses/', ManageAddressesView.as_view(), name='manage_addresses'),
    path('add-address/', AddAddressView.as_view(), name='customer_add_address'),
    path('order/cancel/<int:order_id>/', CancelOrderView.as_view(), name='cancel_order'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
