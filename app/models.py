from django.db import models

class InBox(models.Model):
    EMAIL_SERVICE_CHOICES = [
        ('yandex', 'Yandex'),
        ('gmail', 'Gmail'),
        ('mail', 'Mail.ru'),
    ]

    service = models.CharField(max_length=10, choices=EMAIL_SERVICE_CHOICES)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.email


class Message(models.Model):
    inbox = models.ForeignKey(InBox, on_delete=models.CASCADE, related_name='messages')

    id = models.AutoField(primary_key=True)
    subject = models.CharField(max_length=255)
    sent_date = models.DateTimeField()
    received_date = models.DateTimeField(null=True, blank=True)
    body = models.TextField()
    uid = models.IntegerField()
    attachments = models.ManyToManyField('Attachment', blank=True)

    def __str__(self):
        return self.subject


class Attachment(models.Model):
    file = models.FileField(upload_to='attachments/')

    def __str__(self):
        return self.file.name
