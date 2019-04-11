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
        self.user1 = Player.objects.create(battlenetID="NewUser#0000", username="NewUser0")
        self.user1.role = Player.DAMAGE
        self.user1.university = Player.GVSU
        self.user1.skillRating = 42

        self.user2 = Player.objects.create(battlenetID="NewUser#1111", username="NewUser1")
        self.user2.role = Player.TANK
        self.user2.skillRating = 100

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
            Player.objects.create(
                battlenetID="NewUser#0000", username="NewUser0")

    def test_player_university(self):
        self.assertIsNotNone(Player.objects.filter(university=Player.GVSU))
        self.assertIsNotNone(self.user1.university)
        self.assertIsNone(self.user2.university)

    def test_player_role(self):
        self.assertEqual(self.user1.role, 'Damage')
        self.assertEqual(self.user2.role, 'Tank')
        self.user1.role = Player.SUPPORT
        self.assertEqual(self.user1.role, 'Support')

    def test_player_skill_rating(self):
        self.assertIsNotNone(Player.objects.filter(skillRating__gt=0))
        self.assertIsNotNone(Player.objects.filter(skillRating=100))
        self.assertEqual(self.user1.skillRating, 42)


"""
tests for accessing the Team model objects and 
their information via alias and id 
"""


class TeamModelTests(TestCase):

    def setUp(self):
        self.user0 = Player.objects.create(battlenetID="NewUser#0000",
                                           username="NewUser0")
        self.user1 = Player.objects.create(battlenetID="NewUser#1111",
                                           username="NewUser1")
        Team.objects.create(teamID=1, team_admin=self.user0)
        Team.objects.create(teamID=2, teamAlias="Team2", team_admin=self.user1)
        Team.objects.create(teamID=1234, teamAlias="TeamWhite",
                            organization="GVSU")
        Team.objects.create(teamID=12345, teamAlias="TeamWhite")

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

    def test_team_admin(self):
        self.assertIsNotNone(Team.objects.get(teamID=1).team_admin)
        self.assertIsNotNone(Team.objects.get(teamID=2).team_admin)
        self.assertIsNone(Team.objects.get(teamID=1234).team_admin)
        self.assertIsNone(Team.objects.get(teamID=12345).team_admin)

    def test_org(self):
        self.assertIsNotNone(Team.objects.get(teamID=1234).organization)
        self.assertIsNone(Team.objects.get(teamID=1).organization)

    def test_set_org(self):
        team = Team.objects.get(teamID=1)
        team.organization = "GV"
        team.save()
        self.assertEqual(team.organization, "GV")

    def test_team_active(self):
        self.assertTrue(Team.objects.get(teamID=1).is_active)
        team = Team.objects.get(teamID=2)
        team.is_active = False
        team.save()
        self.assertFalse(Team.objects.get(teamID=2).is_active)


""" tests for all the views along with their errors and weaknesses """


class UserLoginTests(TestCase):
    def setUp(self):
        self.team = Team.objects.create(
            teamID=1,
            teamAlias="test_team"
        )

        self.user1 = Player.objects.create_user(
            username='test_user',
            battlenetID='TestUser#1111',
            email='test@test.com',
            password='test_password',
        )
        self.team.players.add(Player.objects.get(username='test_user'))
        self.team.team_admin = Player.objects.get(username='test_user')
        self.team.save()
        TimeSlot.objects.get(timeSlotID=1).players_available.add(self.user1)

    def test_user_login_context_get(self):
        request = self.client.get(reverse('scheduler:home'))
        self.assertIsNone(request.context['user'])
        self.assertIsNone(request.context['user_teams'])
        self.assertIsNotNone(request.context['login_form'])

    def test_failed_user_login_context(self):
        request = self.client.post(reverse('scheduler:home'),
                                   {'username': 'test_user',
                                    'password': 'bad_password'})
        self.assertIsNone(request.context['user'])
        self.assertIsNone(request.context['user_teams'])
        self.assertIsNotNone(request.context['login_form'])

    def test_user_login_context_post(self):
        request = self.client.post(reverse('scheduler:home'),
                                   {'username': 'test_user',
                                    'password': 'test_password'})
        self.assertIsNotNone(request.context['user'])
        self.assertIsNotNone(request.context['user_teams'])
        self.assertIsNotNone(request.context['login_form'])

    def test_authenticated_login_context(self):
        self.client.login(username='test_user', password='test_password')
        request = self.client.get(reverse('scheduler:home'))
        self.assertIsNotNone(request.context['user_teams'])


