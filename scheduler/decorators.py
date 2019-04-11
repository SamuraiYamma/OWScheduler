from django.core.exceptions import PermissionDenied

from scheduler.models import Player, Team

"""
:returns True if user is the admin of the 
team from function param or a superuser
"""


def is_team_admin_or_superuser(function):
    def wrap(request, *args, **kwargs):
        player = Player.objects.get(username=request.user.username)
        team = Team.objects.get(pk=kwargs['teamID'])
        if team.team_admin == player or request.user.is_superuser:
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


"""
:returns True if the user is the same specified in function 
params or a superuser
"""


def is_user_or_superuser(function):
    def wrap(request, *args, **kwargs):
        if request.user.username == kwargs['username'] or \
                request.user.is_superuser:
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap