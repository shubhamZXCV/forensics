from celery import shared_task
from .models import ForensicRequest, AnalysisResult
from .utils import run_model_wrapper, RESTRICTED_MODELS
import json
import os
import shutil
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_forensic_request(request_id):
    try:
        logger.info(f"🚀 [Task] Starting processing for Request ID: {request_id}")
        req = ForensicRequest.objects.get(id=request_id)
        req.status = 'PROCESSING'
        
        # Create per-request evidence directory
        from django.conf import settings
        evidence_dir = os.path.join(str(settings.MEDIA_ROOT), 'evidence', f'request_{request_id}')
        os.makedirs(evidence_dir, exist_ok=True)
        req.evidence_dir = evidence_dir
        
        # Copy the uploaded file into the evidence directory
        input_filename = os.path.basename(req.input_file.path)
        evidence_input_path = os.path.join(evidence_dir, input_filename)
        if not os.path.exists(evidence_input_path):
            shutil.copy2(req.input_file.path, evidence_input_path)
        
        req.save()
        
        all_results = {}
        
        # Security check: Filter out restricted models for non-admin users
        models_to_run = req.selected_models
        if not req.user.is_superuser:
            models_to_run = [m for m in models_to_run if m not in RESTRICTED_MODELS]
            logger.info(f"🔐 [Task] Non-admin user. Running: {models_to_run}")
        
        for model_name in models_to_run:
            logger.info(f"🔍 [Task] Running model: {model_name}")
            
            # Create a PROCESSING result so the UI knows which stage is active
            result_obj = AnalysisResult.objects.create(
                request=req,
                model_name=model_name,
                status='PROCESSING'
            )
            
            # Pass evidence_dir as output_dir for GradCAM/mask outputs
            success, output, logs = run_model_wrapper(
                model_name, req.input_file.path, output_dir=evidence_dir
            )
            
            status = 'SUCCESS' if success else 'FAILED'
            logger.info(f"✅ [Task] Model {model_name} finished with status: {status}")
            
            result_obj.status = status
            result_obj.output_json = output
            result_obj.logs = logs
            result_obj.save()
            
            if success and output:
                all_results[model_name] = output
        
        # VLM Report Generation — single sanitized user report
        logger.info("🤖 [Task] Starting VLM Report Generation (user report)...")
        vlm_result_obj = AnalysisResult.objects.create(
            request=req,
            model_name="VLM Report Generation",
            status='PROCESSING'
        )
        
        from .report_generators import RemoteOllamaReportGenerator
        generator = RemoteOllamaReportGenerator()
        
        try:
            user_report = generator.generate(
                all_results, 
                input_path=req.input_file.path,
                evidence_dir=evidence_dir
            )
            vlm_result_obj.status = 'SUCCESS'
            # Look for errors in the string if it contains API Error
            if "[API Error:" in user_report:
                vlm_result_obj.logs = "Encountered API Error during generation."
                vlm_result_obj.status = 'FAILED'
            vlm_result_obj.save()
        except Exception as e:
            vlm_result_obj.status = 'FAILED'
            vlm_result_obj.logs = str(e)
            vlm_result_obj.save()
            raise e
        
        req.user_report = user_report
        req.report_content = user_report  # backward compat
        
        # Set to REVIEW — admin must approve before user sees it
        req.status = 'REVIEW'
        req.report_approved = False
        req.save()
        logger.info(f"📋 [Task] Request {request_id} ready for admin review.")
        
    except ForensicRequest.DoesNotExist:
        logger.error(f"❌ [Task] Request {request_id} not found.")
        pass
    except Exception as e:
        logger.error(f"❌ [Task] Error processing request {request_id}: {e}", exc_info=True)
        if 'req' in locals():
            req.status = 'FAILED'
            req.report_content = f"Error during processing: {str(e)}"
            req.save()
