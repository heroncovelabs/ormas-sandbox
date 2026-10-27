from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MessagesConfig(AppConfig):
    name = 'django.contrib.messages'
    verbose_name = _("Messages")

    def ready(self):
        from django.contrib.messages.storage import base
        from django.contrib.messages.utils import get_level_tags
        from django.core.signals import setting_changed

        def update_level_tags(sender, setting, **kwargs):
            if setting == 'MESSAGE_TAGS':
                base.LEVEL_TAGS = get_level_tags()

        setting_changed.connect(
            update_level_tags,
            # Keep the local receiver alive after ready() returns.
            weak=False,
            dispatch_uid='django.contrib.messages.update_level_tags',
        )