class HomeViewTests(TestCase):
    def setUp(self):
        self.team = Team.objects.create(
            teamID=1,
            teamAlias="test_team"
        )

        self.user1 = Player.objects.create_user(
            username='test_user',
            battlenetID='TestUser#1111',
            email='test@test.com',
            password='test_password',
        )
        self.team.players.add(Player.objects.get(username='test_user'))
        self.team.team_admin = Player.objects.get(username='test_user')
        self.team.save()
        TimeSlot.objects.get(timeSlotID=1).players_available.add(self.user1)

    def test_home(self):
        self.assertTemplateUsed(template_name='scheduler/default.html')

    def test_home_login(self):
        request = self.client.post(reverse('scheduler:home'),
                                    {'username': 'test_user',
                                     'password': 'test_password'})
        request.user = self.user1
        self.assertTrue(request.user.is_authenticated)

    def test_home_logout(self):
        self.client.login(username='test_user', password='test_password')
        response = self.client.get(reverse('user_logout'))
        self.assertRedirects(response, '/', status_code=302,
                             target_status_code=200,
                             fetch_redirect_response=False)
        self.assertTemplateUsed(template_name='scheduler/default.html')

    #  other logout tests
    def test_logout_from_teams(self):
        self.client.login(username='test_user', password='test_password')
        response = self.client.get(reverse('user_logout'),
                                   {'next': '/teams/'})
        self.assertRedirects(response, '/teams/', status_code=302,
                             target_status_code=200,
                             fetch_redirect_response=False)
        self.assertTemplateUsed(template_name='scheduler/teams.html')


class PlayersViewTests(TestCase):
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
        )
        self.team.players.add(Player.objects.get(username='test_user'))
        self.team.team_admin = Player.objects.get(username='test_user')
        self.team.save()
        TimeSlot.objects.get(timeSlotID=1).players_available.add(self.user1)

        self.user2 = Player.objects.create_user(
            username='test_user2',
            battlenetID='TestUser#2222',
            email='test2@test2.com',
            password='test_password2'
        )
        self.user3 = Player.objects.create_user(
            username='test_user3',
            battlenetID='TestUser#3333',
            email='test3@test3.com',
            password='test_password3'
        )
        self.admin = Player.objects.create_superuser(
            username='test_admin',
            email='admin@admin.com',
            password='admin'
        )

    def test_players_template(self):
        self.assertTemplateUsed('scheduler/players.html')

    def test_players_list_size(self):
        request = self.client.get(reverse('scheduler:players'))
        self.assertEqual(len(Player.objects.filter(is_active=True)),
                         len(request.context['player_list']))

    def test_login_from_players(self):
        self.client.logout()
        request = self.factory.post(reverse('scheduler:players'),
                                    {'username': 'test_user',
                                     'password': 'test_password'})
        request.user = self.user1
        self.assertTrue(request.user.is_authenticated)

    def test_logout_from_players(self):
        self.client.login(username='test_user', password='test_password')
        response = self.client.get(reverse('user_logout'),
                                   {'next': '/players/'})
        self.assertRedirects(response, '/players/', status_code=302,
                             target_status_code=200,
                             fetch_redirect_response=False)
        self.assertTemplateUsed(template_name='scheduler/players.html')


