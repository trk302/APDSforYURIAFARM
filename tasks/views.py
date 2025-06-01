import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_POST
from users.models import CustomUser, Department
from .models import Task, Analysis
from .forms import TaskForm
from django.db import transaction
from django.conf import settings


logger = logging.getLogger(__name__)


@login_required
def task_dashboard(request):
    user = request.user

    inbox_tasks = Task.objects.filter(
        Q(assigned_user=user) |
        Q(assigned_department=user.department)
    ).exclude(status='completed').order_by('-start_date')

    today = timezone.now().date()
    with transaction.atomic():
        for task in inbox_tasks:
            if task.status != 'overdue' and task.end_date < today:
                task.status = 'overdue'
                task.save()

    if user.role in ['admin', 'manager']:
        sent_tasks = Task.objects.filter(creator=user).order_by('-start_date')
    else:
        sent_tasks = Task.objects.none()

    return render(request, 'tasks/task_dashboard.html', {
        'inbox_tasks': inbox_tasks,
        'sent_tasks': sent_tasks,
        'user': user
    })


@login_required
def create_task(request):
    form = TaskForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        task = form.save(commit=False)
        task.creator = request.user
        task.save()
        messages.success(request, 'Задачу створено.')
        return redirect('task_dashboard')
    return render(request, "tasks/create_task.html", {"form": form})


@login_required
def task_events(request):
    user = request.user
    qs = Task.objects.filter(
        Q(assigned_user=user) | Q(assigned_department=user.department)
    ).exclude(status='completed')

    events = [{
        'title': t.title,
        'start': t.start_date.isoformat(),
        'end': t.end_date.isoformat(),
        'description': t.description,
        'color': get_task_color(t.status),
        'borderColor': get_task_border_color(t.status),
    } for t in qs]

    return JsonResponse(events, safe=False)


@login_required
def task_sent_events(request):
    if request.user.role not in ['admin', 'manager']:
        return JsonResponse([], safe=False)

    qs = Task.objects.filter(creator=request.user)

    events = [{
        'title': f"{t.title} → {get_task_email_only(t)}",
        'start': t.start_date.isoformat(),
        'end': t.end_date.isoformat(),
        'description': (
            f"Опис: {t.description}\n"
            f"Статус: {t.get_status_display()}"
        ),
        'color': get_task_color(t.status),
        'borderColor': get_task_border_color(t.status),
    } for t in qs]

    return JsonResponse(events, safe=False)


def get_task_color(status):
    return {
        'new': '#d0f0ff',
        'in_progress': '#fff5cc',
        'completed': '#d2f5c4',
        'overdue': '#ffd4d4',
    }.get(status, '#ffffff')

def get_task_border_color(status):
    return {
        'new': '#62BAEE',
        'in_progress': '#DCE476',
        'completed': '#9AE476',
        'overdue': '#EE8080',
    }.get(status, '#999')

def get_task_email_only(task):
    if task.assigned_user:
        return f"{task.assigned_user.email}"
    elif task.assigned_department:
        return f"Відділ: {task.assigned_department.name}"
    return "Не вказано"


@login_required
def update_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.user.role not in ['admin', 'manager']:
        return redirect('task_dashboard')

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            old_assigned_user = task.assigned_user
            old_assigned_department = task.assigned_department

            updated_task = form.save(commit=False)

            if form.cleaned_data.get('assigned_user'):
                updated_task.assigned_department = None
            elif form.cleaned_data.get('assigned_department'):
                updated_task.assigned_user = None

            new_assigned_user = updated_task.assigned_user
            new_assigned_department = updated_task.assigned_department

            if (old_assigned_user != new_assigned_user or
                    old_assigned_department != new_assigned_department):
                updated_task.status = 'new'

            updated_task.save()
            messages.success(request, 'Задачу оновлено.')
            return redirect('task_dashboard')
        else:
            messages.error(request, 'Форма містить помилки.')
    else:
        form = TaskForm(instance=task)

    return render(request, 'tasks/update_task.html', {'form': form, 'task': task})


@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.user.role not in ['admin', 'manager']:
        return redirect('task_dashboard')

    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Задачу видалено.')
        return redirect('task_dashboard')

    return render(request, 'tasks/delete_task.html', {'task': task})


@login_required
def email_autocomplete(request):
    if 'term' in request.GET:
        term = request.GET.get('term').strip()
        users = CustomUser.objects.filter(
            Q(full_name__istartswith=term) | Q(email__istartswith=term)
        )
        results = [{
            'label': f'{user.full_name} ({user.email})',
            'value': user.email
        } for user in users]
        return JsonResponse(results, safe=False)

    return JsonResponse([], safe=False)



@login_required
def analysis_autocomplete(request):
    term = request.GET.get('term', '').strip()
    if not term:
        return JsonResponse([], safe=False)

    # Пошук тільки з початку назви (case-insensitive)
    analyses = Analysis.objects.filter(name__istartswith=term)[:10]

    results = [{
        'label': a.name,
        'description': a.description
    } for a in analyses]

    return JsonResponse(results, safe=False)


@login_required
def get_analysis_description(request):
    analysis_id = request.GET.get('id')
    try:
        analysis = Analysis.objects.get(id=analysis_id)
        return JsonResponse({'description': analysis.description})
    except Analysis.DoesNotExist:
        return JsonResponse({'description': ''})


@login_required
@require_POST
def update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if task.assigned_user != request.user:
        return JsonResponse({'error': 'Ви не маєте права змінювати статус цієї задачі.'}, status=403)

    new_status = request.POST.get('status')
    if new_status not in ['in_progress', 'completed']:
        return JsonResponse({'error': 'Недопустимий статус.'}, status=400)

    task.status = new_status
    task.save()
    return JsonResponse({'success': True, 'new_status': task.status})


@login_required
@require_POST
def take_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if not (
        task.assigned_user == request.user or
        (task.assigned_department == request.user.department and request.user.role == 'manager')
    ):
        messages.error(request, "Ви не можете прийняти в роботу цю задачу.")
        return redirect('task_dashboard')

    task.status = 'in_progress'
    task.save()
    messages.success(request, "Задачу прийнято в роботу.")
    return redirect('task_dashboard')


@login_required
@require_POST
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if not (
        task.assigned_user == request.user or
        (task.assigned_department == request.user.department and request.user.role == 'manager')
    ):
        messages.error(request, "Ви не можете завершити цю задачу.")
        return redirect('task_dashboard')

    task.status = 'completed'
    task.save()
    messages.success(request, "Задачу завершено.")
    return redirect('task_dashboard')


@login_required
def check_user_exists(request):
    email = request.GET.get('email', None)
    if email:
        user_exists = CustomUser.objects.filter(email=email).exists()
        return JsonResponse({'exists': user_exists})
    return JsonResponse({'error': 'Email not provided'}, status=400)
