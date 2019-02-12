from django.urls import path, re_path

from . import views

app_name = 'scheduler'
urlpatterns = [
    path('home/', views.home), # home page
    path('players/', views.players), # search for players
    re_path(r'^players/(?P<battlenetID>([A-Za-z]+)#[0-9]{4-5})/', views.playerProfile), # player profile page
    re_path(r'^players/(?P<battlenetID>([A-Za-z]+)#[0-9]{4-5})/account', views.account), # edit player account
    path('teams/', views.teams), # search for teams
    path('team/<int:pk>/', views.teamProfile), # team profile page
]
