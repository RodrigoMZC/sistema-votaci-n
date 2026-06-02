from django.test import TestCase
from django.urls import reverse
from django.core import mail
from .models import CustomUser


# ─────────────────────────────────────────────
#  1. Modelo CustomUser
# ─────────────────────────────────────────────

class CustomUserModelTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@votaciones.com',
            password='TestPass1234!'
        )

    def test_str_returns_username(self):
        """__str__ devuelve el username."""
        self.assertEqual(str(self.user), 'testuser')

    def test_get_absolute_url(self):
        """get_absolute_url apunta a accounts:profile."""
        url = self.user.get_absolute_url()
        self.assertEqual(url, reverse('accounts:profile'))

    def test_user_has_uuid_pk(self):
        """El PK es un UUID (no entero)."""
        import uuid
        self.assertIsInstance(self.user.pk, uuid.UUID)

    def test_bio_blank_by_default(self):
        """El campo bio está vacío por defecto."""
        self.assertEqual(self.user.bio, '')

    def test_avatar_null_by_default(self):
        """El avatar es None por defecto."""
        self.assertFalse(bool(self.user.avatar))


# ─────────────────────────────────────────────
#  2. Vistas de autenticación
# ─────────────────────────────────────────────

class AuthViewTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='authuser',
            email='auth@votaciones.com',
            password='AuthPass1234!'
        )

    def test_login_page_loads(self):
        """La página de login devuelve 200."""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_register_page_loads(self):
        """La página de registro devuelve 200."""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)

    def test_login_correcto_redirige(self):
        """Login con credenciales válidas redirige al home."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'authuser',
            'password': 'AuthPass1234!'
        })
        self.assertEqual(response.status_code, 302)

    def test_login_incorrecto_no_redirige(self):
        """Login con contraseña incorrecta permanece en 200."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'authuser',
            'password': 'ContraseñaWrong!'
        })
        self.assertEqual(response.status_code, 200)

    def test_home_requiere_login(self):
        """El home redirige a login si no hay sesión activa."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])


# ─────────────────────────────────────────────
#  3. Restablecimiento de contraseña
# ─────────────────────────────────────────────

class PasswordResetEmailTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='resetuser',
            email='resetuser@votaciones.com',
            password='TestPass1234!'
        )

    def test_password_reset_email_sent(self):
        """Se envía exactamente 1 correo al solicitar reset."""
        response = self.client.post(
            reverse('accounts:password_reset'),
            {'email': 'resetuser@votaciones.com'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_email_destinatario_correcto(self):
        """El correo llega al email correcto."""
        self.client.post(
            reverse('accounts:password_reset'),
            {'email': 'resetuser@votaciones.com'}
        )
        self.assertEqual(mail.outbox[0].to, ['resetuser@votaciones.com'])

    def test_password_reset_email_not_sent_for_unknown_email(self):
        """No se envía correo si el email no existe."""
        self.client.post(
            reverse('accounts:password_reset'),
            {'email': 'noexiste@example.com'}
        )
        self.assertEqual(len(mail.outbox), 0)
