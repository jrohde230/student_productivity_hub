from django.urls import path

from . import views

app_name = "resources"
urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("reorder/", views.ReorderResourcesView.as_view(), name="reorder"),
]