class PlayerProfileViewTests(TestCase):
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
        )
        self.team.players.add(Player.objects.get(username='test_user'))
        self.team.team_admin = Player.objects.get(username='test_user')
        self.team.save()
        TimeSlot.objects.get(timeSlotID=1).players_available.add(self.user1)

        self.user2 = Player.objects.create_user(
            username='test_user2',
            battlenetID='TestUser#2222',
            email='test2@test2.com',
            password='test_password2'
        )
        self.user3 = Player.objects.create_user(
            username='test_user3',
            battlenetID='TestUser#3333',
            email='test3@test3.com',
            password='test_password3'
        )
        self.admin = Player.objects.create_superuser(
            username='test_admin',
            email='admin@admin.com',
            password='admin'
        )

    def test_existing_player(self):
        request = self.client.get('/players/test_user/')
        self.assertEqual(request.status_code, 200)

    def test_nonexistent_player(self):
        request = self.client.get('/players/not_a_user/')
        self.assertEqual(request.status_code, 404)

    def test_profile_context(self):
        request = self.client.get('/players/test_user/')
        self.assertIsNotNone(request.context['current_player'])
        self.assertIsNotNone(request.context['current_teams'])
        self.assertIsNotNone(request.context['current_admin_teams'])
        self.assertIsNotNone(request.context['availability'])

    def test_player_profile_nocontext(self):
        request = self.client.get('/players/test_user2/')
        self.assertIsNotNone(request.context['current_player'])
        self.assertEqual(len(request.context['current_teams']), 0)
        self.assertEqual(len(request.context['current_admin_teams']), 0)
        self.assertEqual(len(request.context['availability']), 0)


class AccountViewTests(TestCase):
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
        )
        self.team.players.add(Player.objects.get(username='test_user'))
        self.team.team_admin = Player.objects.get(username='test_user')
        self.team.save()
        TimeSlot.objects.get(timeSlotID=1).players_available.add(self.user1)

        self.user2 = Player.objects.create_user(
            username='test_user2',
            battlenetID='TestUser#2222',
            email='test2@test2.com',
            password='test_password2'
        )
        self.user3 = Player.objects.create_user(
            username='test_user3',
            battlenetID='TestUser#3333',
            email='test3@test3.com',
            password='test_password3'
        )
        self.admin = Player.objects.create_superuser(
            username='test_admin',
            email='admin@admin.com',
            password='admin'
        )

    def test_account_not_logged_in(self):
        request = self.client.get('/players/test_user/account/')
        self.assertTemplateUsed('scheduler.access_denied.html')

    def test_nonexistent_player_account(self):
        self.client.login(username='test_user', password='test_password')
        request = self.client.get('/players/not_a_user/account/')
        self.assertTemplateUsed('scheduler.access_denied.html')

    def test_wrong_account(self):
        self.client.login(username='test_user', password='test_password')
        request = self.client.get('/players/test_user2/account/')
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_admin_account_access(self):
        self.client.login(username='test_admin', password='admin')
        request = self.client.get('/players/test_user2/account/')
        self.assertTemplateUsed('scheduler/account.html')

    def test_correct_account(self):
        self.client.login(username='test_user', password='test_password')
        request = self.client.get('/players/test_user/account/')
        self.assertTemplateUsed('scheduler/account.html')

    def test_change_profile_info(self):
        self.client.login(username='test_user', password='test_password')
        self.client.post(reverse('scheduler:account',
                                 kwargs={'username': 'test_user'}),
                         {'set-profile': '',
                          'first_name': 'Ronald',
                          'last_name': 'McDonald',
                          'email': self.user1.email,
                          'battlenetID': self.user1.battlenetID,
                          'university': '',
                          'role': '',
                          'skillRating': ''})
        self.assertEqual(
            Player.objects.get(username='test_user').first_name, 'Ronald')

    def test_form_error_profile_info(self):
        self.client.login(username='test_user', password='test_password')
        response = self.client.post(reverse('scheduler:account',
                                            kwargs={'username': 'test_user'}),
                                    {'set-profile': '',
                                    'first_name': 'Harry',
                                    'last_name': 'Potter',
                                    'email': self.user1.email,
                                    'battlenetID': '',
                                    'university': '',
                                    'role': '',
                                    'skillRating': ''})
        self.assertFormError(response, 'form', 'battlenetID',
                             'This field is required.')

    def test_fail_to_save_profile(self):
        self.client.login(username='test_user', password='test_password')
        response = self.client.post(reverse('scheduler:account',
                                 kwargs={'username': 'test_user'}),
                         {'set-profile': '',
                          'first_name': 'Ronald',
                          'last_name': 'McDonald',
                          'email': self.user1.email,
                          'battlenetID': self.user1.battlenetID,
                          'skillRating': 'hello'})
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), "Failed to save information.")

    def test_change_availability_twice(self):
        self.client.login(username='test_user', password='test_password')
        self.assertNotIn(self.user1, TimeSlot.objects.get(timeSlotID=15).
                         players_available.all())
        self.client.post(reverse('scheduler:account',
                                  kwargs={'username': 'test_user'}),
                         {'set-availability': '',
                          'availability': (15, 16, 20, 21)
                          })
        self.assertIn(self.user1, TimeSlot.objects.get(timeSlotID=15).
                      players_available.all())
        self.client.post(reverse('scheduler:account',
                                 kwargs={'username': 'test_user'}),
                         {'set-availability': '',
                          'availability': 1
                          })
        self.assertNotIn(self.user1, TimeSlot.objects.get(timeSlotID=15).
                         players_available.all())


