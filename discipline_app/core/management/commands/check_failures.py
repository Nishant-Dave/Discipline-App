from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Task, DailyRecord
from core.utils import get_user_local_time, apply_failure_consequences
import pytz

class Command(BaseCommand):
    help = 'Check for overdue tasks and mark them as failed'

    def handle(self, *args, **options):
        # Get all active tasks
        tasks = Task.objects.filter(is_active=True)
        now_utc = timezone.now()
        
        for task in tasks:
            user = task.user
            user_tz = pytz.timezone(user.timezone)
            local_now = now_utc.astimezone(user_tz)
            today = local_now.date()
            
            # Get today's record
            record, created = DailyRecord.objects.get_or_create(
                task=task, date=today, defaults={'status': 'PENDING'}
            )
            
            if record.status == 'PENDING':
                # Build deadline datetime in user's local time
                deadline_local = user_tz.localize(
                    timezone.datetime.combine(today, task.deadline_time)
                )
                # Compare
                if local_now > deadline_local:
                    record.status = 'FAILED'
                    record.failed_at = now_utc
                    record.save()
                    self.stdout.write(f"Marked task {task.id} as failed for user {user.username}")
                    apply_failure_consequences(user)