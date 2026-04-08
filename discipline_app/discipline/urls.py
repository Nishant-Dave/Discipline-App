from django.contrib import admin
from django.urls import path, include
from core import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('create-task/', views.create_task_page, name='new_task_page'),
    path('create-task/submit/', views.create_task, name='create_task'),
    path('checkin/<int:task_id>/', views.checkin, name='checkin'),
    path('deactivate/<int:task_id>/', views.deactivate_task, name='deactivate'),
    path('settings/', views.user_settings, name='user_settings'),
    path('stats/', views.stats, name='stats'),
    path('set-timezone/', views.set_timezone, name='set_timezone'),
    path('api/', include('api.urls')), 
]

