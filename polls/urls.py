from django.urls import path
from . import views

app_name = 'polls'

urlpatterns = [
    path('', views.MyPollsView.as_view(), name='my_polls'),
    path('mis-votos/', views.MyVotesView.as_view(), name='my_votes'),
    path('team/<slug:team_slug>/', views.PollListView.as_view(), name='list'),
    path('team/<slug:team_slug>/create/', views.PollCreateView.as_view(), name='create'),
    path('team/<slug:team_slug>/<uuid:poll_id>/', views.PollDetailView.as_view(), name='detail'),
    path('team/<slug:team_slug>/<uuid:poll_id>/vote/', views.PollVoteView.as_view(), name='vote'),
    path('team/<slug:team_slug>/<uuid:poll_id>/results/', views.PollResultsView.as_view(), name='results'),
    path('team/<slug:team_slug>/<uuid:poll_id>/edit/', views.PollUpdateView.as_view(), name='edit'),
    path('team/<slug:team_slug>/<uuid:poll_id>/delete/', views.PollDeleteView.as_view(), name='delete'),
    path('api/team/<slug:team_slug>/polls/', views.PollListAPIView.as_view(), name='api_poll_list'),
    path('api/team/<slug:team_slug>/polls/<uuid:poll_id>/', views.PollDetailAPIView.as_view(), name='api_poll_detail'),
    path('api/team/<slug:team_slug>/polls/<uuid:poll_id>/vote/', views.PollVoteAPIView.as_view(), name='api_poll_vote'),
    path('api/team/<slug:team_slug>/polls/<uuid:poll_id>/results/', views.PollResultsAPIView.as_view(), name='api_poll_results'),
]
