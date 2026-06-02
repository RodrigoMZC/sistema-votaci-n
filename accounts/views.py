from django.shortcuts import render
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from .models import CustomUser
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import UserSerializer
from .forms import CustomUserCreationForm, CustomUserChangeForm

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
    
class MeAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class RegisterAPIView(APIView):
    """
    POST /api/auth/register/
    Registra un usuario nuevo y devuelve access + refresh tokens.
    Body: { username, email, password, password2 }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username  = request.data.get('username', '').strip()
        email     = request.data.get('email', '').strip()
        password  = request.data.get('password', '')
        password2 = request.data.get('password2', '')

        errors = {}
        if not username:
            errors['username'] = 'El nombre de usuario es obligatorio.'
        elif CustomUser.objects.filter(username=username).exists():
            errors['username'] = 'Este nombre de usuario ya está en uso.'

        if not email:
            errors['email'] = 'El correo electrónico es obligatorio.'
        elif CustomUser.objects.filter(email=email).exists():
            errors['email'] = 'Este correo ya está registrado.'

        if not password:
            errors['password'] = 'La contraseña es obligatoria.'
        elif len(password) < 8:
            errors['password'] = 'La contraseña debe tener al menos 8 caracteres.'
        elif password != password2:
            errors['password2'] = 'Las contraseñas no coinciden.'

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


class LogoutAPIView(APIView):
    """
    POST /api/auth/logout/
    Invalida el refresh token del dispositivo móvil.
    Body: { refresh }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Se requiere el refresh token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Sesión cerrada correctamente.'}, status=status.HTTP_200_OK)
        except TokenError:
            return Response(
                {'error': 'Token inválido o ya expirado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
