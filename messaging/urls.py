from django.urls import path
from . import views

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('send/', views.send_message, name='send_message'),
    path('view/<int:message_id>/', views.view_message, name='view_message'),
    path('email-autocomplete/', views.email_autocomplete, name='email_autocomplete'),
    path('subject-autocomplete/', views.subject_autocomplete, name='subject_autocomplete'),
    path('autocomplete/sent/', views.subject_autocomplete_sent, name='subject_autocomplete_sent'),
    path('received/', views.received_messages, name='received_messages'),
    path('sent/', views.sent_messages, name='sent_messages'),
    path('reply/<int:message_id>/', views.reply_message, name='reply_message'),
    path('edit/<int:message_id>/', views.edit_message, name='edit_message'),
    path('delete/<int:message_id>/', views.delete_message, name='delete_message'),
    path('chats/', views.chat_list, name='chat_list'),
    path('chats/create/', views.create_chat, name='create_chat'),
    path('chats/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('chats/<int:chat_id>/edit/', views.edit_chat, name='edit_chat'),
    path('chats/<int:chat_id>/delete/', views.delete_chat, name='delete_chat'),
    path('chats/<int:chat_id>/leave/', views.leave_chat, name='leave_chat'),
    path('chats/<int:chat_id>/send/', views.send_chat_message, name='send_chat_message'),
    path('check_user_email/', views.check_user_email, name='check_user_email'),
]
