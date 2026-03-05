from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import ForensicRequest, AnalysisResult
from .forms import ForensicRequestForm
from .tasks import process_forensic_request
from .utils import get_available_models, RESTRICTED_MODELS

@login_required
def dashboard(request):
    is_admin = request.user.is_superuser
    
    if request.method == 'POST':
        form = ForensicRequestForm(request.POST, request.FILES, is_admin=is_admin)
        if form.is_valid():
            forensic_req = form.save(commit=False)
            forensic_req.user = request.user
            forensic_req.media_type = 'video'  # Always video
            
            # Get selected models from form
            selected_models = form.cleaned_data.get('selected_models')
            if selected_models:
                forensic_req.selected_models = selected_models
            else:
                forensic_req.selected_models = get_available_models(is_admin=is_admin)
            
            # Security check: Remove restricted models for non-admin users
            if not is_admin:
                forensic_req.selected_models = [m for m in forensic_req.selected_models if m not in RESTRICTED_MODELS]
            
            forensic_req.save()
            
            # Trigger Celery task
            process_forensic_request.delay(forensic_req.id)
            
            return redirect('request_detail', pk=forensic_req.id)
    else:
        form = ForensicRequestForm(is_admin=is_admin)
    
    # Show user's recent requests
    if is_admin:
        requests = ForensicRequest.objects.all().order_by('-created_at')[:5]
    else:
        requests = ForensicRequest.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    return render(request, 'analysis/dashboard.html', {
        'form': form,
        'requests': requests,
        'is_admin': is_admin
    })

@login_required
def request_detail(request, pk):
    if request.user.is_superuser:
        req = get_object_or_404(ForensicRequest, pk=pk)
    else:
        req = get_object_or_404(ForensicRequest, pk=pk, user=request.user)
    results = req.results.all()
    return render(request, 'analysis/detail.html', {'req': req, 'results': results})

@login_required
def request_status_api(request, pk):
    """API endpoint to get request status without full page load"""
    if request.user.is_superuser:
        req = get_object_or_404(ForensicRequest, pk=pk)
    else:
        req = get_object_or_404(ForensicRequest, pk=pk, user=request.user)
    
    # Get the latest results
    results = req.results.all()
    results_data = [{
        'model_name': r.model_name,
        'status': r.status,
        'completed_at': r.completed_at.isoformat() if r.completed_at else None
    } for r in results]
    
    return JsonResponse({
        'id': req.id,
        'status': req.status,
        'report_content': req.report_content if req.report_content else '',
        'selected_models': req.selected_models if req.selected_models else [],
        'results': results_data
    })
