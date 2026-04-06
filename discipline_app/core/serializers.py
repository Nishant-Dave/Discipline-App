from rest_framework import serializers
from .models import Task, DailyRecord, ActivityLog

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'timezone')

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'title', 'description', 'deadline_time', 'is_active', 'created_at')
        read_only_fields = ('created_at', 'is_active')

class DailyRecordSerializer(serializers.ModelSerializer):
    proof_url = serializers.SerializerMethodField()

    class Meta:
        model = DailyRecord
        fields = ('id', 'task', 'date', 'status', 'marked_done_at', 'proof', 'proof_url')
        read_only_fields = ('marked_done_at', 'proof', 'proof_url')

    def get_proof_url(self, obj):
        if obj.proof:
            return obj.proof.url
        return None

class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = ('id', 'action', 'metadata', 'timestamp')
