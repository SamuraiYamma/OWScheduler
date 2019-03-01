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

from scheduler.views import TeamAutoComplete

urlpatterns = [
    path('admin/', admin.site.urls),  # admin page
    path('', include('scheduler.urls')),  # everything else
    path('accounts/', include('django.contrib.auth.urls')),  # all user urls
    url(r'^team-autocomplete/$', TeamAutoComplete.as_view(),
        name='team-autocomplete')
]

handler404 = 'scheduler.views.handler404'
handler500 = 'scheduler.views.handler500'