class MyTeamsViewTests(TestCase):
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
        )
        self.team.players.add(Player.objects.get(username='test_user'))
        self.team.team_admin = Player.objects.get(username='test_user')
        self.team.save()
        TimeSlot.objects.get(timeSlotID=1).players_available.add(self.user1)

        self.user2 = Player.objects.create_user(
            username='test_user2',
            battlenetID='TestUser#2222',
            email='test2@test2.com',
            password='test_password2'
        )
        self.user3 = Player.objects.create_user(
            username='test_user3',
            battlenetID='TestUser#3333',
            email='test3@test3.com',
            password='test_password3'
        )
        self.admin = Player.objects.create_superuser(
            username='test_admin',
            email='admin@admin.com',
            password='admin'
        )

    def test_my_teams_nologin(self):
        self.client.get('/user_team/my-teams/')
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_my_teams_wrong_account(self):
        self.client.login(username='test_user', password='test_password')
        request = self.client.get('/players/test_user2/my-teams/')
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_my_teams_admin_account_access(self):
        self.client.login(username='test_admin', password='admin')
        request = self.client.get('/players/test_user2/my-teams/')
        self.assertTemplateUsed('scheduler/my_teams.html')


class TeamsViewTests(TestCase):

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
        )
        self.team.players.add(Player.objects.get(username='test_user'))
        self.team.team_admin = Player.objects.get(username='test_user')
        self.team.save()
        TimeSlot.objects.get(timeSlotID=1).players_available.add(self.user1)

    def test_teams_template(self):
        self.client.get(reverse('scheduler:teams'))
        self.assertTemplateUsed('scheduler/teams.html')


