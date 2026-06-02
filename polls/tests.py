from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from accounts.models import CustomUser
from teams.models import Team, TeamMember
from .models import Poll, Option, Vote


class PollModelTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='pollowner',
            email='pollowner@votaciones.com',
            password='TestPass1234!'
        )
        self.team = Team.objects.create(
            name='Equipo Polls',
            created_by=self.user
        )
        TeamMember.objects.create(team=self.team, user=self.user, role='admin')
        self.poll = Poll.objects.create(
            title='Votación de prueba',
            description='Descripción test',
            team=self.team,
            created_by=self.user,
        )
        self.option_a = Option.objects.create(poll=self.poll, text='Opción A')
        self.option_b = Option.objects.create(poll=self.poll, text='Opción B')

    def test_poll_str(self):
        """__str__ devuelve el título de la poll."""
        self.assertEqual(str(self.poll), 'Votación de prueba')

    def test_poll_get_absolute_url(self):
        """get_absolute_url incluye team_slug y poll_id."""
        url = self.poll.get_absolute_url()
        self.assertIn(self.team.slug, url)
        self.assertIn(str(self.poll.id), url)

    def test_poll_activa_por_defecto(self):
        """Una poll recién creada está activa."""
        self.assertTrue(self.poll.is_active)

    def test_option_str(self):
        """__str__ de Option incluye título de la poll y texto."""
        self.assertIn('Opción A', str(self.option_a))
        self.assertIn('Votación de prueba', str(self.option_a))

    def test_check_and_close_por_deadline(self):
        """check_and_close cierra la poll si el deadline ya pasó."""
        self.poll.deadline = timezone.now() - timedelta(hours=1)
        self.poll.save()
        self.poll.check_and_close()
        self.poll.refresh_from_db()
        self.assertFalse(self.poll.is_active)

    def test_check_and_close_por_votos_requeridos(self):
        """check_and_close cierra la poll al alcanzar required_votes."""
        self.poll.required_votes = 1
        self.poll.save()
        Vote.objects.create(user=self.user, option=self.option_a)
        self.poll.check_and_close()
        self.poll.refresh_from_db()
        self.assertFalse(self.poll.is_active)

    def test_voto_unico_por_usuario(self):
        """Un usuario no puede votar dos veces en la misma opción."""
        from django.db import IntegrityError
        Vote.objects.create(user=self.user, option=self.option_a)
        with self.assertRaises(IntegrityError):
            Vote.objects.create(user=self.user, option=self.option_a)


class PollViewTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='pollviewer',
            email='pollviewer@votaciones.com',
            password='TestPass1234!'
        )
        self.team = Team.objects.create(
            name='Equipo Vista Polls',
            created_by=self.user
        )
        TeamMember.objects.create(team=self.team, user=self.user, role='admin')
        self.poll = Poll.objects.create(
            title='Poll de vista',
            team=self.team,
            created_by=self.user,
        )
        self.option = Option.objects.create(poll=self.poll, text='Opción test')

    def test_poll_list_requiere_login(self):
        """La lista de polls redirige si no hay sesión."""
        response = self.client.get(
            reverse('polls:list', kwargs={'team_slug': self.team.slug})
        )
        self.assertEqual(response.status_code, 302)

    def test_poll_list_autenticado(self):
        """Un miembro autenticado puede ver la lista de polls."""
        self.client.login(username='pollviewer', password='TestPass1234!')
        response = self.client.get(
            reverse('polls:list', kwargs={'team_slug': self.team.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_poll_detail_autenticado(self):
        """Un miembro autenticado puede ver el detalle de una poll."""
        self.client.login(username='pollviewer', password='TestPass1234!')
        response = self.client.get(
            reverse('polls:detail', kwargs={
                'team_slug': self.team.slug,
                'poll_id': self.poll.id
            })
        )
        self.assertEqual(response.status_code, 200)

    def test_votar_registra_voto(self):
        """Votar crea un objeto Vote en la base de datos."""
        self.client.login(username='pollviewer', password='TestPass1234!')
        self.client.post(
            reverse('polls:vote', kwargs={
                'team_slug': self.team.slug,
                'poll_id': self.poll.id
            }),
            {'option_id': str(self.option.id)}
        )
        self.assertTrue(
            Vote.objects.filter(user=self.user, option=self.option).exists()
        )

    def test_no_votar_dos_veces(self):
        """Un usuario no puede votar dos veces en la misma poll."""
        self.client.login(username='pollviewer', password='TestPass1234!')
        url = reverse('polls:vote', kwargs={
            'team_slug': self.team.slug,
            'poll_id': self.poll.id
        })
        self.client.post(url, {'option_id': str(self.option.id)})
        self.client.post(url, {'option_id': str(self.option.id)})
        # Solo debe existir 1 voto
        self.assertEqual(
            Vote.objects.filter(user=self.user, option__poll=self.poll).count(),
            1
        )
