from django.urls import path
from . import views

urlpatterns = [
    path('tasks/', views.TaskListAPIView.as_view(), name='api-tasks'),
    path('daily-records/', views.DailyRecordListAPIView.as_view(), name='api-daily-records'),
    path('check-in/', views.CheckInAPIView.as_view(), name='api-check-in'),
    path('activity/', views.ActivityLogListAPIView.as_view(), name='api-activity'),
    path('weekly-report/', views.WeeklyReportAPIView.as_view(), name='api-weekly-report'),
]
