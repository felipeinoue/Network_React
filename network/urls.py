
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    # APIs
    path("api_profile/<int:user_id>", views.api_profile, name="api_profile"),
    path("api_follow/<int:user_id>", views.api_follow, name="api_follow")
]
