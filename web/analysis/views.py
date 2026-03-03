from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ForensicRequest, AnalysisResult
from .forms import ForensicRequestForm
from .tasks import process_forensic_request

@login_required
def dashboard(request):
    if request.user.is_superuser:
        requests = ForensicRequest.objects.all().order_by('-created_at')
    else:
        requests = ForensicRequest.objects.filter(user=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        form = ForensicRequestForm(request.POST, request.FILES)
        if form.is_valid():
            forensic_req = form.save(commit=False)
            forensic_req.user = request.user
            forensic_req.save()
            
            # Trigger Celery task
            process_forensic_request.delay(forensic_req.id)
            
            return redirect('dashboard')
    else:
        form = ForensicRequestForm()
    
    return render(request, 'analysis/dashboard.html', {'requests': requests, 'form': form})

@login_required
def request_detail(request, pk):
    if request.user.is_superuser:
        req = get_object_or_404(ForensicRequest, pk=pk)
    else:
        req = get_object_or_404(ForensicRequest, pk=pk, user=request.user)
    results = req.results.all()
    return render(request, 'analysis/detail.html', {'req': req, 'results': results})
