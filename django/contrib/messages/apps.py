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
        from django.contrib.messages.storage import base
        from django.contrib.messages import utils

        if setting == 'MESSAGE_TAGS':
            base.LEVEL_TAGS = utils.get_level_tags()
