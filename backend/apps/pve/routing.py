from django.urls import re_path

from .consumers import PVEConsoleConsumer, LXCConsoleConsumer, SSHConsoleConsumer

websocket_urlpatterns = [
    re_path(r'^ws/pve/console/(?P<vm_id>\d+)/$', PVEConsoleConsumer.as_asgi()),
    re_path(r'^ws/lxc/console/(?P<container_id>\d+)/$', LXCConsoleConsumer.as_asgi()),
    re_path(r'^ws/ssh/(?P<container_id>\d+)/$', SSHConsoleConsumer.as_asgi()),
]
