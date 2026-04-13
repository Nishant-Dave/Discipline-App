from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from core.models import Task, ActivityLog
from core.serializers import TaskSerializer

# Consolidate internal API views by importing them
from core.api_views import DailyRecordListAPIView, CheckInAPIView, HistoryAPIView
from core.api_logs import ActivityLogListAPIView
from core.api_stats import WeeklyReportAPIView

class TaskListAPIView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)
        
    def perform_create(self, serializer):
        task = serializer.save(user=self.request.user)
        ActivityLog.objects.create(
            user=self.request.user,
            action="Task created",
            metadata={'task': task.title}
        )
