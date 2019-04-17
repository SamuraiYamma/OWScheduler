"""
Controls all the forms generated into HTML by django. This includes editing
instances of models and validating data.
"""
import re

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.forms.models import ModelMultipleChoiceField
from django.forms import ValidationError

from dal import autocomplete

from scheduler.models import Player, Team, Match


class PlayerCreationForm(UserCreationForm):
    """ The form used to create a new player/user """
    username = forms.CharField(label='Enter Username',
                               min_length=4, max_length=150)
    email = forms.EmailField(label='Enter Email')
    battlenetID = forms.CharField(label='Enter BattleTag')

    def clean_username(self):
        """
        Checks the username isn't already in use

        :return: username after validating it is available
        """

        username = self.cleaned_data['username'].lower()
        r = Player.objects.filter(username=username)
        if r.count():
            raise ValidationError("Username already exists")
        return username

    def clean_email(self):
        """
        Checks the email isn't already in use

        :return: email after validating it is available
        """
        email = self.cleaned_data['email'].lower()
        r = Player.objects.filter(email=email)
        if r.count():
            raise ValidationError("Email already exists")
        return email

    def clean_battlenetID(self):
        """
        Checks the battlenetID isn't already in use and follows blizzard's
        battletag naming conventions:
        https://us.battle.net/support/en/article/26963

        :return: battlenetID after validating it is available and is a valid
        battletag
        """
        battlenetID = self.cleaned_data['battlenetID'].lower()
        pattern = re.compile("[a-zA-Z][a-zA-Z0-9]{2,11}#[0-9]{4,5}")
        if not pattern.match(battlenetID):
            raise ValidationError("BattleTag is not valid.")
        r = Player.objects.filter(battlenetID=battlenetID)
        if r.count():
            raise ValidationError("BattleTag already in use.")
        return battlenetID

    def save(self, commit=True):
        """ saves the user after assigning the entered battletag """
        user = super(PlayerCreationForm, self).save(commit=False)
        user.battlenetID = self.cleaned_data['battlenetID']
        if commit:
            user.save()
        return user

    class Meta(UserCreationForm):
        model = Player
        fields = (
            'email',
            'username',
            'battlenetID',
            'password1',
            'password2',
        )


class PlayerChangeForm(UserChangeForm):
    """ The form used to change a player's information """
    password = None

    class Meta(UserChangeForm.Meta):
        model = Player
        fields = (
            'first_name',
            'last_name',
            'email',
            'battlenetID',
            'university',
            'role',
            'skillRating',
        )


class CreateTeamForm(forms.ModelForm):
    """ Form that handles creating a team """
    teamID = forms.IntegerField(label="ID")
    teamAlias = forms.CharField(max_length=32,
                            label="Name",
                            help_text="Must be less than 32 characters.")

    def clean_teamID(self):
        """
        Checks if a team ID is already in use

        :return: id that is available for use
        """
        team_id = self.cleaned_data['teamID']
        existing = Team.objects.filter(teamID=team_id)
        if existing.count():
            raise ValidationError("A team with that ID already exists.")
        return team_id

    class Meta:
        model = Team
        fields = ('teamID', 'teamAlias')


class DetailedPlayerModelMultipleChoiceField(ModelMultipleChoiceField):
    """ A class that extends django's ModelMultipleChoiceField
    to display extra attributes in the form's field """
    def label_from_instance(self, obj):
        """
        Adds more detail to the label for each player

        :param obj: player to describe
        :return: a player's battletag and university
        """
        return "%s | %s" % (obj.battlenetID, obj.university)


class TeamAdminForm(forms.ModelForm):
    """A form for a *user* to manage their teams"""
    team_alias = forms.CharField(required=False)
    add_player = forms.ModelChoiceField(
        queryset=Player.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='player-autocomplete'),
        label="Add a Player", required=False
    )
    change_admin = forms.ModelChoiceField(
        queryset=Player.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='player-autocomplete'),
        label="Change Admin", required=False
    )

    def clean_team_alias(self):
        """
        Validates the team alias is url safe in case it needs to be used in
        any url

        :return: an internet safe team alias
        """
        team_alias = self.cleaned_data['team_alias']
        pattern = re.compile(r'^[0-9a-zA-Z\$_\.\+!\*\\\'(),-]*$')
        if not pattern.match(team_alias):
            raise ValidationError("Team name includes invalid characters")
        return team_alias

    class Meta:
        model = Team
        fields = ('team_alias', 'add_player', 'change_admin')
        widgets = {
            'add_player': autocomplete.ModelSelect2(
                url='player-autocomplete'),
            'players':
                autocomplete.ModelSelect2(url='player-autocomplete'),
            'change_admin': autocomplete.ModelSelect2(
                url='player-autocomplete'),
            'players':
                autocomplete.ModelSelect2(url='player-autocomplete')
        }


class TeamDjangoAdminForm(forms.ModelForm):
    """ A form used for *superusers* to manage teams in the admin page. """
    team_admin = forms.ModelChoiceField(
        queryset=Player.objects.all(),
        widget=autocomplete.ModelSelect2(url='player-autocomplete'),
        label="Admin", required=False
    )

    player_autocomplete = forms.ModelMultipleChoiceField(
        queryset=Player.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url='player-autocomplete'),
        label="Players", required=False
    )

    class Meta:
        model = Team
        fields = ('teamAlias', 'teamID', 'team_admin', 'player_autocomplete',
                  'is_active')
        widgets = {'team_admin': autocomplete.ModelSelect2(
                        url='player-autocomplete'),
                   'players': autocomplete.ModelSelect2Multiple(
                       url='player-autocomplete')}


class MatchCreationForm(forms.ModelForm):
    """Manages fields to create a match."""
    class Meta:
        model = Match
        fields = (
            'matchMap',
            # 'time',
            # 'team_1',
            # 'player_set_1',
            # 'team_2',
            # 'player_set_2',
            # 'winner'
        )
