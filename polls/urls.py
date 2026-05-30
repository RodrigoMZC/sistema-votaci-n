from django.urls import path
from . import views

app_name = 'polls'

urlpatterns = [
    path('team/<slug:team_slug>/', views.PollListView.as_view(), name='list'),
    path('team/<slug:team_slug>/create/', views.PollCreateView.as_view(), name='create'),
    path('team/<slug:team_slug>/<uuid:poll_id>/', views.PollDetailView.as_view(), name='detail'),
    path('team/<slug:team_slug>/<uuid:poll_id>/vote/', views.PollVoteView.as_view(), name='vote'),
    path('team/<slug:team_slug>/<uuid:poll_id>/results/', views.PollResultsView.as_view(), name='results'),
]
