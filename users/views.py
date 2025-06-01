from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, CustomUserUpdateForm
from .models import CustomUser
from django.contrib import messages


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'employee'
            user.position = ''
            user.department = None
            user.save()
            login(request, user)
            return redirect('task_dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('profile')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})


@login_required
def profile_view(request):
    return render(request, 'users/profile.html', {'user': request.user})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def edit_profile_view(request):
    user = request.user

    if request.method == 'POST':
        form = CustomUserUpdateForm(
            request.POST,
            request.FILES,
            instance=user,
            request_user=request.user
        )
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = CustomUserUpdateForm(
            instance=user,
            request_user=request.user
        )

    return render(request, 'users/edit_profile.html', {
        'form': form
    })
