from django.db import models


class User(models.Model):
    login = models.CharField(max_length=64, verbose_name='Логин', unique=True)
    password = models.CharField(max_length=64, verbose_name='Пароль')
    url = models.URLField(max_length=128, verbose_name='Ссылка', blank=True, default='')
    domain_or_id = models.CharField(max_length=128, verbose_name='Domain/id пользователя', blank=True, default='')
    initials = models.CharField(max_length=128, verbose_name='ФИО', blank=True, default='')
    app_id = models.CharField(max_length=256, verbose_name='ID приложения', null=True)
    two_factor = models.BooleanField(verbose_name='Двухфакторная аутентификация', default=False)
    is_authed = models.BooleanField(default=False)

    access_token = models.CharField(
        max_length=256,
        verbose_name='Пользовательский Access token',
        blank=True,
        null=True,
    )

    def save(self, *args, **kwargs):
        if not self.url:
            if self.domain_or_id.isdigit():
                self.url = 'https://vk.com/id{}'.format(self.domain_or_id)
            elif self.domain_or_id:
                self.url = 'https://vk.com/{}'.format(self.domain_or_id)
        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return '{} {}'.format(self.login, self.initials)

    class Meta:
        verbose_name = 'Администратор'
        verbose_name_plural = 'Администраторы'
