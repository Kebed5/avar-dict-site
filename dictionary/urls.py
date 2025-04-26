from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search_entries, name='search_entries'),
]
