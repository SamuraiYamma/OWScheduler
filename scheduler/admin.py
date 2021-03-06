"""
This module controls the admin page for django. This is mainly for the
superuser to alter data in the database.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from scheduler.forms import TeamDjangoAdminForm
from scheduler.models import Player, Team


class PlayerAdmin(UserAdmin):
    """
    Controls the fields for creating a user in the admin page.
    This is also why the admin has the ability to set permissions
    """
    model = Player

    # fields for creating a player
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('User', {'fields': (
            'first_name',
            'last_name',
            'email',
            'battlenetID',
            'university',
            'role',
            'skillRating',
        )}),
        ('Permissions', {'fields': ('is_active', 'is_staff')}),
    )

    # fields to show when displaying all users
    list_display = [
        'battlenetID',
        'username',
        'first_name',
        'last_name',
        'university',
    ]


class TeamAdmin(admin.ModelAdmin):
    """
    Sets up the fields for creating a team.
    Uses django's default form aside from a form to add players to the
    specified team.
    """
    # displays form to add players to a team
    def get_form(self, request, obj=None, change=False, **kwargs):
        if request.user.is_superuser:
            return TeamDjangoAdminForm
        return None


# this was in many other code examples I reviewed, but it doesn't seem to work.
# admin.site.unregister(User)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Team, TeamAdmin)
