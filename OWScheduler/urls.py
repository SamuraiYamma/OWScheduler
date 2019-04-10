"""OWScheduler URL Configuration

The `urlpatterns` list routes URLs to views.
Because we specify our views in the scheduler/urls.py, we only need to
specify admin here. I've also included some extra urls to help deal with
django account issues, like a lost password. This also includes a url to
use the autocomplete function in the team admin page.
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views

from scheduler.views import user_logout, register, \
    TeamAutoComplete, PlayerAutoComplete

urlpatterns = [
    path('admin/', admin.site.urls),  # admin page
    path('', include('scheduler.urls')),  # everything else
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html'), name='login'),
    path('logout/', user_logout, name='user_logout'),  # logout current user
    path('register/', register, name='register'),
    path('change-password/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/change_password.html'),
         name='change_password'),

    path('reset-password/', auth_views.PasswordResetView.as_view(
        template_name='accounts/reset_password.html'), name='password_reset'),
    path('reset-password/done/', auth_views.PasswordResetDoneView.as_view(),
         name='password_reset_done'),
    url(r'^/reset/(?P<uidb64>\w*)/(?P<token>[^/]+)/',
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm"),
    path('reset/complete/', auth_views.PasswordResetCompleteView.as_view(),
         name='password_reset_complete'),

    url(r'^team-autocomplete/$', TeamAutoComplete.as_view(),
        name='team-autocomplete'),
    url(r'^player-autocomplete/$', PlayerAutoComplete.as_view(),
        name='player-autocomplete'),
    # path('', include('django.contrib.auth.urls')),
]

handler404 = 'scheduler.views.handler404'
handler500 = 'scheduler.views.handler500'
handler403 = 'scheduler.views.handler403'
