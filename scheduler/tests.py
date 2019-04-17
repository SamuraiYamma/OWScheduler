"""Contains all the tests for scheduler. This includes the models and views."""
from django.test import TestCase, RequestFactory
from django.db import IntegrityError
from django.shortcuts import reverse

from scheduler.models import Player, Team, Match, TimeSlot


class PlayerModelTests(TestCase):
    """ tests for accessing objects of the Player model and their team """

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
        """
        Raise an error when looking up a nonexistent user
        :return: Player.DoesNotExist error
        """
        with self.assertRaises(Player.DoesNotExist):
            Player.objects.get(battlenetID="NoUserHere")

    def test_username_not_found(self):
        """
        Raise a DoesNotExist error when looking up a nonexistent username
        :return: Player.DoesNotExist error
        """
        with self.assertRaises(Player.DoesNotExist):
            Player.objects.get(username="NoUserHere")

    def test_str(self):
        """
        Str method should return a player's battletag
        """
        new_user0 = Player.objects.get(battlenetID="NewUser#0000")
        new_user1 = Player.objects.get(battlenetID="NewUser#1111")
        self.assertEqual(str(new_user0), "NewUser#0000")
        self.assertEqual(new_user1.__str__(), "NewUser#1111")

    def test_find_by_username(self):
        """
        Searching a player by their username
        """
        new_user0 = Player.objects.get(username="NewUser0")
        new_user1 = Player.objects.get(username="NewUser1")
        self.assertEqual(str(new_user0), "NewUser#0000")
        self.assertEqual(str(new_user1), "NewUser#1111")

    def test_duplicate_error(self):
        """
        Raise an error when creating a player with information that is already
        in the database
        """
        with self.assertRaises(IntegrityError):
            Player.objects.create(
                battlenetID="NewUser#0000", username="NewUser0")

    def test_player_university(self):
        """
        Look up a player(s) by their university
        """
        self.assertIsNotNone(Player.objects.filter(university=Player.GVSU))
        self.assertIsNotNone(self.user1.university)
        self.assertIsNone(self.user2.university)

    def test_player_role(self):
        """ Players roles correspond to choices for roles in models"""
        self.assertEqual(self.user1.role, 'Damage')
        self.assertEqual(self.user2.role, 'Tank')
        self.user1.role = Player.SUPPORT
        self.assertEqual(self.user1.role, 'Support')

    def test_player_skill_rating(self):
        """ Test that players can be looked up by their skillRating """
        self.assertIsNotNone(Player.objects.filter(skillRating__gt=0))
        self.assertIsNotNone(Player.objects.filter(skillRating=100))
        self.assertEqual(self.user1.skillRating, 42)


class TeamModelTests(TestCase):
    """
    tests for accessing the Team model objects and
    their information via alias and id
    """
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
        """
        Str for team should be a combination of team name joined with a
        '#' symbol and their id
        """
        team1 = Team.objects.get(teamID=1)
        team2 = Team.objects.get(teamID=2)
        self.assertEqual(str(team1), "#1")
        self.assertEqual(str(team2), "Team2#2")

    def test_same_alias(self):
        """ Two teams can have the same name/alias """
        team1234 = Team.objects.get(teamID=1234)
        team12345 = Team.objects.get(teamID=12345)
        self.assertEqual(team1234.teamAlias, team12345.teamAlias)
        self.assertNotEqual(str(team1234), str(team12345))

    def test_same_id(self):
        """ Two teams cannot have the same id """
        with self.assertRaises(IntegrityError):
            Team.objects.create(teamID=1)

    def test_set_alias(self):
        """ Team alias can be changed """
        team1 = Team.objects.get(teamID=1)
        team1.teamAlias = "Team1"
        self.assertEqual(str(team1), "Team1#1")

    def test_set_multiple_alias(self):
        """ One team alias can be set to several teams at once """
        team_set = Team.objects.filter(teamID__lt=3)
        team_set.update(teamAlias="TeamBlue")
        for team in team_set:
            self.assertEqual(team.teamAlias, "TeamBlue")

    def test_team_admin(self):
        """ Team admins exist when set correctly """
        self.assertIsNotNone(Team.objects.get(teamID=1).team_admin)
        self.assertIsNotNone(Team.objects.get(teamID=2).team_admin)
        self.assertIsNone(Team.objects.get(teamID=1234).team_admin)
        self.assertIsNone(Team.objects.get(teamID=12345).team_admin)

    def test_org(self):
        """ Retrieve a team's organization """
        self.assertIsNotNone(Team.objects.get(teamID=1234).organization)
        self.assertIsNone(Team.objects.get(teamID=1).organization)

    def test_set_org(self):
        """ A team can set an organization """
        team = Team.objects.get(teamID=1)
        team.organization = "GV"
        team.save()
        self.assertEqual(team.organization, "GV")

    def test_team_active(self):
        """ Users should only see active teams """
        self.assertTrue(Team.objects.get(teamID=1).is_active)
        team = Team.objects.get(teamID=2)
        team.is_active = False
        team.save()
        self.assertFalse(Team.objects.get(teamID=2).is_active)


