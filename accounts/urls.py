from django.contrib import admin
from django.urls import path, include
from .views import *

urlpatterns = [
    path('register/', registerView.as_view(), name="register_view"),
    path('validations/', validationsView.as_view(), name="validations"),
    path('login/', loginView.as_view(), name="login_page"),
    path('loggedin/', loggedView.as_view(), name="logged_page"),
    path('logoff/', logoffView.as_view(), name="logoff_page"),
    path('manage/', manageView.as_view(), name="manager_page"),
    path('manage/<int:id>', eachaccountView.as_view(), name="each_account_page"),
    path('changepassword/<int:id>', passchangeView.as_view(), name="passchange_page"),
    path('sessions/', sessionsView.as_view(), name="sessions_page"),
    path('sessions/anonymous', sessionsanomView.as_view(), name="sessionsanom_page"),
]