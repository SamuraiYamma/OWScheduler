
from django.shortcuts import get_object_or_404, render, render_to_response, \
    redirect, reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404

from django.db.models import Q

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, PasswordResetForm

from django.conf import settings
from django.contrib import messages
from django.contrib.messages import get_messages

from dal import autocomplete

from .models import Player, Team, Match, TimeSlot
from .forms import PlayerCreationForm, PlayerChangeForm, TeamAdminForm

""" 
view that handles logging in the current user and 
returns login form and authenticated user
"""


def user_login(request):
    if not request.user.is_authenticated:
        user = None
        form = AuthenticationForm()
        user_team = None
        admin_team = None
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
                    admin_team = Team.objects.filter(team_admin=player)
        return {'login_form': form, 'user': user, 'user_teams': user_team,
                'admin_teams': admin_team}
    else:
        player = Player.objects.get(username=request.user.username)
        user_team = Team.objects.filter(players=player)
        admin_team = Team.objects.filter(team_admin=player)
    return {'user_teams': user_team, 'admin_teams': admin_team}


""" 
view that handles logging out the current user. 
Redirects to previous page after, or home if it can't. 
"""


def user_logout(request):
    next = request.GET.get('next', '/')  # stores previous page, otherwise home
    logout(request)
    return HttpResponseRedirect(next)  # temporary redirect


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request,
                             'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'registration/change_password.html', {
        'form': form
    })


def reset_password(request):
    if request.method == 'POST':
        form = PasswordResetForm(None, request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('scheduler:home'))
    else:
        form = PasswordResetForm()
    return render(request, 'registration/reset_password.html', {'form': form})


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
    player = get_object_or_404(Player, username=username)
    player_teams = Team.objects.filter(players=player)
    admin_teams = Team.objects.filter(team_admin=player)
    times = TimeSlot.objects.filter(players_available=player)
    context = user_login(request)
    context.update({
        'current_player': player,
        'current_teams': player_teams,
        'current_admin_teams': admin_teams,
        'availability': times
    })
    return render(request, 'scheduler/player_profile.html', context)


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

            messages.get_messages(request).used = True
            messages.add_message(request, messages.SUCCESS, "Availability "
                                                            "saved "
                                                            "successfully.")

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
    return render(request, 'scheduler/teams.html', context)


def create_team(request):
    context = user_login(request)
    return render(request, 'scheduler/create_team.html', context)


def my_teams(request, username):
    context = user_login(request)
    if request.user.username == username or request.user.is_superuser:
        return render(request, 'scheduler/my_teams.html', context)
    return render(request, 'scheduler/access_denied.html', context)


def team_admin(request, teamID):
    context = user_login(request)
    team = get_object_or_404(Team, teamID=teamID)
    if request.user == team.team_admin or \
            request.user.is_superuser:

        #  there was a weird problem with setting initial data in the form
        #  used someone else's fix
        #  https://stackoverflow.com/questions/43091200/initial-not-working-on-form-inputs
        if request.POST & TeamAdminForm.base_fields.keys():
            form = TeamAdminForm(request.POST)
        else:
            form = TeamAdminForm(initial={'team_alias': team.teamAlias})

        context.update(
            {
                'form': form,
                'team': team,
                'players': team.players.all(),
                'all_players': Player.objects.order_by('-battlenetID'),
            }
        )

        if request.method == 'POST':
            players_to_add = request.POST.get('players-to-add', None)
            if players_to_add:
                players_to_add = players_to_add.split(',')
                for new_player in players_to_add:
                    if new_player not in team.players.all():
                        team.players.add(Player.objects.get(
                            username=new_player))
                    else:
                        messages.get_messages(request).used = True
                        messages.add_message(request, messages.ERROR,
                                             Player.objects.get(
                                                 username=new_player).
                                             battlenetID + "is already "
                                             "on your team!")
                        context['form'] = TeamAdminForm(
                            initial={'team_alias': team.teamAlias})
                        return render(request, 'scheduler/team_admin.html',
                                      context)

            new_admin = request.POST.get('new-admin', None)
            if new_admin:
                admin = Player.objects.get(username=new_admin)
                # make sure team admin is a different player
                if admin != team.team_admin:
                    team.team_admin = admin
                    team.save()
                    return redirect(reverse('scheduler:my_teams',
                                            kwargs={
                                                'username':
                                                    request.user.username}))
                else:
                    messages.get_messages(request).used = True
                    messages.add_message(request, messages.ERROR,
                                         "You are already the admin. "
                                         "What are you trying to do?")
                    return render(request, 'scheduler/team_admin.html',
                                  context)

            if form.is_valid():
                if form.cleaned_data['team_alias']:
                    team.teamAlias = form.cleaned_data['team_alias']
                    context['form'] = TeamAdminForm(
                        initial={'team_alias': team.teamAlias})
                else:
                    print("alias failed")
        return render(request, 'scheduler/team_admin.html', context)
    return render(request, 'scheduler/access_denied.html')


""" displays the profile page for a team """


