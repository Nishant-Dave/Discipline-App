from django.utils import timezone
import pytz
from .models import Streak, DailyRecord

def get_user_local_time(user):
    """Return current datetime in user's timezone."""
    tz = pytz.timezone(user.timezone)
    return timezone.now().astimezone(tz)

def recalculate_streak(user):
    """
    Recalculate user's current streak based on all active tasks.
    Streak = consecutive days where ALL active tasks were DONE.
    """
    from .models import Task, DailyRecord  # avoid circular import
    today = get_user_local_time(user).date()
    
    streak = 0
    check_date = today
    while True:
        # Get all active tasks for user
        tasks = Task.objects.filter(user=user, is_active=True)
        if not tasks:
            break
        
        # Check if all tasks have DONE record for check_date
        all_done = True
        for task in tasks:
            try:
                record = DailyRecord.objects.get(task=task, date=check_date)
                if record.status != 'DONE':
                    all_done = False
                    break
            except DailyRecord.DoesNotExist:
                all_done = False
                break
        
        if all_done:
            streak += 1
            check_date = check_date - timezone.timedelta(days=1)
        else:
            break
    
    # Update streak object
    streak_obj, _ = Streak.objects.get_or_create(user=user)
    streak_obj.current_streak = streak
    if streak > streak_obj.longest_streak:
        streak_obj.longest_streak = streak
    if streak > 0:
        streak_obj.last_success_date = today
    else:
        streak_obj.last_success_date = None
    streak_obj.save()
    return streak

def apply_failure_consequences(user):
    """Called when ANY task fails. Resets streak."""
    streak_obj, _ = Streak.objects.get_or_create(user=user)
    # Reset current streak
    streak_obj.current_streak = 0
    # longest_streak remains unchanged
    streak_obj.last_success_date = None
    streak_obj.save()
    # Log: we can see failure via DailyRecord failed_at