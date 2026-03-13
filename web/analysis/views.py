from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import ForensicRequest, AnalysisResult
from .forms import ForensicRequestForm
from .tasks import process_forensic_request
from .utils import get_available_models, RESTRICTED_MODELS
import os
import json

@login_required
def dashboard(request):
    is_admin = request.user.is_superuser
    
    if request.method == 'POST':
        form = ForensicRequestForm(request.POST, request.FILES, is_admin=is_admin)
        if form.is_valid():
            forensic_req = form.save(commit=False)
            forensic_req.user = request.user
            forensic_req.media_type = 'video'
            
            selected_models = form.cleaned_data.get('selected_models')
            if selected_models:
                forensic_req.selected_models = selected_models
            else:
                forensic_req.selected_models = get_available_models(is_admin=is_admin)
            
            if not is_admin:
                forensic_req.selected_models = [m for m in forensic_req.selected_models if m not in RESTRICTED_MODELS]
            
            forensic_req.save()
            process_forensic_request.delay(forensic_req.id)
            return redirect('request_detail', pk=forensic_req.id)
    else:
        form = ForensicRequestForm(is_admin=is_admin)
    
    if is_admin:
        requests_list = ForensicRequest.objects.all().order_by('-created_at')[:20]
    else:
        requests_list = ForensicRequest.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    return render(request, 'analysis/dashboard.html', {
        'form': form,
        'requests': requests_list,
        'is_admin': is_admin
    })

@login_required
def request_detail(request, pk):
    is_admin = request.user.is_superuser
    
    if is_admin:
        req = get_object_or_404(ForensicRequest, pk=pk)
    else:
        req = get_object_or_404(ForensicRequest, pk=pk, user=request.user)
    
    results = req.results.all()
    
    # Helper: build media URL from absolute file path
    def _build_media_url(file_path):
        from django.conf import settings
        media_root = str(settings.MEDIA_ROOT)
        if file_path.startswith(media_root):
            relative_path = file_path[len(media_root):].lstrip('/')
            return f"/media/{relative_path}"
        return None
    
    # Determine which report to show
    if is_admin:
        report_raw = req.user_report or req.report_content or ''
    else:
        # User only sees report if approved
        if req.report_approved:
            report_raw = req.user_report or req.report_content or ''
        else:
            report_raw = ''
    
    # Try to parse the report as JSON (new per-model card format)
    model_cards = []
    report_to_show = ''  # Fallback for old markdown format
    
    if report_raw:
        try:
            cards_data = json.loads(report_raw)
            if isinstance(cards_data, list):
                # New format: per-model cards
                for card in cards_data:
                    evidence_url = None
                    if card.get('evidence_basename') and req.evidence_dir:
                        evidence_path = os.path.join(req.evidence_dir, card['evidence_basename'])
                        if os.path.exists(evidence_path):
                            evidence_url = _build_media_url(evidence_path)
                    
                    model_cards.append({
                        'model_number': card.get('model_number', '?'),
                        'prediction_label': card.get('prediction_label', 'N/A'),
                        'prediction_score': card.get('prediction_score', 'N/A'),
                        'evidence_url': evidence_url,
                        'evidence_type': card.get('evidence_type'),
                        'vlm_reasoning': card.get('vlm_reasoning', ''),
                    })
            else:
                # Unexpected JSON shape — fall back to markdown
                report_to_show = report_raw
        except (json.JSONDecodeError, TypeError):
            # Old markdown format — render as before
            report_to_show = report_raw
    
    # Determine the input file type for template
    input_filename = req.input_file.name.lower() if req.input_file else ''
    is_video = any(input_filename.endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm'])
    is_image = any(input_filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'])
    
    # Parse model results for admin table
    model_results_table = []
    if is_admin:
        for result in results:
            output = result.output_json
            if isinstance(output, str):
                try:
                    output = json.loads(output)
                except:
                    output = {}
            if not isinstance(output, dict):
                output = {}
            
            model_results_table.append({
                'name': result.model_name,
                'status': result.status,
                'score': output.get('score', 'N/A'),
                'label': output.get('label', 'N/A'),
                'raw': json.dumps(output, indent=2) if output else '{}',
                'logs': result.logs or '',
                'completed_at': result.completed_at,
            })
    
    context = {
        'req': req,
        'results': results,
        'is_admin': is_admin,
        'model_cards': model_cards,
        'report_to_show': report_to_show,
        'is_video': is_video,
        'is_image': is_image,
        'model_results_table': model_results_table,
    }
    
    return render(request, 'analysis/detail.html', context)

@login_required
def admin_edit_report(request, pk):
    """Admin can edit the user-facing report before approving."""
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    req = get_object_or_404(ForensicRequest, pk=pk)
    
    if request.method == 'POST':
        edited_report = request.POST.get('user_report', '')
        req.user_report = edited_report
        
        # Handle "Save & Approve" button
        if request.POST.get('save_and_approve'):
            req.report_approved = True
            req.approved_by = request.user
            req.approved_at = timezone.now()
            req.status = 'COMPLETED'
        
        req.save()
        return redirect('request_detail', pk=pk)
    
    return render(request, 'analysis/admin_edit.html', {'req': req})

@login_required
def admin_approve_report(request, pk):
    """Admin approves the report — makes it visible to the user."""
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    if request.method == 'POST':
        req = get_object_or_404(ForensicRequest, pk=pk)
        req.report_approved = True
        req.approved_by = request.user
        req.approved_at = timezone.now()
        req.status = 'COMPLETED'
        req.save()
    
    return redirect('request_detail', pk=pk)

@login_required
def request_status_api(request, pk):
    """API endpoint for AJAX polling."""
    is_admin = request.user.is_superuser
    
    if is_admin:
        req = get_object_or_404(ForensicRequest, pk=pk)
    else:
        req = get_object_or_404(ForensicRequest, pk=pk, user=request.user)
    
    results = req.results.all()
    results_data = [{
        'model_name': r.model_name,
        'status': r.status,
        'completed_at': r.completed_at.isoformat() if r.completed_at else None
    } for r in results]
    
    # Determine report content based on role + approval
    if is_admin:
        report = req.user_report or req.report_content or ''
    elif req.report_approved:
        report = req.user_report or req.report_content or ''
    else:
        report = ''
    
    return JsonResponse({
        'id': req.id,
        'status': req.status,
        'report_content': report,
        'report_approved': req.report_approved,
        'selected_models': req.selected_models if req.selected_models else [],
        'results': results_data
    })
