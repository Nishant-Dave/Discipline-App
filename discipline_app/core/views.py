from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import pytz
import logging

from .forms import CustomUserCreationForm
from .models import Task, DailyRecord, Streak, ActivityLog
from .utils import get_user_local_time, recalculate_streak, update_discipline_score
from services.consequence_engine import ConsequenceEngine

logger = logging.getLogger(__name__)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Timezone is set via dashboard JS or default 'UTC'
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def set_timezone(request):
    try:
        data = json.loads(request.body)
        tz = data.get('timezone')
        if tz in pytz.all_timezones:
            request.user.timezone = tz
            request.user.save()
            return JsonResponse({'status': 'ok'})
    except Exception as e:
        logger.error(f"Error setting timezone for {request.user.username}: {e}")
    
    # Fallback to UTC
    request.user.timezone = 'UTC'
    request.user.save()
    return JsonResponse({'status': 'fallback', 'timezone': 'UTC'})

@login_required
def user_settings(request):
    if request.method == 'POST':
        tz = request.POST.get('timezone')
        if tz in pytz.all_timezones:
            request.user.timezone = tz
            request.user.save()
            return redirect('dashboard')
    
    return render(request, 'settings.html', {'timezones': pytz.all_timezones})

@login_required
def dashboard(request):
    user = request.user
    local_now = get_user_local_time(user)
    today = local_now.date()
    
    tasks = Task.objects.filter(user=user, is_active=True)
    
    task_data = []
    all_done_today = True
    day_str = today.strftime('%a').lower()
    
    # 1. Sweep and fail all past pending records
    past_pending = DailyRecord.objects.filter(
        task__user=user, 
        status='PENDING', 
        date__lt=today
    )
    for record in past_pending:
        ConsequenceEngine.apply_failure(record)
    
    # 2. Setup today's items based on days_of_week
    for task in tasks:
        if day_str not in task.days_of_week:
            continue
            
        record, created = DailyRecord.objects.get_or_create(
            task=task, date=today, defaults={'status': 'PENDING'}
        )
        
        if record.status != 'DONE':
            all_done_today = False
        
        task_data.append({'task': task, 'record': record})
    
    streak_obj, _ = Streak.objects.get_or_create(user=user)
    
    context = {
        'tasks': task_data,
        'streak': streak_obj.current_streak,
        'longest_streak': streak_obj.longest_streak,
        'today': today,
        'all_done': all_done_today,
    }
    return render(request, 'dashboard.html', context)

@login_required
def create_task_page(request):
    return render(request, 'create_task.html')

@login_required
@require_http_methods(["POST"])
def create_task(request):
    user = request.user
    title = request.POST.get('title')
    description = request.POST.get('description', '')
    days_of_week = request.POST.getlist('days_of_week')
    consequence_level = request.POST.get('consequence_level', 'medium')
    
    if not title or not days_of_week:
        return JsonResponse({'error': 'Title and at least one day required'}, status=400)
    
    Task.objects.create(
        user=user, title=title, description=description,
        days_of_week=days_of_week, consequence_level=consequence_level, is_active=True
    )
    ActivityLog.objects.create(
        user=user,
        action="Task created",
        metadata={'task': title}
    )
    return redirect('dashboard')

@login_required
@require_http_methods(["POST"])
def checkin(request, task_id):
    user = request.user
    task = get_object_or_404(Task, id=task_id, user=user, is_active=True)
    local_now = get_user_local_time(user)
    today = local_now.date()
    
    record, created = DailyRecord.objects.get_or_create(
        task=task, date=today, defaults={'status': 'PENDING'}
    )
    
    if record.date < today:
        return JsonResponse({'error': 'Cannot edit past tasks'}, status=400)
    
    if record.status != 'PENDING':
        return JsonResponse({'error': f'Record is locked (Status: {record.status})'}, status=400)
    
    if local_now.date() > record.date:
        return JsonResponse({'error': 'Deadline passed. Record is locked.'}, status=403)
    
    record.status = 'DONE'
    record.marked_done_at = timezone.now()
    record.save()
    recalculate_streak(user)
    update_discipline_score(user)

    ActivityLog.objects.create(
        user=user,
        action="Task completed",
        metadata={'task': task.title}
    )
    
    return redirect('dashboard')

@login_required
@require_http_methods(["POST"])
def deactivate_task(request, task_id):
    user = request.user
    task = get_object_or_404(Task, id=task_id, user=user, is_active=True)
    
    if DailyRecord.objects.filter(task=task, status='FAILED').exists():
        return JsonResponse({'error': 'Cannot deactivate a failed task.'}, status=403)
    
    task.is_active = False
    task.save()
    recalculate_streak(user)
    return redirect('dashboard')

@login_required
def stats(request):
    user = request.user
    streak_obj = Streak.objects.get_or_create(user=user)[0]
    failed_records = DailyRecord.objects.filter(task__user=user, status='FAILED').select_related('task')
    total = DailyRecord.objects.filter(task__user=user).count()
    completed = DailyRecord.objects.filter(task__user=user, status='DONE').count()
    
    percentage = (completed / total * 100) if total > 0 else 0

    return render(request, 'stats.html', {
        'streak': streak_obj.current_streak,
        'longest_streak': streak_obj.longest_streak,
        'failures': failed_records,
        'completion_percentage': round(percentage, 2),
    })