class UserLoginTests(TestCase):
    """ tests for all the views along with their errors and weaknesses """

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
        """ login_context should not exist for unauthenticated user """
        request = self.client.get(reverse('scheduler:home'))
        self.assertIsNone(request.context['user'])
        self.assertIsNone(request.context['user_teams'])
        self.assertIsNotNone(request.context['login_form'])

    def test_failed_user_login_context(self):
        """ User failed to login and therefore some context does not exist """
        request = self.client.post(reverse('scheduler:home'),
                                   {'username': 'test_user',
                                    'password': 'bad_password'})
        self.assertIsNone(request.context['user'])
        self.assertIsNone(request.context['user_teams'])
        self.assertIsNotNone(request.context['login_form'])

    def test_user_login_context_post(self):
        """ templates have context referencing an authenticated user """
        request = self.client.post(reverse('scheduler:home'),
                                   {'username': 'test_user',
                                    'password': 'test_password'})
        self.assertIsNotNone(request.context['user'])
        self.assertIsNotNone(request.context['user_teams'])
        self.assertIsNotNone(request.context['login_form'])

    def test_authenticated_login_context(self):
        """ User authenticated by django should have teams """
        self.client.login(username='test_user', password='test_password')
        request = self.client.get(reverse('scheduler:home'))
        self.assertIsNotNone(request.context['user_teams'])


class HomeViewTests(TestCase):
    """all the tests for the home method in views"""
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
        """ Make sure home uses the right html file """
        self.assertTemplateUsed(template_name='scheduler/default.html')

    def test_home_login(self):
        """ test logging in from home page """
        request = self.client.post(reverse('scheduler:home'),
                                   {'username': 'test_user',
                                    'password': 'test_password'})
        request.user = self.user1
        self.assertTrue(request.user.is_authenticated)

    def test_home_logout(self):
        """ logging out from home page and correct redirects """
        self.client.login(username='test_user', password='test_password')
        response = self.client.get(reverse('user_logout'))
        self.assertRedirects(response, '/', status_code=302,
                             target_status_code=200,
                             fetch_redirect_response=False)
        self.assertTemplateUsed(template_name='scheduler/default.html')

    #  other logout tests
    def test_logout_from_teams(self):
        """ logout from another page to make sure it redirects properly """
        self.client.login(username='test_user', password='test_password')
        response = self.client.get(reverse('user_logout'),
                                   {'next': '/teams/'})
        self.assertRedirects(response, '/teams/', status_code=302,
                             target_status_code=200,
                             fetch_redirect_response=False)
        self.assertTemplateUsed(template_name='scheduler/teams.html')


