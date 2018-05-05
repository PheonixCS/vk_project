from django.db import models
from django.utils.encoding import smart_str
from vk_scraping_posting import config


class Setting(models.Model):
    SETTINGS_TYPES = (
        ('bool', 'bool'),
        ('str', 'str'),
        ('int', 'int'),
    )

    key = models.CharField(max_length=128, primary_key=True)
    key_type = models.CharField(max_length=32, choices=SETTINGS_TYPES)
    value = models.CharField(max_length=256)
    description = models.CharField(max_length=256, blank=True, null=True)

    @staticmethod
    def get_value(self, key):
        setting = Setting.objects.get(key=key)
        if setting.value:
            if setting.key_type == 'bool':
                if setting.value.lower() in ['true', 'false']:
                    value = setting.value.lower() == 'true'
                else:
                    value = int(setting.value) != 0
            elif setting.key_type == 'int':
                value = int(setting.value)
            elif setting.key_type == 'str':
                value = smart_str(setting.value)
        else:
            value = config.settings[key]
        return value
