from django.views import View
import re
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin,PermissionRequiredMixin
from main.forms import FoodForm, FoodRatingForm , EmployeeForm , SignupForm , DiscountForm , CommentReplyForm
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test ,login_required
from django.contrib.auth.models import User
from django.views.generic import TemplateView , UpdateView , View , DeleteView , ListView, CreateView,DetailView , CreateView
from django.contrib import messages
from main.models import Discount , User,CartItem,Food, Cart,Order, OrderItem, Employee ,FoodRating,Address
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count , F
from decimal import Decimal
from django.utils.dateparse import parse_date
from collections import Counter
 
@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})
 
def user_is_admin(user):
    return user.is_staff 

class EmployeeRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(name='Employee').exists()

    def handle_no_permission(self):
        return redirect('home')
    
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        return redirect('home')    

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'home.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            
            if request.user.is_superuser:
                return redirect(reverse_lazy('manager_dashboard'))
            
            elif request.user.groups.filter(name='Employee').exists():
                return redirect(reverse_lazy('employee_dashboard'))
            
            return redirect(reverse_lazy('customer_dashboard'))
        
        return super().dispatch(request, *args, **kwargs)
    
class SignUpView(CreateView):
    model = User
    form_class = SignupForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = form.cleaned_data.get('role') 
        user.save()
        return super().form_valid(form)

@login_required
def manager_dashboard(request):
    if not request.user.is_staff:
        return redirect('home') 
    return render(request, 'manager/manager_dashboard.html')

@login_required
def discount_list_create_view(request):
    if not request.user.is_staff:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('manager_dashboard')

    if request.method == "POST":
        form = DiscountForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Discount code added successfully!")
            return redirect('discount_list')
    else:
        form = DiscountForm()

    discounts = Discount.objects.all()
    return render(request, 'manager/discount_list.html', {
        'discounts': discounts,
        'form': form,
    })

@login_required
def discount_delete_view(request, pk):
    if not request.user.is_staff:
        messages.error(request, "You are not authorized to delete discount codes.")
        return redirect('discount_list')

    discount = get_object_or_404(Discount, pk=pk)
    discount.delete()
    messages.success(request, "Discount code deleted successfully.")
    return redirect('discount_list')

class FoodListView(LoginRequiredMixin, View):
    def get(self, request):
        category = request.GET.get('category', None)
        
        if category:
            foods = Food.objects.filter(category=category)
        else:
            foods = Food.objects.all()
        
        return render(request, 'manager/food_list.html', {'foods': foods})

class FoodDetailView(LoginRequiredMixin, View):
    def get(self, request, food_id):
        food = get_object_or_404(Food, id=food_id)
        ratings = food.ratings.all()
        form = FoodRatingForm()
        return render(request, 'manager/food_detail.html', {'food': food, 'ratings': ratings, 'form': form})

    def post(self, request, food_id):
        food = get_object_or_404(Food, id=food_id)
        ratings = food.ratings.all()
        form = FoodRatingForm(request.POST)
        if form.is_valid():
            if FoodRating.objects.filter(food=food, user=request.user).exists():
                form.add_error(None, "You have already rated this food.")
                return render(request, 'manager/food_detail.html', {'food': food, 'ratings': ratings, 'form': form})

            rating = form.save(commit=False)
            rating.food = food
            rating.user = request.user
            rating.save()
            food.update_rating()
            return redirect('food_detail', food_id=food.id)
        return render(request, 'manager/food_detail.html', {'food': food, 'ratings': ratings, 'form': form})

class AddFoodView(PermissionRequiredMixin, View):
    permission_required = 'main.add_food'

    def get(self, request):
        food_form = FoodForm()
        rating_form = FoodRatingForm()
        return render(request, 'manager/add_food.html', {
            'food_form': food_form,
            'rating_form': rating_form
        })

    def post(self, request):
        food_form = FoodForm(request.POST, request.FILES)
        rating_form = FoodRatingForm(request.POST)
        if food_form.is_valid() and rating_form.is_valid():
            food = food_form.save(commit=False)
            food.created_by = request.user
            food.save()
            
            rating = rating_form.save(commit=False)
            rating.food = food
            rating.user = request.user
            rating.save()
            
            return redirect('food_list')
        
        return render(request, 'manager/add_food.html', {
            'food_form': food_form,
            'rating_form': rating_form
        })

