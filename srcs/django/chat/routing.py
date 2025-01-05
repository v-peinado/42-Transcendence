from django.urls import re_path

from .consumers.chatconsumers import MainChatConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_name>\w+)/$", MainChatConsumer.as_asgi()),
]
