from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from analysis.models import ForensicRequest

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email')

@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    total_users = CustomUser.objects.count()
    total_requests = ForensicRequest.objects.count()
    recent_requests = ForensicRequest.objects.all().order_by('-created_at')[:10]
    users = CustomUser.objects.all().order_by('-date_joined')[:10]
    
    context = {
        'total_users': total_users,
        'total_requests': total_requests,
        'recent_requests': recent_requests,
        'users': users
    }
    return render(request, 'accounts/admin_dashboard.html', context)

@user_passes_test(lambda u: u.is_superuser)
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # login(request, user) # Admin adds user, don't log them in as the new user
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})
