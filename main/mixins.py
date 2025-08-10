from django.shortcuts import redirect
from django.contrib.auth.mixins import AccessMixin
from django.urls import reverse_lazy

class LoggedOutOnlyMixin(AccessMixin):
    redirect_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.redirect_url)
        return super().dispatch(request, *args, **kwargs)

# class ManagerRequiredMixin(UserPassesTestMixin, LoginRequiredMixin):
#     def test_func(self):
#         return self.request.user.is_manager()
    
# class EmployeeRequiredMixin(UserPassesTestMixin):
#     def test_func(self):
#         return self.request.user.groups.filter(name='Employee').exists()

#     def handle_no_permission(self):
#         return redirect('home')
    
# class CustomerRequiredMixin(UserPassesTestMixin):
#     def test_func(self):
#         return not self.request.user.groups.filter(name='Employee').exists() and not self.request.user.is_superuser

#     def handle_no_permission(self):
#         return redirect('home')
    
