from django.urls import path, re_path

from . import views
app_name = 'scheduler'
urlpatterns = [
    path('', views.home, name='home'),  # home page
    path('players/', views.players), # search for players
    path('players/<str:username>/profile', views.player_profile),  # player profile page
    path('players/<str:username>/account', views.account),  # edit player account
    path('register/',  views.register, name='register'),
    path('teams/', views.teams, name='teams'),  # search for teams
    path('team/<int:teamID>/', views.team_profile, name='team_profile'),  # team profile page

    path('logout/', views.user_logout, name='user_logout'),  # logout current user
]
