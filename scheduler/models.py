"""
This module controls django's generated database. Each model determines
an entity while each field corresponds to an attribute or relationship. This
controls the information to be stored for each Player, Team, Match, and
TimeSlot.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class Team(models.Model):
    """
    The Team model identifies an ID and Alias as identifiers.
    Although teams can have the same alias, our database will need a unique ID
    for each.
    """
    teamID = models.IntegerField(primary_key=True)
    teamAlias = models.CharField(max_length=32)
    team_admin = models.ForeignKey('Player', blank=True, null=True,
                                   on_delete=models.SET_NULL,
                                   related_name='team_admin')
    players = models.ManyToManyField('Player', blank=True)
    organization = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.teamAlias) + "#" + str(self.teamID)


class Player(AbstractUser):
    """
    This is the model for Players (users) to store in the database.
    It uses django's AbstractUser which already stores first name, last name,
    email, username, and password. This allows us to use django's secure password
    hashing but still give our users attributes like university, role,
    battletag, sr, and team. The team in this model is an optional foreign key
    that can be null and/or blank. The default string for a player is their
    battletag. It also restricts the roles to either damage, tank, or support.
    """

    # by making these variables, we can access them easier
    # ROLES
    DAMAGE = "Damage"
    TANK = "Tank"
    SUPPORT = "Support"

    ROLE_CHOICES = (
        (DAMAGE, 'Damage'),
        (TANK, 'Tank'),
        (SUPPORT, 'Support'),
    )

    # UNIVERSITIES
    GVSU = 'Grand Valley State University'

    UNIVERSITY_CHOICES = (
        (GVSU, 'Grand Valley State University'),
    )

    university = models.CharField(max_length=100, choices=UNIVERSITY_CHOICES,
                                  blank=True, null=True)

    # damage, tank, or support
    role = models.CharField(max_length=7, choices=ROLE_CHOICES,
                            blank=True, null=True)

    battlenetID = models.CharField("BattleTag", max_length=64,
                                   primary_key=True)
    # USERNAME_FIELD = 'battlenetID'
    # in the future, we may want to use the battletag in place of the username
    # however, this may cause problems for urls

    skillRating = models.IntegerField("SR", null=True, blank=True)

    def __str__(self):
        """
        overriding the default string for a player to their battletag

        :return: player's battletag
        """
        return self.battlenetID


class TimeSlot(models.Model):
    """
    The model for TimeSlot allows users to set their availability.
    The ID avoids the composite key issue from django. Since they don't allow
    composite keys, this is the next best option.
    """
    MON = 0
    TUES = 1
    WED = 2
    THURS = 3
    FRI = 4
    SAT = 5
    SUN = 6

    DAYS_OF_WEEK = (
        (MON, "Monday"),
        (TUES, "Tuesday"),
        (WED, "Wednesday"),
        (THURS, "Thursday"),
        (FRI, "Friday"),
        (SAT, "Saturday"),
        (SUN, "Sunday")
    )

    # alternative solution for composite key
    timeSlotID = models.AutoField(primary_key=True)
    dayOfWeek = models.IntegerField(choices=DAYS_OF_WEEK)
    hour = models.IntegerField(default=0)
    players_available = models.ManyToManyField(Player, related_name=
                                               "player_availabilities")


class Match(models.Model):
    """ Model to store match information. """
    matchID = models.AutoField(primary_key=True)

    CG = "Château Guillard"
    DOR = "Dorado"
    EICH = "Eichenwalde"
    HANA = "Hanamura"
    HOL = "Hollywood"
    HLC = "Horizon Lunar Colony"
    ILI = "Ilios"
    KR = "King's Row"
    LT = "Lijang Tower"
    NEP = "Nepal"
    NUM = "Numbani"
    OAS = "Oasis"
    R66 = "Route 66"
    TA = "Temple of Anubis"
    VI = "Volskaya Industries"
    WG = "Watchpoint: Gibraltar"

    MAP_CHOICES = (
        (CG, "Château Guillard"),
        (DOR, "Dorado"),
        (EICH, "Eichenwalde"),
        (HANA, "Hanamura"),
        (HOL, "Hollywood"),
        (HLC, "Horizon Lunar Colony"),
        (ILI, "Ilios"),
        (KR, "King's Row"),
        (LT, "Lijang Tower"),
        (NEP, "Nepal"),
        (NUM, "Numbani"),
        (OAS, "Oasis"),
        (R66, "Route 66"),
        (TA, "Temple of Anubis"),
        (VI, "Volskaya Industries"),
        (WG, "Watchpoint: Gibraltar"),
    )

    matchMap = models.CharField(max_length=50, choices=MAP_CHOICES,
                                blank=True, null=True)

    # time match is scheduled
    time = models.DateTimeField(default=timezone.now)

    # first team
    # players is distinguished from teams
    # since teams can have more than 6 players
    player_set_1 = models.ManyToManyField('Player',
                                          related_name="player_set_1",
                                          blank=True)
    team_1 = models.ForeignKey('Team', related_name="team_1",
                               on_delete=models.SET_NULL, null=True)

    # second team
    player_set_2 = models.ManyToManyField('Player',
                                          related_name="player_set_2",
                                          blank=True)
    team_2 = models.ForeignKey('Team', related_name="team_2",
                               on_delete=models.SET_NULL, null=True)

    # winner is either team 1 or team 2
    TEAM_1 = 1
    TEAM_2 = 2

    TEAMS = (
        (TEAM_1, 'Team 1'),
        (TEAM_2, 'Team 2'),
    )
    winner = models.IntegerField(choices=TEAMS, blank=True, null=True)
