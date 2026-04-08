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
        from core.utils import get_user_local_time
        today = get_user_local_time(user).date()
        seven_days_ago = today - datetime.timedelta(days=6)
        
        # Optimize with single query using annotate
        stats = DailyRecord.objects.filter(
            task__user=user, 
            date__range=[seven_days_ago, today]
        ).values('date').annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='DONE')),
            failed=Count('id', filter=Q(status='FAILED'))
        ).order_by('date')
        
        stats_dict = {
            item['date']: item
            for item in stats
        }
        
        report = []
        for i in range(7):
            d = today - datetime.timedelta(days=6-i)
            day_data = stats_dict.get(d, {'total': 0, 'completed': 0, 'failed': 0})
            
            total = day_data['total']
            completed = day_data['completed']
            failed = day_data['failed']
            
            percentage = (completed / total * 100) if total > 0 else 0
            
            report.append({
                'date': d.isoformat(),
                'total_tasks': total,
                'completed_tasks': completed,
                'failed_tasks': failed,
                'completion_percentage': round(percentage, 2)
            })
        
        return Response(report)