class TeamAdminViewTests(TestCase):
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
        )
        self.team.players.add(Player.objects.get(username='test_user'))
        self.team.team_admin = Player.objects.get(username='test_user')
        self.team.save()
        TimeSlot.objects.get(timeSlotID=1).players_available.add(self.user1)

        self.user2 = Player.objects.create_user(
            username='test_user2',
            battlenetID='TestUser#2222',
            email='test2@test2.com',
            password='test_password2'
        )
        self.user3 = Player.objects.create_user(
            username='test_user3',
            battlenetID='TestUser#3333',
            email='test3@test3.com',
            password='test_password3'
        )
        self.admin = Player.objects.create_superuser(
            username='test_admin',
            email='admin@admin.com',
            password='admin'
        )

    def test_ta_notlogin(self):
        self.client.get(reverse('scheduler:team_admin', kwargs={'teamID': 1}))
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_ta_not_admin(self):
        self.client.login(username='test_user2', password='test_password2')
        self.client.get(reverse('scheduler:team_admin', kwargs={'teamID': 1}))
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_ta_superuser(self):
        self.client.login(username=self.admin.username,
                          password=self.admin.password)
        self.client.get(reverse('scheduler:team_admin', kwargs={'teamID': 1}))
        self.assertTemplateUsed('scheduler/team_admin.html')

    def test_ta_admin_login(self):
        self.client.login(username=self.user1.username,
                          password=self.user1.password)
        self.client.get(reverse('scheduler:team_admin', kwargs={'teamID': 1}))
        self.assertTemplateUsed('scheduler/team_admin.html')

    def test_ta_context(self):
        self.client.login(username='test_user',
                          password='test_password')
        response = self.client.get(
            reverse('scheduler:team_admin', kwargs={'teamID': 1}))
        self.assertEqual(len(response.context['players']),
                         len(Team.objects.get(teamID=1).players.all()))

    def test_ta_add_single_player(self):
        self.client.login(username='test_user',
                          password='test_password')
        self.client.post(reverse('scheduler:team_admin', kwargs={'teamID': 1}),
                         {'players-to-add': 'test_user2'})
        self.assertIn(Player.objects.get(username='test_user2'),
                      Team.objects.get(teamID=1).players.all())

    def test_ta_add_players(self):
        self.client.login(username='test_user',
                          password='test_password')
        self.client.post(reverse('scheduler:team_admin', kwargs={'teamID': 1}),
                         {'players-to-add': 'test_user2,test_user3'})
        self.assertIn(Player.objects.get(username='test_user2'),
                      Team.objects.get(teamID=1).players.all())
        self.assertIn(Player.objects.get(username='test_user3'),
                      Team.objects.get(teamID=1).players.all())

    def test_ta_add_same_player(self):
        self.client.login(username='test_user',
                          password='test_password')
        self.client.post(reverse('scheduler:team_admin', kwargs={'teamID': 1}),
                         {'players-to-add': 'test_user2'})
        self.assertIn(Player.objects.get(username='test_user2'),
                      Team.objects.get(teamID=1).players.all())
        response = self.client.post(reverse('scheduler:team_admin',
                                            kwargs={'teamID': 1}),
                                    {'players-to-add': 'test_user2'})
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]),
                         "TestUser#2222 is already on your team!")

    def test_ta_same_admin(self):
        self.client.login(username='test_user',
                          password='test_password')
        response = self.client.post(reverse('scheduler:team_admin', kwargs={'teamID': 1}),
                         {'new-admin': 'test_user'})
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]),
                         "You are already the admin. "
                         "What are you trying to do?")

    def test_ta_new_admin(self):
        self.client.login(username='test_user',
                          password='test_password')
        response = self.client.post(reverse('scheduler:team_admin', kwargs={'teamID': 1}),
                                    {'new-admin': 'test_user2'})
        self.assertRedirects(response, '/players/test_user/my-teams/',
                             status_code=302,
                             target_status_code=200,
                             fetch_redirect_response=False)
        self.assertTemplateUsed(template_name='scheduler/my_teams.html')

    def test_ta_new_alias(self):
        self.client.login(username='test_user',
                          password='test_password')
        response = self.client.post(
            reverse('scheduler:team_admin', kwargs={'teamID': 1}),
            {'team_alias': 'testarino'})
        self.assertEqual(Team.objects.get(teamID=1).teamAlias, 'testarino')

    def test_ta_alias_error(self):
        self.client.login(username='test_user',
                          password='test_password')
        response = self.client.post(
            reverse('scheduler:team_admin', kwargs={'teamID': 1}),
            {'team_alias': 'test!@#$%^&*()'})
        self.assertFormError(response, 'form', 'team_alias',
                             'Team name includes invalid characters')


class TeamProfileViewTests(TestCase):
    def setUp(self):
        self.team = Team.objects.create(
            teamID=1,
            teamAlias="test_team"
        )

        self.user1 = Player.objects.create_user(
            username='test_user',
            battlenetID='TestUser#1111',
            email='test@test.com',
            password='test_password',
            skillRating=100
        )
        self.team.players.add(Player.objects.get(username='test_user'))
        self.team.team_admin = Player.objects.get(username='test_user')
        self.team.save()
        TimeSlot.objects.get(timeSlotID=1).players_available.add(self.user1)

        self.user2 = Player.objects.create_user(
            username='test_user2',
            battlenetID='TestUser#2222',
            email='test2@test2.com',
            password='test_password2'
        )
        TimeSlot.objects.get(timeSlotID=2).players_available.add(self.user2)

    def test_team_profile_valid(self):
        request = self.client.get('/teams/1/')
        self.assertTemplateUsed('scheduler/team_profile.html')
        self.assertEqual(request.status_code, 200)

    def test_team_profile_fail(self):
        request = self.client.get('/teams/not_a_team/')
        self.assertEqual(request.status_code, 404)

    def test_team_prof_context(self):
        request = self.client.get(reverse('scheduler:team_profile',
                                          kwargs={'teamID': 1}))
        self.assertEqual(request.context['avg_sr'], 100)

    def test_team_prof_all_avail(self):
        self.team.players.add(Player.objects.get(username='test_user2'))
        request = self.client.get(reverse('scheduler:team_profile',
                                          kwargs={'teamID': 1}))
        self.assertEqual(len(request.context['selected_players']), 2)

    def test_team_prof_select_all(self):
        self.team.players.add(Player.objects.get(username='test_user2'))
        request = self.client.post(reverse('scheduler:team_profile',
                                          kwargs={'teamID': 1}),
                                   {'selected_user': ['TestUser#1111',
                                                      'TestUser#2222']})
        self.assertEqual(len(request.context['selected_players']), 2)

    def test_team_prof_select_none(self):
        self.team.players.add(Player.objects.get(username='test_user2'))
        request = self.client.post(reverse('scheduler:team_profile',
                                          kwargs={'teamID': 1}),
                                   {'selected_user': []})
        self.assertEqual(len(request.context['selected_players']), 0)

    def test_team_prof_select_players(self):
        self.team.players.add(Player.objects.get(username='test_user2'))
        self.assertIn(self.user2,
                      TimeSlot.objects.get(timeSlotID=2).
                      players_available.all())
        request = self.client.post(reverse('scheduler:team_profile',
                                          kwargs={'teamID': 1}),
                                   {'selected_user': 'TestUser#1111'})
        self.assertEqual(len(request.context['selected_times']), 1)
        self.assertEqual(request.context['selected_times'][0].timeSlotID, 1)


