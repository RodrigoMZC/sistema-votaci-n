from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, View, TemplateView
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from .models import Poll, Option, Vote
from teams.models import Team, TeamMember


class MyPollsView(LoginRequiredMixin, TemplateView):
    """Todas las votaciones de todos los equipos del usuario."""
    template_name = 'polls/my_polls.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        filtro = self.request.GET.get('estado', 'todas')

        # Cerrar automáticamente encuestas con deadline vencida
        stale = Poll.objects.filter(
            team__members__user=user,
            is_active=True
        ).distinct()
        for poll in stale:
            poll.check_and_close()

        user_teams = Team.objects.filter(members__user=user).prefetch_related(
            Prefetch(
                'polls',
                queryset=Poll.objects.annotate(
                    total_votes=Count('options__votes')
                ).order_by('-created_at'),
                to_attr='all_polls'
            )
        )

        teams_with_polls = []
        total_polls = 0
        for team in user_teams:
            polls = team.all_polls
            if filtro == 'activas':
                polls = [p for p in polls if p.is_active]
            elif filtro == 'cerradas':
                polls = [p for p in polls if not p.is_active]

            # Marcar si el usuario ya votó en cada encuesta
            for poll in polls:
                poll.user_voted = Vote.objects.filter(
                    user=user, option__poll=poll
                ).exists()

            if polls:
                teams_with_polls.append({'team': team, 'polls': polls})
            total_polls += len(polls)

        context['teams_with_polls'] = teams_with_polls
        context['total_polls'] = total_polls
        context['filtro'] = filtro
        return context


class MyVotesView(LoginRequiredMixin, TemplateView):
    """Historial de votos emitidos por el usuario."""
    template_name = 'polls/my_votes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        votes = (
            Vote.objects
            .filter(user=user)
            .select_related('option__poll__team', 'option')
            .order_by('-voted_at')
        )

        context['votes'] = votes
        context['total'] = votes.count()
        return context


class PollCreateView(LoginRequiredMixin, View):
    template_name = 'polls/poll_create.html'

    def _get_team_or_403(self, request, team_slug):
        team = get_object_or_404(Team, slug=team_slug, members__user=request.user)
        is_admin = team.members.filter(user=request.user, role='admin').exists()
        if not is_admin:
            return None, None
        return team, True

    def get(self, request, team_slug):
        team, is_admin = self._get_team_or_403(request, team_slug)
        if team is None:
            messages.error(request, 'Solo los administradores pueden crear votaciones.')
            return redirect('teams:detail', slug=team_slug)
        return render(request, self.template_name, {'team': team})

    def post(self, request, team_slug):
        team, is_admin = self._get_team_or_403(request, team_slug)
        if team is None:
            messages.error(request, 'Solo los administradores pueden crear votaciones.')
            return redirect('teams:detail', slug=team_slug)

        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        poll_type = request.POST.get('type', 'simple')
        required_votes = request.POST.get('required_votes', '0').strip() or '0'
        deadline_raw = request.POST.get('deadline', '').strip()
        option_texts = request.POST.getlist('option_text')
        option_weights = request.POST.getlist('option_weight')

        errors = []
        if not title:
            errors.append('El título es obligatorio.')

        options_clean = [t.strip() for t in option_texts if t.strip()]
        if len(options_clean) < 2:
            errors.append('Debes agregar al menos 2 opciones.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, self.template_name, {
                'team': team,
                'form_data': request.POST,
            })

        deadline = None
        if deadline_raw:
            from django.utils.dateparse import parse_datetime
            deadline = parse_datetime(deadline_raw)
            if deadline and timezone.is_naive(deadline):
                deadline = timezone.make_aware(deadline)

        poll = Poll.objects.create(
            title=title,
            description=description,
            type=poll_type if poll_type in ('simple', 'weighted') else 'simple',
            required_votes=int(required_votes) if required_votes.isdigit() else 0,
            deadline=deadline,
            team=team,
            created_by=request.user,
            is_active=True,
        )

        for i, text in enumerate(options_clean):
            weight = 1.0
            if poll_type == 'weighted':
                try:
                    weight = float(option_weights[i]) if i < len(option_weights) else 1.0
                except (ValueError, IndexError):
                    weight = 1.0
            Option.objects.create(poll=poll, text=text, weight=weight)

        messages.success(request, f'Votación "{poll.title}" creada exitosamente.')
        return redirect('teams:detail', slug=team_slug)