class PlayersViewTests(TestCase):
    """contains tests for players method in views"""
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
        """ make sure players uses the correct template"""
        self.assertTemplateUsed('scheduler/players.html')

    def test_players_list_size(self):
        """
        the context to get list of players should be the same size as the
        list of all players
        """
        request = self.client.get(reverse('scheduler:players'))
        self.assertEqual(len(Player.objects.filter(is_active=True)),
                         len(request.context['player_list']))

    def test_login_from_players(self):
        """ logging in from players """
        self.client.logout()
        request = self.factory.post(reverse('scheduler:players'),
                                    {'username': 'test_user',
                                     'password': 'test_password'})
        request.user = self.user1
        self.assertTrue(request.user.is_authenticated)

    def test_logout_from_players(self):
        """ logging out from players and redirect back to the page """
        self.client.login(username='test_user', password='test_password')
        response = self.client.get(reverse('user_logout'),
                                   {'next': '/players/'})
        self.assertRedirects(response, '/players/', status_code=302,
                             target_status_code=200,
                             fetch_redirect_response=False)
        self.assertTemplateUsed(template_name='scheduler/players.html')


class PlayerProfileViewTests(TestCase):
    """ All tests related to viewing a user's profile """
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
        """ successful visit of a profile page """
        request = self.client.get('/players/test_user/')
        self.assertEqual(request.status_code, 200)

    def test_nonexistent_player(self):
        """ visit a profile that does not exist should return a 404 """
        request = self.client.get('/players/not_a_user/')
        self.assertEqual(request.status_code, 404)

    def test_profile_context(self):
        """ validate the correct context for a player's profile """
        request = self.client.get('/players/test_user/')
        self.assertIsNotNone(request.context['current_player'])
        self.assertIsNotNone(request.context['current_teams'])
        self.assertIsNotNone(request.context['current_admin_teams'])
        self.assertIsNotNone(request.context['availability'])

    def test_player_profile_nocontext(self):
        """ validate another player's context """
        request = self.client.get('/players/test_user2/')
        self.assertIsNotNone(request.context['current_player'])
        self.assertEqual(len(request.context['current_teams']), 0)
        self.assertEqual(len(request.context['current_admin_teams']), 0)
        self.assertEqual(len(request.context['availability']), 0)


class AccountViewTests(TestCase):
    """ All tests dealing with editing a player's account """
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
        """ Attempt to get account page without being authenticated """
        self.client.get('/players/test_user/account/')
        self.assertTemplateUsed('scheduler.access_denied.html')

    def test_nonexistent_player_account(self):
        """ attempt to view an account page that doesn't exist """
        self.client.login(username='test_user', password='test_password')
        self.client.get('/players/not_a_user/account/')
        self.assertTemplateUsed('scheduler.access_denied.html')

    def test_wrong_account(self):
        """ attempt to view an account page for a different player """
        self.client.login(username='test_user', password='test_password')
        self.client.get('/players/test_user2/account/')
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_admin_account_access(self):
        """ attempt to view an account page as a superuser """
        self.client.login(username='test_admin', password='admin')
        self.client.get('/players/test_user2/account/')
        self.assertTemplateUsed('scheduler/account.html')

    def test_correct_account(self):
        """ successful view of a players own account page """
        self.client.login(username='test_user', password='test_password')
        self.client.get('/players/test_user/account/')
        self.assertTemplateUsed('scheduler/account.html')

    def test_change_profile_info(self):
        """ change first and last name without errors """
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
        """ no battlenetID should return a form error """
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
        """ attempt to put a string into an integer field: skillRating """
        self.client.login(username='test_user', password='test_password')
        response = self.client.post(reverse('scheduler:account',
                                            kwargs={'username': 'test_user'}),
                                    {
                                        'set-profile': '',
                                        'first_name': 'Ronald',
                                        'last_name': 'McDonald',
                                        'email': self.user1.email,
                                        'battlenetID': self.user1.battlenetID,
                                        'skillRating': 'hello'
                                    })
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]), "Failed to save information.")

    def test_change_availability_twice(self):
        """ changing availability multiple times to ensure state is saved """
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
    """ All tests related to viewing a player's my team page """
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
        """ Cannot view my teams without being logged in """
        self.client.get('/user_team/my-teams/')
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_my_teams_wrong_account(self):
        """ Cannot view my teams of another user """
        self.client.login(username='test_user', password='test_password')
        self.client.get('/players/test_user2/my-teams/')
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_my_teams_admin_account_access(self):
        """ View my teams as a superuser"""
        self.client.login(username='test_admin', password='admin')
        self.client.get('/players/test_user2/my-teams/')
        self.assertTemplateUsed('scheduler/my_teams.html')


