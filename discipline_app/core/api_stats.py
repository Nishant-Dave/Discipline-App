from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Streak, DailyRecord
from django.db.models import Count, Q

class UserStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Get Streak
        streak_obj, _ = Streak.objects.get_or_create(user=user)
        
        # Calculate stats
        total_records = DailyRecord.objects.filter(task__user=user).count()
        completed_records = DailyRecord.objects.filter(task__user=user, status='DONE').count()
        failed_records = DailyRecord.objects.filter(task__user=user, status='FAILED').count()
        
        completion_percentage = 0
        if total_records > 0:
            completion_percentage = (completed_records / total_records) * 100
        
        data = {
            'current_streak': streak_obj.current_streak,
            'longest_streak': streak_obj.longest_streak,
            'total_failures': failed_records,
            'completion_percentage': round(completion_percentage, 2)
        }
        
        return Response(data)
