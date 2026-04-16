from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_redirect, name='dashboard_redirect'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    path('change-password/', views.change_password, name='change_password'),
]
