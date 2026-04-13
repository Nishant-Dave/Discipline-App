import logging
from django.utils import timezone
from core.models import Streak, ActivityLog
from core.utils import update_discipline_score
import logging

logger = logging.getLogger(__name__)

class ConsequenceEngine:
    @staticmethod
    def get_monthly_completion_percentage(user):
        from core.models import DailyRecord
        from core.utils import get_user_local_time
        from django.db.models import Count, Q
        
        local_now = get_user_local_time(user)
        current_month = local_now.date().replace(day=1)
        
        stats = DailyRecord.objects.filter(
            task__user=user, 
            date__gte=current_month
        ).aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='DONE'))
        )
        
        total = stats['total']
        completed = stats['completed']
        
        if total == 0:
            return 100.0
            
        return (completed / total) * 100

    @staticmethod
    def apply_failure(daily_record):
        # Mark record as FAILED
        daily_record.status = 'FAILED'
        daily_record._bypass_lock = True
        daily_record.save()

        # Update user failure count
        user = daily_record.task.user
        user.failure_count += 1
        user.save()
        update_discipline_score(user)

        # Apply consequence based on level
        from core.models import DailyRecord, Task
        from core.utils import get_user_local_time
        from datetime import timedelta
        
        consequence = daily_record.task.consequence_level
        monthly_pct = ConsequenceEngine.get_monthly_completion_percentage(user)
        if monthly_pct < 80:
            consequence = 'hard'

        streak_obj, _ = Streak.objects.get_or_create(user=user)

        if consequence == 'easy':
            # Do not reset streak, only failure count increments
            pass
        elif consequence == 'medium':
            # Reset streak to 0
            streak_obj.current_streak = 0
            streak_obj.last_success_date = None
            streak_obj.save()
        elif consequence == 'hard':
            # Reset streak to 0
            streak_obj.current_streak = 0
            streak_obj.last_success_date = None
            streak_obj.save()
            
            # Create a penalty daily record via a new task since DailyRecord relies on Task.title
            local_now = get_user_local_time(user)
            tomorrow = local_now.date() + timedelta(days=1)
            tomorrow_day_str = tomorrow.strftime('%a').lower()
            
            penalty_task = Task.objects.create(
                user=user,
                title=f"Penalty: {daily_record.task.title}",
                description="Automatic penalty for failing a HARD task.",
                days_of_week=[tomorrow_day_str],
                consequence_level='hard',
                is_active=True
            )
            
            DailyRecord.objects.create(
                task=penalty_task,
                date=tomorrow,
                status='PENDING'
            )
            
            ActivityLog.objects.create(
                user=user,
                action="Penalty created",
                metadata={'task': penalty_task.title}
            )

        # Log Activity
        ActivityLog.objects.create(
            user=user,
            action="Task failed",
            metadata={
                'task': daily_record.task.title,
                'consequence': daily_record.task.consequence_level
            }
        )

        logger.warning(f"Task '{daily_record.task.title}' failed for user '{user.username}'. Consequence level: {consequence} (Monthly Pct: {monthly_pct:.2f}%)")