@login_required
@user_passes_test(user_is_admin)
def edit_food(request, pk):
    food = get_object_or_404(Food, pk=pk)
    ratings = FoodRating.objects.filter(food=food)

    if request.method == 'POST':
        form = FoodForm(request.POST, instance=food)
        if form.is_valid():
            form.save()
            return redirect('food_list')
    else:
        form = FoodForm(instance=food)
    
    return render(request, 'manager/edit_food.html', {
        'form': form,
        'food': food,
        'ratings': ratings,
    })
    
@login_required
@user_passes_test(user_is_admin)
def edit_rating(request, pk):
    rating = get_object_or_404(FoodRating, pk=pk)
    if request.method == 'POST':
        form = FoodRatingForm(request.POST, instance=rating)
        if form.is_valid():
            form.save()
            return redirect('edit_food', pk=rating.food.pk)
    else:
        form = FoodRatingForm(instance=rating)
    
    return render(request, 'manager/edit_rating.html', {
        'form': form,
        'rating': rating,
    })

@login_required
@user_passes_test(user_is_admin)
def delete_rating(request, pk):
    rating = get_object_or_404(FoodRating, pk=pk)
    food_pk = rating.food.pk
    rating.delete()
    return redirect('edit_food', pk=food_pk)
    
@login_required
@user_passes_test(user_is_admin)
def delete_food(request, pk):
    food = get_object_or_404(Food, pk=pk)
    if request.method == 'POST':
        food.delete()
        return redirect('food_list')
    return render(request, 'manager/delete_food.html', {'food': food})

@login_required
def food_comments(request, food_id):
    food = get_object_or_404(Food, id=food_id)
    ratings = food.ratings.all()
    
    if request.method == 'POST':
        form = CommentReplyForm(request.POST)
        rating_id = request.POST.get('rating_id') 
        if form.is_valid():
            rating = get_object_or_404(FoodRating, id=rating_id)
            reply = form.save(commit=False)
            reply.rating = rating
            reply.user = request.user
            reply.save()
            return redirect('food_comments', food_id=food.id)
    else:
        form = CommentReplyForm()

    return render(request, 'manager/food_comments.html', {
        'food': food,
        'ratings': ratings,
        'form': form,
    })

@login_required
def reply_to_comment(request, rating_id):
    rating = get_object_or_404(FoodRating, id=rating_id)
    if request.method == 'POST':
        form = CommentReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.rating = rating
            reply.user = request.user
            reply.save()
            return redirect('food_comments', food_id=rating.food.id)
    else:
        form = CommentReplyForm()

    return render(request, 'manager/food_comments.html', {'form': form, 'rating': rating})


