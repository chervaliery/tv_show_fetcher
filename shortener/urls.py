from django.urls import path

from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("list/", views.list_view, name="list"),
    path("list/<path:path>", views.list_view, name="list"),
    path("shorten", views.shorten_view, name="shorten"),
    path("delete/<keyword>", views.delete_view, name="delete"),
    path("refresh/", views.refresh_view, name="refresh"),
    path("refresh/<path:path>", views.refresh_view, name="refresh_with_path"),
]