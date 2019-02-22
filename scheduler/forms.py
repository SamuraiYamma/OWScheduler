from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.forms.models import ModelMultipleChoiceField

from dal import autocomplete

from .models import Player, Team


""" The form used to create a new player/user """


class PlayerCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = Player
        fields = (
            'first_name',
            'last_name',
            'email',
            'battlenetID',
            'username',
            'password1',
            'password2',
        )
        # widgets = {
        #     'first_name': forms.TextInput(attrs={'class':'form-field'}),
        #     'last_name': forms.TextInput(attrs={'class':'form-field'}),
        #     'email': forms.EmailInput(attrs={'class':'form-field'}),
        #     'battlenetID': forms.TextInput(attrs={'class':'form-field'}),
        #     'username': forms.TextInput(attrs={'class':'form-field'}),
        #     'password1': forms.PasswordInput(attrs={'class':'form-field'}),
        #     'password2': forms.PasswordInput(attrs={'class':'form-field'}),
        # }


""" The form used to change a player's information """


class PlayerChangeForm(UserChangeForm):
    team_autocomplete = forms.ModelChoiceField(
        queryset=Team.objects.all(),
        widget=autocomplete.ModelSelect2(url='team-autocomplete'),
        label="Team"
    )

    def __init__(self, *args, **kargs):
        super(PlayerChangeForm, self).__init__(*args, **kargs)

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


""" A class that extends django's ModelMultipleChoiceField to display extra attributes in field """


class DetailedPlayerModelMultipleChoiceField(ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return "%s | %s" % (obj.battlenetID, obj.university)


""" A form used to manage teams in the admin page. """


class AddToTeamForm(forms.ModelForm):

    players = DetailedPlayerModelMultipleChoiceField(
        label='Players',
        queryset=Player.objects.get_queryset(),
        widget=forms.CheckboxSelectMultiple,
        required=False,

    )

    def __init__(self, *args, **kwargs):
        super(AddToTeamForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance:
            # set players on team to already be selected
            self.fields['players'].initial = Player.objects.filter(team=instance.teamID)

    def clean_players(self):
        value = self.cleaned_data['players']
        # if len(value) > 6:
        #     raise forms.ValidationError('Only 6 players can be on a team!')
        return value

    def save(self, commit=True):
        players = self.cleaned_data.get('players', None)
        team_id = self.cleaned_data.get('id', None)

        old_team = Player.objects.filter(team=team_id)  # make sure only the players selected are on the team
        old_team.update(team=None)  # unselect all old players
        players.update(team=team_id)  # reselect new players

        return super(AddToTeamForm, self).save(commit=commit)

    class Meta:
        model = Team
        fields = ('teamAlias', 'teamID', 'players', 'is_active')