class EmployeeCreateView(AdminRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employee_form.html'
    success_url = '/employee/list/'

    def form_valid(self, form):
        form.save()
        return redirect(self.success_url)

class EmployeeListView(AdminRequiredMixin, ListView):
    model = Employee
    template_name = 'employee_list.html'
    context_object_name = 'employees'
        
class EmployeeDeleteView(AdminRequiredMixin, DeleteView):
    model = Employee
    template_name = 'delete_employee.html'
    context_object_name = 'employee'

    def get_success_url(self):
        return reverse_lazy('employee_list') 
    
class EmployeeUpdateView(AdminRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employee_form.html'
    
    def get_object(self, queryset=None):
        return self.model.objects.get(pk=self.kwargs['pk'])
    
    def get_success_url(self):
        return reverse_lazy('employee_list')

class OrderListView(ListView):
    model = Order
    template_name = 'order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        status_filter = self.request.GET.get('status', None)
        start_date = self.request.GET.get('start_date', None)
        end_date = self.request.GET.get('end_date', None)

        queryset = Order.objects.all()

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if start_date:
            queryset = queryset.filter(order_date__gte=parse_date(start_date))
        if end_date:
            queryset = queryset.filter(order_date__lte=parse_date(end_date))

        if self.request.user.is_superuser:
            return queryset
        else:
            return queryset.filter(customer=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        status_filter = self.request.GET.get('status', None)
        start_date = self.request.GET.get('start_date', None)
        end_date = self.request.GET.get('end_date', None)

        context['status_filter'] = status_filter
        context['start_date'] = start_date
        context['end_date'] = end_date

        total_revenue = Decimal('0.00') 
        for order in context['orders']:
            for item in order.items.all():
                total_revenue += Decimal(item.total_price)
        
        context['total_revenue'] = total_revenue

        return context

class OrderDetailView(AdminRequiredMixin, DetailView):
    model = Order
    template_name = 'order_detail.html'
    context_object_name = 'order'
    paginate_by = 10

    def get_object(self):
        if self.request.user.is_staff or self.request.user.groups.filter(name='Employee').exists():
            return get_object_or_404(Order, id=self.kwargs['pk'])
        else:
            return get_object_or_404(Order, id=self.kwargs['pk'], customer=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()

        items = order.items.all()

        paginator = Paginator(items, self.paginate_by)
        page = self.request.GET.get('page')
        try:
            paginated_items = paginator.page(page)
        except PageNotAnInteger:
            paginated_items = paginator.page(1)
        except EmptyPage:
            paginated_items = paginator.page(paginator.num_pages)

        context['paginated_items'] = paginated_items
        return context

class TopSellingFoodsView(TemplateView):
    template_name = 'manager/top_selling_foods.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        top_selling_foods = (
            OrderItem.objects.values('food__name', 'food__image')
            .annotate(total_sales=Count('id'))
            .order_by('-total_sales')[:10]
        )
        context['top_selling_foods'] = top_selling_foods
        return context
    
# -----------------------------

class EmployeeDashboardView(EmployeeRequiredMixin, View):
    def get(self, request):
        return render(request, 'employee_dashboard.html')

class OrderPendingListView(LoginRequiredMixin, EmployeeRequiredMixin, ListView):
    model = Order
    template_name = 'order_pending_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(status='pending')

class OrderCompletedListView(LoginRequiredMixin, EmployeeRequiredMixin, ListView):
    model = Order
    template_name = 'order_completed_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(status='completed')
    
class OrderCompleteView(LoginRequiredMixin, EmployeeRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if order.status == 'pending':
            order.status = 'completed'
            order.save()
            return redirect('order_pending_list')
        return redirect('order_detail', pk=pk)

# ----------------------------
    
def customer_dashboard(request):
    cart = Cart.objects.filter(customer=request.user).first()
    cart_items = cart.items.all() if cart else []  
    orders = Order.objects.filter(customer=request.user)

    total_price = sum(cart_item.food.price * cart_item.quantity for cart_item in cart_items)

    return render(request, 'customer_dashboard.html', {
        'cart_items': cart_items,
        'orders': orders,
        'total_price': total_price,
    })

def food_list(request):
    categories = dict(Food.CATEGORY_CHOICES)
    selected_category = request.GET.get('category')
    sort_by = request.GET.get('sort_by', 'rating')
    
    if selected_category:
        foods = Food.objects.filter(category=selected_category)
    else:
        foods = Food.objects.all()
    
    if sort_by == 'rating':
        foods = foods.order_by('-rating')  
    elif sort_by == 'price_asc':
        foods = foods.order_by('price') 
    elif sort_by == 'price_desc':
        foods = foods.order_by('-price')  
    
    recommended_foods = recommend_foods(request.user)
    
    return render(request, 'customer/food_list.html', {
        'foods': foods,
        'categories': categories,
        'selected_category': selected_category,
        'sort_by': sort_by,
        'recommended_foods': recommended_foods
    })

def rate_food(request, food_id):
    food = Food.objects.get(id=food_id)

    if request.method == 'POST':
        form = FoodRatingForm(request.POST)
        if form.is_valid():
            if FoodRating.objects.filter(user=request.user, food=food).exists():
                messages.error(request, 'You have already rated this food.')
                return redirect('customer_food_list')  

            rating = form.save(commit=False)
            rating.user = request.user
            rating.food = food
            rating.save()

            food.update_rating()

            messages.success(request, 'Your rating has been submitted successfully!')
            return redirect('customer_food_list')

    else:
        form = FoodRatingForm()

    return render(request, 'customer/rate_food.html', {'food': food, 'form': form})

def cart_detail(request):
    cart, created = Cart.objects.get_or_create(customer=request.user)
    return render(request, 'customer/cart_detail.html', {'cart': cart})

def add_to_cart(request, food_id):
    food = get_object_or_404(Food, id=food_id)
    
    cart, created = Cart.objects.get_or_create(customer=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, food=food)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1)) 
        if quantity < 1:
            messages.error(request, "Quantity must be at least 1.")
            return redirect('customer_food_list')

        cart_item.quantity += quantity-1
        cart_item.save()

        messages.success(request, f'{food.name} has been added to your cart with {quantity} quantity.')

    return redirect('customer_cart_detail')

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__customer=request.user)
    cart_item.delete()
    return redirect('customer_cart_detail')

def order_list(request):
    orders = Order.objects.filter(customer=request.user).order_by('-order_date', 'status')
    return render(request, 'customer/order_list.html', {'orders': orders})

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, 'customer/order_detail.html', {'order': order})

