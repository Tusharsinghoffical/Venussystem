from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone # type: ignore
from django.utils.timezone import localtime
from .models import Attendance, Profile
from .forms import ProfileForm
import json
from django.db.models import Count
from django.db.models.functions import TruncWeek, TruncMonth, TruncYear
import csv




def home(request):
    return render(request, 'home.html') 


# ✅ Homepage (Dashboard)
@login_required
def index(request):
    return render(request, 'index.html')


# ✅ Login View
def loginUser(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/")
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'login.html')


# ✅ Logout View
def logoutUser(request):
    logout(request)
    return redirect("/login")


@login_required
def profile_view(request):
    return render(request, 'profile.html', {
        'user': request.user
    })

# ✅ Profile View
def profile_view(request):
    user_profile = request.user.profile  # or however you're fetching it

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
    else:
        form = ProfileForm(instance=user_profile)

    context = {
        'form': form,
        'profile': user_profile,
        'user': request.user
    }
    return render(request, 'profile.html', context)

# ✅ Attendance Scanner Page
@login_required
def attendance(request):
    user = request.user
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        profile = None  # or handle error/logging

    context = {
        'full_name': user.get_full_name() or user.username,
        'email': user.email,
        'username': user.username,
        'user_id': user.id,
        'profile': profile,
    }
    return render(request, "attendance.html", context)


# ✅ Attendance History Page
@login_required
def attendance_history(request):
    records = Attendance.objects.filter(user=request.user).order_by('-date', '-time')
    
    context = {
        'records': records,
        'name': request.user.get_full_name() or request.user.username,
        'email': request.user.email,
        'username': request.user.username,
        'user_id': request.user.id,
    }
    return render(request, 'attendance_history.html', context)


# ✅ QR Attendance Scanner Page
@login_required
def qr_attendance_view(request):
    user = request.user

    context = {
        "user": user,
        "name": user.get_full_name() or user.username,
        "email": user.email,
        "username": user.username,
        "user_id": user.id,
    }
    return render(request, "attendance.html", context)


# ✅ API to Mark Attendance
@csrf_exempt
@login_required
def mark_attendance(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            qr_data = data.get("qr_data")
            location_name = data.get("location_name")
            today = timezone.now().date()
            now_time = localtime().time()

            # Check if a record already exists for today
            record, created = Attendance.objects.get_or_create(
                user=request.user,
                date=today,
                defaults={
                    "name": request.user.get_full_name() or request.user.username,
                    "email": request.user.email,
                    "qr_code": qr_data,
                    "location_name": location_name,
                    "check_in": now_time,  # ⏱ Check-in on first scan
                }
            )

            if not created:
                if not record.check_out:
                    record.check_out = now_time  # ⏱ Check-out on second scan
                    record.save()
                    return JsonResponse({"message": "✅ Check-Out marked successfully!"})
                else:
                    return JsonResponse({"message": "ℹ️ Already Checked In and Out today."})
            else:
                return JsonResponse({
                    "message": "✅ Check-In marked successfully!",
                    "location_name": location_name
                })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)



@login_required
def attendance_report(request):
    user = request.user

    # Weekly summary
    weekly = Attendance.objects.filter(user=user).annotate(
        week=TruncWeek('date')
    ).values('week').annotate(total=Count('id')).order_by('-week')

    # Monthly summary
    monthly = Attendance.objects.filter(user=user).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(total=Count('id')).order_by('-month')

    # Yearly summary
    yearly = Attendance.objects.filter(user=user).annotate(
        year=TruncYear('date')
    ).values('year').annotate(total=Count('id')).order_by('-year')

    return render(request, "attendance_report.html", {
        "weekly": weekly,
        "monthly": monthly,
        "yearly": yearly,
    })



@login_required
def export_attendance_csv(request):
    records = Attendance.objects.filter(user=request.user).order_by('-date')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="my_attendance.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Check-In', 'Check-Out', 'Location', 'QR Code'])

    for record in records:
        writer.writerow([
            record.date,
            record.check_in,
            record.check_out,
            record.location_name,
            record.qr_code,
        ])

    return response