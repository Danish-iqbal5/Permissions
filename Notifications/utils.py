# notifications/utils.py

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification  # optional DB model

def send_notification(user, message):
    
    Notification.objects.create(user=user, message=message)


    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "notify",
            "message": message,
        }
    )