class PollListView(LoginRequiredMixin, ListView):
    """Lista todas las encuestas activas de un equipo"""
    model = Poll
    template_name = 'polls/poll_list.html'
    context_object_name = 'polls'
    paginate_by = 10

    def get_queryset(self):
        self.team = get_object_or_404(
            Team,
            slug=self.kwargs['team_slug'],
            members__user=self.request.user
        )
        # Cerrar automáticamente las encuestas con deadline vencida antes de listar
        for poll in Poll.objects.filter(team=self.team, is_active=True):
            poll.check_and_close()

        # Muestra todas (activas y cerradas), activas primero
        return Poll.objects.filter(
            team=self.team
        ).annotate(
            vote_count=Count('options__votes')
        ).order_by('-is_active', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = self.team
        context['is_admin'] = self.team.members.filter(
            user=self.request.user, role='admin'
        ).exists()
        for poll in context['polls']:
            poll.total_votes = Vote.objects.filter(option__poll=poll).count()
        return context


class PollDetailView(LoginRequiredMixin, DetailView):
    """Vista detalle para ver una encuesta y sus opciones"""
    model = Poll
    template_name = 'polls/poll_detail.html'
    context_object_name = 'poll'
    pk_url_kwarg = 'poll_id'

    def get_queryset(self):
        team = get_object_or_404(
            Team,
            slug=self.kwargs['team_slug'],
            members__user=self.request.user
        )
        return Poll.objects.filter(team=team)

    def get_object(self, queryset=None):
        poll = super().get_object(queryset)
        # Cerrar automáticamente si el plazo venció o se alcanzaron los votos
        poll.check_and_close()
        return poll

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        poll = self.object
        user = self.request.user

        # Verificar si el usuario ya votó
        voted_options = Vote.objects.filter(
            user=user,
            option__poll=poll
        ).values_list('option_id', flat=True)

        context['has_voted'] = voted_options.exists()
        context['voted_options'] = voted_options
        context['options_with_votes'] = poll.options.annotate(
            vote_count=Count('votes')
        ).order_by('-vote_count')

        # Calcular totales
        total_votes = Vote.objects.filter(option__poll=poll).count()
        context['total_votes'] = total_votes

        # Verificar si es admin del equipo
        context['is_admin'] = poll.team.members.filter(
            user=user, role='admin'
        ).exists()

        return context


class PollVoteView(LoginRequiredMixin, View):
    """Procesa el voto de un usuario en una encuesta"""

    def post(self, request, team_slug, poll_id):
        # Verificar que el usuario es miembro del equipo
        team = get_object_or_404(
            Team,
            slug=team_slug,
            members__user=request.user
        )

        poll = get_object_or_404(Poll, id=poll_id, team=team)

        # Verificar que la encuesta sigue activa
        if not poll.is_active:
            messages.error(request, 'Esta encuesta ya ha sido cerrada.')
            return redirect('polls:detail', team_slug=team_slug, poll_id=poll_id)

        # Verificar que no haya pasado la fecha límite
        if poll.deadline and timezone.now() >= poll.deadline:
            poll.is_active = False
            poll.save()
            messages.error(request, 'El plazo de votación ha expirado.')
            return redirect('polls:detail', team_slug=team_slug, poll_id=poll_id)

        option_id = request.POST.get('option_id')
        
        if not option_id:
            messages.error(request, 'Debes seleccionar una opción.')
            return redirect('polls:detail', team_slug=team_slug, poll_id=poll_id)

        option = get_object_or_404(Option, id=option_id, poll=poll)

        # Verificar si ya votó (depende del tipo de encuesta)
        existing_vote = Vote.objects.filter(user=request.user, option__poll=poll).first()

        if existing_vote:
            # Si ya votó en esta encuesta, no permitir votar de nuevo
            messages.warning(request, 'Ya has votado en esta encuesta.')
            return redirect('polls:detail', team_slug=team_slug, poll_id=poll_id)

        # Crear el voto
        vote = Vote.objects.create(user=request.user, option=option)
        messages.success(request, f'Tu voto por "{option.text}" ha sido registrado.')

        # Verificar si se debe cerrar la encuesta
        poll.check_and_close()

        return redirect('polls:detail', team_slug=team_slug, poll_id=poll_id)


class PollResultsView(LoginRequiredMixin, DetailView):
    """Vista para ver los resultados de una encuesta"""
    model = Poll
    template_name = 'polls/poll_results.html'
    context_object_name = 'poll'
    pk_url_kwarg = 'poll_id'

    def get_queryset(self):
        team = get_object_or_404(
            Team,
            slug=self.kwargs['team_slug'],
            members__user=self.request.user
        )
        return Poll.objects.filter(team=team)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        poll = self.object

        # Obtener todas las opciones con conteo de votos
        options_with_stats = []
        total_votes = Vote.objects.filter(option__poll=poll).count()

        for option in poll.options.all().order_by('text'):
            vote_count = option.votes.count()
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            
            options_with_stats.append({
                'option': option,
                'vote_count': vote_count,
                'percentage': round(percentage, 2)
            })

        # Ordenar por votos descendente
        options_with_stats.sort(key=lambda x: x['vote_count'], reverse=True)

        context['options_with_stats'] = options_with_stats
        context['total_votes'] = total_votes
        context['is_admin'] = poll.team.members.filter(
            user=self.request.user, role='admin'
        ).exists()

        return context


class PollUpdateView(LoginRequiredMixin, View):
    """Editar título, descripción, configuración y opciones de una encuesta."""
    template_name = 'polls/poll_edit.html'

    def _get_poll_or_403(self, request, team_slug, poll_id):
        team = get_object_or_404(Team, slug=team_slug, members__user=request.user)
        poll = get_object_or_404(Poll, id=poll_id, team=team)
        if not team.members.filter(user=request.user, role='admin').exists():
            return None, None
        return team, poll

    def get(self, request, team_slug, poll_id):
        team, poll = self._get_poll_or_403(request, team_slug, poll_id)
        if poll is None:
            messages.error(request, 'Solo los administradores pueden editar votaciones.')
            return redirect('polls:detail', team_slug=team_slug, poll_id=poll_id)
        return render(request, self.template_name, {'team': team, 'poll': poll})

    def post(self, request, team_slug, poll_id):
        team, poll = self._get_poll_or_403(request, team_slug, poll_id)
        if poll is None:
            messages.error(request, 'Solo los administradores pueden editar votaciones.')
            return redirect('polls:detail', team_slug=team_slug, poll_id=poll_id)

        title          = request.POST.get('title', '').strip()
        description    = request.POST.get('description', '').strip()
        poll_type      = request.POST.get('type', poll.type)
        required_votes = request.POST.get('required_votes', '0').strip() or '0'
        deadline_raw   = request.POST.get('deadline', '').strip()
        is_active      = request.POST.get('is_active') == 'on'
        option_ids     = request.POST.getlist('option_id')
        option_texts   = request.POST.getlist('option_text')
        option_weights = request.POST.getlist('option_weight')

        if not title:
            messages.error(request, 'El título es obligatorio.')
            return render(request, self.template_name, {'team': team, 'poll': poll})

        options_clean = [(oid, t.strip(), w) for oid, t, w in
                         zip(option_ids, option_texts, option_weights) if t.strip()]
        if len(options_clean) < 2:
            messages.error(request, 'Debe haber al menos 2 opciones.')
            return render(request, self.template_name, {'team': team, 'poll': poll})

        # Actualizar campos del poll
        deadline = None
        if deadline_raw:
            from django.utils.dateparse import parse_datetime
            deadline = parse_datetime(deadline_raw)
            if deadline and timezone.is_naive(deadline):
                deadline = timezone.make_aware(deadline)

        poll.title          = title
        poll.description    = description
        poll.type           = poll_type if poll_type in ('simple', 'weighted') else 'simple'
        poll.required_votes = int(required_votes) if required_votes.isdigit() else 0
        poll.deadline       = deadline
        poll.is_active      = is_active
        poll.save()

        # Actualizar opciones existentes / agregar nuevas
        existing_ids = set(str(o.id) for o in poll.options.all())
        submitted_ids = set()

        for oid, text, weight in options_clean:
            try:
                w = float(weight) if weight else 1.0
            except ValueError:
                w = 1.0

            if oid and oid in existing_ids:
                # Actualizar opción existente
                poll.options.filter(id=oid).update(
                    text=text,
                    weight=w if poll.type == 'weighted' else 1.0
                )
                submitted_ids.add(oid)
            else:
                # Nueva opción
                opt = Option.objects.create(poll=poll, text=text, weight=w)
                submitted_ids.add(str(opt.id))

        # Eliminar opciones que ya no están (solo si no tienen votos)
        for opt in poll.options.all():
            if str(opt.id) not in submitted_ids:
                if not opt.votes.exists():
                    opt.delete()

        messages.success(request, f'Votación "{poll.title}" actualizada correctamente.')
        return redirect('polls:detail', team_slug=team_slug, poll_id=poll_id)


class PollDeleteView(LoginRequiredMixin, View):
    """Eliminar una encuesta (solo admins)."""
    template_name = 'polls/poll_confirm_delete.html'

    def _get_poll_or_403(self, request, team_slug, poll_id):
        team = get_object_or_404(Team, slug=team_slug, members__user=request.user)
        poll = get_object_or_404(Poll, id=poll_id, team=team)
        if not team.members.filter(user=request.user, role='admin').exists():
            return None, None
        return team, poll

    def get(self, request, team_slug, poll_id):
        team, poll = self._get_poll_or_403(request, team_slug, poll_id)
        if poll is None:
            messages.error(request, 'Solo los administradores pueden eliminar votaciones.')
            return redirect('polls:detail', team_slug=team_slug, poll_id=poll_id)
        total_votes = Vote.objects.filter(option__poll=poll).count()
        return render(request, self.template_name, {
            'team': team, 'poll': poll, 'total_votes': total_votes
        })

    def post(self, request, team_slug, poll_id):
        team, poll = self._get_poll_or_403(request, team_slug, poll_id)
        if poll is None:
            messages.error(request, 'Solo los administradores pueden eliminar votaciones.')
            return redirect('polls:detail', team_slug=team_slug, poll_id=poll_id)
        name = poll.title
        poll.delete()
        messages.success(request, f'Votación "{name}" eliminada.')
        return redirect('teams:detail', slug=team_slug)
