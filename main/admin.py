from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Food, Order, Cart, Discount, FoodRating ,OrderItem,CartItem,CommentReply

class UserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role',)}),
    )

class FoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'rating')
    list_filter = ('category', 'created_by')
    search_fields = ('name', 'category')
    ordering = ('name',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'total_price', 'order_date')
    inlines = [OrderItemInline]
    
    def total_price(self, obj):
        return sum(item.total_price for item in obj.items.all())
    total_price.short_description = 'Total Price'

class CartAdmin(admin.ModelAdmin):
    list_display = ('customer', 'get_food_names', 'get_quantities', 'get_total_price')

    def get_food_names(self, obj):
        return ", ".join([item.food.name for item in obj.items.all()])
    get_food_names.short_description = 'Food Items'

    def get_quantities(self, obj):
        return ", ".join([str(item.quantity) for item in obj.items.all()])
    get_quantities.short_description = 'Quantities'

    def get_total_price(self, obj):
        return sum([item.total_price for item in obj.items.all()])
    get_total_price.short_description = 'Total Price'

class DiscountAdmin(admin.ModelAdmin):
    list_display = ('code', 'percent', 'is_active', 'created_at', 'expires_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('code',)

class FoodRatingAdmin(admin.ModelAdmin):
    list_display = ('food', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('food__name', 'user__username')

admin.site.register(User, UserAdmin)
admin.site.register(Food, FoodAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem)
admin.site.register(CommentReply)
admin.site.register(Discount, DiscountAdmin)
admin.site.register(FoodRating, FoodRatingAdmin)

