import email
from email.header import decode_header

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Max
from django.http import JsonResponse
import imaplib
from .models import InBox, Message, Attachment
from .utils import check_mailbox, check_gmail, get_server_and_port


def get_mailbox_settings(request):
    try:
        inbox = InBox.objects.latest('id')
        data = {
            'email': inbox.email,
            'password': inbox.password,
            'service': inbox.service
        }
    except InBox.DoesNotExist:
        data = {
            'email': '',
            'password': '',
            'service': ''
        }

    return JsonResponse(data)


def save_mailbox_settings(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        service = request.POST.get('service')

        if not email or not password or not service:
            return JsonResponse({'message': 'Все поля обязательны для заполнения.'}, status=400)

        try:
            if service == 'gmail':
                is_valid = check_gmail(email, password)
            else:
                server, port = get_server_and_port(service)
                is_valid = check_mailbox(email, password, server, port)
        except ValueError as e:
            return JsonResponse({'message': str(e)}, status=400)

        if is_valid:
            inbox, created = InBox.objects.get_or_create(
                defaults={
                    'email': email,
                    'password': password,
                    'service': service,
                }
            )

            if not created:
                inbox.email = email
                inbox.password = password
                inbox.service = service
                inbox.save()

            return JsonResponse({'message': 'Данные успешно сохранены!'})

        return JsonResponse({'message': 'Не удалось подключиться к почтовому ящику. Проверьте введённые данные.'}, status=400)

    return JsonResponse({'message': 'Неверный метод запроса.'}, status=400)


def decode_mime_header(header):
    decoded_parts = decode_header(header)
    return ''.join(
        part.decode(encoding if encoding else 'utf-8') if isinstance(part, bytes) else part
        for part, encoding in decoded_parts
    )

def send_new_message_via_websocket(message):
    channel_layer = get_channel_layer()

    # Преобразуем дату в формат Django, если она не None
    sent_date_formatted = message.sent_date.strftime('%d.%m.%Y %H:%M:%S') if message.sent_date else ''
    received_date_formatted = message.received_date.strftime('%d.%m.%Y %H:%M:%S') if message.received_date else None

    # Обрезаем тело сообщения до 100 символов и добавляем многоточие
    body_truncated = (message.body[:100] + '...') if len(message.body) > 100 else message.body

    # Декодируем заголовок и тело сообщения
    subject_decoded = decode_mime_header(message.subject)
    body_decoded = decode_mime_header(body_truncated)

    async_to_sync(channel_layer.group_send)(
        'email_group',
        {
            'type': 'new_message',
            'message': {
                'subject': subject_decoded,
                'sent_date': sent_date_formatted,
                'received_date': received_date_formatted,
                'body': body_decoded,
                'attachments': [
                    {'file_name': attachment.file.name, 'file_url': attachment.file.url}
                    for attachment in message.attachments.all()
                ]
            }
        }
    )

def fetch_emails():
    inbox = InBox.objects.first()
    if not inbox:
        return 0

    mail = imaplib.IMAP4_SSL('imap.' + inbox.service + '.com')
    mail.login(inbox.email, inbox.password)
    mail.select('inbox')

    last_uid = Message.objects.filter(inbox=inbox).aggregate(Max('uid'))['uid__max']
    search_criteria = f'(UID {last_uid + 1}:*)' if last_uid else 'ALL'

    status, data = mail.uid('search', None, search_criteria)
    email_uids = data[0].split()

    for i, uid in enumerate(email_uids):
        status, data = mail.uid('fetch', uid, '(RFC822)')
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject = msg['subject']
        sent_date = email.utils.parsedate_to_datetime(msg['date'])
        body = ""
        attachments = []

        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True).decode()
            elif part.get_content_disposition() == 'attachment':
                filename = part.get_filename()
                attachment = Attachment.objects.create(file=filename)
                attachments.append(attachment)

        message = Message.objects.create(
            inbox=inbox,
            subject=subject,
            sent_date=sent_date,
            body=body,
            uid=int(uid)
        )
        message.attachments.set(attachments)

        # Отправляем сообщение через WebSocket немедленно
        send_new_message_via_websocket(message)

        yield int((i + 1) / len(email_uids) * 100)

    mail.logout()
    return len(email_uids)
