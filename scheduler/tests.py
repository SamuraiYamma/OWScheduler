from django.test import TestCase, RequestFactory
from django.db import IntegrityError
from django.contrib import auth, messages
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import reverse

from .models import Player, Team, Match, TimeSlot
from . import views
from scheduler import urls

""" tests for accessing objects of the Player model and their team """

class PlayerModelTests(TestCase):

    def setUp(self):
        Team.objects.create(teamID=1)
        Team.objects.create(teamID=2)
        Player.objects.create(battlenetID="NewUser#0000", username="NewUser0")
        Player.objects.create(battlenetID="NewUser#1111", username="NewUser1")

    def test_player_not_found(self):
        with self.assertRaises(Player.DoesNotExist):
            Player.objects.get(battlenetID="NoUserHere")

    def test_username_not_found(self):
        with self.assertRaises(Player.DoesNotExist):
            Player.objects.get(username="NoUserHere")

    def test_str(self):
        newUser0 = Player.objects.get(battlenetID="NewUser#0000")
        newUser1 = Player.objects.get(battlenetID="NewUser#1111")
        self.assertEqual(str(newUser0), "NewUser#0000")
        self.assertEqual(newUser1.__str__(), "NewUser#1111")

    def test_find_by_username(self):
        newUser0 = Player.objects.get(username="NewUser0")
        newUser1 = Player.objects.get(username="NewUser1")
        self.assertEqual(str(newUser0), "NewUser#0000")
        self.assertEqual(str(newUser1), "NewUser#1111")

    def test_duplicate_error(self):
        with self.assertRaises(IntegrityError):
            Player.objects.create(battlenetID="NewUser#0000", username="NewUser0")

    def test_get_none_team(self):
        self.assertEqual(Player.objects.get(battlenetID="NewUser#0000").team, None)

    def test_set_team(self):
        newUser0 = Player.objects.get(battlenetID="NewUser#0000")
        team1 = Team.objects.get(teamID=1)
        newUser0.team = team1
        self.assertEqual(newUser0.team, team1)

    def test_set_team_all_players(self):
        team2 = Team.objects.get(teamID=2)
        new_user_set = Player.objects.all()
        new_user_set.update(team=team2)
        for player in new_user_set:
            self.assertEqual(player.team, team2)

    def test_leave_team(self):
        newUser0 = Player.objects.get(battlenetID="NewUser#0000")
        newUser0.team = None
        self.assertEqual(newUser0.team, None)

    def test_set_nonexistent_team(self):
        with self.assertRaises(ValueError):
            newUser0 = Player.objects.get(battlenetID="NewUser#0000")
            newUser0.team = 3


""" tests for accessing the Team model objects and their information via alias and id """


class TeamModelTests(TestCase):

    def setUp(self):
        Team.objects.create(teamID=1)
        Team.objects.create(teamID=2, teamAlias="Team2")
        Team.objects.create(teamID=1234, teamAlias="TeamWhite")
        Team.objects.create(teamID=12345, teamAlias="TeamWhite")
        Player.objects.create(battlenetID="NewUser#0000", username="NewUser0")
        Player.objects.create(battlepermissionsnetID="NewUser#1111", username="NewUser1")

    def test_str(self):
        team1 = Team.objects.get(teamID=1)
        team2 = Team.objects.get(teamID=2)
        self.assertEqual(str(team1), "#1")
        self.assertEqual(str(team2), "Team2#2")

    def test_same_alias(self):
        team1234 = Team.objects.get(teamID=1234)
        team12345 = Team.objects.get(teamID=12345)
        self.assertEqual(team1234.teamAlias, team12345.teamAlias)
        self.assertNotEqual(str(team1234), str(team12345))

    def test_same_id(self):
        with self.assertRaises(IntegrityError):
            Team.objects.create(teamID=1)

    def test_set_alias(self):
        team1 = Team.objects.get(teamID=1)
        team1.teamAlias = "Team1"
        self.assertEqual(str(team1), "Team1#1")

    def test_set_multiple_alias(self):
        team_set = Team.objects.filter(teamID__lt=3)
        team_set.update(teamAlias="TeamBlue")
        for team in team_set:
            self.assertEqual(team.teamAlias, "TeamBlue")


""" tests for all the views along with their errors and weaknesses """


class ViewTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.team = Team.objects.create(
            teamID=1,
            teamAlias="test_team"
        )
        self.user1 = Player.objects.create_user(
            username='test_user',
            battlenetID='TestUser#1111',
            email='test@test.com',
            password='test_password',
            team=Team.objects.get(teamID=1)
        )
        self.user2 = Player.objects.create_user(
            username='test_user2',
            battlenetID='TestUser#2222',
            email='test2@test2.com',
            password='test_password2'
        )
        self.admin = Player.objects.create_superuser(
            username='test_admin',
            email='admin@admin.com',
            password='admin'
        )

    #  user login tests
    def test_user_login_context_get(self):
        request = self.client.get(reverse('scheduler:home'))
        self.assertIsNone(request.context['user'])
        self.assertIsNone(request.context['user_team'])
        self.assertIsNotNone(request.context['login_form'])

    def test_failed_user_login_context(self):
        request = self.client.post(reverse('scheduler:home'), {'username': 'test_user', 'password': 'bad_password'})
        self.assertIsNone(request.context['user'])
        self.assertIsNone(request.context['user_team'])
        self.assertIsNotNone(request.context['login_form'])

    def test_user_login_context_post(self):
        request = self.client.post(reverse('scheduler:home'), {'username': 'test_user', 'password': 'test_password'})
        self.assertIsNotNone(request.context['user'])
        self.assertIsNotNone(request.context['user_team'])
        self.assertIsNotNone(request.context['login_form'])

    def test_authenticated_login_context(self):
        self.client.login(username='test_user', password='test_password')
        request = self.client.get(reverse('scheduler:home'))
        self.assertIsNotNone(request.context['user_team'])

    #  home tests
    def test_home(self):
        self.assertTemplateUsed(template_name='scheduler/default.html')

    def test_home_login(self):
        request = self.factory.post(reverse('scheduler:home'), {'username': 'test_user', 'password': 'test_password'})
        request.user = self.user1
        self.assertTrue(request.user.is_authenticated)

    def test_home_logout(self):
        self.client.login(username='test_user', password='test_password')
        response = self.client.get(reverse('scheduler:user_logout'))
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, fetch_redirect_response=False)
        self.assertTemplateUsed(template_name='scheduler/default.html')

    #  other logout tests
    def test_logout_from_teams(self):
        self.client.login(username='test_user', password='test_password')
        response = self.client.get(reverse('scheduler:user_logout'), {'next': '/teams/'})
        self.assertRedirects(response, '/teams/', status_code=302, target_status_code=200, fetch_redirect_response=False)
        self.assertTemplateUsed(template_name='scheduler/teams.html')

    def test_logout_from_players(self):
        self.client.login(username='test_user', password='test_password')
        response = self.client.get(reverse('scheduler:user_logout'), {'next': '/players/'})
        self.assertRedirects(response, '/players/', status_code=302, target_status_code=200, fetch_redirect_response=False)
        self.assertTemplateUsed(template_name='scheduler/players.html')

    #  players tests
    def test_players_template(self):
        self.assertTemplateUsed('scheduler/players.html')

    def test_players_list_size(self):
        request = self.client.get(reverse('scheduler:players'))
        self.assertEqual(len(Player.objects.filter(is_active=True)), len(request.context['player_list']))

    def test_players_search(self):
        request = self.client.get(reverse('scheduler:players'), {'player_search': 'TestUser#1'})
        self.assertEqual(len(request.context['player_list']), 1)

    #  player profile tests
    def test_existing_player(self):
        request = self.client.get('/players/test_user/')
        self.assertEqual(request.status_code, 200)

    def test_nonexistent_player(self):
        request = self.client.get('/players/not_a_user/')
        self.assertEqual(request.status_code, 404)

    #  player account tests
    def test_nonexistent_player_account(self):
        request = self.client.get('/players/not_a_user/account/')
        self.assertEqual(request.status_code, 404)

    def test_wrong_account(self):
        self.client.login(username='test_user', password='test_password')
        request = self.client.get('/players/test_user2/account/')
        self.assertTemplateUsed('scheduler/permission_denied.html')

    def test_admin_account_access(self):
        self.client.login(username='test_admin', password='admin')
        request = self.client.get('/players/test_user2/account/')
        self.assertTemplateUsed('scheduler/account.html')

    def test_correct_account(self):
        self.client.login(username='test_user', password='test_password')
        request = self.client.get('/players/test_user/account/')
        self.assertTemplateUsed('scheduler/account.html')

    #  teams tests
    def test_teams_template(self):
        self.client.get(reverse('scheduler:teams'))
        self.assertTemplateUsed('scheduler/teams.html')

    def test_teams_search_alias(self):
        request = self.client.get(reverse('scheduler:teams'), {'team_search': 'test'})
        self.assertEqual(request.context['team_list'][0], Team.objects.get(teamID=1))

    def test_teams_search_id(self):
        request = self.client.get(reverse('scheduler:teams'), {'team_search': '1'})
        self.assertEqual(request.context['team_list'][0], Team.objects.get(teamID=1))

    def test_teams_search_fail(self):
        request = self.client.get(reverse('scheduler:teams'), {'team_search': 'nothing_here'})
        self.assertEqual(len(request.context['team_list']), 0)

    #  team profile tests
    def test_team_profile_valid(self):
        request = self.client.get('/teams/1/')
        self.assertTemplateUsed('scheduler/team_profile.html')
        self.assertEqual(request.status_code, 200)

    def test_team_profile_fail(self):
        request = self.client.get('/teams/not_a_team/')
        self.assertEqual(request.status_code, 404)

    #  join team tests
    def test_join_team_authenticated(self):
        self.client.login(username='test_user2', password='test_password2')
        request = self.client.get('/join_team/1/test_user2/')
        self.assertEqual(Player.objects.get(username='test_user2').team.teamID, 1)

    def test_join_team_not_authenticated(self):
        self.client.logout()
        request = self.client.get('/join_team/1/test_user2/')
        self.assertIsNotNone(messages.get_messages(request))

    def test_join_team_wrong_user(self):
        self.client.login(username='test_user', password='test_password')
        request = self.client.get('/join_team/1/test_user2/')
        self.assertRedirects(request, reverse('scheduler:teams'))

    #  leave team tests
    def test_leave_team_authenticated(self):
        self.client.login(username='test_user2', password='test_password2')
        request = self.client.get('/leave_team/test_user2/')
        self.assertIsNone(Player.objects.get(username='test_user2').team)

    def test_leave_team_not_authenticated(self):
        self.client.logout()
        request = self.client.get('/leave_team/test_user/')
        self.assertIsNotNone(messages.get_messages(request))

    def test_leave_team_wrong_user(self):
        self.client.login(username='test_user', password='test_password')
        request = self.client.get('/leave_team/test_user2/')
        self.assertRedirects(request, reverse('scheduler:teams'))

    #  register tests
    def test_register_template(self):
        request = self.client.get(reverse('scheduler:register'))
        self.assertTemplateUsed('scheduler/create_player.html')

    def test_register_uses_form(self):
        request = self.client.get(reverse('scheduler:register'))
        self.assertIsNotNone(request.context['form'])

    

