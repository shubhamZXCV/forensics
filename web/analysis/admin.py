from django.contrib import admin
from .models import ForensicRequest, AnalysisResult

class AnalysisResultInline(admin.StackedInline):
    model = AnalysisResult
    extra = 0
    readonly_fields = ('completed_at', 'logs', 'output_json')

@admin.register(ForensicRequest)
class ForensicRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'created_at', 'media_type')
    list_filter = ('status', 'media_type', 'created_at')
    search_fields = ('user__username', 'id')
    readonly_fields = ('created_at', 'report_content')
    inlines = [AnalysisResultInline]

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'request', 'model_name', 'status', 'completed_at')
    list_filter = ('status', 'model_name', 'completed_at')
    search_fields = ('request__user__username', 'model_name')
    readonly_fields = ('config', 'logs', 'output_json') if hasattr(AnalysisResult, 'config') else ('logs', 'output_json')