def food_detail(request, food_id):
    food = get_object_or_404(Food, id=food_id)
    
    existing_rating = FoodRating.objects.filter(food=food, user=request.user).first()

    if request.method == 'POST':
        rating_value = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if existing_rating:
            existing_rating.rating = rating_value
            existing_rating.comment = comment
            existing_rating.save()
        else:
            FoodRating.objects.create(
                food=food,
                user=request.user,
                rating=rating_value,
                comment=comment
            )
        
        return redirect('customer_food_detail', food_id=food.id)
    
    return render(request, 'customer/food_detail.html', {
        'food': food,
        'existing_rating': existing_rating
    })

def checkout(request):
    try:
        cart = Cart.objects.get(customer=request.user)
        total_price = sum(item.total_price for item in cart.items.all())

        if cart.items.count() == 0:
            messages.error(request, 'Your cart is empty.')
            return redirect('customer_food_list')

        discount_amount = 0
        final_price = total_price

        if request.method == 'POST':
            # Retrieve discount code from the form
            discount_code = request.POST.get('discount_code', '').strip()

            # Validate and apply discount
            if discount_code:
                try:
                    discount = Discount.objects.get(code=discount_code, is_active=True, expires_at__gte=now())
                    discount_amount = discount.apply_discount(total_price)
                    final_price = total_price - discount_amount
                except Discount.DoesNotExist:
                    messages.error(request, 'Invalid or expired discount code.')
                    return redirect('customer_checkout')

            # Process address
            address_id = request.POST.get('address_id')
            new_address = request.POST.get('new_address')

            if new_address:
                title = request.POST.get('title', '').strip()
                city = request.POST.get('city', '').strip()
                postal_code = request.POST.get('postal_code', '').strip()

                # Validation
                if not re.match(r'^[a-zA-Z\s]+$', title):
                    messages.error(request, 'Title must only contain letters.')
                    return redirect('customer_checkout')

                if not re.match(r'^[a-zA-Z\s]+$', city):
                    messages.error(request, 'City must only contain letters.')
                    return redirect('customer_checkout')

                if not re.match(r'^\d{10}$', postal_code):
                    messages.error(request, 'Postal Code must be a 10-digit number.')
                    return redirect('customer_checkout')

                address = Address.objects.create(
                    customer=request.user,
                    title=title,
                    address=new_address,
                    city=city,
                    postal_code=postal_code,
                )

            elif address_id:
                address = Address.objects.get(id=address_id, customer=request.user)
            else:
                messages.error(request, 'Please select an address or enter a new one.')
                return redirect('customer_checkout')

            order = Order.objects.create(
                customer=request.user,
                address=address.address,
                total_price=final_price, 
                discount_amount=discount_amount,
                discount_code=discount_code if discount_code else None
            )


            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    food=cart_item.food,
                    quantity=cart_item.quantity
                )

                food = cart_item.food
                quantity = cart_item.quantity

                if food.stock >= quantity:
                    food.stock = F('stock') - quantity
                    food.save()
                else:
                    messages.error(request, f"Insufficient stock for {food.name}.")
                    return redirect('customer_checkout')

            cart.items.all().delete()
            messages.success(request, 'Your order has been successfully placed!')
            return redirect('customer_order_list')

        addresses = Address.objects.filter(customer=request.user)
        return render(request, 'customer/checkout.html', {
            'cart': cart,
            'total_price': total_price,
            'addresses': addresses,
            'discount_amount': discount_amount,
            'final_price': final_price
        })

    except Cart.DoesNotExist:
        messages.error(request, 'Your cart is empty or unavailable.')
        return redirect('customer_food_list')

