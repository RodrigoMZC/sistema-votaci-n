from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser
from .models import Team, TeamMember


class TeamModelTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='teamowner',
            email='owner@votaciones.com',
            password='TestPass1234!'
        )
        self.team = Team.objects.create(
            name='Equipo Test',
            description='Descripción de prueba',
            created_by=self.user
        )

    def test_str_returns_name(self):
        """__str__ devuelve el nombre del equipo."""
        self.assertEqual(str(self.team), 'Equipo Test')

    def test_slug_auto_generado(self):
        """El slug se genera automáticamente del nombre."""
        self.assertEqual(self.team.slug, 'equipo-test')

    def test_get_absolute_url(self):
        """get_absolute_url apunta a teams:detail con el slug."""
        url = self.team.get_absolute_url()
        self.assertEqual(url, reverse('teams:detail', kwargs={'slug': self.team.slug}))

    def test_colores_por_defecto(self):
        """Los colores por defecto son los del brand."""
        self.assertEqual(self.team.primary_color, '#E8192C')
        self.assertEqual(self.team.secondary_color, '#1a1a2e')


class TeamMemberModelTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='memberuser',
            email='member@votaciones.com',
            password='TestPass1234!'
        )
        self.team = Team.objects.create(
            name='Equipo Miembro',
            created_by=self.user
        )
        self.membership = TeamMember.objects.create(
            team=self.team,
            user=self.user,
            role='admin'
        )

    def test_str_membership(self):
        """__str__ de TeamMember incluye usuario, equipo y rol."""
        self.assertIn('memberuser', str(self.membership))
        self.assertIn('Equipo Miembro', str(self.membership))
        self.assertIn('admin', str(self.membership))

    def test_unique_together_team_user(self):
        """No se puede agregar el mismo usuario dos veces al mismo equipo."""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            TeamMember.objects.create(
                team=self.team,
                user=self.user,
                role='member'
            )


class TeamViewTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='viewuser',
            email='view@votaciones.com',
            password='TestPass1234!'
        )
        self.team = Team.objects.create(
            name='Equipo Vista',
            created_by=self.user
        )
        TeamMember.objects.create(team=self.team, user=self.user, role='admin')

    def test_team_list_requiere_login(self):
        """La lista de equipos redirige si no hay sesión."""
        response = self.client.get(reverse('teams:list'))
        self.assertEqual(response.status_code, 302)

    def test_team_list_autenticado(self):
        """Un usuario autenticado puede ver la lista de equipos."""
        self.client.login(username='viewuser', password='TestPass1234!')
        response = self.client.get(reverse('teams:list'))
        self.assertEqual(response.status_code, 200)

    def test_team_detail_visible(self):
        """El detalle del equipo es visible para sus miembros."""
        self.client.login(username='viewuser', password='TestPass1234!')
        response = self.client.get(reverse('teams:detail', kwargs={'slug': self.team.slug}))
        self.assertEqual(response.status_code, 200)

    def test_team_create_page_loads(self):
        """La página de creación de equipo carga correctamente."""
        self.client.login(username='viewuser', password='TestPass1234!')
        response = self.client.get(reverse('teams:create'))
        self.assertEqual(response.status_code, 200)
