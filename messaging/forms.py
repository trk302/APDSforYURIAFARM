from django import forms
from .models import Message, Chat
from users.models import CustomUser
from django.forms.widgets import ClearableFileInput

class NoClearFileInput(ClearableFileInput):
    show_clear_checkbox = False

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["is_initial"] = False
        context["widget"]["initial_text"] = ""
        context["widget"]["clear_checkbox_label"] = ""
        context["widget"]["show_clear_checkbox"] = False
        return context


class MessageForm(forms.ModelForm):
    receiver = forms.CharField(
        label="Одержувач (email)",
        widget=forms.TextInput(attrs={
            'id': 'id_receiver',
            'autocomplete': 'off'
        })
    )

    class Meta:
        model = Message
        fields = ['receiver', 'subject', 'body', 'attachment']
        widgets = {
            'subject': forms.TextInput(attrs={'placeholder': 'Введіть тему'}),
            'body': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Введіть текст повідомлення'}),
            'attachment': NoClearFileInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, readonly_subject=False, **kwargs):
        super().__init__(*args, **kwargs)
        if readonly_subject:
            self.fields['subject'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("receiver")
        try:
            user = CustomUser.objects.get(email=email)
            cleaned_data["receiver"] = user
        except CustomUser.DoesNotExist:
            self.add_error("receiver", "Користувача з такою електронною адресою не знайдено.")
        return cleaned_data


class ChatForm(forms.ModelForm):
    participants_email = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Email користувача', 'autocomplete': 'off'}),
        required=False,
        label="Додати учасників за email"
    )

    participants = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Учасники чату'
    )

    class Meta:
        model = Chat
        fields = ['name', 'participants', 'participants_email']
