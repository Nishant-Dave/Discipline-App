from django.contrib import admin
from .models import User, Task, DailyRecord, Streak

admin.site.register(User)
admin.site.register(Task)
admin.site.register(DailyRecord)
admin.site.register(Streak)