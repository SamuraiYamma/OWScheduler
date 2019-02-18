"""OWScheduler URL Configuration

The `urlpatterns` list routes URLs to views. Because we specify our views in the scheduler/urls.py, we only need to
specify admin here.
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include

from scheduler import urls,views

urlpatterns = [
    path('admin/', admin.site.urls),  # admin page
    path('', include('scheduler.urls')),  # everything else
]
