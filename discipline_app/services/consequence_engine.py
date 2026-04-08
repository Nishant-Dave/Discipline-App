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

        # Apply consequence based on level
        from core.utils import apply_failure_consequences
        apply_failure_consequences(user, consequence_level=daily_record.task.consequence_level)

        # Log Activity
        ActivityLog.objects.create(
            user=user,
            action="Task failed",
            metadata={
                'task': daily_record.task.title,
                'consequence': daily_record.task.consequence_level
            }
        )

        logger.warning(f"Task '{daily_record.task.title}' failed for user '{user.username}'. Streak penalty applied.")
