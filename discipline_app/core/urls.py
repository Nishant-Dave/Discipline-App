from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, api_views, api_stats, api_logs
# ... imports ...

urlpatterns = [
    # ... existing ...
    path('api/activity/', api_logs.ActivityLogListAPIView.as_view(), name='api_activity'),
    path('api/weekly-report/', api_stats.WeeklyReportAPIView.as_view(), name='api_weekly_report'),
    # ...
]

