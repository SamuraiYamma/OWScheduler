"""
This file handles the connections between the server and client. The views
provide information for the html files and handle redirection and rendering
of templates. The views also ensure access protection for users, and require
authentication on certain pages.

Allison Bickford
4/11/2019
"""
from django.shortcuts import get_object_or_404, render, render_to_response, \
    redirect, reverse
from django.http import HttpResponseRedirect

from django.db.models import Q, Avg

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

from django.contrib import messages

from dal import autocomplete

from scheduler.models import Player, Team, Match, TimeSlot
from scheduler.forms import PlayerCreationForm, PlayerChangeForm, \
    TeamAdminForm, MatchCreationForm, CreateTeamForm
from scheduler.decorators import is_team_admin_or_superuser, \
    is_user_or_superuser


def login_context(request):
    """
    view that handles logging in the current user and returning the context

    :param request: network request info, such as user
    :returns dict containing login form, authenticated user,
        teams, and teams user admins
    """
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

    player = Player.objects.get(username=request.user.username)
    user_team = Team.objects.filter(players=player)
    admin_team = Team.objects.filter(team_admin=player)
    return {'user_teams': user_team, 'admin_teams': admin_team}


@login_required
def user_logout(request):
    """
    view that handles logging out the current user.
    Redirects to previous page after, or home if it can't.
    """
    next = request.GET.get('next', '/')  # stores previous page, otherwise home
    logout(request)
    return HttpResponseRedirect(next)  # temporary redirect


def home(request):
    """
    Home page

    :param request: network request info
    :return: template and variables to pass into it
    """
    context = login_context(request)  # has user, user_team, and login_form
    return render(request, 'scheduler/default.html', context)


def players(request):
    """
    Goes to the players page using the list of players sorted by battletags and
    uses the player search bar to generate the list of players matching the
    search.

    :param request: network request info
    :return: login context and list of all players
    """
    player_list = Player.objects.filter(is_active=True). \
        order_by('-battlenetID')

    context = login_context(request)
    context.update({
        'player_list': player_list,
    })
    return render(request, 'scheduler/players.html', context)


def player_profile(request, username):
    """
    displays the profile page for a player by username
    the battletag doesn't work in url so the username is another key we can use to
    identify the player

    :param request: network request info
    :param username: username of the players whose profile to view
    """
    player = get_object_or_404(Player, username=username)
    player_teams = Team.objects.filter(players=player)
    admin_teams = Team.objects.filter(team_admin=player)
    times = TimeSlot.objects.filter(players_available=player)
    context = login_context(request)
    context.update({
        'current_player': player,
        'current_teams': player_teams,
        'current_admin_teams': admin_teams,
        'availability': times
    })
    return render(request, 'scheduler/player_profile.html', context)


@login_required
@is_user_or_superuser
def account(request, username):
    """
    displays the player account info that allows the user to change their
    password, add information to their profile, and set their availability.
    This is only available to the user themselves, or a superuser.

    :param request: network session info
    :param username: username of user whose the account to edit
    :returns template with context to change user info, or access denied
    template if user is not verified
    """
    player = get_object_or_404(Player, username=username)
    context = login_context(request)

    timeslots = TimeSlot.objects.filter(players_available=player)

    #  creating a list for each hour to fill a table row by row (hour by
    #  hour)
    hour_lists = {}
    for i in range(24):
        hour_lists['hour{0}'.format(i)] = TimeSlot.objects.filter(hour=i)
    context['timeslots'] = timeslots
    context['hour_lists'] = hour_lists

    if request.method == 'POST':
        if 'set-profile' in request.POST:
            form = PlayerChangeForm(request.POST, instance=player)
            if form.is_valid():
                form.save()
                messages.get_messages(request).used = True
                messages.add_message(request, messages.SUCCESS,
                                     "Information has been updated.")
            else:
                messages.get_messages(request).used = True
                messages.add_message(request, messages.ERROR,
                                     "Failed to save information.")

        if 'set-availability' in request.POST:
            form = PlayerChangeForm(instance=player)
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
    else:
        form = PlayerChangeForm(instance=player)

    context['form'] = form
    context['player'] = player
    return render(request, 'scheduler/account.html', context)


