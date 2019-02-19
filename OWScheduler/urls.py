"""OWScheduler URL Configuration

The `urlpatterns` list routes URLs to views. Because we specify our views in the scheduler/urls.py, we only need to
specify admin here.
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views

from scheduler.views import TeamAutoComplete

urlpatterns = [
    path('admin/', admin.site.urls),  # admin page
    path('', include('scheduler.urls')),  # everything else
    path('accounts/', include('django.contrib.auth.urls')),  # all user urls
    # path('accounts/reset-password', auth_views.PasswordChangeView.as_view(), name='reset-password'),  # change password
    # path('accounts/reset-password-done', auth_views.PasswordChangeDoneView.as_view, name='reset-password-done'),
    url(r'^team-autocomplete/$', TeamAutoComplete.as_view(), name='team-autocomplete')
]
