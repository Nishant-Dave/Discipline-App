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
        
        # Tasks are valid for the entire day, time-based checks are removed.            
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

class HistoryAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        records = DailyRecord.objects.filter(
            task__user=request.user
        ).select_related('task').order_by('-date', '-id')[:20]
        
        data = []
        for r in records:
            data.append({
                'task_title': r.task.title,
                'status': r.status,
                'date': r.date.isoformat(),
                'proof': r.proof.url if r.proof else None
            })
            
        return response.Response(data)