def teams(request):
    """
    displays the page that lists all the teams, sorted by their teamID. This
    also implements searching for teams by their name or id.

    :param request: HttpRequest with network info
    :return: template for teams with login context and list of all teams
    """
    team_list = Team.objects.order_by('-teamID')

    context = login_context(request)
    context.update({'team_list': team_list})
    return render(request, 'scheduler/teams.html', context)


@login_required
def create_team(request):
    """
    handles creating a team

    :param request: network session info
    :return: template with login context to create a team
    """

    form = CreateTeamForm()
    if request.method == 'POST':
        form = CreateTeamForm(request.POST)
        if form.is_valid():
            form.save()
            admin = Player.objects.get(username=request.user.username)
            new_team = Team.objects.get(teamID=form.cleaned_data["teamID"])
            new_team.team_admin = admin
            new_team.save()
            messages.get_messages(request).used = True
            messages.add_message(request, messages.SUCCESS,
                                 "Information has been updated.")
            return redirect(reverse("scheduler:my_teams", kwargs={"username":request.user.username}))
        else:
            messages.get_messages(request).used = True
            messages.add_message(request, messages.ERROR,
                                 "Failed to save information.")

    context = login_context(request)
    context['form'] = form
    return render(request, 'scheduler/create_team.html', context)


@login_required
@is_user_or_superuser
def my_teams(request, username):
    """
    handles view for accessing teams user is a part of and
    teams the user is the admin of


    :param request: network session info
    :param username: username of player's teams to view
    :return: template with relevant matches and teams in context
    """
    context = login_context(request)
    player = Player.objects.get(username=username)

    # matches a player's team is playing
    teams_playing = Team.objects.filter(players=player)
    user_matches = Match.objects.filter(
        Q(team_1__in=teams_playing) | Q(team_2__in=teams_playing))\
        .distinct()

    # all matches a player is playing in
    playing_matches = Match.objects.filter(
        Q(player_set_1=player) | Q(player_set_2=player)).distinct()

    # all matches for the team they admin
    admin_teams = Team.objects.filter(team_admin=player)
    team_matches = Match.objects.filter(
        Q(team_1__in=admin_teams) | Q(team_2__in=admin_teams)).distinct()

    match_events = []
    for match in playing_matches:
        match_events.append({
            'id': match.matchID,
            'title': str(match.team_1) + ' vs. ' + str(match.team_2),
            'start': str(match.time.year) + '-' +
                     str(match.time.month) + '-' +
                     str(match.time.day),
            'backgroundColor': '#ffb135',
            'participation': 'You are playing in this match!',
            'players_1': list(match.player_set_1.values_list(
                'battlenetID', flat=True)),
            'players_2': list(match.player_set_2.values_list(
                'battlenetID', flat=True)),
        })
    for match in user_matches:
        if match not in playing_matches and match not in team_matches:
            match_events.append({
                'id': match.matchID,
                'title': str(match.team_1) + ' vs. ' + str(match.team_2),
                'start': str(match.time.year) + '-' +
                         str(match.time.month) + '-' +
                         str(match.time.day),
                'backgroundColor': '#007bff',
                'participation': 'Your team is playing this match!',
                'players_1': list(match.player_set_1.values_list(
                    'battlenetID', flat=True)),
                'players_2': list(match.player_set_2.values_list(
                    'battlenetID', flat=True)),
            })
    for match in team_matches:
        if match not in playing_matches:
            match_events.append({
                'id': match.matchID,
                'title': str(match.team_1) + ' vs. ' + str(match.team_2),
                'start': str(match.time.year) + '-' +
                         str(match.time.month) + '-' +
                         str(match.time.day),
                'backgroundColor': '#a0ffa3',
                'participation': 'You admin a team in this match!',
                'players_1': list(match.player_set_1.values_list(
                    'battlenetID', flat=True)),
                'players_2': list(match.player_set_2.values_list(
                    'battlenetID', flat=True)),
            })
    context['matches_playing_json'] = match_events
    return render(request, 'scheduler/my_teams.html', context)


