from django.shortcuts import get_object_or_404, render
from .models import Player, Team, Match, TimeSlot

"""
Go to the home page
"""


def home(request):
    return render(request, 'scheduler/home.html')


"""
Goes to the players page using the list of players sorted by battletags
"""


def players(request):
    player_list = Player.objects.order_by('-battlenetID')
    context = { 'player_list' : player_list }
    return render(request, 'scheduler/players.html', context)


"""
displays the profile page for a player by battletag
"""


def playerProfile(request, battlenetID):
    player = get_object_or_404(Player, pk=battlenetID)
    return render(request, 'scheduler/playerProfile.html')


"""
displays the player account info
"""


def account(request, battlenetID):
    player = get_object_or_404(Player, pk=battlenetID)
    return render(request, 'scheduler/account.html')


"""
displays the page that lists all the teams, sorted by their teamID
"""


def teams(request):
    team_list = Team.objects.order_by('-teamID')
    context = { 'team_list' : team_list }
    return render(request, 'scheduler/teams.html', context)


"""
displays the profile page for a team
"""


def teamProfile(request, teamID):
    team = get_object_or_404(Team, pk=teamID)
    return render(request, 'scheduler/teamProfile.html')
