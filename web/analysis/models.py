from django.db import models
from django.conf import settings
import os

class ForensicRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    input_file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    media_type = models.CharField(max_length=10, choices=[('image', 'Image'), ('video', 'Video')])
    selected_models = models.JSONField(default=list) # List of model names
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    report_content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Request {self.id} by {self.user.username} ({self.status})"

class AnalysisResult(models.Model):
    request = models.ForeignKey(ForensicRequest, related_name='results', on_delete=models.CASCADE)
    model_name = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default='PENDING') # SUCCESS, FAILED
    output_json = models.JSONField(blank=True, null=True)
    logs = models.TextField(blank=True, null=True)
    completed_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.model_name} for Request {self.request.id}"
