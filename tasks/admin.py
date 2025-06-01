from django.contrib import admin
from .models import Analysis


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ['name', 'description']



