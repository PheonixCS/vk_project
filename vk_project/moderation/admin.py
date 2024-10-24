from django.contrib import admin
from .models import ModerationRule, Filter
from django import forms
import ast
import logging

log = logging.getLogger('moderation.core.checks')


# Форма для добавления ключевиков через админку
class FilterAdminForm(forms.ModelForm):
    class Meta:
        model = Filter
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        answers_file = cleaned_data.get("answers")

        # Проверяем, что файл имеет расширение .txt
        if answers_file and not answers_file.name.endswith('.txt'):
            raise forms.ValidationError("Пожалуйста, загрузите файл формата .txt.")
        # Проверка на корректный формат файла
        try:
            content = answers_file.read().decode('utf-8')
            try:
                content = content.strip()
                sentences = ast.literal_eval(content)  # Преобразуем строку в список
            except (SyntaxError, ValueError):
                variables = {
                    'grouplink': 'http://example.com'  # Такие же замены
                }
                sentences = eval(content, {"__builtins__": {}}, variables)

        except:  # Перехватываем возможные ошибки
            log.info('error format')
            raise forms.ValidationError("неверный формат файла")
        return cleaned_data


class FilterAdmin(admin.ModelAdmin):
    form = FilterAdminForm


admin.site.register(Filter, FilterAdmin)
admin.site.register(ModerationRule)
