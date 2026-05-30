from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields= ('username', 'email', 'password1', 'password2')

class CustomUserChangeForm(UserChangeForm):
    password = None

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'avatar', 'bio')