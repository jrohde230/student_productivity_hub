from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import EmailLoginView, ProfileView, SignUpView

urlpatterns = [
    path("login/", EmailLoginView.as_view(), name="login"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
]
