from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='problemset.views.index'),
    path('my_submissions/', views.my_submissions,
         name='problemset.views.my_submissions'),
    path('submissions', views.submissions,
         name='problemset.views.submissions'),
    path('submission/<int:pk>/', views.submission,
         name='problemset.views.submission'),
    path('task/', views.view_tasks,
         name='problemset.views.tasks'),
    path('task/<int:pk>/', views.view_task,
         name='problemset.views.task'),
    path('task/<int:pk>/submit', views.submit_solution,
         name='problemset.views.submit'),

    path('task/manage/', views.manage_tasks,
         name='problemset.views.manage_tasks'),
    path('task/manage/add', views.add_task,
         name='problemset.views.add_task'),
    path('task/manage/<int:pk>/delete', views.delete_task,
         name='problemset.views.delete_task'),
    path('task/manage/<int:pk>/', views.manage_task,
         name='problemset.views.manage_task'),
]