class JoinTeamViewTests(TestCase):
    def setUp(self):
        self.team = Team.objects.create(
            teamID=1,
            teamAlias="test_team"
        )

        self.user1 = Player.objects.create_user(
            username='test_user',
            battlenetID='TestUser#1111',
            email='test@test.com',
            password='test_password',
        )
        self.team.players.add(Player.objects.get(username='test_user'))
        self.team.team_admin = Player.objects.get(username='test_user')
        self.team.save()
        TimeSlot.objects.get(timeSlotID=1).players_available.add(self.user1)

        self.user2 = Player.objects.create_user(
            username='test_user2',
            battlenetID='TestUser#2222',
            email='test2@test2.com',
            password='test_password2'
        )
        self.user3 = Player.objects.create_user(
            username='test_user3',
            battlenetID='TestUser#3333',
            email='test3@test3.com',
            password='test_password3'
        )
        self.admin = Player.objects.create_superuser(
            username='test_admin',
            email='admin@admin.com',
            password='admin'
        )

    def test_join_team_authenticated(self):
        self.client.login(username='test_user2', password='test_password2')
        self.client.get('/join_team/1/test_user2/')
        self.assertIn(Player.objects.get(username='test_user2'),
                      Team.objects.get(teamID=1).players.all())

    def test_jt_superuser(self):
        self.client.login(username='test_admin', password='admin')
        self.client.get('/leave_team/1/test_user2/')
        self.assertNotIn(Player.objects.get(username='test_user2'),
                         Team.objects.get(teamID=1).players.all())
        self.client.get('/join_team/1/test_user2/')
        self.assertIn(Player.objects.get(username='test_user2'),
                      Team.objects.get(teamID=1).players.all())

    def test_join_team_not_authenticated(self):
        self.client.logout()
        response = self.client.get('/join_team/1/test_user2/', follow=True)
        self.assertTemplateUsed('accounts/login.html')

    def test_join_team_wrong_user(self):
        self.client.login(username='test_user3', password='test_password3')
        response = self.client.get('/join_team/1/test_user2/', follow=True)
        self.assertRedirects(response,
                             reverse('scheduler:my_teams',
                                     kwargs={'username': 'test_user3'}))
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]),
                         "Join team failed. "
                         "Please check your login credentials.")

    def test_jt_already_on(self):
        self.client.login(username='test_user', password='test_password')
        response = self.client.get('/join_team/1/test_user/', follow=True)
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]),
                         "You cannot join a team you are already in.")

    def test_jt_add_50(self):
        self.client.login(username='test_admin', password='admin')
        for i in range(0, 49):
            player = Player.objects.create(
                username='user'+str(i),
                password='test_pass',
                battlenetID='User'+str(i)+'#'+str(i)+'000',
                email='user'+str(i)+'@tester.com'
            )
            response = self.client.get('/join_team/1/user'+str(i)+'/')
            self.assertRedirects(response,
                                 '/players/test_admin/my-teams/',
                                 status_code=302,
                                 target_status_code=200,
                                 fetch_redirect_response=False)

        player = Player.objects.create(
            username="edgecase",
            password="edgecase",
            battlenetID="EdgyCase#1234",
            email='email@emailer.com'
        )
        response = self.client.get('/join_team/1/edgecase/', follow=True)
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]),
                         "Join team failed. Only 50 players can be on a team.")