@login_required
@is_team_admin_or_superuser
def team_admin(request, teamID):
    """
    handles view to manage team including players, name, etc. This is only
    available to the team manager/admin and superusers.

    :param request: network session info
    :param teamID: primary key of team to manage
    :return: template with
    """
    context = login_context(request)
    team = get_object_or_404(Team, teamID=teamID)

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
            'all_players': Player.objects.filter(is_active=True).
                           order_by('-battlenetID'),
        }
    )

    if request.method == 'POST':
        players_to_add = request.POST.get('players-to-add', None)
        if players_to_add:
            players_to_add = players_to_add.split(',')
            for new_player in players_to_add:
                if Player.objects.get(username=new_player) \
                        not in team.players.all():
                    team.players.add(Player.objects.get(
                        username=new_player))
                else:
                    messages.get_messages(request).used = True
                    messages.add_message(request, messages.ERROR,
                                         Player.objects.get(
                                             username=new_player).
                                         battlenetID + " is already "
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

            messages.get_messages(request).used = True
            messages.add_message(request, messages.ERROR,
                                 "You are already the admin. "
                                 "What are you trying to do?")
            return render(request, 'scheduler/team_admin.html', context)

        if form.is_valid():
            if form.cleaned_data['team_alias']:
                team.teamAlias = form.cleaned_data['team_alias']
                team.save()
                context['form'] = TeamAdminForm(
                    initial={'team_alias': team.teamAlias})
    return render(request, 'scheduler/team_admin.html', context)


def team_profile(request, teamID):
    """
    displays the profile page for a team and their relevant information

    :param request: network session info
    :param teamID: primary key of team to view profile of
    :return: template with information about the requested team
    """
    team = get_object_or_404(Team, teamID=teamID)
    context = login_context(request)
    # team currently viewing
    context['current_team'] = team

    # players in team
    roster = Team.objects.get(teamID=teamID).players.all()
    context['roster'] = roster

    # avg player skill rating
    if roster.aggregate(avg_sr=Avg('skillRating'))['avg_sr']:
        context['avg_sr'] = int(
            roster.aggregate(avg_sr=Avg('skillRating'))['avg_sr'])
    else:
        context['avg_sr'] = None

    # get available times for all players
    if roster:
        all_times = TimeSlot.objects.filter(
            players_available=roster[0])
        for player in roster:
            all_times = all_times.filter(
                players_available=player).order_by('dayOfWeek', 'hour')
            # filter so that times only contains that teams availability

        context['selected_players'] = roster
        context['selected_times'] = all_times

    # filter times based on selected players
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
                                                       Player.objects.get(
                                                           battlenetID=
                                                           player)) \
                                                .order_by('dayOfWeek', 'hour')

            context['selected_players'] = selected_roster
            context['selected_times'] = selected_times
        else:
            context['selected_players'] = []
            context['selected_times'] = []

    return render(request, 'scheduler/team_profile.html', context)