class TeamsViewTests(TestCase):
    """ All tests related to viewing all teams """
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
        """ verify teams uses correct template """
        self.client.get(reverse('scheduler:teams'))
        self.assertTemplateUsed('scheduler/teams.html')


class TeamAdminViewTests(TestCase):
    """ All tests related to managing a team via the team admin view """
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
        """ viewing an admin page without being logged in should fail """
        self.client.get(reverse('scheduler:team_admin', kwargs={'teamID': 1}))
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_ta_not_admin(self):
        """ viewing an admin page as a team member, not admin """
        self.client.login(username='test_user2', password='test_password2')
        self.client.get(reverse('scheduler:team_admin', kwargs={'teamID': 1}))
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_ta_superuser(self):
        """ superusers should have access to team admin page """
        self.client.login(username=self.admin.username,
                          password=self.admin.password)
        self.client.get(reverse('scheduler:team_admin', kwargs={'teamID': 1}))
        self.assertTemplateUsed('scheduler/team_admin.html')

    def test_ta_admin_login(self):
        """
        successful login by team admin should provide team admin template
        """
        self.client.login(username=self.user1.username,
                          password=self.user1.password)
        self.client.get(reverse('scheduler:team_admin', kwargs={'teamID': 1}))
        self.assertTemplateUsed('scheduler/team_admin.html')

    def test_ta_context(self):
        """ validate context received by team admin page """
        self.client.login(username='test_user',
                          password='test_password')
        response = self.client.get(
            reverse('scheduler:team_admin', kwargs={'teamID': 1}))
        self.assertEqual(len(response.context['players']),
                         len(Team.objects.get(teamID=1).players.all()))

    def test_ta_add_single_player(self):
        """ add a single player to the team correctly """
        self.client.login(username='test_user',
                          password='test_password')
        self.client.post(reverse('scheduler:team_admin', kwargs={'teamID': 1}),
                         {'players-to-add': 'test_user2'})
        self.assertIn(Player.objects.get(username='test_user2'),
                      Team.objects.get(teamID=1).players.all())

    def test_ta_add_players(self):
        """ add multiple players to the team correctly"""
        self.client.login(username='test_user',
                          password='test_password')
        self.client.post(reverse('scheduler:team_admin', kwargs={'teamID': 1}),
                         {'players-to-add': 'test_user2,test_user3'})
        self.assertIn(Player.objects.get(username='test_user2'),
                      Team.objects.get(teamID=1).players.all())
        self.assertIn(Player.objects.get(username='test_user3'),
                      Team.objects.get(teamID=1).players.all())

    def test_ta_add_same_player(self):
        """ adding a player multiple times should provide an error message """
        self.client.login(username='test_user',
                          password='test_password')
        self.client.post(reverse('scheduler:team_admin', kwargs={'teamID': 1}),
                         {'players-to-add': 'test_user2'})
        self.assertIn(Player.objects.get(username='test_user2'),
                      Team.objects.get(teamID=1).players.all())
        response = self.client.post(reverse('scheduler:team_admin',
                                            kwargs={'teamID': 1}),
                                    {'players-to-add': 'test_user2'})
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]),
                         "TestUser#2222 is already on your team!")

    def test_ta_same_admin(self):
        """
        attempting to change admin to the current team admin should
        provide an error message
        """
        self.client.login(username='test_user',
                          password='test_password')
        response = self.client.post(reverse('scheduler:team_admin',
                                            kwargs={'teamID': 1}),
                                    {'new-admin': 'test_user'})
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]),
                         "You are already the admin. "
                         "What are you trying to do?")

    def test_ta_new_admin(self):
        """ changing an admin successfully should redirect the user to my teams
        """
        self.client.login(username='test_user',
                          password='test_password')
        response = self.client.post(reverse('scheduler:team_admin',
                                            kwargs={'teamID': 1}),
                                    {'new-admin': 'test_user2'})
        self.assertRedirects(response, '/players/test_user/my-teams/',
                             status_code=302,
                             target_status_code=200,
                             fetch_redirect_response=False)
        self.assertTemplateUsed(template_name='scheduler/my_teams.html')

    def test_ta_new_alias(self):
        """ changing team alias correctly """
        self.client.login(username='test_user',
                          password='test_password')
        self.client.post(reverse('scheduler:team_admin', kwargs={'teamID': 1}),
                         {'team_alias': 'testarino'})
        self.assertEqual(Team.objects.get(teamID=1).teamAlias, 'testarino')

    def test_ta_alias_error(self):
        """
        form error should be raised from changing team name to an invalid
        name
        """
        self.client.login(username='test_user',
                          password='test_password')
        response = self.client.post(
            reverse('scheduler:team_admin', kwargs={'teamID': 1}),
            {'team_alias': 'test!@#$%^&*()'})
        self.assertFormError(response, 'form', 'team_alias',
                             'Team name includes invalid characters')


