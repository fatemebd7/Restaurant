from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from datetime import timedelta
from django.utils.timezone import now
from django.core.exceptions import ValidationError
import re


# =======================
#  User Model
# =======================
class User(AbstractUser):
    MANAGER = 'manager'
    EMPLOYEE = 'employee'
    CUSTOMER = 'customer'

    ROLE_CHOICES = [
        (MANAGER, 'Manager'),
        (EMPLOYEE, 'Employee'),
        (CUSTOMER, 'Customer'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=CUSTOMER)

    def __str__(self):
        return self.username


# =======================
#  Food Model
# =======================
class Food(models.Model):
    CATEGORY_CHOICES = [
        ('irani', 'Irani'),
        ('kebab', 'Kebab'),
        ('pizza', 'Pizza'),
        ('burger', 'Burger'),
        ('strips', 'Strips'),
        ('salad', 'Salad'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='food_images/', default='food_images/default_food.jpg')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='irani')
    stock = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0, blank=True)
    rating_count = models.PositiveIntegerField(default=0)
    preparation_time = models.PositiveBigIntegerField(default=30)

    def __str__(self):
        return self.name

    def update_rating(self):
        ratings = self.ratings.all()
        if ratings:
            total_rating = sum(r.rating for r in ratings)
            self.rating_count = ratings.count()
            self.rating = total_rating / self.rating_count
            self.save()

    def reduce_stock(self, quantity):
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
        else:
            raise ValueError("Not enough stock available")


# =======================
#  Order Models
# =======================
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.TextField()
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_code = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} by {self.customer.username}"

    def is_cancellable(self):
        return self.status == 'pending' and now() <= self.order_date + timedelta(minutes=30)

    def update_total_price(self):
        self.total_price = sum(item.total_price for item in self.items.all())
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        return self.food.price * self.quantity

    def __str__(self):
        return f"{self.food.name} - {self.quantity}"


# =======================
#  Rating & Comment Models
# =======================
class FoodRating(models.Model):
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=2, decimal_places=1, choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    reply = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['food', 'user']

    def __str__(self):
        return f'{self.user.username} rated {self.food.name} with {self.rating}'


class CommentReply(models.Model):
    rating = models.ForeignKey(FoodRating, related_name='replies', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reply = models.TextField()

    def __str__(self):
        return f"Reply to Rating #{self.rating.id} by {self.user.username}"


# =======================
#  Employee Model
# =======================
class Employee(models.Model):
    ROLE_CHOICES = [
        ('garson', 'Garson'),
        ('staff', 'Staff')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    role = models.CharField(max_length=100, choices=ROLE_CHOICES)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


# =======================
#  Discount Model
# =======================
class Discount(models.Model):
    code = models.CharField(max_length=20, unique=True)
    percent = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.percent}%"

    def apply_discount(self, total_price):
        return (self.percent / 100) * total_price


# =======================
#  Cart Models
# =======================
class Cart(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.customer.username}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        return self.food.price * self.quantity

    def __str__(self):
        return f"{self.food.name} - {self.quantity}"


# =======================
#  Address Model
# =======================
class Address(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    title = models.CharField(max_length=50)
    address = models.TextField()
    city = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {self.customer.username}"

    # --- Validation helpers ---
    def clean_title(self):
        if len(self.title) < 5:
            raise ValidationError('Title must be at least 5 characters long.')
        if not self.title.isalpha():
            raise ValidationError('Title must only contain letters.')

    def clean_city(self):
        if len(self.city) < 5:
            raise ValidationError('City must be at least 5 characters long.')
        if not self.city.isalpha():
            raise ValidationError('City must only contain letters.')

    def clean_address(self):
        if len(self.address) < 10:
            raise ValidationError('Address must be at least 10 characters long.')
        if not re.match(r'^[A-Za-z0-9]+$', self.address):
            raise ValidationError(
                'Address must be a combination of letters and numbers, no spaces or special characters.'
            )

    def clean_postal_code(self):
        if len(self.postal_code) != 10:
            raise ValidationError('Postal code must be exactly 10 characters long.')
        if not self.postal_code.isdigit():
            raise ValidationError('Postal code must contain only digits.')
        if int(self.postal_code) < 0:
            raise ValidationError('Postal code cannot be negative.')

    def clean(self):
        self.clean_title()
        self.clean_city()
        self.clean_address()
        self.clean_postal_code()

        if self.is_default:
            if Address.objects.filter(customer=self.customer, is_default=True).exclude(id=self.id).exists():
                raise ValidationError('You can only have one default address.')

        super().clean()
