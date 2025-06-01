from django.conf import settings
from django.db import models
from users.models import Department

class Task(models.Model):
    STATUS_CHOICES = [
        ('new', 'Не прийнято'),
        ('in_progress', 'У роботі'),
        ('completed', 'Виконано'),
        ('overdue', 'Прострочено'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date   = models.DateField()

    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="assigned_tasks"
    )
    assigned_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="department_tasks"
    )

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_tasks"
    )
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    position   = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Analysis(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name