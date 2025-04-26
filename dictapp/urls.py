from django.urls import path
from .views import search_view, api_search
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('search/', views.search_view, name='search'),
    path('api/search/', views.api_search, name='api_search'),

    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='dictapp/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register_view, name='register'),
    path('suggest/', views.suggest_entry_view, name='suggest'),
    path('upload-audio/', views.upload_audio_view, name='upload_audio'),
    path('review-suggestions/', views.review_suggestions_view, name='review_suggestions'),
    path('approve-suggestion/<int:suggestion_id>/', views.approve_suggestion_view, name='approve_suggestion'),
    path('reject-suggestion/<int:suggestion_id>/', views.reject_suggestion_view, name='reject_suggestion'),
]
