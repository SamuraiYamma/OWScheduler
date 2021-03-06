"""
Includes all the definitions for urls related to the scheduler app
"""
from django.urls import path

from scheduler import views

app_name = 'scheduler'
urlpatterns = [
    path('', views.home, name='home'),  # home page
    path('players/', views.players, name='players'),  # search for players
    path('players/<str:username>/', views.player_profile,
         name='player_profile'),  # player profile page
    path('players/<str:username>/account/',
         views.account, name='account'),  # edit player account
    path('teams/', views.teams, name='teams'),  # search for teams
    path('players/<str:username>/my-teams/', views.my_teams, name='my_teams'),
    path('teams/<int:teamID>/', views.team_profile,
         name='team_profile'),  # team profile page
    path('teams/<int:teamID>/admin/', views.team_admin, name='team_admin'),
    path('teams/create-team/', views.create_team, name='create_team'),
    path('create-match/', views.create_match, name='create_match'),
    path('edit-match/<int:match_id>/', views.edit_match, name='edit_match'),
    path('create-match/next/<int:match_id>/', views.create_match_next,
         name='create_match_next'),
    path('join_team/<int:teamID>/<str:username>/', views.join_team,
         name='join_team'),
    path('leave_team/<int:teamID>/<str:username>/', views.leave_team,
         name='leave_team'),
    path('delete_team/<int:teamID>/', views.delete_team, name='delete_team')
]
