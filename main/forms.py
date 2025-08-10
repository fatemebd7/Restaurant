from django import forms
from main.models import Food, FoodRating, Order , Employee , Discount
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from main.models import User


class SignupForm(UserCreationForm):
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=False)
    first_name = forms.CharField(max_length=100, required=True, help_text="Your first name")
    last_name = forms.CharField(max_length=100, required=True, help_text="Your last name")
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password1', 'password2', 'role']


class FoodForm(forms.ModelForm):
    class Meta:
        model = Food
        fields = ['name', 'description', 'price', 'image', 'category', 'stock']

    CATEGORY_CHOICES = [
        ('irani', 'Irani'),
        ('kebab', 'Kebab'),
        ('pizza', 'Pizza'),
        ('burger', 'Burger'),
        ('strips', 'Strips'),
        ('salad', 'Salad'),
    ]
    category = forms.ChoiceField(choices=CATEGORY_CHOICES, required=True)

class FoodRatingForm(forms.ModelForm):
    class Meta:
        model = FoodRating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your review...'})
        }
  

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields ='__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['food'].queryset = Food.objects.filter(stock__gt=0)

class EmployeeForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    password = forms.CharField(widget=forms.PasswordInput(), required=True)
    salary = forms.DecimalField(max_digits=10, decimal_places=2, required=True)

    class Meta:
        model = Employee
        fields = ['username', 'first_name', 'last_name', 'phone_number', 'password', 'role', 'salary']

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit() or len(phone_number) < 10:
            raise forms.ValidationError("Phone number must be at least 10 digits and contain only numbers.")
        return phone_number

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name.isalpha():
            raise forms.ValidationError("First name must contain only letters.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name.isalpha():
            raise forms.ValidationError("Last name must contain only letters.")
        return last_name

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_salary(self):
        salary = self.cleaned_data.get('salary')
        if salary <= 0:
            raise forms.ValidationError("Salary must be a positive number.")
        return salary

    def save(self, commit=True):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        employee = super().save(commit=False)
        employee.user = user
        employee.salary = self.cleaned_data['salary']
        employee.phone_number = self.cleaned_data['phone_number']
        if commit:
            employee.save()
        return employee

class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = ['code', 'percent', 'expires_at']
        widgets = {
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


from django import forms
from .models import CommentReply

class CommentReplyForm(forms.ModelForm):
    class Meta:
        model = CommentReply
        fields = ['reply']
