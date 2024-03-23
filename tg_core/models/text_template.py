import os
from pathlib import Path

from django.conf import settings
from django.db import models

from tg_core.models.base import BaseModel

NA_MESSAGE_TEXT = 'Что-то пошло не так. Сообщите в поддержку.'


class Slugs:
    horoscope_common = 'horoscope_common'


SLUGS = [
    Slugs.horoscope_common,
]


class TemplatesManager(models.Manager):
    def get_by_slug(self, slug: str):
        template_obj, created = self.get_or_create(slug=slug)
        result = NA_MESSAGE_TEXT

        if created:
            result = template_obj
        else:
            templates_path = Path(os.path.join(settings.BASE_DIR, 'tg_core/templates/messages/'))
            for t in templates_path.iterdir():
                if t.name == f'{slug}.html':
                    result = t.open().read()
                    break

        template_obj.template = result

        template_obj.save()

        return template_obj


class TextTemplate(BaseModel):
    slugs = Slugs

    slug = models.CharField(max_length=128, unique=True, verbose_name='Уникальное имя шаблона.')
    template = models.TextField(default='', verbose_name='Шаблон сообщения в html-формате.')

    objects = TemplatesManager()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'Template {self.pk} {self.slug}'
