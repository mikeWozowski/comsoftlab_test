import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from .views import fetch_emails

class EmailConsumer(WebsocketConsumer):
    def connect(self):
        # Присоединение к группе
        async_to_sync(self.channel_layer.group_add)("email_group", self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        # Отключение от группы
        async_to_sync(self.channel_layer.group_discard)("email_group", self.channel_name)

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        command = text_data_json.get('command')

        if command == 'start_import':
            self.send(text_data=json.dumps({
                'status': 'Progress',
                'progress': 0
            }))
            for progress in fetch_emails():
                self.send(text_data=json.dumps({
                    'status': 'Progress',
                    'progress': progress
                }))
            self.send(text_data=json.dumps({
                'status': 'Completed',
                'progress': 100
            }))

    # Обработка нового сообщения, поступившего через WebSocket
    def new_message(self, event):
        message = event['message']
        self.send(text_data=json.dumps({
            'status': 'NewMessage',
            'message': message
        }))