class LeaveTeamViewTests(TestCase):
    def setUp(self):
        self.team = Team.objects.create(
            teamID=1,
            teamAlias="test_team"
        )

        self.user1 = Player.objects.create_user(
            username='test_user',
            battlenetID='TestUser#1111',
            email='test@test.com',
            password='test_password',
        )
        self.team.players.add(Player.objects.get(username='test_user'))
        self.team.team_admin = Player.objects.get(username='test_user')
        self.team.save()
        TimeSlot.objects.get(timeSlotID=1).players_available.add(self.user1)

        self.user2 = Player.objects.create_user(
            username='test_user2',
            battlenetID='TestUser#2222',
            email='test2@test2.com',
            password='test_password2'
        )
        self.user3 = Player.objects.create_user(
            username='test_user3',
            battlenetID='TestUser#3333',
            email='test3@test3.com',
            password='test_password3'
        )
        self.admin = Player.objects.create_superuser(
            username='test_admin',
            email='admin@admin.com',
            password='admin'
        )

    def test_lt_just_fine(self):
        self.client.login(username='test_user2', password='test_password2')
        Team.objects.get(teamID=1).players.add(
            Player.objects.get(username='test_user2')
        )
        response = self.client.get('/leave_team/1/test_user2/', follow=True)
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), "Left team successfully.")

    def test_leave_team_authenticated(self):
        self.client.login(username='test_user2', password='test_password2')
        request = self.client.get('/leave_team/1/test_user2/')
        self.assertNotIn(Player.objects.get(username='test_user2'),
                         Team.objects.get(teamID=1).players.all())

    def test_leave_team_not_authenticated(self):
        self.client.logout()
        request = self.client.get('/leave_team/1/test_user/')
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_leave_team_wrong_user(self):
        self.client.login(username='test_user3', password='test_password3')
        response = self.client.get('/leave_team/1/test_user2/', follow=True)
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]),
                         "Leave team failed. "
                         "Please check your login credentials.")

    def test_lt_admin_kick(self):
        self.client.login(username='test_user', password='test_password')
        Team.objects.get(teamID=1).players.add(
            Player.objects.get(username='test_user2')
        )
        response = self.client.get('/leave_team/1/test_user2/', follow=True)
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]),
                         "Removed player successfully.")

    def test_lt_admin_not_in_team(self):
        self.client.login(username='test_user', password='test_password')
        response = self.client.get('/leave_team/1/test_user2/', follow=True)
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]),
                         "Cannot remove player because "
                         "they are not in this team.")


class DeleteTeamViewTests(TestCase):
    def setUp(self):
        self.team = Team.objects.create(
            teamID=1,
            teamAlias="test_team"
        )

        self.user1 = Player.objects.create_user(
            username='test_user',
            battlenetID='TestUser#1111',
            email='test@test.com',
            password='test_password',
        )
        self.team.players.add(Player.objects.get(username='test_user'))
        self.team.team_admin = Player.objects.get(username='test_user')
        self.team.save()

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

    def test_del_nologin(self):
        response = self.client.get('/delete_team/1/', follow=True)
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_del_wrong_user(self):
        self.client.login(username='test_user2', password='test_password2')
        response = self.client.get('/delete_team/1/', follow=True)
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_del_team_admin(self):
        self.client.login(username='test_user', password='test_password')
        response = self.client.get('/delete_team/1/', follow=True)
        self.assertRedirects(response,
                             '/teams/',
                             status_code=302,
                             target_status_code=200,
                             fetch_redirect_response=False)
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), "Deleted team successfully.")

    def test_del_superuser(self):
        self.client.login(username='test_admin', password='admin')
        response = self.client.get('/delete_team/1/', follow=True)
        self.assertRedirects(response,
                             '/teams/',
                             status_code=302,
                             target_status_code=200,
                             fetch_redirect_response=False)
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]), "Deleted team successfully.")


