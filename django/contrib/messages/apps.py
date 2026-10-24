from django.apps import AppConfig
from django.core.signals import setting_changed
from django.utils.translation import gettext_lazy as _


def update_level_tags(setting, **kwargs):
    """Update the cached level tags when the MESSAGE_TAGS setting changes."""
    if setting == 'MESSAGE_TAGS':
        from django.contrib.messages.storage import base
        from django.contrib.messages.utils import get_level_tags

        base.LEVEL_TAGS = get_level_tags()


class MessagesConfig(AppConfig):
    name = 'django.contrib.messages'
    verbose_name = _("Messages")

    def ready(self):
        setting_changed.connect(update_level_tags)
