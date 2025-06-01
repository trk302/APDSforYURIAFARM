from django.db import models
from users.models import CustomUser
from django.contrib.auth import get_user_model

User = get_user_model()

class Chat(models.Model):
    name = models.CharField(max_length=255, blank=True)
    participants = models.ManyToManyField(User, related_name='chats')
    is_group = models.BooleanField(default=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_chats')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name if self.name else f"Чат {self.id}"

class Message(models.Model):
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Відправник'
    )
    receiver = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name='Одержувач'
    )
    subject = models.CharField('Тема', max_length=255)
    body = models.TextField('Текст')
    attachment = models.FileField('Вкладення', upload_to='attachments/', null=True, blank=True)
    timestamp = models.DateTimeField('Дата та час', auto_now_add=True)
    is_read = models.BooleanField('Прочитано', default=False)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Повідомлення'
        verbose_name_plural = 'Повідомлення'

    def __str__(self):
        return f'Лист від {self.sender.email} до {self.receiver.email} — {self.subject}'

    @property
    def short_body(self):
        return (self.body[:50] + '...') if len(self.body) > 50 else self.body

class ChatMessage(models.Model):
    room = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.email} > {self.room.name or self.room.id}: {self.content[:30]}"
