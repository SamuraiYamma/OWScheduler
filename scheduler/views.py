from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404, render, render_to_response
from django.db.models import Q
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic import TemplateView, View
from django.conf import settings

from dal import autocomplete

from .models import Player, Team, Match, TimeSlot
from .forms import PlayerCreationForm, PlayerChangeForm

""" Home page that also manages login and it's form """


def home(request):
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
                # or any other success page
                return render(request, 'scheduler/default.html')

    context = {
        'form': form,
        'user': user,
    }

    return render(request, 'scheduler/default.html', context)


""" view that handles logging out the current user. """


def user_logout(request):
    logout(request)
    return render(request, 'scheduler/default.html')


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
    context = {'player_list': player_list}
    return render(request, 'scheduler/players.html', context)


""" displays the profile page for a player by username (battletag doesn't work in url) """


def player_profile(request, username):
    player = Player.objects.get(username=username)
    return render(request, 'scheduler/player_profile.html', {'current_player': player})


""" displays the player account info """


def account(request, username):
    player = get_object_or_404(Player, username=username)
    form = PlayerChangeForm
    context = {
        'form': form,
        'player': player,
    }
    return render(request, 'scheduler/account.html', context)


""" displays the page that lists all the teams, sorted by their teamID """


def teams(request):
    team_list = Team.objects.order_by('-teamID')
    context = {'team_list': team_list}
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


def teamProfile(request, teamID):
    team = get_object_or_404(Team, pk=teamID)
    return render(request, 'scheduler/teamProfile.html')


""" view to add a new user """


def register(request):
    if request.method == 'POST':
        form = PlayerCreationForm(request.POST)
    else:
        form = PlayerCreationForm()

    context = {
        'form': form
    }

    return render(request, 'scheduler/create_player.html', context)
