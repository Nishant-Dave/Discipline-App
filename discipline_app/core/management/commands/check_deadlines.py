from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import DailyRecord
from services.consequence_engine import ConsequenceEngine
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Checks for overdue tasks and applies consequences'

    def handle(self, *args, **options):
        now = timezone.now()
        # Fetch all pending DailyRecords that are past their deadline
        overdue_records = DailyRecord.objects.filter(
            status='PENDING',
            task__deadline_time__lt=now.time(), # Compare only time part of deadline
            date=now.date() # Ensure it's for today
        )

        if not overdue_records.exists():
            self.stdout.write(self.style.SUCCESS('No overdue tasks found.'))
            return

        self.stdout.write(f'Found {overdue_records.count()} overdue tasks.')

        for record in overdue_records:
            try:
                # Apply failure consequences using the service
                ConsequenceEngine.apply_failure(record)
                self.stdout.write(self.style.SUCCESS(f"Successfully processed overdue task: {record.task.title} for {record.task.user.username}"))
            except Exception as e:
                logger.error(f"Error processing overdue task {record.task.title} for {record.task.user.username}: {e}")
                self.stdout.write(self.style.ERROR(f"Error processing task: {record.task.title}. Check logs."))

        self.stdout.write(self.style.SUCCESS('Finished checking deadlines.'))
