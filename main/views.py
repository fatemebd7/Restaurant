from django.forms import ValidationError
from django.views import View
from django.views.generic import (
    TemplateView, UpdateView, DeleteView, ListView,
    CreateView, DetailView, FormView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import now
from django.db.models import Count, F
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.dateparse import parse_date
from collections import Counter
from decimal import Decimal
import re

from main.models import Discount, CartItem, Food, Cart, Order, OrderItem, Employee, FoodRating, Address
from main.forms import (
    FoodForm, FoodRatingForm, EmployeeForm, SignupForm,
    DiscountForm, CommentReplyForm
)


# ---------------------- Mixins ----------------------

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


# ---------------------- Common Views ----------------------

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


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
    form_class = SignupForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = form.cleaned_data.get('role')
        user.save()
        return super().form_valid(form)


# ---------------------- Manager Views ----------------------

class ManagerDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'manager/manager_dashboard.html'


class DiscountListCreateView(AdminRequiredMixin, TemplateView):
    template_name = 'manager/discount_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['discounts'] = Discount.objects.all()
        context['form'] = DiscountForm()
        return context

    def post(self, request, *args, **kwargs):
        form = DiscountForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Discount code added successfully!")
        return redirect('discount_list')


class DiscountDeleteView(AdminRequiredMixin, DeleteView):
    model = Discount
    template_name = 'manager/discount_confirm_delete.html'
    success_url = reverse_lazy('discount_list')


class FoodListView(LoginRequiredMixin, ListView):
    model = Food
    template_name = 'manager/food_list.html'
    context_object_name = 'foods'

    def get_queryset(self):
        category = self.request.GET.get('category')
        if category:
            return Food.objects.filter(category=category)
        return Food.objects.all()


class FoodDetailView(LoginRequiredMixin, View):
    template_name = 'manager/food_detail.html'

    def get(self, request, food_id):
        food = get_object_or_404(Food, id=food_id)
        ratings = food.ratings.all()
        return render(request, self.template_name, {
            'food': food,
            'ratings': ratings,
            'form': FoodRatingForm()
        })

    def post(self, request, food_id):
        food = get_object_or_404(Food, id=food_id)
        form = FoodRatingForm(request.POST)
        if form.is_valid():
            if FoodRating.objects.filter(food=food, user=request.user).exists():
                form.add_error(None, "You have already rated this food.")
            else:
                rating = form.save(commit=False)
                rating.food = food
                rating.user = request.user
                rating.save()
                food.update_rating()
                return redirect('food_detail', food_id=food.id)
        ratings = food.ratings.all()
        return render(request, self.template_name, {'food': food, 'ratings': ratings, 'form': form})


class AddFoodView(PermissionRequiredMixin, View):
    permission_required = 'main.add_food'
    template_name = 'manager/add_food.html'

    def get(self, request):
        return render(request, self.template_name, {
            'food_form': FoodForm(),
            'rating_form': FoodRatingForm()
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
        return render(request, self.template_name, {
            'food_form': food_form,
            'rating_form': rating_form
        })


class EditFoodView(AdminRequiredMixin, UpdateView):
    model = Food
    form_class = FoodForm
    template_name = 'manager/edit_food.html'
    success_url = reverse_lazy('food_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ratings'] = FoodRating.objects.filter(food=self.object)
        return context


class DeleteFoodView(AdminRequiredMixin, DeleteView):
    model = Food
    template_name = 'manager/delete_food.html'
    success_url = reverse_lazy('food_list')


class EditRatingView(AdminRequiredMixin, UpdateView):
    model = FoodRating
    form_class = FoodRatingForm
    template_name = 'manager/edit_rating.html'

    def get_success_url(self):
        return reverse_lazy('edit_food', kwargs={'pk': self.object.food.pk})


class DeleteRatingView(AdminRequiredMixin, DeleteView):
    model = FoodRating
    template_name = 'manager/delete_rating.html'

    def get_success_url(self):
        return reverse_lazy('edit_food', kwargs={'pk': self.object.food.pk})


class FoodCommentsView(LoginRequiredMixin, TemplateView):
    template_name = 'manager/food_comments.html'

    def get_context_data(self, **kwargs):
        food = get_object_or_404(Food, id=self.kwargs['food_id'])
        return {
            'food': food,
            'ratings': food.ratings.all(),
            'form': CommentReplyForm()
        }

    def post(self, request, *args, **kwargs):
        form = CommentReplyForm(request.POST)
        rating_id = request.POST.get('rating_id')
        rating = get_object_or_404(FoodRating, id=rating_id)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.rating = rating
            reply.user = request.user
            reply.save()
        return redirect('food_comments', food_id=rating.food.id)


class ReplyToCommentView(LoginRequiredMixin, View):
    def post(self, request, rating_id):
        form = CommentReplyForm(request.POST)
        rating = get_object_or_404(FoodRating, id=rating_id)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.rating = rating
            reply.user = request.user
            reply.save()
        return redirect('food_comments', food_id=rating.food.id)


# ---------------------- Employee Views ----------------------

class EmployeeCreateView(AdminRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employee_form.html'
    success_url = reverse_lazy('employee_list')


class EmployeeListView(AdminRequiredMixin, ListView):
    model = Employee
    template_name = 'employee_list.html'
    context_object_name = 'employees'


class EmployeeDeleteView(AdminRequiredMixin, DeleteView):
    model = Employee
    template_name = 'delete_employee.html'
    success_url = reverse_lazy('employee_list')


class EmployeeUpdateView(AdminRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employee_form.html'
    success_url = reverse_lazy('employee_list')


class EmployeeDashboardView(EmployeeRequiredMixin, TemplateView):
    template_name = 'employee_dashboard.html'


# ---------------------- Orders ----------------------

class OrderListView(ListView):
    model = Order
    template_name = 'order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        qs = Order.objects.all()
        status_filter = self.request.GET.get('status')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if start_date:
            qs = qs.filter(order_date__gte=parse_date(start_date))
        if end_date:
            qs = qs.filter(order_date__lte=parse_date(end_date))
        if not self.request.user.is_superuser:
            qs = qs.filter(customer=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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

    def get_object(self, queryset=None):
        if self.request.user.is_staff or self.request.user.groups.filter(name='Employee').exists():
            return get_object_or_404(Order, id=self.kwargs['pk'])
        return get_object_or_404(Order, id=self.kwargs['pk'], customer=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items = self.object.items.all()
        paginator = Paginator(items, self.paginate_by)
        page = self.request.GET.get('page')
        try:
            context['paginated_items'] = paginator.page(page)
        except PageNotAnInteger:
            context['paginated_items'] = paginator.page(1)
        except EmptyPage:
            context['paginated_items'] = paginator.page(paginator.num_pages)
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


# ---------------------- Customer Views ----------------------

class CustomerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'customer_dashboard.html'

    def get_context_data(self, **kwargs):
        cart = Cart.objects.filter(customer=self.request.user).first()
        cart_items = cart.items.all() if cart else []
        orders = Order.objects.filter(customer=self.request.user)
        total_price = sum(item.food.price * item.quantity for item in cart_items)
        return {
            'cart_items': cart_items,
            'orders': orders,
            'total_price': total_price
        }


class CustomerFoodListView(LoginRequiredMixin, TemplateView):
    template_name = 'customer/food_list.html'

    def get_context_data(self, **kwargs):
        categories = dict(Food.CATEGORY_CHOICES)
        selected_category = self.request.GET.get('category')
        sort_by = self.request.GET.get('sort_by', 'rating')
        foods = Food.objects.filter(category=selected_category) if selected_category else Food.objects.all()

        if sort_by == 'rating':
            foods = foods.order_by('-rating')
        elif sort_by == 'price_asc':
            foods = foods.order_by('price')
        elif sort_by == 'price_desc':
            foods = foods.order_by('-price')

        recommended_foods = recommend_foods(self.request.user)
        return {
            'foods': foods,
            'categories': categories,
            'selected_category': selected_category,
            'sort_by': sort_by,
            'recommended_foods': recommended_foods
        }


class RateFoodView(LoginRequiredMixin, FormView):
    template_name = 'customer/rate_food.html'
    form_class = FoodRatingForm

    def dispatch(self, request, *args, **kwargs):
        self.food = get_object_or_404(Food, id=kwargs['food_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if FoodRating.objects.filter(user=self.request.user, food=self.food).exists():
            messages.error(self.request, 'You have already rated this food.')
            return redirect('customer_food_list')

        rating = form.save(commit=False)
        rating.user = self.request.user
        rating.food = self.food
        rating.save()
        self.food.update_rating()
        messages.success(self.request, 'Your rating has been submitted successfully!')
        return redirect('customer_food_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['food'] = self.food
        return context


class CartDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'customer/cart_detail.html'

    def get_context_data(self, **kwargs):
        cart, _ = Cart.objects.get_or_create(customer=self.request.user)
        return {'cart': cart}


class AddToCartView(LoginRequiredMixin, View):
    def post(self, request, food_id):
        food = get_object_or_404(Food, id=food_id)
        cart, _ = Cart.objects.get_or_create(customer=request.user)
        cart_item, _ = CartItem.objects.get_or_create(cart=cart, food=food)

        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            messages.error(request, "Quantity must be at least 1.")
            return redirect('customer_food_list')

        cart_item.quantity += quantity - 1
        cart_item.save()
        messages.success(request, f'{food.name} has been added to your cart with {quantity} quantity.')
        return redirect('customer_cart_detail')


class RemoveFromCartView(LoginRequiredMixin, View):
    def post(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, cart__customer=request.user)
        cart_item.delete()
        return redirect('customer_cart_detail')


class CustomerOrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'customer/order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).order_by('-order_date', 'status')


class CustomerOrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'customer/order_detail.html'
    context_object_name = 'order'

    def get_object(self, queryset=None):
        return get_object_or_404(Order, id=self.kwargs['order_id'], customer=self.request.user)


class CustomerFoodDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'customer/food_detail.html'

    def dispatch(self, request, *args, **kwargs):
        self.food = get_object_or_404(Food, id=kwargs['food_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        existing_rating = FoodRating.objects.filter(food=self.food, user=self.request.user).first()
        return {'food': self.food, 'existing_rating': existing_rating}

    def post(self, request, *args, **kwargs):
        existing_rating = FoodRating.objects.filter(food=self.food, user=request.user).first()
        rating_value = request.POST.get('rating')
        comment = request.POST.get('comment')

        if existing_rating:
            existing_rating.rating = rating_value
            existing_rating.comment = comment
            existing_rating.save()
        else:
            FoodRating.objects.create(
                food=self.food,
                user=request.user,
                rating=rating_value,
                comment=comment
            )
        return redirect('customer_food_detail', food_id=self.food.id)

class CheckoutView(LoginRequiredMixin, TemplateView):
    template_name = 'customer/checkout.html'

    def get_context_data(self, **kwargs):
        cart = Cart.objects.get(customer=self.request.user)
        total_price = sum(item.total_price for item in cart.items.all())
        addresses = Address.objects.filter(customer=self.request.user)
        return {
            'cart': cart,
            'total_price': total_price,
            'addresses': addresses,
            'discount_amount': 0,
            'final_price': total_price
        }

    def post(self, request, *args, **kwargs):
        try:
            cart = Cart.objects.get(customer=request.user)
            total_price = sum(item.total_price for item in cart.items.all())

            if cart.items.count() == 0:
                messages.error(request, 'Your cart is empty.')
                return redirect('customer_food_list')

            discount_amount = 0
            final_price = total_price

            # --- تخفیف ---
            discount_code = request.POST.get('discount_code', '').strip()
            if discount_code:
                try:
                    discount = Discount.objects.get(
                        code=discount_code,
                        is_active=True,
                        expires_at__gte=now()
                    )
                    discount_amount = discount.apply_discount(total_price)
                    final_price = total_price - discount_amount
                except Discount.DoesNotExist:
                    messages.error(request, 'Invalid or expired discount code.')
                    return redirect('customer_checkout')

            # --- آدرس ---
            address_id = request.POST.get('address_id')
            new_address = request.POST.get('new_address')

            if new_address:
                title = request.POST.get('title', '').strip()
                city = request.POST.get('city', '').strip()
                postal_code = request.POST.get('postal_code', '').strip()

                address = Address(
                    customer=request.user,
                    title=title,
                    address=new_address,
                    city=city,
                    postal_code=postal_code,
                )
                try:
                    address.full_clean()
                    address.save()
                except ValidationError as e:
                    messages.error(request, str(e))
                    return redirect('customer_checkout')

            elif address_id:
                address = Address.objects.get(id=address_id, customer=request.user)
            else:
                messages.error(request, 'Please select an address or enter a new one.')
                return redirect('customer_checkout')

            # --- سفارش ---
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

        except Cart.DoesNotExist:
            messages.error(request, 'Your cart is empty or unavailable.')
            return redirect('customer_food_list')


class ManageAddressesView(LoginRequiredMixin, TemplateView):
    template_name = 'customer/manage_addresses.html'

    def get_context_data(self, **kwargs):
        return {'addresses': Address.objects.filter(customer=self.request.user)}

    def post(self, request, *args, **kwargs):
        if 'delete' in request.POST:
            Address.objects.get(id=request.POST['delete'], customer=request.user).delete()
        elif 'set_default' in request.POST:
            Address.objects.filter(customer=request.user).update(is_default=False)
            Address.objects.filter(id=request.POST['set_default'], customer=request.user).update(is_default=True)
        return redirect('manage_addresses')

class AddAddressView(LoginRequiredMixin, TemplateView):
    template_name = 'customer/add_address.html'

    def post(self, request, *args, **kwargs):
        title = request.POST.get('title', '').strip()
        address_text = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()

        address = Address(
            customer=request.user,
            title=title,
            address=address_text,
            city=city,
            postal_code=postal_code,
        )
        try:
            address.full_clean()
            address.save()
            messages.success(request, 'Address added successfully!')
            return redirect('customer_dashboard')
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('customer_add_address')


class CancelOrderView(LoginRequiredMixin, View):
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, customer=request.user)
        if order.is_cancellable():
            order.status = 'cancelled'
            order.save()
            messages.success(request, 'Your order has been successfully cancelled.')
        else:
            messages.error(request, 'You cannot cancel this order.')
        return redirect('customer_order_list')


# ---------------------- Recommendation Helpers ----------------------

def recommend_foods(customer):
    previous_orders = Order.objects.filter(customer=customer)
    previous_foods = Food.objects.filter(orderitem__order__in=previous_orders)
    categories = [food.category for food in previous_foods]
    return Food.objects.filter(category__in=categories).exclude(id__in=[food.id for food in previous_foods])


def popular_foods():
    food_sales = Counter()
    orders = Order.objects.filter(status='completed')
    for order in orders:
        for item in order.items.all():
            food_sales[item.food] += item.quantity
    return [food for food, _ in food_sales.most_common(5)]


def get_food_recommendations(customer):
    return set(recommend_foods(customer)) | set(popular_foods())
