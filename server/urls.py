from django.contrib import admin
from django.urls import path, include

from server import views

urlpatterns = [
    path('', views.main_data, name='main_data'),
    path('<int:event_id>/', views.detail_view, name='detail_view'),
    path('hidden_update', views.database_update, name='database_update'),
]