class RegisterViewTests(TestCase):
    def setUp(self):
        self.team = Team.objects.create(
            teamID=1,
            teamAlias="test_team"
        )

        self.user1 = Player.objects.create_user(
            username='test_user',
            battlenetID='TestUser#1111',
            email='test@test.com',
            password='test_password',
        )
        self.team.players.add(Player.objects.get(username='test_user'))
        self.team.team_admin = Player.objects.get(username='test_user')
        self.team.save()
        TimeSlot.objects.get(timeSlotID=1).players_available.add(self.user1)

        self.user2 = Player.objects.create_user(
            username='test_user2',
            battlenetID='TestUser#2222',
            email='test2@test2.com',
            password='test_password2'
        )
        self.user3 = Player.objects.create_user(
            username='test_user3',
            battlenetID='TestUser#3333',
            email='test3@test3.com',
            password='test_password3'
        )
        self.admin = Player.objects.create_superuser(
            username='test_admin',
            email='admin@admin.com',
            password='admin'
        )

    def test_register_template(self):
        request = self.client.get(reverse('register'))
        self.assertTemplateUsed('scheduler/create_player.html')

    def test_register_uses_form(self):
        request = self.client.get(reverse('register'))
        self.assertIsNotNone(request.context['form'])

    def test_register_withlogin(self):
        self.client.login(username='test_user', password='test_password')
        response = self.client.get('/register/')
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_valid_register(self):
        response = self.client.post('/register/', {
            'email': 'newuser@email.com',
            'username': 'newuser',
            'battlenetID': 'newuser#1234',
            'password1': 'new_password0',
            'password2': 'new_password0'
        }, follow=True)
        new_player = Player.objects.get(username='newuser')
        self.assertIsNotNone(new_player)
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]),
                         "Your account has been created "
                         "successfully! Make sure to add "
                         "information to your profile using the "
                         "account page.")
        self.assertRedirects(response,
                             '/',
                             status_code=302,
                             target_status_code=200,
                             fetch_redirect_response=False)

    def test_fail_register_pass_is_username(self):
        response = self.client.post('/register/', {
            'email': 'newuser@email.com',
            'username': 'newuser',
            'battlenetID': 'newuser#1234',
            'password1': 'newuser',  # password same as username is invalid
            'password2': 'newuser'
        }, follow=True)
        self.assertFormError(response, 'form', 'password2',
                             'The password is too similar to the username.')
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]),
                         "There was a problem creating your account.")

    def test_fail_register_no_email(self):
        response = self.client.post('/register/', {
            'email': '',
            'username': 'newuser',
            'battlenetID': 'newuser#1234',
            'password1': 'new_password0',
            'password2': 'new_password0'
        }, follow=True)
        self.assertFormError(response, 'form', 'email',
                             'This field is required.')
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]),
                         "There was a problem creating your account.")

    def test_fail_register_no_username(self):
        response = self.client.post('/register/', {
            'email': 'newuser@email.com',
            'username': '',
            'battlenetID': 'newuser#1234',
            'password1': 'new_password0',
            'password2': 'new_password0'
        }, follow=True)
        self.assertFormError(response, 'form', 'username',
                             'This field is required.')
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]),
                         "There was a problem creating your account.")

    def test_fail_register_no_battle(self):
        response = self.client.post('/register/', {
            'email': 'newuser@email.com',
            'username': 'newuser',
            'battlenetID': '',
            'password1': 'new_password0',
            'password2': 'new_password0'
        }, follow=True)
        self.assertFormError(response, 'form', 'battlenetID',
                             'This field is required.')
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]),
                         "There was a problem creating your account.")

    def test_fail_register_pass_mismatch(self):
        response = self.client.post('/register/', {
            'email': 'newuser@email.com',
            'username': 'newuser',
            'battlenetID': 'newuser#1234',
            'password1': 'new_password0',
            'password2': 'new_pass'
        }, follow=True)
        self.assertFormError(response, 'form', 'password2',
                             'The two password fields didn\'t match.')
        messages = list(response.context['messages'])
        self.assertEqual(str(messages[0]),
                         "There was a problem creating your account.")



