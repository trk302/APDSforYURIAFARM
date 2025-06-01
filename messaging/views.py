from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from users.models import CustomUser
from .forms import MessageForm, ChatForm
from .models import Message, Chat, ChatMessage
from django.db.models import Q
import re
from django.utils import timezone

@login_required
def inbox(request):
    user = request.user
    tab = request.GET.get('tab', 'inbox')
    search = request.GET.get('search', '').strip()
    date_sort = request.GET.get('date_sort')
    message_type = request.GET.get('message_type')

    inbox_messages = Message.objects.filter(receiver=user)
    sent_messages = Message.objects.filter(sender=user)

    if tab == 'inbox' and search:
        inbox_messages = inbox_messages.filter(subject__icontains=search)
    elif tab == 'sent' and search:
        sent_messages = sent_messages.filter(subject__icontains=search)

    if message_type == 'normal':
        inbox_messages = inbox_messages.exclude(subject__istartswith="Re:")
        sent_messages = sent_messages.exclude(subject__istartswith="Re:")
    elif message_type == 'reply':
        inbox_messages = inbox_messages.filter(subject__istartswith="Re:")
        sent_messages = sent_messages.filter(subject__istartswith="Re:")

    if date_sort == 'newest':
        inbox_messages = inbox_messages.order_by('-timestamp')
        sent_messages = sent_messages.order_by('-timestamp')
    elif date_sort == 'oldest':
        inbox_messages = inbox_messages.order_by('timestamp')
        sent_messages = sent_messages.order_by('timestamp')

    return render(request, 'messaging/inbox.html', {
        'inbox_messages': inbox_messages,
        'sent_messages': sent_messages,
        'active_tab': tab,
        'search_query': search
    })


@login_required
def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            receiver = form.cleaned_data['receiver']

            if receiver == request.user:
                messages.error(request, 'Неможливо відправити повідомлення самому собі.')
                return redirect('send_message')

            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = receiver
            message.save()

            messages.success(request, 'Повідомлення надіслано успішно.')
            return redirect('inbox')
    else:
        form = MessageForm()

    return render(request, 'messaging/send_message.html', {'form': form})

@login_required
def view_message(request, message_id):
    message = get_object_or_404(
        Message.objects.filter(
            id=message_id,
        ).filter(
            Q(receiver=request.user) | Q(sender=request.user)
        )
    )
    return render(request, 'messaging/view_message.html', {'message': message})

@login_required
def email_autocomplete(request):
    if 'term' in request.GET:
        search_term = request.GET.get('term').strip()
        users = CustomUser.objects.filter(
            Q(full_name__istartswith=search_term) |
            Q(email__istartswith=search_term)
        )

        emails = [{
            'label': f'{user.full_name} ({user.email})',
            'value': user.email
        } for user in users]

        return JsonResponse(emails, safe=False)

    return JsonResponse([], safe=False)


@login_required
def subject_autocomplete(request):
    term = request.GET.get('term', '').strip().lower()
    mode = request.GET.get('mode', 'inbox')

    messages_qs = Message.objects.filter(receiver=request.user) if mode == 'inbox' \
        else Message.objects.filter(sender=request.user)

    subjects = messages_qs.values_list('subject', flat=True).distinct()
    results = []

    for subj in subjects:
        clean = re.sub(r'^(Re:\s*)+', '', subj, flags=re.IGNORECASE).strip().lower()
        if term in clean:
            results.append(subj)
            if len(results) >= 10:
                break

    return JsonResponse(results, safe=False)

@login_required
def subject_autocomplete_sent(request):
    if 'term' in request.GET:
        term = request.GET.get('term')
        subjects = Message.objects.filter(
            subject__icontains=term,
            sender=request.user
        ).values_list('subject', flat=True).distinct()[:10]

        return JsonResponse(list(subjects), safe=False)
    return JsonResponse([], safe=False)

@login_required
def received_messages(request):
    received_msgs = Message.objects.filter(receiver=request.user).order_by('-sent_at')
    return render(request, 'messaging/messages.html', {'received_messages': received_msgs})

@login_required
def sent_messages(request):
    sent_msgs = Message.objects.filter(sender=request.user).order_by('-sent_at')
    return render(request, 'messaging/messages.html', {'sent_messages': sent_msgs})


@login_required
def edit_message(request, message_id):
    message = get_object_or_404(Message, id=message_id, sender=request.user)
    old_attachment = message.attachment

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES, instance=message)

        if form.is_valid():
            updated_message = form.save(commit=False)

            if 'attachment' not in request.FILES:
                updated_message.attachment = old_attachment

            updated_message.save()
            form.save_m2m()

            messages.success(request, 'Повідомлення оновлено.')
            return redirect('inbox')
    else:
        form = MessageForm(
            instance=message,
            initial={'receiver': message.receiver.email}
        )

    return render(request, 'messaging/edit_message.html', {'form': form, 'message': message})

@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id, sender=request.user)
    if request.method == 'POST':
        message.delete()
        messages.success(request, 'Повідомлення видалено.')
        return redirect('inbox')
    return render(request, 'messaging/delete_message.html', {'message': message})


