from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

class User(AbstractUser):
    timezone = models.CharField(max_length=50, default='UTC', null=False, blank=False)
    failure_count = models.IntegerField(default=0)
    discipline_score = models.FloatField(default=0.0)
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='core_user_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='core_user_set',
        related_query_name='user',
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='core_user_set',
        related_query_name='user',
    )

    def __str__(self):
        return self.username

def default_days_of_week():
    return ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

class Task(models.Model):
    CONSEQUENCE_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    days_of_week = models.JSONField(default=default_days_of_week)
    consequence_level = models.CharField(max_length=10, choices=CONSEQUENCE_CHOICES, default='medium')
    start_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    class Meta:
        ordering = ['-created_at']

class DailyRecord(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('DONE', 'Done'),
        ('FAILED', 'Failed'),
    ]
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    marked_done_at = models.DateTimeField(null=True, blank=True)
    proof = models.ImageField(upload_to='proofs/', blank=True, null=True)

    class Meta:
        unique_together = ('task', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.task.title} - {self.date}: {self.status}"

    def save(self, *args, **kwargs):
        if self.pk:
            from django.core.exceptions import ValidationError
            from django.utils import timezone
            import pytz
            from .utils import get_user_local_time

            old = DailyRecord.objects.get(pk=self.pk)
            local_now = get_user_local_time(self.task.user)

            is_past_record = old.date < local_now.date()
            bypass = getattr(self, '_bypass_lock', False)

            if is_past_record:
                if old.status == 'PENDING' and self.status == 'DONE':
                     raise ValidationError("Cannot mark task as done after deadline.")
                
                # If automated failure bypass is running, allow it
                if old.status == 'PENDING' and bypass and self.status == 'FAILED':
                    pass
                elif bypass:
                    pass
                elif old.status != self.status or old.proof != self.proof:
                     raise ValidationError("Past tasks cannot be edited. Record is immutable.")

        super().save(*args, **kwargs)

class Streak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_success_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - Current: {self.current_streak}, Longest: {self.longest_streak}"

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    metadata = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
