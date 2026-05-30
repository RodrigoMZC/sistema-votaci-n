from django.test import TestCase
from django.urls import reverse
from django.core import mail
from .models import CustomUser

class PasswordResetEmailTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='testuser@votaciones.com',
            password='TestPass1234!'
        )

    def test_password_reset_email_sent(self):
        response = self.client.post(reverse('accounts:password_reset'), {'email': 'testuser@votaciones.com'})

        self.assertEqual(response.status_code, 302)  # Redirige después de enviar el formulario
        self.assertEqual(len(mail.outbox), 1)  # Se envió un correo
        self.assertEqual(mail.outbox[0].to, ['testuser@votaciones.com'])  # El correo se envió al usuario correcto
        self.assertIn('contrase', mail.outbox[0].subject.lower())  # El asunto del correo contiene

    def test_password_reset_email_not_sent_for_unknown_email(self):
        self.client.post(reverse('accounts:password_reset'), {
            'email': 'noexiste@example.com'
        })
        self.assertEqual(len(mail.outbox), 0)