class TeamProfileViewTests(TestCase):
    """ All tests related to viewing a team's profile"""
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
        """ validating the template used to view a team """
        request = self.client.get('/teams/1/')
        self.assertTemplateUsed('scheduler/team_profile.html')
        self.assertEqual(request.status_code, 200)

    def test_team_profile_fail(self):
        """ attempt to view a team profile for a nonexistent team """
        request = self.client.get('/teams/not_a_team/')
        self.assertEqual(request.status_code, 404)

    def test_team_prof_context(self):
        """ validate avg_sr context by view """
        request = self.client.get(reverse('scheduler:team_profile',
                                          kwargs={'teamID': 1}))
        self.assertEqual(request.context['avg_sr'], 100)

    def test_team_prof_all_avail(self):
        """ validate all users are selected on page visit """
        self.team.players.add(Player.objects.get(username='test_user2'))
        request = self.client.get(reverse('scheduler:team_profile',
                                          kwargs={'teamID': 1}))
        self.assertEqual(len(request.context['selected_players']), 2)

    def test_team_prof_select_all(self):
        """ get availability for all when selecting all users """
        self.team.players.add(Player.objects.get(username='test_user2'))
        request = self.client.post(reverse('scheduler:team_profile',
                                           kwargs={'teamID': 1}),
                                   {'selected_user': ['TestUser#1111',
                                                      'TestUser#2222']})
        self.assertEqual(len(request.context['selected_players']), 2)

    def test_team_prof_select_none(self):
        """ get no availability when no players are selected """
        self.team.players.add(Player.objects.get(username='test_user2'))
        request = self.client.post(reverse('scheduler:team_profile',
                                           kwargs={'teamID': 1}),
                                   {'selected_user': []})
        self.assertEqual(len(request.context['selected_players']), 0)

    def test_team_prof_select_players(self):
        """ get availability for only the player that's selected """
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
    """ All tests related to joining a team via url """
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
        """ joining a team correctly """
        self.client.login(username='test_user2', password='test_password2')
        self.client.get('/join_team/1/test_user2/')
        self.assertIn(Player.objects.get(username='test_user2'),
                      Team.objects.get(teamID=1).players.all())

    def test_jt_superuser(self):
        """ superuser should be able to add anyone to a team """
        self.client.login(username='test_admin', password='admin')
        self.client.get('/leave_team/1/test_user2/')
        self.assertNotIn(Player.objects.get(username='test_user2'),
                         Team.objects.get(teamID=1).players.all())
        self.client.get('/join_team/1/test_user2/')
        self.assertIn(Player.objects.get(username='test_user2'),
                      Team.objects.get(teamID=1).players.all())

    def test_join_team_not_authenticated(self):
        """ cannot join a team without being logged in """
        self.client.logout()
        self.client.get('/join_team/1/test_user2/', follow=True)
        self.assertTemplateUsed('accounts/login.html')

    def test_join_team_wrong_user(self):
        """
        attempt to join a team while being logged into a different account.
        should return an error message
        """
        self.client.login(username='test_user3', password='test_password3')
        response = self.client.get('/join_team/1/test_user2/', follow=True)
        self.assertRedirects(response,
                             reverse('scheduler:my_teams',
                                     kwargs={'username': 'test_user3'}))
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]),
                         "Join team failed. "
                         "Please check your login credentials.")

    def test_jt_already_on(self):
        """
        attempt to join a team a player is already on should return
        an error message
        """
        self.client.login(username='test_user', password='test_password')
        response = self.client.get('/join_team/1/test_user/', follow=True)
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]),
                         "You cannot join a team you are already in.")

    def test_jt_add_50(self):
        """ attempt to join a team that has the max (50) players on it """
        self.client.login(username='test_admin', password='admin')
        for i in range(0, 49):
            Player.objects.create(
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
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]),
                         "Join team failed. Only 50 players can be on a team.")


