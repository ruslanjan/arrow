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

    # Problem files
    path('problem/<int:pk>/file/', views.view_files,
         name='polygon.views.files'),
    path('problem/<int:pk>/file/upload', views.upload_file,
         name='polygon.views.upload_file'),
    path('problem/<int:problem_id>/file/<int:pk>/', views.delete_file,
         name='polygon.views.delete_file'),

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
    path('problem/<int:problem_id>/statement/<int:pk>/preview',
         views.preview_statement,
         name='polygon.views.preview_statement'),

    # Test
    path('problem/<int:pk>/test/', views.view_tests,
         name='polygon.views.tests'),
    path('problem/<int:pk>/test/reindex', views.reindex_tests,
         name='polygon.views.reindex_tests'),
    path('problem/<int:pk>/test/delete/all', views.delete_all_tests,
         name='polygon.views.delete_all_tests'),
    path('problem/<int:pk>/test/generate_tests_from_script',
         views.generate_tests_from_script,
         name='polygon.views.generate_tests_from_script'),
    path('problem/<int:pk>/test/create', views.create_test,
         name='polygon.views.create_test'),
    path('problem/<int:problem_id>/test/<int:pk>/delete/', views.delete_test,
         name='polygon.views.delete_test'),
    path('problem/<int:problem_id>/test/<int:pk>', views.view_test,
         name='polygon.views.test'),

    # Generator
    path('problem/<int:pk>/generator/', views.view_generators,
         name='polygon.views.generators'),
    path('problem/<int:pk>/generator/create/', views.create_generator,
         name='polygon.views.create_generator'),
    path('problem/<int:problem_id>/generator/<int:pk>/delete/',
         views.delete_generator,
         name='polygon.views.delete_generator'),
    path('problem/<int:problem_id>/generator/<int:pk>/', views.view_generator,
         name='polygon.views.generator'),

    # Submission
    path('submission/', views.view_submissions,
         name='polygon.views.submissions'),
    path('submission/<int:pk>', views.view_submission,
         name='polygon.views.submission'),
    path('submission/<int:pk>/rejudge', views.rejudge_submission,
         name='polygon.views.rejudge_submission'),
    path('submission/rejudge', views.rejudge_submissions,
         name='polygon.views.rejudge_submissions'),

    # test_submission
    path('problem/<int:pk>/test_submission/', views.test_submission,
         name='polygon.views.test_submission'),

]
