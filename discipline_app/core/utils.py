from django.utils import timezone
import pytz
from .models import Streak, DailyRecord

def update_discipline_score(user):
    from .models import DailyRecord
    total = DailyRecord.objects.filter(task__user=user).count()
    completed = DailyRecord.objects.filter(task__user=user, status='DONE').count()
    score = (completed / total * 100) if total > 0 else 0
    user.discipline_score = round(score, 2)
    user.save()

def get_user_local_time(user):
    """Return current datetime in user's timezone."""
    tz = pytz.timezone(user.timezone)
    return timezone.now().astimezone(tz)

def recalculate_streak(user):
    """
    Incremental streak update for today. Handless 'no task days'.
    """
    from .models import Task, DailyRecord
    today = get_user_local_time(user).date()
    streak_obj, _ = Streak.objects.get_or_create(user=user)
    
    day_str = today.strftime('%a').lower()
    tasks_today = [t for t in Task.objects.filter(user=user, is_active=True) if day_str in t.days_of_week]
    
    # Handle "no task day"
    if not tasks_today:
        return streak_obj.current_streak
        
    all_done = True
    for task in tasks_today:
        if not DailyRecord.objects.filter(task=task, date=today, status='DONE').exists():
            all_done = False
            break
            
    if all_done:
        if streak_obj.last_success_date != today:
            streak_obj.current_streak += 1
            streak_obj.last_success_date = today
            if streak_obj.current_streak > streak_obj.longest_streak:
                streak_obj.longest_streak = streak_obj.current_streak
            streak_obj.save()
            
    return streak_obj.current_streak
