from django.urls import path

from . import views

app_name = "calendar"
urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
]
