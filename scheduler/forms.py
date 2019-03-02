import re

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.forms.models import ModelMultipleChoiceField
from django.forms import ValidationError

from dal import autocomplete

from .models import Player, Team


""" The form used to create a new player/user """


class PlayerCreationForm(UserCreationForm):
    username = forms.CharField(label='Enter Username',
                               min_length=4, max_length=150)
    email = forms.EmailField(label='Enter Email')
    battlenetID = forms.CharField(label='Enter BattleTag')

    def clean_username(self):
        username = self.cleaned_data['username'].lower()
        r = Player.objects.filter(username=username)
        if r.count():
            raise ValidationError("Username already exists")
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        r = Player.objects.filter(email=email)
        if r.count():
            raise ValidationError("Email already exists")
        return email

    def clean_battlenetID(self):
        battlenetID = self.cleaned_data['battlenetID'].lower()
        pattern = re.compile("[a-zA-Z][a-zA-Z0-9]{2,11}#[0-9]{4,5}")
        if not pattern.match(battlenetID):
            raise ValidationError("BattleTag is not valid.")
        r = Player.objects.filter(battlenetID=battlenetID)
        if r.count():
            raise ValidationError("BattleTag already in use.")
        return battlenetID

    def save(self, commit=True):
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


""" The form used to change a player's information """


class PlayerChangeForm(UserChangeForm):
    team_autocomplete = forms.ModelChoiceField(
        queryset=Team.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url='multiple-team-autocomplete'),
        label="Team", required=False
    )

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
            'team_autocomplete'
        )
        widgets = {
            'team_autocomplete': autocomplete.ModelSelect2Multiple(
                url='multiple-team-autocomplete')
        }


class CreateTeamForm(forms.ModelForm):
    id = forms.IntegerField(label="ID")
    alias = forms.CharField(max_length=32, label="Name", help_text="Must be" 
                            "less than 32 characters.")

    def clean_id(self):
        id = self.cleaned_data['id']
        existing = Team.objects.filter(teamID=id)
        if existing.count():
            raise ValidationError("A team with that ID already exists.")

    class Meta:
        model = Team
        fields = ('id', 'alias')


""" A class that extends django's ModelMultipleChoiceField 
to display extra attributes in field """


class DetailedPlayerModelMultipleChoiceField(ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return "%s | %s" % (obj.battlenetID, obj.university)


""" A form used to manage teams in the admin page. """


class TeamAdminForm(forms.ModelForm):

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

    # def save(self, commit=True):
    #     players = self.cleaned_data.get('player_autocomplete')
    #     team_id = self.cleaned_data.get('teamID')
    #     Team.objects.get(teamID=team_id).players.clear()
    #     Team.objects.get(teamID=team_id).players.add(players)
    #     return super(TeamAdminForm, self).save(commit=commit)

    # def __init__(self, *args, **kwargs):
    #     super(TeamAdminForm, self).__init__(*args, **kwargs)
    #     instance = getattr(self, 'instance', None)
    #     if instance:
    #         # set players on team to already be selected
    #         self.fields['players'].initial = \
    #             Team.objects.get(teamID=instance.teamID)
    #
    # def clean_players(self):
    #     value = self.cleaned_data['players']
    #     # if len(value) > 6:
    #     #     raise forms.ValidationError('Only 6 players can be on a team!')
    #     return value
    #
    # def save(self, commit=True):
    #     players = self.cleaned_data.get('players', None)
    #     team_id = self.cleaned_data.get('id', None)
    #
    #     # make sure only the players selected are on the team
    #     old_team = Team.objects.get(teamID=team_id).players
    #     old_team.remove(team_id)  # unselect all old players
    #     Team.objects.get(teamID=team_id).players.add(players)  # reselect new
    #     # players
    #
    #     return super(TeamAdminForm, self).save(commit=commit)

    class Meta:
        model = Team
        fields = ('teamAlias', 'teamID', 'team_admin', 'player_autocomplete',
                  'is_active')
        widgets = {'team_admin': autocomplete.ModelSelect2(
            url='player-autocomplete'), 'players':
            autocomplete.ModelSelect2Multiple(
                url='player-autocomplete')}
