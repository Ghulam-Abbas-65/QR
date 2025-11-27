from django.urls import path
from . import auth_views

urlpatterns = [
    path('register/', auth_views.register_user, name='register'),
    path('login/', auth_views.login_user, name='login'),
    path('logout/', auth_views.logout_user, name='logout'),
    path('profile/', auth_views.user_profile, name='user_profile'),
    path('profile/update/', auth_views.update_profile, name='update_profile'),
    path('check-username/', auth_views.check_username, name='check_username'),
    path('check-email/', auth_views.check_email, name='check_email'),
]