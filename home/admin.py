from django.contrib import admin  # type: ignore
from django.contrib.auth.models import User, Group  # type: ignore
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin  # type: ignore
from django.http import HttpResponse  # type: ignore
from home.models import Profile
from import_export.admin import ImportExportModelAdmin  # type: ignore
from import_export import resources  # type: ignore
import csv
from .models import Attendance, Profile

def before_import(self, dataset, using_transactions, dry_run, **kwargs):
    print("CSV Headers:", dataset.headers)

# ✅ Inline Profile Admin
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'

# ✅ Export Users to CSV
def export_user_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['Username', 'Email', 'First Name', 'Last Name', 'Is Staff', 'Mobile', 'Gender', 'Address'])

    for user in queryset:
        profile = Profile.objects.filter(user=user).first()
        writer.writerow([
            user.username,
            user.email,
            user.first_name,
            user.last_name,
            user.is_staff,
            profile.mobile if profile else '',
            profile.gender if profile else '',
            profile.address if profile else '',
        ])
    return response

export_user_csv.short_description = "Export Selected Users to CSV"

# ✅ Custom Import Resource (Safe & Password-protected)
class CustomUserResource(resources.ModelResource):
    class Meta:
        model = User
        import_id_fields = ['username']
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        username = row.get('username')
        if User.objects.filter(username=username).exists():
            raise Exception(f"User '{username}' already exists. Skipping.")
        # Hash password before saving
        raw_password = row.get('password')
        if raw_password:
            temp_user = User()
            temp_user.set_password(raw_password)
            row['password'] = temp_user.password

# ✅ Custom User Admin
class CustomUserAdmin(ImportExportModelAdmin):
    resource_class = CustomUserResource
    inlines = [ProfileInline]
    actions = [export_user_csv]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    search_fields = ['username', 'email']

# ✅ Register Updated Admin
admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(User, CustomUserAdmin)


# ✅ Step 1: Export Attendance CSV Function — put this FIRST
def export_attendance_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['Username', 'Email', 'Date', 'Check-In', 'Check-Out', 'Location', 'QR Code'])

    for record in queryset:
        writer.writerow([
            record.user.username,
            record.email,
            record.date,
            record.check_in,
            record.check_out,
            record.location_name,
            record.qr_code,
        ])
    return response

export_attendance_csv.short_description = "Export Selected Attendance Records to CSV"

# ✅ Step 2: Attendance Admin Class — use the function
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'check_in', 'check_out', 'location_name')
    search_fields = ('user__username', 'location_name', 'email')
    list_filter = ('date', 'user')
    actions = [export_attendance_csv]  # ✅ now this works
