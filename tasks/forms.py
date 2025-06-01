from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import Task, Analysis
from users.models import CustomUser, Department


class TaskForm(forms.ModelForm):
    assigned_user = forms.CharField(
        required=False,
        label="Призначити працівнику",
        widget=forms.TextInput(attrs={
            'id': 'user-autocomplete',
            'placeholder': 'Почніть вводити ПІБ або e-mail…',
            'class': 'styled-input',
            'autocomplete': 'off',
        })
    )

    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'start_date',
            'end_date',
            'assigned_user',
            'assigned_department',
        ]
        labels = {
            'title': 'Заголовок',
            'description': 'Опис',
            'start_date': 'Початок',
            'end_date': 'Кінець',
            'assigned_user': 'Призначити працівнику',
            'assigned_department': 'Призначити відділу',
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'id': 'title-autocomplete',
                'placeholder': 'Почніть вводити назву аналізу…',
                'class': 'styled-input',
                'autocomplete': 'off',
            }),
            'description': forms.Textarea(attrs={
                'id': 'id_description',
                'rows': 3,
                'class': 'styled-textarea',
            }),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'assigned_department': forms.Select(attrs={
                'class': 'transparent-empty',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            if self.instance.assigned_user:
                user_display = f"{self.instance.assigned_user.full_name} ({self.instance.assigned_user.email})"
                self.fields['assigned_user'].widget.attrs['value'] = user_display
                self.initial['assigned_user'] = user_display
            elif self.instance.assigned_department:
                self.fields['assigned_user'].widget.attrs['value'] = ""
                self.initial['assigned_user'] = ""

    def clean_assigned_user(self):
        val = self.cleaned_data.get('assigned_user')
        if not val:
            return None

        if '(' in val and val.endswith(')'):
            email_part = val.split('(')[-1].rstrip(')')
            try:
                user = CustomUser.objects.get(email=email_part)
                return user
            except CustomUser.DoesNotExist:
                pass

        try:
            user = CustomUser.objects.get(
                Q(full_name__istartswith=val) | Q(email__istartswith=val)
            )
        except CustomUser.DoesNotExist:
            raise ValidationError("Користувача з такими даними не знайдено.")
        return user

    def clean(self):
        cleaned = super().clean()
        user = cleaned.get('assigned_user')
        dept = cleaned.get('assigned_department')
        if not user and not dept:
            raise ValidationError("Вкажіть користувача або відділ, куди призначається задача.")
        if user and dept:
            raise ValidationError("Призначайте або користувача, або відділ, а не обох одночасно.")
        return cleaned