class LeaveTeamViewTests(TestCase):
    """ all tests related to leaving a team via url"""
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
        """ successfully leaving a team """
        self.client.login(username='test_user2', password='test_password2')
        Team.objects.get(teamID=1).players.add(
            Player.objects.get(username='test_user2')
        )
        response = self.client.get('/leave_team/1/test_user2/', follow=True)
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]), "Left team successfully.")

    def test_leave_team_authenticated(self):
        """ leave a team while being logged in correctly """
        self.client.login(username='test_user2', password='test_password2')
        self.client.get('/leave_team/1/test_user2/')
        self.assertNotIn(Player.objects.get(username='test_user2'),
                         Team.objects.get(teamID=1).players.all())

    def test_leave_team_not_authenticated(self):
        """ leave a team without being logged in """
        self.client.logout()
        self.client.get('/leave_team/1/test_user/')
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_leave_team_wrong_user(self):
        """ leave a team as a different user should return error message """
        self.client.login(username='test_user3', password='test_password3')
        response = self.client.get('/leave_team/1/test_user2/', follow=True)
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]),
                         "Leave team failed. "
                         "Please check your login credentials.")

    def test_lt_admin_kick(self):
        """ team admin is able to remove players from their team """
        self.client.login(username='test_user', password='test_password')
        Team.objects.get(teamID=1).players.add(
            Player.objects.get(username='test_user2')
        )
        response = self.client.get('/leave_team/1/test_user2/', follow=True)
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]),
                         "Removed player successfully.")

    def test_lt_admin_not_in_team(self):
        """ attempt to remove a player from a team they are not in """
        self.client.login(username='test_user', password='test_password')
        response = self.client.get('/leave_team/1/test_user2/', follow=True)
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]),
                         "Cannot remove player because "
                         "they are not in this team.")


