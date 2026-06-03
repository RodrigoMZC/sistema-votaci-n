from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Team, TeamMember
from .forms import TeamForm, TeamMemberForm
from .serializers import TeamSerializer, TeamMemberSerializer

User = get_user_model()


class TeamListView(LoginRequiredMixin, ListView):
    model = Team
    template_name = 'teams/team_list.html'
    context_object_name = 'teams'

    def get_queryset(self):
        return Team.objects.filter(members__user=self.request.user)


class TeamDetailView(LoginRequiredMixin, DetailView):
    model = Team
    template_name = 'teams/team_detail.html'
    context_object_name = 'team'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['members'] = self.object.members.select_related('user')
        context['is_admin'] = self.object.members.filter(
            user=self.request.user, role='admin'
        ).exists()
        return context


class TeamCreateView(LoginRequiredMixin, CreateView):
    model = Team
    form_class = TeamForm
    template_name = 'teams/team_form.html'
    success_url = reverse_lazy('teams:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        TeamMember.objects.create(team=self.object, user=self.request.user, role='admin')
        messages.success(self.request, f'Equipo "{self.object.name}" creado exitosamente.')
        return response


class TeamUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Team
    form_class = TeamForm
    template_name = 'teams/team_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def test_func(self):
        team = self.get_object()
        return team.members.filter(user=self.request.user, role='admin').exists()

    def get_success_url(self):
        messages.success(self.request, 'Equipo actualizado correctamente.')
        return reverse_lazy('teams:detail', kwargs={'slug': self.object.slug})


class TeamDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Team
    template_name = 'teams/team_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('teams:list')

    def test_func(self):
        team = self.get_object()
        return team.members.filter(user=self.request.user, role='admin').exists()

    def form_valid(self, form):
        messages.success(self.request, f'Equipo "{self.object.name}" eliminado.')
        return super().form_valid(form)


class AddMemberView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = TeamMember
    form_class = TeamMemberForm
    template_name = 'teams/add_member.html'

    def test_func(self):
        team = get_object_or_404(Team, slug=self.kwargs['slug'])
        return team.members.filter(user=self.request.user, role='admin').exists()

    def form_valid(self, form):
        team = get_object_or_404(Team, slug=self.kwargs['slug'])
        form.instance.team = team
        messages.success(self.request, 'Miembro agregado correctamente.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('teams:detail', kwargs={'slug': self.kwargs['slug']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = get_object_or_404(Team, slug=self.kwargs['slug'])
        return context


class RemoveMemberView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = TeamMember
    template_name = 'teams/remove_member.html'

    def test_func(self):
        member = self.get_object()
        return member.team.members.filter(user=self.request.user, role='admin').exists()

    def form_valid(self, form):
        messages.success(self.request, 'Miembro removido del equipo.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('teams:detail', kwargs={'slug': self.object.team.slug})
    
class TeamListAPIView(generics.ListCreateAPIView):
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Team.objects.filter(members__user=self.request.user)
    
    def perform_create(self, serializer):
        team = serializer.save(created_by=self.request.user)
        TeamMember.objects.get_or_create(team=team, user=self.request.user, defaults={'role': 'admin'})

class TeamDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        return Team.objects.filter(members__user=self.request.user)
    
    def perform_update(self, serializer):
        team = self.get_object()
        is_admin = team.members.filter(user=self.request.user, role='admin').exists()

        if not is_admin:
            raise permissions.PermissionDenied('Solo los administradores pueden editar el equipo.')
        serializer.save()

    def perform_destroy(self, instance):
        is_admin = instance.members.filter(user=self.request.user, role='admin').exists()
        if not is_admin:
            raise permissions.PermissionDenied('Solo los administradores pueden eliminar el equipo.')
        instance.delete()

class TeamMemberAPIView(generics.ListCreateAPIView):
    serializer_class = TeamMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        team = get_object_or_404(Team, slug=self.kwargs['slug'])
        return team.members.select_related('user')

    def perform_create(self, serializer):
        team = get_object_or_404(Team, slug=self.kwargs['slug'])
        is_admin = team.members.filter(user=self.request.user, role='admin').exists()
        if not is_admin:
            raise permissions.PermissionDenied('Solo los administradores pueden agregar miembros.')

        username = self.request.data.get('username')
        if not username:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'username': 'Este campo es requerido.'})

        user = get_object_or_404(User, username=username)

        if team.members.filter(user=user).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'username': f'"{username}" ya es miembro de este equipo.'})

        serializer.save(team=team, user=user)

class RemoveMemberAPIView(generics.DestroyAPIView):
    serializer_class = TeamMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        team = get_object_or_404(Team, slug=self.kwargs['slug'])
        is_admin = team.members.filter(user=self.request.user, role='admin').exists()
        if not is_admin:
            raise permissions.PermissionDenied('Solo los administradores pueden remover miembros.')
        return get_object_or_404(TeamMember, pk=self.kwargs['pk'], team=team)