def manage_addresses(request):
    addresses = Address.objects.filter(customer=request.user)
    if request.method == 'POST':
        if 'delete' in request.POST:
            Address.objects.get(id=request.POST['delete'], customer=request.user).delete()
        elif 'set_default' in request.POST:
            Address.objects.filter(customer=request.user).update(is_default=False)
            Address.objects.filter(id=request.POST['set_default'], customer=request.user).update(is_default=True)
    return render(request, 'customer/manage_addresses.html', {'addresses': addresses})

def add_address(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        address = request.POST.get('address')
        city = request.POST.get('city')
        postal_code = request.POST.get('postal_code')

        if len(title) < 3:
            messages.error(request, 'Title must be at least 5 characters long.')
            return redirect('customer_add_address')
        if not title.isalpha():
            messages.error(request, 'Title must only contain letters.')
            return redirect('customer_add_address')

        if len(city) < 3:
            messages.error(request, 'City must be at least 5 characters long.')
            return redirect('customer_add_address')
        if not city.isalpha():
            messages.error(request, 'City must only contain letters.')
            return redirect('customer_add_address')

        if len(address) < 8:
            messages.error(request, 'Address must be at least 10 characters long.')
            return redirect('customer_add_address')
        # if not re.match(r'^[A-Za-z0-9]+$', address):
        #     messages.error(request, 'Address must be a combination of letters and numbers, no spaces or special characters.')
        #     return redirect('customer_add_address')

        if len(postal_code) != 10:
            messages.error(request, 'Postal code must be exactly 10 characters long.')
            return redirect('customer_add_address')
        if not postal_code.isdigit():
            messages.error(request, 'Postal code must contain only digits.')
            return redirect('customer_add_address')
        if int(postal_code) < 0:
            messages.error(request, 'Postal code cannot be negative.')
            return redirect('customer_add_address')

        try:
            Address.objects.create(
                customer=request.user,
                title=title,
                address=address,
                city=city,
                postal_code=postal_code,
            )
            messages.success(request, 'Address added successfully!')
            return redirect('customer_dashboard')
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('customer_add_address')
    
    return render(request, 'customer/add_address.html') 

def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)

    if order.is_cancellable():
        order.status = 'cancelled'
        order.save()
        messages.success(request, 'Your order has been successfully cancelled.')
    else:
        messages.error(request, 'You cannot cancel this order. Either it has already been processed or the cancellation window (30 minutes) has expired.')

    return redirect('customer_order_list')

# --------------------------

def recommend_foods(customer):
    previous_orders = Order.objects.filter(customer=customer)
    
    previous_foods = Food.objects.filter(orderitem__order__in=previous_orders)
    
    categories = [food.category for food in previous_foods]
    
    recommended_foods = Food.objects.filter(category__in=categories).exclude(id__in=[food.id for food in previous_foods])
    
    return recommended_foods

def popular_foods():
    food_sales = Counter()
    
    orders = Order.objects.filter(status='completed')
    for order in orders:
        for item in order.items.all():
            food_sales[item.food] += item.quantity

    most_popular_foods = [food for food, count in food_sales.most_common(5)]
    
    return most_popular_foods

def get_food_recommendations(customer):
    similar_category_foods = recommend_foods(customer)
    
    popular_foods_list = popular_foods()
    combined_recommendations = set(similar_category_foods) | set(popular_foods_list)
    
    return combined_recommendations
