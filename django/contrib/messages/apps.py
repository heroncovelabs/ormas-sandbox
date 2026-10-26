from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MessagesConfig(AppConfig):
    name = 'django.contrib.messages'
    verbose_name = _("Messages")

    def ready(self):
        from django.core.signals import setting_changed

        setting_changed.connect(update_level_tags)


def update_level_tags(setting, **kwargs):
    """
    Refresh the cached message level tags when MESSAGE_TAGS changes, e.g.
    through override_settings() in tests (on entry and on restoration).
    """
    if setting == 'MESSAGE_TAGS':
        from django.contrib.messages.storage import base
        from django.contrib.messages.utils import get_level_tags

        base.LEVEL_TAGS = get_level_tags()
