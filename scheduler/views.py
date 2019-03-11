from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404, render, render_to_response, \
    redirect, reverse
from django.db.models import Q
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.views.generic import TemplateView, View
from django.conf import settings
from django.contrib import messages

from dal import autocomplete

from .models import Player, Team, Match, TimeSlot
from .forms import PlayerCreationForm, PlayerChangeForm

""" 
view that handles logging in the current user and 
returns login form and authenticated user
"""


def user_login(request):
    if not request.user.is_authenticated:
        user = None
        form = AuthenticationForm()
        user_team = None
        if request.method == 'POST':
            form = AuthenticationForm(data=request.POST)
            if form.is_valid():
                form.clean()
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(request,
                                    username=username,
                                    password=password)
                if user is not None:
                    login(request, user)
                    player = Player.objects.get(username=username)
                    user_team = Team.objects.filter(players=player)
        return {'login_form': form, 'user': user, 'user_teams': user_team}
    else:
        player = Player.objects.get(username=request.user.username)
        user_team = Team.objects.filter(players=player)
    return {'user_teams': user_team}


""" 
view that handles logging out the current user. 
Redirects to previous page after, or home if it can't. 
"""


def user_logout(request):
    next = request.GET.get('next', '/')  # stores previous page, otherwise home
    logout(request)
    return HttpResponseRedirect(next)  # temporary redirect


""" Home page """


def home(request):
    context = user_login(request)  # has user, user_team, and login_form
    return render(request, 'scheduler/default.html', context)


"""
Goes to the players page using the list of players sorted by battletags and 
uses the player search bar to generate the list of players matching the search.
"""


def players(request):
    player_list = Player.objects.order_by('-battlenetID')
    if request.method == "GET":
        search_query = request.GET.get(
            'player_search', None)  # get text from search
        if search_query:
            player_list = Player.objects.filter(
                battlenetID__icontains=search_query)

    context = user_login(request)
    context.update({
        'player_list': player_list,
    })
    return render(request, 'scheduler/players.html', context)


""" 
displays the profile page for a player by username 
the battletag doesn't work in url so the username is another key we can use to 
identify the player

:param the username of the profile to view
"""


def player_profile(request, username):
    try:
        player = Player.objects.get(username=username)
        times = TimeSlot.objects.filter(players_available=player)
        return render(request, 'scheduler/player_profile.html',
                      {'current_player': player, 'availability': times})
    except Player.DoesNotExist:
        raise Http404


"""
displays the player account info that allows the user to change their 
password, add information to their profile, and set their availability

:param the username of the account to edit
"""


def account(request, username):
    player = get_object_or_404(Player, username=username)
    context = user_login(request)

    if player == request.user or request.user.is_superuser:
        form = PlayerChangeForm(instance=player)
        timeslots = TimeSlot.objects.filter(players_available=player)

        #  creating a list for each hour to fill a table row by row (hour by
        #  hour)
        hour_lists = {}
        for i in range(24):
            hour_lists['hour{0}'.format(i)] = TimeSlot.objects.filter(hour=i)
        context['timeslots'] = timeslots
        context['hour_lists'] = hour_lists

        if request.method == 'POST':
            #  remove previous availability
            for slot in TimeSlot.objects.filter(players_available=player):
                slot.players_available.remove(player)
            #  restore with new availability
            available_times = request.POST.getlist('availability')
            for slot in available_times:
                TimeSlot.objects.get(timeSlotID=slot).players_available.add(
                    player)

        context['form'] = form
        context['player'] = player
        return render(request, 'scheduler/account.html', context)
    return render(request, 'scheduler/access_denied.html')

""" sets the availability of a user based on thier input """

""" 
displays the page that lists all the teams, sorted by their teamID. This 
also implements searching for teams by their name or id.
"""


def teams(request):
    user = request.user
    team_list = Team.objects.order_by('-teamID')
    if request.method == 'GET':
        search_query = request.GET.get('team_search', None)
        if search_query:
            if search_query.isdigit():
                team_list = Team.objects.filter(
                    teamID__exact=int(search_query))
            else:
                team_list = Team.objects.filter(
                    teamAlias__icontains=search_query)

    context = user_login(request)
    context.update({'team_list': team_list})
    print(context['user_teams'])
    return render(request, 'scheduler/teams.html', context)


