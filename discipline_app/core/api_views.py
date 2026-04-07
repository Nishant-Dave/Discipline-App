from rest_framework import generics, status, views, response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from .models import Task, DailyRecord, ActivityLog
from .serializers import TaskSerializer, DailyRecordSerializer
from .utils import get_user_local_time, recalculate_streak

# ... rest of code ...

# def perform_create(self, serializer):
#     task = serializer.save(user=self.request.user)
#     ActivityLog.objects.create(
#         user=self.request.user,
#         action="Task created",
#         metadata={'task': task.title}
#     )


class DailyRecordListAPIView(generics.ListAPIView):
    serializer_class = DailyRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        local_now = get_user_local_time(self.request.user)
        return DailyRecord.objects.filter(task__user=self.request.user, date=local_now.date())

class CheckInAPIView(views.APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        task_id = request.data.get('task_id')
        proof = request.data.get('proof')

        if not task_id:
            return response.Response({'error': 'task_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            task = Task.objects.get(id=task_id, user=request.user, is_active=True)
        except Task.DoesNotExist:
            return response.Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
            
        local_now = get_user_local_time(request.user)
        today = local_now.date()
        
        record, created = DailyRecord.objects.get_or_create(
            task=task, date=today, defaults={'status': 'PENDING'}
        )
        
        if record.date < today:
             return response.Response({'error': 'Cannot edit past tasks'}, status=status.HTTP_400_BAD_REQUEST)
        
        if record.status != 'PENDING':
            return response.Response({'error': f'Record is locked (Status: {record.status})'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Strict deadline check using accurate user timezone localization
        import pytz
        user_tz = pytz.timezone(request.user.timezone)
        naive_dt = timezone.datetime.combine(today, task.deadline_time)
        try:
            deadline_local = user_tz.localize(naive_dt)
        except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
            deadline_local = user_tz.localize(naive_dt, is_dst=False)
        
        if local_now > deadline_local:
            return response.Response({'error': 'Deadline passed. Record is locked.'}, status=status.HTTP_403_FORBIDDEN)
            
        # Proof validation (if required by task - this logic needs to be implemented in Task model)
        # For now, assume proof is optional or handled by serializer validation later
        
        record.status = 'DONE'
        record.marked_done_at = timezone.now()
        if proof: # Only save proof if it exists
            record.proof = proof
        record.save()
        
        recalculate_streak(request.user)
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action="Task completed",
            metadata={'task': task.title}
        )
        
        # Include proof URL in response if available
        response_data = {'status': 'DONE'}
        if record.proof:
            response_data['proof_url'] = record.proof.url
            
        return response.Response(response_data, status=status.HTTP_200_OK)

