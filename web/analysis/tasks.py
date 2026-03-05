from celery import shared_task
from .models import ForensicRequest, AnalysisResult
from .utils import run_model_wrapper, RESTRICTED_MODELS
# from .llm import generate_report # To be implemented
import json

import logging

logger = logging.getLogger(__name__)

@shared_task
def process_forensic_request(request_id):
    try:
        logger.info(f"🚀 [Task] Starting processing for Request ID: {request_id}")
        req = ForensicRequest.objects.get(id=request_id)
        req.status = 'PROCESSING'
        req.save()
        
        all_results = {}
        
        # Security check: Filter out restricted models for non-admin users
        models_to_run = req.selected_models
        if not req.user.is_superuser:
            models_to_run = [m for m in models_to_run if m not in RESTRICTED_MODELS]
            logger.info(f"🔐 [Task] Non-admin user detected. Filtered out restricted models. Running: {models_to_run}")
        
        for model_name in models_to_run:
            logger.info(f"🔍 [Task] Running model: {model_name}")
            
            # Create Model Log
            # result_obj = AnalysisResult.objects.create(request=req, model_name=model_name, status='PROCESSING')
            
            success, output, logs = run_model_wrapper(model_name, req.input_file.path)
            
            status = 'SUCCESS' if success else 'FAILED'
            logger.info(f"✅ [Task] Model {model_name} finished with status: {status}")
            
            AnalysisResult.objects.create(
                request=req,
                model_name=model_name,
                status=status,
                output_json=output,
                logs=logs
            )
            
            if success and output:
                all_results[model_name] = output
        
        # LLM Generation
        logger.info("🤖 [Task] Starting VLM Report Generation...")
        
        # Switch to Remote Ollama VLM (OpenAI-compatible)
        from .report_generators import RemoteOllamaReportGenerator
        generator = RemoteOllamaReportGenerator()
        
        report = generator.generate(all_results, input_path=req.input_file.path)
        req.report_content = report
        
        req.status = 'COMPLETED'
        req.save()
        logger.info(f"✨ [Task] Request {request_id} completed successfully.")
        
    except ForensicRequest.DoesNotExist:
        logger.error(f"❌ [Task] Request {request_id} not found.")
        pass
    except Exception as e:
        logger.error(f"❌ [Task] Error processing request {request_id}: {e}", exc_info=True)
        if 'req' in locals():
            req.status = 'FAILED'
            req.report_content = f"Error during processing: {str(e)}"
            req.save()
