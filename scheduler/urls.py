from django.urls import path, re_path

from . import views
app_name = 'scheduler'
urlpatterns = [
    path('', views.home, name='home'),  # home page
    path('players/', views.players, name='players'),  # search for players
    path('players/<str:username>/', views.player_profile, name='player_profile'),  # player profile page
    path('players/<str:username>/account', views.account),  # edit player account
    path('players/<str:username>/set-availability', views.set_availability, name='set_availability'),
    path('register/',  views.register, name='register'),
    path('teams/', views.teams, name='teams'),  # search for teams
    path('team/<int:teamID>/', views.team_profile, name='team_profile'),  # team profile page

    path('logout/', views.user_logout, name='user_logout'),  # logout current user
    path('join_team/<int:teamID>/<str:username>', views.join_team, name='join_team'),
    path('leave_team/<int:teamID>/<str:username>', views.leave_team, name='leave_team'),
    path('default/', views.available_slots, name='get_ava')
]