@login_required
def reply_message(request, message_id):
    original_message = get_object_or_404(Message, id=message_id)
    initial_subject = "Re: " + original_message.subject

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES, readonly_subject=True)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.sender = request.user
            reply.receiver = CustomUser.objects.get(email=request.POST.get('receiver'))
            reply.subject = initial_subject  # 🛡 Захист від змін
            reply.save()
            messages.success(request, "Відповідь надіслано.")
            return redirect('inbox')
    else:
        form = MessageForm(
            initial={
                'subject': initial_subject,
                'receiver': original_message.sender.email
            },
            readonly_subject=True
        )

    return render(request, 'messaging/reply_message.html', {
        'form': form,
        'original_message': original_message
    })


@login_required
def create_chat(request):
    if request.method == 'POST':
        form = ChatForm(request.POST)
        if form.is_valid():
            chat = form.save(commit=False)
            chat.creator = request.user
            chat.is_group = True
            chat_name = request.POST.get('chat_name', '').strip()
            if chat_name:
                chat.name = chat_name
                chat.save()
                form.save_m2m()

            participants_emails = request.POST.get('receiver_email', '').strip()
            if participants_emails:
                email_list = [email.strip() for email in participants_emails.split(',') if email.strip()]

                for email in email_list:
                    try:
                        receiver = CustomUser.objects.get(email=email)

                        if receiver == request.user:
                            messages.error(request, 'Ви не можете додати себе до чату.')
                            chat.delete()
                            return redirect('create_chat')

                        chat.participants.add(receiver)

                    except CustomUser.DoesNotExist:
                        messages.error(request, f'Користувача з email {email} не знайдено.')
                        chat.delete()
                        return redirect('create_chat')

            chat.participants.add(request.user)
            messages.success(request, 'Чат успішно створено.')

            return redirect('chat_detail', chat_id=chat.id)
    else:
        form = ChatForm()
    return render(request, 'messaging/create_chat.html', {'form': form})


@login_required
def chat_list(request):
    chats = request.user.chats.all()

    chat_list = []
    for chat in chats:
        last_message = chat.messages.select_related('sender').order_by('-timestamp').first()

        chat_data = {
            'chat': chat,
            'last_message': last_message,
            'last_message_sender': last_message.sender if last_message else None,
            'last_message_time': last_message.timestamp if last_message else chat.created_at,
            'sort_time': last_message.timestamp if last_message else chat.created_at
        }
        chat_list.append(chat_data)

    chat_list.sort(key=lambda x: x['sort_time'], reverse=True)

    sorted_chats = []
    for item in chat_list:
        chat = item['chat']
        chat.last_message = item['last_message']
        chat.last_message_sender = item['last_message_sender']
        chat.last_message_time = item['last_message_time']
        sorted_chats.append(chat)

    return render(request, 'messaging/chat_list.html', {'chats': sorted_chats})


@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    messages_in_chat = chat.messages.select_related('sender').order_by('timestamp')
    return render(request, 'messaging/chat_detail.html', {
        'chat': chat,
        'messages': messages_in_chat,
    })


@login_required
def edit_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if request.user not in chat.participants.all():
        return redirect('chat_list')

    if request.method == 'POST':
        chat_name = request.POST.get('chat_name', '').strip()
        if chat_name:
            chat.name = chat_name
            chat.save()

        new_participants_emails = request.POST.get('receiver_email', '').strip()
        if new_participants_emails:
            email_list = [email.strip() for email in new_participants_emails.split(',') if email.strip()]

            for email in email_list:
                try:
                    user = CustomUser.objects.get(email=email)
                    if user not in chat.participants.all():
                        chat.participants.add(user)
                except CustomUser.DoesNotExist:
                    messages.error(request, f'Користувача з email {email} не знайдено.')

        removed_participants_emails = request.POST.get('removed_participants', '').strip()
        if removed_participants_emails:
            email_list = [email.strip() for email in removed_participants_emails.split(',') if email.strip()]

            for email in email_list:
                try:
                    user = CustomUser.objects.get(email=email)
                    # Не дозволяємо видалити автора чату
                    if user != chat.creator and user in chat.participants.all():
                        chat.participants.remove(user)
                except CustomUser.DoesNotExist:
                    pass  # Ігноруємо, якщо користувача не існує

        messages.success(request, 'Чат успішно оновлено.')
        return redirect('chat_detail', chat_id=chat.id)

    return render(request, 'messaging/edit_chat.html', {'chat': chat})


@login_required
def delete_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if request.user not in chat.participants.all():
        return redirect('chat_list')

    if request.method == 'POST':
        chat.delete()
        messages.success(request, 'Чат видалено.')
        return redirect('chat_list')
    return render(request, 'messaging/delete_chat.html', {'chat': chat})


@login_required
def leave_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if request.user in chat.participants.all():
        chat.participants.remove(request.user)
        messages.info(request, 'Ви покинули чат.')
    return redirect('chat_list')


@require_POST
@login_required
def send_chat_message(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            ChatMessage.objects.create(
                room=chat,
                sender=request.user,
                content=body
            )

    return redirect('chat_detail', chat_id=chat.id)


@login_required
def check_user_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            return JsonResponse({'exists': True})
        except CustomUser.DoesNotExist:
            return JsonResponse({'exists': False})
