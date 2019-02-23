# Generated by Django 2.1.7 on 2019-02-22 16:09

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Player',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('university', models.CharField(max_length=100, null=True)),
                ('role', models.CharField(choices=[('DAMAGE', 'Damage'), ('TANK', 'Tank'), ('SUPPORT', 'Support')], max_length=7, null=True)),
                ('battlenetID', models.CharField(max_length=64, primary_key=True, serialize=False, verbose_name='BattleTag')),
                ('skillRating', models.IntegerField(null=True, verbose_name='SR')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Match',
            fields=[
                ('matchID', models.AutoField(primary_key=True, serialize=False)),
                ('matchMap', models.CharField(max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('teamID', models.IntegerField(primary_key=True, serialize=False)),
                ('teamAlias', models.CharField(max_length=32)),
                ('is_active', models.BooleanField(default=True)),
                ('team_admin', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='team_admin', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TimeSlot',
            fields=[
                ('timeSlotID', models.AutoField(primary_key=True, serialize=False)),
                ('dayOfWeek', models.CharField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')], max_length=8)),
                ('hour', models.IntegerField(default=0)),
                ('players_available', models.ManyToManyField(related_name='player_availabilities', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='match',
            name='captureTeam',
            field=models.ForeignKey(db_column='capture_id', on_delete=django.db.models.deletion.CASCADE, related_name='capture_id', to='scheduler.Team'),
        ),
        migrations.AddField(
            model_name='match',
            name='defenseTeam',
            field=models.ForeignKey(db_column='defense_id', on_delete=django.db.models.deletion.CASCADE, related_name='defense_id', to='scheduler.Team'),
        ),
        migrations.AddField(
            model_name='match',
            name='loser',
            field=models.ForeignKey(db_column='loser_id', on_delete=django.db.models.deletion.CASCADE, related_name='loser_id', to='scheduler.Team'),
        ),
        migrations.AddField(
            model_name='match',
            name='match_time',
            field=models.ForeignKey(db_column='match_time_id', null=True, on_delete=django.db.models.deletion.SET_NULL, to='scheduler.TimeSlot'),
        ),
        migrations.AddField(
            model_name='match',
            name='winner',
            field=models.ForeignKey(db_column='winner_id', on_delete=django.db.models.deletion.CASCADE, related_name='winner_id', to='scheduler.Team'),
        ),
        migrations.AddField(
            model_name='player',
            name='team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='team_id', to='scheduler.Team'),
        ),
        migrations.AddField(
            model_name='player',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
    ]
