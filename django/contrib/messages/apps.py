from django.apps import AppConfig
from django.core.signals import setting_changed
from django.utils.translation import gettext_lazy as _


class MessagesConfig(AppConfig):
    name = 'django.contrib.messages'
    verbose_name = _("Messages")

    def ready(self):
        setting_changed.connect(self._update_level_tags)

    @staticmethod
    def _update_level_tags(setting, **kwargs):
        if setting == 'MESSAGE_TAGS':
            from django.contrib.messages.storage import base
            from django.contrib.messages.utils import get_level_tags
            base.LEVEL_TAGS = get_level_tags()
