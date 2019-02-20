from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404, render, render_to_response, redirect
from django.db.models import Q
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic import TemplateView, View
from django.conf import settings

from dal import autocomplete

from .models import Player, Team, Match, TimeSlot
from .forms import PlayerCreationForm, PlayerChangeForm


def user_login(request):
    user = None
    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            form.clean()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
    return {'login_form': form, 'user': user}


""" view that handles logging out the current user. Redirects to home page after. """


def user_logout(request):
    logout(request)
    return render(request, 'scheduler/default.html')


""" Home page """


def home(request):
    context = user_login(request)

    return render(request, 'scheduler/default.html', context)


""" WARINING: this is currently useless. """


class Home(View):

    def get(self, request, *args, **kwargs):
        return render(request, 'scheduler/default.html')

    def post(self):
        form = AuthenticationForm(data=self.request.POST)
        if form.is_valid():
            form.clean()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(self.request, username=username, password=password)
            if user is not None:
                login(self.request, user)
                # or any other success page
                return render(self.request, 'scheduler/default.html')

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data()
    #     context['form'] = AuthenticationForm()
    #     context['user'] = None
    #     return context


"""
Goes to the players page using the list of players sorted by battletags
"""


def players(request):
    player_list = Player.objects.order_by('-battlenetID')
    if request.method == "GET":
        search_query = request.GET.get('player_search', None)
        if search_query:
            player_list = Player.objects.filter(battlenetID__icontains=search_query)

    context = {
        'player_list': player_list,
    }
    return render(request, 'scheduler/players.html', context)


""" displays the profile page for a player by username (battletag doesn't work in url) """


def player_profile(request, username):
    player = Player.objects.get(username=username)
    return render(request, 'scheduler/player_profile.html', {'current_player': player})


""" displays the player account info """


def account(request, username):
    player = get_object_or_404(Player, username=username)
    form = PlayerChangeForm

    context = user_login(request)
    context.update({
        'form': form,
        'player': player,
    })

    return render(request, 'scheduler/account.html', context)


""" displays the page that lists all the teams, sorted by their teamID """


def teams(request):
    user = request.user
    team_list = Team.objects.order_by('-teamID')
    if request.method == 'GET':
        search_query = request.GET.get('team_search', None)
        if search_query:
            if search_query.isdigit():
                team_list = Team.objects.filter(teamID__exact=int(search_query))
            else:
                team_list = Team.objects.filter(teamAlias__icontains=search_query)

    context = user_login(request)
    context['team_list'] = team_list
    if user:
        context['users_current_team'] = Player.objects.get(username=user.username).team_id
    return render(request, 'scheduler/teams.html', context)


""" Creates the parameters used to search for a team in PlayerChangeForm team field, which is a drop down search. """


class TeamAutoComplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):

        if not self.request.user.is_authenticated():
            return Team.objects.none()

        queryset = Team.objects.filter(is_active=True)

        if self.q:
            queryset = queryset.filter(Q(teamAlias__icontains=self.q) | Q(teamID__exact=self.q))

        return queryset


""" displays the profile page for a team """


def team_profile(request, teamID):
    team = get_object_or_404(Team, teamID=teamID)
    context = user_login(request)
    context['current_team'] = team
    return render(request, 'scheduler/team_profile.html', context)


def join_team(request, teamID, username):
    if request.method == 'GET':
        player_set = Player.objects.filter(username=username).update(team=teamID)
        return render(request, 'scheduler/team_profile.html')


def leave_team(request, teamID, username):
    if request.method == 'GET':
        player_set = Player.objects.filter(username=username).update(team=None)
        return render(request, 'scheduler/teams.html')


""" view to add a new user and log them in """


def register(request):
    if request.method == 'POST':
        form = PlayerCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('scheduler:home')
    else:
        form = PlayerCreationForm()

    context = {
        'form': form
    }

    return render(request, 'scheduler/create_player.html', context)
