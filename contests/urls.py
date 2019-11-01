from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='contests.views.index'),

    # Manage Contest
    path('manage/contest/', views.manage_contests,
         name='contests.views.manage_contests'),
    path('manage/contest/create/', views.create_contest,
         name='contests.views.create_contest', ),
    path('manage/contest/<int:pk>/manage/', views.manage_contest,
         name='contests.views.manage_contest', ),
    path('manage/contest/<int:pk>/delete/', views.delete_contest,
         name='contests.views.delete_contest', ),
    # Manage Contest Task
    path('manage/contest/<int:pk>/task/', views.manage_contest_tasks,
         name='contests.views.manage_contest_tasks'),
    path('manage/contest/<int:pk>/task/reorder/', views.reorder_tasks,
         name='contests.views.reorder_tasks'),
    path('manage/contest/<int:pk>/task/add/', views.add_contest_task,
         name='contests.views.add_contest_task'),
    path('manage/contest/<int:contest_id>/task/<int:pk>/',
         views.manage_contest_task,
         name='contests.views.manage_contest_task'),
    path('manage/contest/<int:contest_id>/task/<int:pk>/delete/',
         views.delete_contest_task,
         name='contests.views.delete_contest_task'),
]
