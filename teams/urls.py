from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    path('', views.TeamListView.as_view(), name='list'),
    path('create/', views.TeamCreateView.as_view(), name='create'),
    path('<slug:slug>/', views.TeamDetailView.as_view(), name='detail'),
    path('<slug:slug>/edit/', views.TeamUpdateView.as_view(), name='edit'),
    path('<slug:slug>/delete/', views.TeamDeleteView.as_view(), name='delete'),
    path('<slug:slug>/members/add/', views.AddMemberView.as_view(), name='add_member'),
    path('members/<uuid:pk>/remove/', views.RemoveMemberView.as_view(), name='remove_member'),
    path('api/teams/', views.TeamListAPIView.as_view(), name='api_team_list'),
    path('api/teams/<slug:slug>/', views.TeamDetailAPIView.as_view(), name='api_team_detail'),
    path('api/teams/<slug:slug>/members/', views.TeamMemberAPIView.as_view(), name='api_team_members'),
    path('api/teams/<slug:slug>/members/<uuid:pk>/remove/', views.RemoveMemberAPIView.as_view(), name='api_remove_member'),
]