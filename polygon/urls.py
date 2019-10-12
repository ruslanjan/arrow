from django.urls import path

from polygon import views

urlpatterns = [
    path('', views.index, name='polygon.views.index'),
    path('problem/create', views.create_problem,
         name='polygon.views.create_problem'),
    path('problem/<int:pk>/delete/', views.delete_problem,
         name='polygon.views.delete_problem'),
    path('problem/<int:pk>/', views.view_problem,
         name='polygon.views.problem'),

    # Statement
    path('problem/<int:pk>/statement/', views.view_statements,
         name='polygon.views.statements'),
    path('problem/<int:pk>/statement/create', views.create_statement,
         name='polygon.views.create_statement'),
    path('problem/<int:problem_id>/statement/<int:pk>/delete/',
         views.delete_statement,
         name='polygon.views.delete_statement'),
    path('problem/<int:problem_id>/statement/<int:pk>', views.view_statement,
         name='polygon.views.statement'),

    # Test
    path('problem/<int:pk>/test/', views.view_tests,
         name='polygon.views.tests'),
    path('problem/<int:pk>/test/create', views.create_test,
         name='polygon.views.create_test'),
    path('problem/<int:problem_id>/test/<int:pk>/delete/', views.delete_test,
         name='polygon.views.delete_test'),
    path('problem/<int:problem_id>/test/<int:pk>', views.view_test,
         name='polygon.views.test'),

    # test_submission
    path('problem/<int:pk>/test_submission/', views.test_submission,
         name='polygon.views.test_submission'),
]
