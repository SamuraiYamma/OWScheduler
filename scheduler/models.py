from django.db import models

from django import forms

# Create your models here based on ER
# Each model is a "table" in the schema

# TODO: create player model
class Player(models.Model):
    email = models.CharField(max_length=320)
    name = models.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput())
    role = models.CharField(max_length=7) #damage, tank, or support
    battlenetID = models.CharField(max_length=64, primary_key=True)
    skillRating = models.IntegerField()
    team = models.ForeignKey('Team', null=True, on_delete=models.SET_NULL) #column will be named team_id

# TODO: create team model
class Team(models.Model):
    teamID = models.AutoField(primary_key=True)
    teamAlias = models.CharField(max_length=32)

# TODO: create time_slot model
class TimeSlot(models.Model):
    timeSlotID = models.AutoField(primary_key=True) #alternative solution for composite key
    dayOfWeek = models.CharField(max_length=8) #monday, tuesday, wednesday, etc.
    hour = models.IntegerField(default=0)

# TODO: create match model
class Match(models.Model):
    matchID = models.AutoField(primary_key=True)
    matchMap = models.CharField(max_length=32)
    captureTeam = models.ForeignKey('Team', on_delete=models.CASCADE, db_column='capture_id', related_name='capture_id') #named capture_id
    defenseTeam = models.ForeignKey('Team', on_delete=models.CASCADE, db_column='defense_id', related_name='defense_id') #named defense_id
    winner = models.ForeignKey('Team', on_delete=models.CASCADE, db_column='winner_id', related_name='winner_id') # named winner_id
    loser = models.ForeignKey('Team', on_delete=models.CASCADE, db_column='loser_id', related_name='loser_id') # named loser_id
