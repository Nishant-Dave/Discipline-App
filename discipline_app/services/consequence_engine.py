import logging
from django.utils import timezone
from core.models import Streak, ActivityLog
from core.utils import update_discipline_score
import logging

logger = logging.getLogger(__name__)

class ConsequenceEngine:
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

        # Reset user streak
        streak, _ = Streak.objects.get_or_create(user=user)
        streak.current_streak = 0
        streak.save()

        # Log Activity
        ActivityLog.objects.create(
            user=user,
            action="Task failed",
            metadata={'task': daily_record.task.title}
        )

        logger.warning(f"Task '{daily_record.task.title}' failed for user '{user.username}'. Streak reset.")
