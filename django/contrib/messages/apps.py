from django.apps import AppConfig
from django.core.signals import setting_changed
from django.utils.translation import gettext_lazy as _


def update_level_tags(setting, **kwargs):
    """Refresh cached level tags when MESSAGE_TAGS changes."""
    if setting == 'MESSAGE_TAGS':
        from django.contrib.messages import utils
        from django.contrib.messages.storage import base

        base.LEVEL_TAGS = utils.get_level_tags()


class MessagesConfig(AppConfig):
    name = 'django.contrib.messages'
    verbose_name = _("Messages")

    def ready(self):
        setting_changed.connect(update_level_tags)
