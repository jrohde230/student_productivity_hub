from django.urls import path

from .views import TagSearchView

app_name = "tags"

urlpatterns = [
    path("search/", TagSearchView.as_view(), name="search"),
]
