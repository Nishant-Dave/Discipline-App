from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Streak, DailyRecord
from django.db.models import Count, Q
from django.utils import timezone
import datetime

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
        
        from services.consequence_engine import ConsequenceEngine
        monthly_pct = ConsequenceEngine.get_monthly_completion_percentage(user)
        
        data = {
            'current_streak': streak_obj.current_streak,
            'longest_streak': streak_obj.longest_streak,
            'total_failures': failed_records,
            'discipline_score': user.discipline_score,
            'monthly_completion_percentage': round(monthly_pct, 2)
        }
        
        return Response(data)

class WeeklyReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        report = []
        for i in range(7):
            date = today - datetime.timedelta(days=i)
            records = DailyRecord.objects.filter(task__user=user, date=date)
            
            total = records.count()
            completed = records.filter(status='DONE').count()
            failed = records.filter(status='FAILED').count()
            
            percentage = (completed / total * 100) if total > 0 else 0
            
            report.append({
                'date': date.isoformat(),
                'total_tasks': total,
                'completed_tasks': completed,
                'failed_tasks': failed,
                'completion_percentage': round(percentage, 2)
            })
        
        # Sort by date (ascending)
        report.sort(key=lambda x: x['date'])
        return Response(report)
