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
        
        # We can now use the pre-calculated score from the User model
        
        data = {
            'current_streak': streak_obj.current_streak,
            'longest_streak': streak_obj.longest_streak,
            'total_failures': failed_records,
            'discipline_score': user.discipline_score
        }
        
        return Response(data)
