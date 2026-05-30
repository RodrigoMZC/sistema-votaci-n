from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from teams.models import Team
from polls.models import Poll, Vote


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_teams = Team.objects.filter(members__user=user)
        context['teams_count']  = user_teams.count()
        context['polls_count']  = Poll.objects.filter(team__in=user_teams).count()
        context['votes_count']  = Vote.objects.filter(user=user).count()
        context['active_polls'] = Poll.objects.filter(team__in=user_teams, is_active=True).count()
        return context
