from django.contrib import admin
from .models import ModerationRule, Filter, Token
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



@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ('app_id', 'is_community_token', 'access_token_lifetime')
    fields = ('app_id', 'access_token', 'refresh_token', 'access_token_lifetime', 'is_community_token')
    readonly_fields = ('access_token_lifetime',)  # если нужно, чтобы время жизни токена не редактировалось
    search_fields = ('app_id',)
    list_filter = ('is_community_token',)


admin.site.register(Filter, FilterAdmin)
admin.site.register(ModerationRule)
