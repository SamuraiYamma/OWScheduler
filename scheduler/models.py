from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here based on ER
# Each model is a "table" in the schema

"""
The Team model identifies an ID and Alias as identifiers. 
Although teams can have the same alias, our database will need a unique ID 
for each.
"""


class Team(models.Model):
    teamID = models.IntegerField(primary_key=True)
    teamAlias = models.CharField(max_length=32)
    team_admin = models.ForeignKey('Player', blank=True, null=True,
                                   on_delete=models.SET_NULL,
                                   related_name='team_admin')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.teamAlias) + "#" + str(self.teamID)


"""
This is the model for Players (users) to store in the database.
It uses django's AbstractUser which already stores first name, last name, 
email, username, and password. This allows us to use django's secure password 
hashing but still give our users attributes like university, role, 
battletag, sr, and team. The team in this model is an optional foreign key 
that can be null and/or blank. The default string for a player is their 
battletag. It also restricts the roles to either damage, tank, or support.
"""


class Player(AbstractUser):
    # by making these variables, we can access them easier
    DAMAGE = "DAMAGE"
    TANK = "TANK"
    SUPPORT = "SUPPORT"

    ROLE_CHOICES = (
        (DAMAGE, 'Damage'),
        (TANK, 'Tank'),
        (SUPPORT, 'Support'),
    )

    university = models.CharField(max_length=100, blank=True, null=True)

    # damage, tank, or support
    role = models.CharField(max_length=7, choices=ROLE_CHOICES,
                            blank=True, null=True)

    battlenetID = models.CharField("BattleTag", max_length=64,
                                   primary_key=True)
    # USERNAME_FIELD = 'battlenetID'
    # in the future, we may want to use the battletag in place of the username
    # however, this may cause problems for urls

    skillRating = models.IntegerField("SR", null=True, blank=True)
    team = models.ForeignKey('Team', blank=True, null=True,
                             on_delete=models.SET_NULL,
                             related_name='team_id')

    # overriding the default string for a player to their battletag
    def __str__(self):
        return self.battlenetID


"""
The model for TimeSlot allows users to set their availability. 
The ID avoids the composite key issue from django. Since they don't allow 
composite keys, this is the next best option.
"""


class TimeSlot(models.Model):
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
    players_available = models.ManyToManyField(Player,
                                               related_name=
                                               "player_availabilities")


""" Model to store match information. """


class Match(models.Model):
    matchID = models.AutoField(primary_key=True)
    matchMap = models.CharField(max_length=32)
    match_time = models.ForeignKey('TimeSlot', null=True,
                                   on_delete=models.SET_NULL,
                                   db_column='match_time_id')
    captureTeam = models.ForeignKey('Team', on_delete=models.CASCADE,
                                    db_column='capture_id',
                                    related_name='capture_id')
    defenseTeam = models.ForeignKey('Team', on_delete=models.CASCADE,
                                    db_column='defense_id',
                                    related_name='defense_id')
    winner = models.ForeignKey('Team', on_delete=models.CASCADE,
                               db_column='winner_id',
                               related_name='winner_id')
    loser = models.ForeignKey('Team', on_delete=models.CASCADE,
                              db_column='loser_id',
                              related_name='loser_id')
