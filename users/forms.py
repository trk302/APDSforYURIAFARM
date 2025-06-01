from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Department
from django.forms.widgets import ClearableFileInput

class NoClearableFileInput(ClearableFileInput):
    show_clear_checkbox = False

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["is_initial"] = False
        context["widget"]["initial_text"] = ""
        context["widget"]["clear_checkbox_label"] = ""
        return context

class CustomUserCreationForm(UserCreationForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label='Виберіть відділ',
        label='Відділ',
        widget=forms.Select(attrs={
            'class': 'form-control department-select',
            'required': 'required',
        })
    )

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'phone_number', 'department', 'photo']
        labels = {
            'full_name': 'ПІБ',
            'email': 'Електронна пошта',
            'phone_number': 'Номер телефону',
            'photo': 'Фото',
        }
        widgets = {
            'photo': NoClearableFileInput(attrs={'class': 'form-control'})
        }

class CustomUserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'phone_number', 'department', 'position', 'photo']
        labels = {
            'full_name': 'ПІБ',
            'email': 'Електронна пошта',
            'phone_number': 'Номер телефону',
            'position': 'Посада',
            'photo': 'Фото',
        }
        widgets = {
            'photo': NoClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)

        if not (self.request_user and self.request_user.role == 'admin'):
            self.fields['department'].disabled = True
            self.fields['department'].initial = self.instance.department
            self.fields['position'].disabled = True
            self.fields['position'].initial = 'Почекайте, поки адміністратор змінить'