def team_profile(request, teamID):
    team = get_object_or_404(Team, teamID=teamID)
    context = user_login(request)
    context['current_team'] = team
    roster = Team.objects.get(teamID=teamID).players.all()
    context['roster'] = roster

    if roster:
        all_times = TimeSlot.objects.filter(
            players_available=roster[0])
        for player in roster:
            all_times = all_times.filter(
                players_available=player).order_by('dayOfWeek', 'hour')
            # filter so that times only contains that teams availability

        context['selected_players'] = roster
        context['selected_times'] = all_times

    if request.method == 'POST':
        selected_roster = request.POST.getlist('selected_user')
        #  don't filter through every player if we already have it stored
        if len(selected_roster) == len(roster):
            context['selected_times'] = all_times
            context['selected_players'] = roster
        #  filter list by availability for all selected team members
        elif selected_roster and roster:
            #  filter by the first player
            player1 = Player.objects.get(battlenetID=selected_roster[0])
            selected_times = TimeSlot.objects.filter(
                players_available=player1)
            #  filter by everyone else
            for player in selected_roster:
                selected_times = selected_times.filter(players_available=
                                      Player.objects.get(battlenetID=player))\
                    .order_by('dayOfWeek', 'hour')

            context['selected_players'] = selected_roster
            context['selected_times'] = selected_times
        else:
            context['selected_players'] = []
            context['selected_times'] = []

    return render(request, 'scheduler/team_profile.html', context)


"""
Allows a user to join a team. Also provides a way for a superuser to add a 
player to a team without going through the admin page.

:param the teamID of the team to join
:param the username of the player to add to a team
"""


def join_team(request, teamID, username):
    #  user must be logged in and
    #  user is joining a team themselves or is superuser or is team admin
    if request.user.is_authenticated and \
            (request.user.username == username or
             request.user.is_superuser or
             Player.objects.get(username=request.user.username) ==
             Team.objects.get(teamID=teamID).team_admin):
        if request.method == 'GET':
            #  a team can have 50 players
            if len(Team.objects.get(teamID=teamID).players.all()) >= 50:
                messages.get_messages(request).used = True
                messages.add_message(
                    request, messages.ERROR, "Join team failed. Only 50 "
                                             "players can be on a team."
                )
                return redirect('scheduler:teams')
            #  TODO: test this !
            print(len(Team.objects.get(teamID=teamID).players.all()))
            player = Player.objects.get(username=username)
            team = Team.objects.get(teamID=teamID)
            if player not in team.players.all():
                team.players.add(player)
            else:
                messages.get_messages(request).used = True
                messages.add_message(request, messages.ERROR, "You cannot "
                                                              "join a team "
                                                              "you are "
                                                              "already in.")
    else:
        messages.get_messages(request).used = True
        messages.add_message(
            request, messages.ERROR, "Join team failed. Please check your "
                                     "login credentials.")
    return redirect('scheduler:teams')


"""
Allows a user to leave a team. Allows a superuser to remove a player from 
their team. This can be used later to allow team leaders to remove players.

:param the username of the player to remove from a team
"""


def leave_team(request, teamID, username):
    # verify player and team exists, otherwise 404
    get_object_or_404(Team, teamID=teamID)
    get_object_or_404(Player, username=username)

    if request.user.is_authenticated:
        #  user is superuser or trying to remove themselves from a team
        if request.user.username == username or \
                request.user.is_superuser:
            if request.method == 'GET':
                player = Player.objects.get(username=username)
                team = Team.objects.get(teamID=teamID)
                if player in team.players.all():
                    team.players.remove(player)
                    messages.get_messages(request).used = True
                    messages.add_message(request, messages.SUCCESS,
                                         "Left team successfully.")
                else:
                    messages.get_messages(request).used = True
                    messages.add_message(request, messages.ERROR,
                                         "You cannot leave a team you are "
                                         "not in.")

        #  team admin kicking a player from a team
        if Player.objects.get(username=request.user.username) == \
                Team.objects.get(teamID=teamID).team_admin:
            if request.method == 'GET':
                player = Player.objects.get(username=username)
                team = Team.objects.get(teamID=teamID)
                if player in team.players.all():
                    team.players.remove(player)
                    messages.get_messages(request).used = True
                    messages.add_message(request,
                                         messages.SUCCESS,
                                         "Removed player successfully.")
                else:
                    messages.get_messages(request).used = True
                    messages.add_message(request,
                                         messages.ERROR,
                                         "Cannot remove player because they "
                                         "were not in this team.")
                return redirect(reverse('scheduler:team_admin', kwargs={
                    'teamID': teamID}))

    else:
        messages.get_messages(request).used = True
        messages.add_message(request, messages.ERROR, "Leave team failed. "
                                                      "Please check your "
                                                      "login credentials.")
    return redirect('scheduler:teams')


def delete_team(request, teamID):
    team = get_object_or_404(Team, teamID=teamID)
    if Player.objects.get(username=request.user.username) == team.team_admin or \
            request.user.is_superuser:
        team.delete()
        messages.get_messages(request).used = True
        messages.add_message(request, messages.SUCCESS, "Deleted team "
                                                        "successfully.")
        return redirect(reverse('scheduler:teams'))
    return render(request, 'scheduler/access_denied.html')


"""
view to add a new user and log them in. Redirects on successful user 
creation or shows form errors if the input was not valid.
"""


def register(request):
    if not request.user.is_authenticated:
        if request.method == 'POST':
            form = PlayerCreationForm(request.POST)
            if form.is_valid():
                form.save()
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=password)
                login(request, user)
                messages.get_messages(request).used = True
                messages.add_message(request, messages.SUCCESS,
                                     "Your account has been created "
                                     "successfully! Make sure to add "
                                     "information to your profile using the "
                                     "account page.")
                return HttpResponseRedirect(reverse('scheduler:home'))
            else:
                messages.get_messages(request).used = True
                messages.add_message(request, messages.ERROR,
                                     "There was a problem creating your "
                                     "account.")
        else:
            form = PlayerCreationForm()

        context = {
            'form': form
        }

        return render(request, 'scheduler/create_player.html', context)

    # TODO: make a page to tell user to logout
    return render(request, 'scheduler/access_denied.html')


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


def handler403(request, exception,
               template_name="scheduler/access_denied.html"):
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
