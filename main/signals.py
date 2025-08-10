from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.conf import settings

@receiver(user_logged_in)
def set_user_as_customer(sender, request, user, **kwargs):
    if user.role != 'customer':
        user.role = 'customer'
        user.save()
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User

@receiver(post_save, sender=User)
def set_user_as_customer(sender, instance, created, **kwargs):
    if created and not instance.role:
        instance.role = User.CUSTOMER  
        instance.save()