def my_teams(request, username):
    context = user_login(request)
    if request.user.username == username or request.user.is_superuser:
        return render(request, 'scheduler/my_teams.html', context)
    return render(request, 'scheduler/access_denied.html', context)


""" displays the profile page for a team """


def team_profile(request, teamID):
    team = get_object_or_404(Team, teamID=teamID)
    context = user_login(request)
    context['current_team'] = team
    roster = Team.objects.get(teamID=teamID).players.all()
    context['roster'] = roster

    possible_times = TimeSlot.objects.filter(players_available=roster[0])
    for player in roster:
        possible_times = possible_times.filter(
            players_available=player).order_by('dayOfWeek', 'hour')
    # filter so that times only contains that teams availability
    context['times'] = possible_times

    return render(request, 'scheduler/team_profile.html', context)


"""
Allows a user to join a team. Also provides a way for a superuser to add a 
player to a team without going through the admin page.

:param the teamID of the team to join
:param the username of the player to add to a team
"""


def join_team(request, teamID, username):
    if request.user.is_authenticated and \
            (request.user.username == username or request.user.is_superuser):
        if request.method == 'GET':
            player = Player.objects.get(username=username)
            Team.objects.get(teamID=teamID).players.add(player)
    else:
        messages.add_message(
            request, messages.ERROR, "You cannot join a team until you are "
                                     "logged in correctly.")
    return redirect('scheduler:teams')


"""
Allows a user to leave a team. Allows a superuser to remove a player from 
their team. This can be used later to allow team leaders to remove players.

:param the username of the player to remove from a team
"""


def leave_team(request, teamID, username):
    if request.user.is_authenticated and \
            (request.user.username == username or request.user.is_superuser):
        if request.method == 'GET':
            player = Player.objects.get(username=username)
            Team.objects.get(teamID=teamID).players.add(player)
    else:
        messages.add_message(request, messages.ERROR, "You cannot join a "
                                                      "team until you are  "
                                                      "logged in correctly.")
    return redirect('scheduler:teams')


"""
view to add a new user and log them in. Redirects on successful user 
creation or shows form errors if the input was not valid.
"""


def register(request):
    if request.method == 'POST':
        form = PlayerCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.add_message(request, messages.SUCCESS,
                                 "Your account has been created successfully!")
            return HttpResponseRedirect(reverse('scheduler:home'))
        else:
            messages.add_message(request, messages.ERROR,
                                 "There was a problem creating your account.")
    else:
        form = PlayerCreationForm()

    context = {
        'form': form
    }

    return render(request, 'scheduler/create_player.html', context)


"""
using code adapted from https://stackoverflow.com/questions/17662928
/django-creating-a-custom-500-404-error-page 
"""


def handler404(request, exception, template_name="scheduler/404.html"):
    response = render_to_response("scheduler/404.html")
    response.status_code = 404
    return response


def handler500(request, exception, template_name="scheduler/500.html"):
    response = render_to_response("scheduler/500")
    response.status_code = 500
    return response


def handler403(request, exception, template_name="scheduler/access_denied.html"):
    response = render_to_response("scheduler/access_denied.html")
    response.status_code = 403
    return response


""" 
Extends the autocomplete plugin. Creates the parameters used to search for 
a team in PlayerChangeForm team field, which is a drop down search.
"""


class TeamAutoComplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Team.objects.none()

        queryset = Team.objects.filter(is_active=True)
        if self.q:
            if self.q.isdigit():
                queryset = queryset.filter(teamID__exact=self.q)
            else:
                queryset = queryset.filter(teamAlias__icontains=self.q)

        return queryset


class PlayerAutoComplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Player.objects.none()

        queryset = Player.objects.filter(is_active=True)
        if self.q:
            queryset = queryset.filter(battlenetID__icontains=self.q)

        return queryset
