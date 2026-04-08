from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Task, DailyRecord
from core.utils import get_user_local_time, apply_failure_consequences
import pytz

class Command(BaseCommand):
    help = 'Check for overdue tasks and mark them as failed'

    def handle(self, *args, **options):
        # Get all PENDING records from the past
        now_utc = timezone.now()
        
        pending_records = DailyRecord.objects.filter(status='PENDING').select_related('task', 'task__user')
        count = 0
        
        for record in pending_records:
            user = record.task.user
            user_tz = pytz.timezone(user.timezone)
            local_now = now_utc.astimezone(user_tz)
            
            # If the record's date is strictly before the user's current local date, the day is over
            if record.date < local_now.date():
                from services.consequence_engine import ConsequenceEngine
                # Mark as failed via consequence engine
                setattr(record, '_bypass_lock', True)
                record.status = 'FAILED'
                record.save()
                
                ConsequenceEngine.apply_failure(record)
                
                self.stdout.write(f"Marked task {record.task.id} as failed for user {user.username}")
                count += 1
                
        self.stdout.write(f"Sweep complete. Marked {count} records as failed.")