from django.contrib import admin
from django.urls import path
from home import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('', views.index, name='index'),
    path('login/', views.loginUser, name='login'),     # ✅ Corrected
    path('logout/', views.logoutUser, name='logout'),  # ✅ Corrected
     path("profile/", views.profile_view, name="profile"),
    path("attendance/", views.attendance, name="attendance"),
    path("mark_attendance/", views.mark_attendance, name="mark_attendance"),
    path('attendance/history/', views.attendance_history, name='attendance_history'),
    path("attendance/report/", views.attendance_report, name="attendance_report"),
    path("attendance/export/", views.export_attendance_csv, name="export_attendance_csv"),



]
