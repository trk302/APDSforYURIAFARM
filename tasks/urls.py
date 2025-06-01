from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_dashboard, name='task_dashboard'),
    path('create/', views.create_task, name='create_task'),
    path('calendar/events/', views.task_events, name='task_events'),
    path('calendar/sent-events/', views.task_sent_events, name='task_sent_events'),
    path('update/<int:task_id>/', views.update_task, name='update_task'),
    path('delete/<int:task_id>/', views.delete_task, name='delete_task'),
    path('email-autocomplete/', views.email_autocomplete, name='email_autocomplete'),
    path('analysis-autocomplete/', views.analysis_autocomplete, name='analysis_autocomplete'),
    path('get-analysis-description/', views.get_analysis_description, name='get_analysis_description'),
    path('take/<int:task_id>/', views.take_task, name='take_task'),
    path('complete/<int:task_id>/', views.complete_task, name='complete_task'),
    path('update-status/<int:task_id>/', views.update_task_status, name='update_task_status'),
    path('check-user-exists/', views.check_user_exists, name='check_user_exists'),
]