class DeleteTeamViewTests(TestCase):
    """ all tests for deleting a team """
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
        """ attempt to delete a team without being logged in """
        self.client.get('/delete_team/1/', follow=True)
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_del_wrong_user(self):
        """ attempt to delete a team without being team admin """
        self.client.login(username='test_user2', password='test_password2')
        self.client.get('/delete_team/1/', follow=True)
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_del_team_admin(self):
        """ delete team as a team admin """
        self.client.login(username='test_user', password='test_password')
        response = self.client.get('/delete_team/1/', follow=True)
        self.assertRedirects(response,
                             '/teams/',
                             status_code=302,
                             target_status_code=200,
                             fetch_redirect_response=False)
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]), "Deleted team successfully.")

    def test_del_superuser(self):
        """ delete team as a superuser """
        self.client.login(username='test_admin', password='admin')
        response = self.client.get('/delete_team/1/', follow=True)
        self.assertRedirects(response,
                             '/teams/',
                             status_code=302,
                             target_status_code=200,
                             fetch_redirect_response=False)
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]), "Deleted team successfully.")


class RegisterViewTests(TestCase):
    """ all tests related to creating a user/player """
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
        """ validate register uses correct template """
        self.client.get(reverse('register'))
        self.assertTemplateUsed('scheduler/create_player.html')

    def test_register_uses_form(self):
        """ register must use a form """
        request = self.client.get(reverse('register'))
        self.assertIsNotNone(request.context['form'])

    def test_register_withlogin(self):
        """ attempt to register while being logged in should fail """
        self.client.login(username='test_user', password='test_password')
        self.client.get('/register/')
        self.assertTemplateUsed('scheduler/access_denied.html')

    def test_valid_register(self):
        """ successful registration should return success message """
        response = self.client.post('/register/', {
            'email': 'newuser@email.com',
            'username': 'newuser',
            'battlenetID': 'newuser#1234',
            'password1': 'new_password0',
            'password2': 'new_password0'
        }, follow=True)
        new_player = Player.objects.get(username='newuser')
        self.assertIsNotNone(new_player)
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]),
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
        """ attempt to register with password same as username returns error
        """
        response = self.client.post('/register/', {
            'email': 'newuser@email.com',
            'username': 'newuser',
            'battlenetID': 'newuser#1234',
            'password1': 'newuser',  # password same as username is invalid
            'password2': 'newuser'
        }, follow=True)
        self.assertFormError(response, 'form', 'password2',
                             'The password is too similar to the username.')
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]),
                         "There was a problem creating your account.")

    def test_fail_register_no_email(self):
        """ attempt to register without email should fail """
        response = self.client.post('/register/', {
            'email': '',
            'username': 'newuser',
            'battlenetID': 'newuser#1234',
            'password1': 'new_password0',
            'password2': 'new_password0'
        }, follow=True)
        self.assertFormError(response, 'form', 'email',
                             'This field is required.')
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]),
                         "There was a problem creating your account.")

    def test_fail_register_no_username(self):
        """ attempt to register without username should fail """
        response = self.client.post('/register/', {
            'email': 'newuser@email.com',
            'username': '',
            'battlenetID': 'newuser#1234',
            'password1': 'new_password0',
            'password2': 'new_password0'
        }, follow=True)
        self.assertFormError(response, 'form', 'username',
                             'This field is required.')
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]),
                         "There was a problem creating your account.")

    def test_fail_register_no_battle(self):
        """ attempt to register without battlenetID should fail """
        response = self.client.post('/register/', {
            'email': 'newuser@email.com',
            'username': 'newuser',
            'battlenetID': '',
            'password1': 'new_password0',
            'password2': 'new_password0'
        }, follow=True)
        self.assertFormError(response, 'form', 'battlenetID',
                             'This field is required.')
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]),
                         "There was a problem creating your account.")

    def test_fail_register_pass_mismatch(self):
        """ attempt to register with different passwords should fail """
        response = self.client.post('/register/', {
            'email': 'newuser@email.com',
            'username': 'newuser',
            'battlenetID': 'newuser#1234',
            'password1': 'new_password0',
            'password2': 'new_pass'
        }, follow=True)
        self.assertFormError(response, 'form', 'password2',
                             'The two password fields didn\'t match.')
        curr_messages = list(response.context['messages'])
        self.assertEqual(str(curr_messages[0]),
                         "There was a problem creating your account.")
