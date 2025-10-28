from django.contrib import admin
from django.urls import path, include

from server import views

urlpatterns = [
    path('', views.main_data, name='main_data'),
]