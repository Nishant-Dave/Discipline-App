from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, api_views, api_stats, api_logs

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('create-task/', views.create_task_page, name='create_task_page'),
    path('create-task/submit/', views.create_task, name='create_task'),
    path('checkin/<int:task_id>/', views.checkin, name='checkin'),
    path('deactivate/<int:task_id>/', views.deactivate_task, name='deactivate_task'),
    path('stats/', views.stats, name='stats'),
    path('set-timezone/', views.set_timezone, name='set_timezone'),
    
    # API endpoints
    path('api/tasks/', api_views.TaskCreateAPIView.as_view(), name='api_tasks'),
    path('api/daily-records/', api_views.DailyRecordListAPIView.as_view(), name='api_daily_records'),
    path('api/checkin/', api_views.CheckInAPIView.as_view(), name='api_checkin'),
    path('api/stats/', api_stats.UserStatsAPIView.as_view(), name='api_stats'),
    path('api/activity/', api_logs.ActivityLogListAPIView.as_view(), name='api_activity'),
    path('api/weekly-report/', api_stats.WeeklyReportAPIView.as_view(), name='api_weekly_report'),
]

