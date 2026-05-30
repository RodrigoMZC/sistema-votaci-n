from django.shortcuts import render
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser

# Create your views here.
class RegisterView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('core:home')

    def form_valid(self,form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response
    
class ProfileView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user