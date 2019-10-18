#  Copyright (c) 2019 Jankurazov Ruslan - All Rights Reserved.
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential

from django.urls import path

from . import views

urlpatterns = [
    path('login', views.login_view, name='accounts.views.login'),
    path('register', views.register, name='accounts.views.register'),
    path('logout', views.logout_view, name='accounts.views.logout'),
]