from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordChangeView,
    PasswordChangeDoneView,
)
from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'users'

urlpatterns = [
    path(
        'password_change/done/',
        login_required(PasswordChangeDoneView.as_view(
            template_name='users/password_change_done.html')),
        name='password_change_done'
    ),
    path(
        'password_change/',
        login_required(PasswordChangeView.as_view(
            template_name='users/password_change_form.html')),
        name='password_change_form'
    ),
    path(
        'logout/',
        LogoutView.as_view(template_name='users/logged_out.html'),
        name='logout'
    ),
    path(
        'login/',
        LoginView.as_view(template_name='users/login.html'),
        name='login'
    ),
    path(
        'password_reset_form/',
        PasswordResetView.as_view(),
        name='password_reset_form'
    ),
    path(
        'signup/',
        views.SignUp.as_view(),
        name='signup'
    )
]