@login_required
def join_team(request, teamID, username):
    """
    Allows a user to join a team. Also provides a way for a superuser to add a
    player to a team without going through the admin page.

    :param request: network session info
    :param teamID: primary key of team to join
    :param username: username of player requesting to join team
    :return: redirect to my teams view
    """
    #  user must be logged in and
    #  user is joining a team themselves or is superuser or is team admin
    if (request.user.username == username or
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
                return redirect('scheduler:my_teams',
                                username=request.user.username)
            player = Player.objects.get(username=username)
            team = Team.objects.get(teamID=teamID)
            if player not in team.players.all():
                team.players.add(player)
                messages.success(request, "Joined team successfully.")
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
    return redirect('scheduler:my_teams', username=request.user.username)


@login_required
def leave_team(request, teamID, username):
    """
    Allows a user to leave a team. Allows a superuser to remove a player from
    their team. This can be used later to allow team leaders to remove players.

    :param request: network session info
    :param teamID: primary key of team to get removed from
    :param username: username of the player to remove from team
    :return: redirects to team page for users and superusers, while admins are
    redirected to their admin page
    """
    # verify player and team exists, otherwise 404
    get_object_or_404(Team, teamID=teamID)
    get_object_or_404(Player, username=username)

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
    elif Player.objects.get(username=request.user.username) == \
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
                                     "are not in this team.")
            return redirect(reverse('scheduler:team_admin', kwargs={
                'teamID': teamID}))
    else:
        messages.get_messages(request).used = True
        messages.add_message(
            request, messages.ERROR, "Leave team failed. Please check your "
                                     "login credentials.")
    return redirect('scheduler:my_teams', username=request.user.username)


@login_required
@is_team_admin_or_superuser
def delete_team(request, teamID):
    """
    handles deleting a team instance. Requires team admin or superuser
    permissions

    :param request: network session info
    :param teamID: primary key of team to delete
    :return: redirect to all teams view
    """
    team = get_object_or_404(Team, teamID=teamID)
    team.delete()
    messages.get_messages(request).used = True
    messages.add_message(request, messages.SUCCESS, "Deleted team "
                                                    "successfully.")
    return redirect(reverse('scheduler:teams'))


def register(request):
    """
    view to add a new user and log them in. Redirects on successful user
    creation or shows form errors if the input was not valid.

    :param request: network session info
    :return: access denied if user is logged in, otherwise the register
    template
    """
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


@login_required
def create_match(request):
    """
    handles creating a match between teams.

    :param request: network session info
    :return: redirects to next step in creating a match, or access denied if
    a user does not manage/admin any teams
    """
    context = login_context(request)
    if Team.objects.filter(team_admin=
                           Player.objects.get(username=request.user.username)):
        context['all_teams'] = Team.objects.all()
        context['my_team'] = None
        context['opponent_team'] = None
        my_team = None
        opp_team = None
        if request.method == 'POST':
            if request.POST.get('my-team') and \
                    request.POST.get('opponent-team'):
                my_team = Team.objects.get(
                    teamID=request.POST.get('my-team'))
                context['my_team'] = my_team
                opp_team = Team.objects.get(
                    teamID=request.POST.get('opponent-team'))
                context['opponent_team'] = opp_team
                new_match = Match.objects.create(
                    time=request.POST.get('match-time'),
                    team_1=my_team,
                    team_2=opp_team
                )
                return redirect(reverse('scheduler:create_match_next',
                                        kwargs={
                                            'match_id': new_match.matchID}
                                        ))

            messages.get_messages(request).used = True
            messages.add_message(request, messages.ERROR, "Cannot continue. "
                                                          "Please "
                                                          "make sure "
                                                          "all fields are "
                                                          "filled.")

        return render(request, 'scheduler/create_match.html', context)
    return render(request, 'scheduler/access_denied.html')


@login_required
def edit_match(request, match_id):
    """
    Handles changing a match's teams and times. The user must be an admin
    of either team.

    :param request: network session info
    :param match_id: primary key of match to edit
    :return: redirects to create_match_next, or access denied if not an admin
    """
    context = login_context(request)
    match = get_object_or_404(Match, matchID=match_id)

    if (match.team_1.team_admin ==
            Player.objects.get(username=request.user.username) or
            match.team_2.team_admin ==
            Player.objects.get(username=request.user.username)):
        context['is_team_1'] = False
        if match.team_1.team_admin == \
                Player.objects.get(username=request.user.username):
            context['is_team_1'] = True
        context['match'] = match
        context['all_teams'] = Team.objects.all()
        if request.method == 'POST':
            if request.POST.get('my-team'):
                my_team = Team.objects.get(
                    teamID=request.POST.get('my-team'))
                match.team_1 = my_team
            if request.POST.get('opponent-team'):
                opp_team = Team.objects.get(
                    teamID=request.POST.get('opponent-team'))
                match.team_2 = opp_team
            match.time = request.POST.get('match-time')
            match.save()
            return redirect(reverse('scheduler:create_match_next',
                                    kwargs={'match_id': match.matchID}))

        return render(request, 'scheduler/edit_match.html', context)
    return render(request, 'scheduler/access_denied.html')


