from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.http import HttpResponse, Http404

from .models import Player, Team, Match, TimeSlot

def home(request):
    return render(request, 'scheduler/home.html')

def players(request):
    player_list = Player.objects.order_by('-battlenetID')
    context = { 'player_list' : player_list }
    return render(request, 'scheduler/players.html', context)

def playerProfile(request, battlenetID):
    player = get_object_or_404(Player, pk=battlenetID)
    return render(request, 'scheduler/playerProfile.html')

def account(request, battlenetID):
    player = get_object_or_404(Player, pk=battlenetID)
    return render(request, 'scheduler/account.html')

def teams(request):
    team_list = Team.objects.order_by('-teamID')
    context = { 'team_list' : team_list }
    return render(request, 'scheduler/teams.html', context)

def teamProfile(request, teamID):
    team = get_object_or_404(Team, pk=teamID)
    return render(request, 'scheduler/teamProfile.html')