@login_required
def create_match_next(request, match_id):
    """
    Handles creating/editing optional details for a match. User must be an
    admin of either team.

    :param request: network session info
    :param match_id: primary key of match to change
    :return: redirects to my teams on successful change, access denied if user
    is not an admin, otherwise returns the create_match_next template
    """
    context = login_context(request)
    match = get_object_or_404(Match, matchID=match_id)

    if (match.team_1.team_admin ==
            Player.objects.get(username=request.user.username) or
            match.team_2.team_admin ==
            Player.objects.get(username=request.user.username)):
        match_form = MatchCreationForm(initial={'matchMap': match.matchMap})
        context['match_form'] = match_form
        context['match'] = match

        players_str = ''
        for player in match.player_set_1.all():
            players_str += str(player) + ','
        context['my_players'] = players_str[:-1]

        opponents = ''
        for player in match.player_set_2.all():
            opponents += str(player) + ','

        context['opponent_players'] = opponents[:-1]

        if request.method == 'POST':
            match_form = MatchCreationForm(request.POST)
            my_players = request.POST.get('my-players')
            opp_players = request.POST.get('opponent-players')
            if my_players:
                my_players = my_players.split(',')
                allies = []
                for player in my_players:
                    allies.append(Player.objects.get(username=player))
                match.player_set_1.set(allies)

            if opp_players:
                opp_players = opp_players.split(',')
                enemies = []
                for player in opp_players:
                    enemies.append(Player.objects.get(username=player))
                match.player_set_2.set(enemies)

            if match_form.is_valid():
                map = match_form.cleaned_data['matchMap']
                match.matchMap = map

            if request.POST.get('match-winner'):
                match.winner = request.POST.get('match-winner')
            match.save()
            messages.get_messages(request).used = True
            messages.add_message(request, messages.SUCCESS,
                                 "Created match successfully.")
            return redirect(reverse('scheduler:my_teams',
                                    kwargs={
                                        'username': request.user.username}))

        messages.get_messages(request).used = True
        messages.add_message(request, messages.ERROR,
                             "Failed to create match.")

        return render(request, 'scheduler/create_match_next.html', context)
    return render(request, 'scheduler/access_denied.html')


def handler404(request, exception=None, template_name="scheduler/404.html"):
    """
    using code adapted from https://stackoverflow.com/questions/17662928
    /django-creating-a-custom-500-404-error-page
    """
    response = render_to_response("scheduler/404.html")
    response.status_code = 404
    return response


def handler500(request, exception=None, template_name="scheduler/500.html"):
    """
    using code adapted from https://stackoverflow.com/questions/17662928
    /django-creating-a-custom-500-404-error-page
    """
    response = render_to_response("scheduler/500.html")
    response.status_code = 500
    return response


def handler403(request, exception=None,
               template_name="scheduler/access_denied.html"):
    """
    using code adapted from https://stackoverflow.com/questions/17662928
    /django-creating-a-custom-500-404-error-page
    """
    response = render_to_response("scheduler/access_denied.html")
    response.status_code = 403
    return response


class TeamAutoComplete(autocomplete.Select2QuerySetView):
    """
    Extends the autocomplete plugin. Creates the parameters used to search for
    a team in PlayerChangeForm team field, which is a drop down search.
    """

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
    """
    handles autocomplete for players
    """

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Player.objects.none()

        queryset = Player.objects.filter(is_active=True)
        if self.q:
            queryset = queryset.filter(battlenetID__icontains=self.q)

        return queryset
