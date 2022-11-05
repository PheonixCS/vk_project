# Документация по боту
Адрес админки: http://80.211.178.81/admin

## Установка
Вам понадобится:

* python > 3.7
* postgresql > 10

Далее активируйте виртуальное окружение (любое, какое нравится: venv, pyenv, pipenv, conda...):

```shell
pip3 install -r requirements.txt --no-deps

```

### Подготовка к запуску

Подготовка БД:
```sql
CREATE DATABASE vk_db;

CREATE USER vk_bot WITH PASSWORD '123qwe';

GRANT ALL PRIVILEGES ON DATABASE vk_db TO vk_bot;
```


Для правильной работы нужны переменные окружения:
```shell
export DB_NAME='vk_db'
export DB_PASSWORD='123qwe'
export DB_LOGIN='vk_bot'
export DB_HOST='localhost'
export DB_PORT='5432'
export SERVER_ROLE='test'
```

Необходимо сделать миграции

```shell
python3 manage.py migrate
```

И создать суперюзера:

```shell
python3 manage.py createsuperuser

```

И круто бы собрать статику:

```shell
python3 manage.py collectstatic

```

### Запуск
```shell
python3 manage.py runserver
```

И можно заходить на https://127.0.0.1:8000

###Тестирование
> Тесты - они как секс. Если он есть, но мало - это лучше, если бы его совсем не было.  

На какие-то функции сделаны тесты. Они были не сразу, в последствии на каждую новую функцию старались делать тест.
Также и на баги делали тесты.

Запуск простой: 

```shell
pytest
```

### Логи в telegram
Можно активировать зендлер для телеграма в логинге

Нужно будет добавить токены:
```shell
TELEGRAM_TOKEN
TELEGRAM_CHAT_ID
```

## Полезные команды

### Сервер
На сервере всё завязано на одном мейкфайле. Так что просто в корне проекта выполяем команду `make` и у нас всё перезагружается.

### Логи на сервере
Они хранятся в папке `/var/log/vk_sp_logs/`. Грепать удобно

Логи хранятся 7 дней. Используется logrotate

Можно настроить чтение файла удаленно из iTerm.

### БД на сервере
На сервере открыт удаленный доступ к бд. Порт 5432.

Логин vk_bot. Пароль тот же, что и от админки

### Передача файлов
С сервера и на сервер:
```shell
scp vk_scraping_posting@80.211.178.81:/home/vk_scraping_posting/vk_scraping_posting/<file> ./<file>
scp ./<file> vk_scraping_posting@80.211.178.81:/home/vk_scraping_posting/vk_scraping_posting/<file> 

```

## Бизнес логика

Ограничение на постинг:

* Пост в группе не будет выпущен, если последний пост выпущен из того же донора. Отключается настройкой donors_alternation в каждой группе.
Глобально это правило может отключаться настройкой IGNORE_DONORS_REPEAT
* Обычный пост может быть выпущен только по расписанию. Исключением является мешающий рекламный пост:
если во время минуты постинга есть реклама, этот пост должен быть выпущен после 1 часа и 5 минут от времени постинга
рекламы

### Модерация
#### Бан админов доноров
Каждый день собираем админов у активных доноров, баним их навсегда 

#### Удаление комментариев

Причины для удаления комментариев:

* Есть слова из списка бан-слов (is_stop_words_in_text)
* В одном слове слова из разных алфавитов (например, шкоlolo) (is_scam_words_in_text)
* Есть видео в комментарии (is_video_in_attachments)
* Есть ссылка в приложении (is_link_in_attachments)
* Комментарий от группы (is_group)
* Есть ссылки в тексте (is_links_in_text)
* Есть vk-ссылки в тексте (is_vk_links_in_text)
* Одновременно аудио и фото в комментарии (is_audio_and_photo_in_attachments)

Причины для бана комментирующих:

* Комментарий от группы (is_audio_and_photo_in_attachments)
* Одновременно аудио и фото в комментарии (is_audio_and_photo_in_attachments)
* Больше 4 комментариев с одинаковым текстом за сутки
* Больше 4 комментариев с одинаковыми вложениями за сутки

### Постинг (posting)

#### Фильмы
Берем информацию о фильмах тут https://www.themoviedb.org/

### Реклама (promotion)
Смотри техническое описание
### Скрапинг (scraping)
Смотри техническое описание
### Сервисы (services)
Смотри техническое описание
### Остальное
Смотри техническое описание

## Технические штуки

### Модерация (moderation)

Для получения данных от вк используется вебхук webhook/. Есть вьюха webhook, которая принимает POST от вк и сохраняет
в БД. Создается запись `WebhookTransaction`. Далее транзакции обрабатываются таской `process_transactions` раз в минуту.

#### Периодические задачи

* `ban_donors_admins.py` - в 3:00 по МСК каждый день.
* `delete_old_transactions.py` - в 3:00 по МСК каждый день.
* `process_transactions.py` - каждую минуту

#### ban_donors_admins.py
Берем все активные группы.
В каждой активной группе получаем список всех доноров. В каждом доноре берем контакты. Если контакт идет с user_id, то
баним этого пользователя **навсегда**.

#### delete_old_transactions.py
Удаляем транзакции, которые старше OLD_MODERATION_TRANSACTIONS_HOURS (48 часов по дефолту), чтобы не засорять бд.

#### process_transactions.py`
Собираем все необработанные транзакции, разделяем на наши группы, процессим каждый (process_comment), сохраняем в бд.

#### process_comment
Собираем правила модерации **ModerationRule**. Они содержат вайт лист людей, которых не надо банить. Также содержат
слова, за которые мы баним.

Причины банов реализованы в checks.py.

#### helpers.py
Всякие функции для упрощения работы с комментами

### Постинг (posting)
Постинг реализован вокруг периодической задачи examine_groups, которая выполняется каждую минуту

#### Периодические задачи

* `delete_old_ads.py` - каждый час в 31 минуту
* `delete_old_blocks.py` - в 00:00 по МСК каждый день 
* `delete_old_stat.py` - в 3:32 по МСК каждый день
* `examine_groups.py` - каждую минуту
* `pin_best_post.py` - в 1:01 по МСК каждый день. Подробнее [pin_best_post.py](#pin_best_post.py)
* `sex_statistics_weekly.py` - в 3:30 по МСК каждое воскресенье
* `update_statistics.py` - в 4:03 по МСК каждый день. Подробнее [update_statistics.py](#update_statistics.py)

#### delete_old_ads.py
#### delete_old_blocks.py
Часть функционала, который не был реализован до конца.
#### delete_old_stat.py
#### examine_groups.py
Выполняется каждую минуту. Супер перегруженная функция.

* Берем каждую группу с админом и с is_posting_active=true
* Если в группе были рекламные посты - пропускаем постинг (are_any_ads_posted_recently)
* Проверяем, нужно ли постить в группе, были ли посты за последний период постинга (is_it_time_to_post)
* Далее идет проверка на разные типы групп 
  * is_movies_condition -> Постинг отдельных фильмов (трейлеры) [post_movie.py](#post_movie.py)
  * is_horoscopes_conditions -> Постинг гороскопов [post_horoscope.py](#post_horoscope.py)
  * is_common_condition -> Постинг обычных постов [post_record.py](#post_record.py)


####<a name="pin_best_post.py">pin_best_post.py</a>
В 1:01 по МСК каждый день

* Собираем все активные группы с настройкой is_pin_enabled=True. Далее, для каждой активной группы
* Собираем все посты за последние 24 часа
* Среди этих постов ищем тот, у которого максимум по просмотрам (views)
* Закрепляем этот пост

####<a name="post_horoscope.py">post_horoscope.py</a>
За постинг гороскопа отвечает одна таска. Принимает id группы и horoscope_record_id.

Тут важно уточнить, почему используется не Record, а HoroscopeRecord. Исторически сложилось, делали быстро. Но хорошо 
бы отказаться от HoroscopeRecord в пользу Record.

Алгоритм работы:

* Собираем текст гороскопа
* **Если** включена HOROSCOPES_TO_IMAGE_ENABLED, то мы создаем картинку с гороскопом (transfer_horoscope_to_image)
  * Для женского гороскопа (29038248) мы дополнительно вставляем в картинку случайные значения: любовь, здоровье, удача, финансы (paste_horoscopes_rates)
* **Иначе**
  * Заменяем буквы с русского на английский, если в группе включена `is_replace_russian_with_english` (replace_russian_with_english_letters)
  * Удаляем все хетеги из текста (delete_hashtags_from_text)
  * Если в гороскопе есть картинка, подгружаем её
* Если гороскопы основные (HOROSCOPES_MAIN, т.е. Мужской и Женский), то убираем весь текст.
* Если гороскопы основные (HOROSCOPES_MAIN), добавляем источник `copyright_text`
* Если гороскопы обычные (HOROSCOPES_COMMON, т.е. знаковые):
  * Закрепляем этот пост
  * Отправляем задачу в X1Y1Z1 (add_promotion_task)
  * Сохраняем этот гороскоп для основных групп (save_horoscope_for_main_groups)

####<a name="post_movie.py">post_movie.py</a>
**В данный момент отключено**

За постинг трейлера отвечает одна таска. Принимает id группы и movie_id. Сам объект Movie сильно отличается от Record, 
но его тоже хочется унифицировать до Record, чтобы не плодить миллион сущностей.

Из важного:

* Сильно важен порядок картинок, первым должна быть обложка
* Если нужно мерджить постер и кадры в одну картинку, есть настройка **ENABLE_MERGE_IMAGES_MOVIES**
* Если есть трейлер и включена PUT_TRAILERS_TO_ATTACHMENTS, то прикрепляем и трейлер

####<a name="post_music.py">post_music.py</a>
За постинг аудио-постов отвечает одна таска. Принимает id группы и record_id

С музыкой в вк всё странно. У нас постоянно возникает ошибки: либо меняется количество аудио произвольно, либо что-то ещё. 
Писали и поддержке ВК, и в сообщество библиотеки vk_api - ни у кого нет вариантов решения. 

####<a name="post_record.py">post_record.py</a>

За основной постинг отвечает одна таска. Принимает id группы и record_id.

Из важного:
* Ставим копирайт, если в группе или доноре есть настройка is_copyright_needed
* Если текст по длине меньше (MAX_TEXT_TO_FILL_LENGTH, 70 по умолчанию), перемещаем его на картинку, текст из поста убираем
* Если is_text_delete_enabled - удаляем весь текст
* Если is_replace_russian_with_english - заменяем кириллицу на латиницу
* Если is_photos_shuffle_enabled - мешаем порядок фоток
* Если группа для фильмов (), то sort_images_for_movies - сортируем картинки
* merge_six_images_condition - условие: is_merge_images_enabled, картинок 6, все картинки вертикальные
* Если is_image_mirror_enabled и изображение не содержит текст - зеркалим
* Если группа музыкальная (MUSIC_COMMON), то отправляем вложения для вк в обратном порядке. Это связано с тем, что иначе
, по какой-то неведанной мне хуйне, картинки в музыкальных пабликах задваиватся, если присылаем их и ещё 9 аудио
* 

####<a name="sex_statistics_weekly.py">sex_statistics_weekly.py</a>
**Временно неактивно, есть баг**

Эта таска обновляет процент мужчин к женщинам во всех группах. Нужно для подбора подходящих по полу постов.

####<a name="update_statistics.py">update_statistics.py</a>
Обновляем данные для статистики: 

* Изменение количества подписчиков с прошлого дня.  
* Количество подписчиков группы
* Количество постов за прошлый день
* Количество рекламы за пролый день

### Реклама (promotion)
Это модуль накрутки. Интеграция с сервисом z1y1x1.ru. Апи лежит тут http://api.z1y1x1.ru.

### Скрапинг (scraping)
Модуль сбора, фильтрации и оценки для постинга обычных постов.

#### Периодические задачи

* `check_attachments_availability.py` - каждый час в 18 и 48 минуты
* `delete_old_horoscope_records.py` - каждый день в 3 ночи по МСК
* `delete_oldest.py` - каждый день в 8:15 по МСК
* `download_youtube_trailers.py` - каждый час в 10 и 40 минуты
* `parse_horoscopes.py` - каждый день в 14:55 по МСК 
* `rate_new_posts.py` - каждый час в 15 и 45 минут
* `run_scraper.py` - каждый час в 0 минуту
* `scrap_new_movies.py` - каждое воскресенье в 0:30 по МСК
* `set_donors_avera# Документация по боту

## Бизнес логика

Ограничение на постинг:

* Пост в группе не будет выпущен, если последний пост выпущен из того же донора. Отключается настройкой donors_alternation в каждой группе.
  Глобально это правило может отключаться настройкой IGNORE_DONORS_REPEAT
* Обычный пост может быть выпущен только по расписанию. Исключением является мешающий рекламный пост:
  если во время минуты постинга есть реклама, этот пост должен быть выпущен после 1 часа и 5 минут от времени постинга
  рекламы

### Модерация
#### Бан админов доноров
Каждый день собираем админов у активных доноров, баним их навсегда

#### Удаление комментариев

Причины для удаления комментариев:

* Есть слова из списка бан-слов (is_stop_words_in_text)
* В одном слове слова из разных алфавитов (например, шкоlolo) (is_scam_words_in_text)
* Есть видео в комментарии (is_video_in_attachments)
* Есть ссылка в приложении (is_link_in_attachments)
* Комментарий от группы (is_group)
* Есть ссылки в тексте (is_links_in_text)
* Есть vk-ссылки в тексте (is_vk_links_in_text)
* Одновременно аудио и фото в комментарии (is_audio_and_photo_in_attachments)

Причины для бана комментирующих:

* Комментарий от группы (is_audio_and_photo_in_attachments)
* Одновременно аудио и фото в комментарии (is_audio_and_photo_in_attachments)
* Больше 4 комментариев с одинаковым текстом за сутки
* Больше 4 комментариев с одинаковыми вложениями за сутки

### Постинг (posting)

#### Фильмы
Берем информацию о фильмах тут https://www.themoviedb.org/

### Реклама (promotion)
### Скрапинг (scraping)
### Сервисы (services)
### Остальное


## Технические штуки

### Модерация (moderation)

Для получения данных от вк используется вебхук webhook/. Есть вьюха webhook, которая принимает POST от вк и сохраняет
в БД. Создается запись `WebhookTransaction`. Далее транзакции обрабатываются таской `process_transactions` раз в минуту.

#### Периодические задачи

* `ban_donors_admins.py` - в 3:00 по МСК каждый день.
* `delete_old_transactions.py` - в 3:00 по МСК каждый день.
* `process_transactions.py` - каждую минуту

#### ban_donors_admins.py
Берем все активные группы.
В каждой активной группе получаем список всех доноров. В каждом доноре берем контакты. Если контакт идет с user_id, то
баним этого пользователя **навсегда**.

#### delete_old_transactions.py
Удаляем транзакции, которые старше OLD_MODERATION_TRANSACTIONS_HOURS (48 часов по дефолту), чтобы не засорять бд.

#### process_transactions.py`
Собираем все необработанные транзакции, разделяем на наши группы, процессим каждый (process_comment), сохраняем в бд.

#### process_comment
Собираем правила модерации **ModerationRule**. Они содержат вайт лист людей, которых не надо банить. Также содержат
слова, за которые мы баним.

Причины банов реализованы в checks.py.

#### helpers.py
Всякие функции для упрощения работы с комментами

### Постинг (posting)
Постинг реализован вокруг периодической задачи examine_groups, которая выполняется каждую минуту

#### Периодические задачи

* `delete_old_ads.py` - каждый час в 31 минуту
* `delete_old_blocks.py` - в 00:00 по МСК каждый день
* `delete_old_stat.py` - в 3:32 по МСК каждый день
* `examine_groups.py` - каждую минуту
* `pin_best_post.py` - в 1:01 по МСК каждый день. Подробнее [pin_best_post.py](#pin_best_post.py)
* `sex_statistics_weekly.py` - в 3:30 по МСК каждое воскресенье
* `update_statistics.py` - в 4:03 по МСК каждый день. Подробнее [update_statistics.py](#update_statistics.py)

#### delete_old_ads.py
#### delete_old_blocks.py
Часть функционала, который не был реализован до конца.
#### delete_old_stat.py
#### examine_groups.py
Выполняется каждую минуту. Супер перегруженная функция.

* Берем каждую группу с админом и с is_posting_active=true
* Если в группе были рекламные посты - пропускаем постинг (are_any_ads_posted_recently)
* Проверяем, нужно ли постить в группе, были ли посты за последний период постинга (is_it_time_to_post)
* Далее идет проверка на разные типы групп
  * is_movies_condition -> Постинг отдельных фильмов (трейлеры) [post_movie.py](#post_movie.py)
  * is_horoscopes_conditions -> Постинг гороскопов [post_horoscope.py](#post_horoscope.py)
  * is_common_condition -> Постинг обычных постов [post_record.py](#post_record.py)


####<a name="pin_best_post.py">pin_best_post.py</a>
В 1:01 по МСК каждый день

* Собираем все активные группы с настройкой is_pin_enabled=True. Далее, для каждой активной группы
* Собираем все посты за последние 24 часа
* Среди этих постов ищем тот, у которого максимум по просмотрам (views)
* Закрепляем этот пост

####<a name="post_horoscope.py">post_horoscope.py</a>
За постинг гороскопа отвечает одна таска. Принимает id группы и horoscope_record_id.

Тут важно уточнить, почему используется не Record, а HoroscopeRecord. Исторически сложилось, делали быстро. Но хорошо
бы отказаться от HoroscopeRecord в пользу Record.

Алгоритм работы:

* Собираем текст гороскопа
* **Если** включена HOROSCOPES_TO_IMAGE_ENABLED, то мы создаем картинку с гороскопом (transfer_horoscope_to_image)
  * Для женского гороскопа (29038248) мы дополнительно вставляем в картинку случайные значения: любовь, здоровье, удача, финансы (paste_horoscopes_rates)
* **Иначе**
  * Заменяем буквы с русского на английский, если в группе включена `is_replace_russian_with_english` (replace_russian_with_english_letters)
  * Удаляем все хетеги из текста (delete_hashtags_from_text)
  * Если в гороскопе есть картинка, подгружаем её
* Если гороскопы основные (HOROSCOPES_MAIN, т.е. Мужской и Женский), то убираем весь текст.
* Если гороскопы основные (HOROSCOPES_MAIN), добавляем источник `copyright_text`
* Если гороскопы обычные (HOROSCOPES_COMMON, т.е. знаковые):
  * Закрепляем этот пост
  * Отправляем задачу в X1Y1Z1 (add_promotion_task)
  * Сохраняем этот гороскоп для основных групп (save_horoscope_for_main_groups)

####<a name="post_movie.py">post_movie.py</a>
**В данный момент отключено**

За постинг трейлера отвечает одна таска. Принимает id группы и movie_id. Сам объект Movie сильно отличается от Record,
но его тоже хочется унифицировать до Record, чтобы не плодить миллион сущностей.

Из важного:

* Сильно важен порядок картинок, первым должна быть обложка
* Если нужно мерджить постер и кадры в одну картинку, есть настройка **ENABLE_MERGE_IMAGES_MOVIES**
* Если есть трейлер и включена PUT_TRAILERS_TO_ATTACHMENTS, то прикрепляем и трейлер

####<a name="post_music.py">post_music.py</a>
За постинг аудио-постов отвечает одна таска. Принимает id группы и record_id

С музыкой в вк всё странно. У нас постоянно возникает ошибки: либо меняется количество аудио произвольно, либо что-то ещё.
Писали и поддержке ВК, и в сообщество библиотеки vk_api - ни у кого нет вариантов решения.

####<a name="post_record.py">post_record.py</a>

За основной постинг отвечает одна таска. Принимает id группы и record_id.

Из важного:
* Ставим копирайт, если в группе или доноре есть настройка is_copyright_needed
* Если текст по длине меньше (MAX_TEXT_TO_FILL_LENGTH, 70 по умолчанию), перемещаем его на картинку, текст из поста убираем
* Если is_text_delete_enabled - удаляем весь текст
* Если is_replace_russian_with_english - заменяем кириллицу на латиницу
* Если is_photos_shuffle_enabled - мешаем порядок фоток
* Если группа для фильмов (), то sort_images_for_movies - сортируем картинки
* merge_six_images_condition - условие: is_merge_images_enabled, картинок 6, все картинки вертикальные
* Если is_image_mirror_enabled и изображение не содержит текст - зеркалим
* Если группа музыкальная (MUSIC_COMMON), то отправляем вложения для вк в обратном порядке. Это связано с тем, что иначе
  , по какой-то неведанной мне хуйне, картинки в музыкальных пабликах задваиватся, если присылаем их и ещё 9 аудио
*

####<a name="sex_statistics_weekly.py">sex_statistics_weekly.py</a>
**Временно неактивно, есть баг**

Эта таска обновляет процент мужчин к женщинам во всех группах. Нужно для подбора подходящих по полу постов.

####<a name="update_statistics.py">update_statistics.py</a>
Обновляем данные для статистики:

* Изменение количества подписчиков с прошлого дня.
* Количество подписчиков группы
* Количество постов за прошлый день
* Количество рекламы за пролый день

### Реклама (promotion)
Это модуль накрутки. Интеграция с сервисом z1y1x1.ru. Апи лежит тут http://api.z1y1x1.ru.

### Скрапинг (scraping)
Модуль сбора, фильтрации и оценки для постинга обычных постов.

#### Периодические задачи

* `check_attachments_availability.py` - каждый час в 18 и 48 минуты, [check_attachments_availability.py](check_attachments_availability.py)
* `delete_old_horoscope_records.py` - каждый день в 3 ночи по МСК, удаляются гороскомы старше OLD_HOROSCOPES_HOURS (48) часов
* `delete_oldest.py` - каждый день в 8:15 по МСК, удаление лишних записей, если их больше COMMON_RECORDS_COUNT_FOR_DONOR (100) для донора
* `download_youtube_trailers.py` - каждый час в 10 и 40 минуты, скачивание трейлеров из youtube
* `parse_horoscopes.py` - каждый день в 14:55 по МСК, парсинг источников гороскопов
* `rate_new_posts.py` - каждый час в 15 и 45 минут, [rate_new_posts.py](rate_new_posts.py)
* `run_scraper.py` - каждый час в 0 минуту
* `scrap_new_movies.py` - каждое воскресенье в 0:30 по МСК
* `set_donors_average_view.py` - каждый день в 4:30 по МСК 

####<a name="check_attachments_availability.py">check_attachments_availability.py</a>
Задача на проверку доступности вложения для перепостинга. 
Проверяем в основном видео, так как у них есть ограниченный доступ, из-за чего нам не подходит эта запись. Делается эта
задача перед самым постингом, чтобы не напороться на заблокированное видео.

####<a name="rate_new_posts.py">rate_new_posts.py</a>
Оценка поста и простановка ему рейтинга. Пост с самым высоким рейтингом постится у нас.
Сейчас используется простой подсчет: `рейтинг = просмотр у поста / средние просмотры у донора * 1000`.

Собирается много данных, которые можно использовать, но от предложения разработать хорошую систему оценки отказались.

### Сервисы (services)
Это приложение содержит все обертки над API, которые мы используем:

* horoscopes - Гороскопы https://horo.mail.ru и https://goroskop365.ru/
* z1y1x1 - Сервис накрутки z1y1x1.ru
* themoviedb - Сервис с киношкой https://www.themoviedb.org/
* vk - https://vk.com - все взаимодействия с апи прячем под функциями, работаем в основном с внутренними объектами 
(Но так случается не всегда, в начале мы об этом не задумывались)
* youtube - https://youtuve.com, скачиваем с помощью библиотеки pytube трейлеры из YT

### Остальное
Приложение shapranov отвечает за расположение какого-то текста, + тут располагается эта документация, просто делается из
md файла html с помощью стандартной библы и просто прокидывается во вьюху с доступом только для залогиненых.

#### Токен Яндекса
В корне проекта лежит файл для поисковика: yandex_89a7c0b097d6ca89.html

#### Кастомные команды
Есть ещё кастомные команды, но использовлись давно, каждый день они не нужны

### Периодические задачи

`delete_oldest.py` - удаляет старые записи донора в 8:15 по мск, если их количество превышает COMMON_RECORDS_COUNT_FOR_DONOR (80)

### Переменные

* **VK_API_VERSION** -**5.131**, str
* **MIN_STRING_MATCH_RATIO**: (0.85, **Non documented**)
* **HOROSCOPES_DONOR_ID**: (**83815413**, **Horoscopes specific donor id**, str)
* **MAX_TEXT_TO_FILL_LENGTH**: (70, **Maximum text length to adding on image**)
* **MIN_QUANTITY_OF_PIXELS**: (700, **Minimum pixels of any size of image for scraping**)
* **PIXELS_TO_CUT_FROM_BOTTOM**: (10, **Pixels to cut from bottom**)
* **PERCENTAGE_TO_CROP_FROM_EDGES**: (0.05, **Non documented**)
* **FONT_NAME**: (**SFUIDisplay-Regular.otf**, **Font name for filling**, str)
* **FONT_SIZE_PERCENT**: (6, **Font size percent of all image**)
* **THE_SAME_SIZE_FACTOR**: (0.03, **allowable size divergence**, float)
* **WALL_RECORD_COUNT_TO_PIN**: (50, **How many records analise to pin post**)
* **OLD_RECORDS_HOURS**: (24, **Time for records expiring**)
* **OLD_AD_RECORDS_HOURS**: (30, **Time for advertising records expiring**)
* **OLD_HOROSCOPES_HOURS**: (48, **Time for horoscope records expiring**)
* **OLD_MODERATION_TRANSACTIONS_HOURS**: (48, **Time for moderation transactions expiring**)
* **IS_DEV**: (False, **Is server role for development?**, bool)
* **SIX_IMAGES_OFFSET**: (6, **Offset between two images in merging**, int)
* **SIX_IMAGES_WIDTH**: (2560, **Default width of image after merging**, int)
* **POSTING_BASED_ON_SEX**: (False, **Use sex data to filter best post**, bool)
* **RECORDS_SELECTION_PERCENT**: (20, **Percent of best records using in posting based on sex**, int)
* **HOROSCOPES_TO_IMAGE_ENABLED**: (False, **Is transport horoscopes to image enabled?**, bool)
* **HOROSCOPES_POSTING_INTERVAL**: (3, **Horoscopes posting interval**, int)
* **HOROSCOPES_FONT_TITLE**: (80, **Text in horoscopes font size**, int)
* **HOROSCOPES_FONT_BODY**: (60, **Text in horoscopes font size**, int)
* **TMDB_API_KEY**: (****, **The movie db api key**, str)
* **TMDB_SEARCH_START_YEAR**: (1998, **Discover movies starts with given year**, int)
* **TMDB_NEW_MOVIES_OFFSET**: (2, **Number of years for searching new movies**, int)
* **TMDB_MIN_TRAILERS_COUNT**: (4, **Minimum count of downloaded youtube trailers**, int)
* **FORCE_MOVIE_POST**: (False, **Just for dev. Forcing movie posting**, bool)
* **TMDB_SCRAPING_ENABLED**: (False, **Just for dev. Is TMDB scraping enabled**, bool)
* **ENABLE_MERGE_IMAGES_MOVIES**: (True, **Enable merging images in movies to one**, bool)
* **PUT_TRAILERS_TO_ATTACHMENTS**: (True, **Put trailers to attachments. Otherwise, put link in desc**, bool)
* **IMAGE_SIDE_OFFSET_ABS**: (10, **Absolute offset of text and image boarders (all sides)**, int)
* **IMAGE_SPACING_ABS**: (5, **Absolute spacing between lines of text**, int)
* **TMDB_MOVIE_INTERVALS**: (**[(60, 65), (65, 70), (70, 75), (75, 80), (80, 101)]**, **Intervals for posting. Note that values must be integers**, - str)
* **OLD_MOVIES_TIME_THRESHOLD**: (7, **Number of days when movie become old**, int)
* **TMDB_NUMBER_OF_STORED_TRAILERS**: (3, **Number of movie trailers to store in db**, int)
* **FORCE_USE_ABSTRACTION**: (False, **Forcing using of abstraction in music**, bool)
* **COMMON_RECORDS_COUNT_FOR_DONOR**: (80, **Number of records that we need to rate donor**, int)
* **NEW_RECORD_MATURITY_MINUTES**: (120, **How old must be a record when we rate it**, int)
* **CUT_ONE_AUDIO_ATTACHMENT**: (False, **Cut one random audio attachment from posts**)
* **EXCLUDE_GROUPS_FROM_SEX_STATISTICS_UPDATE**: (**[42440233, 28446706, 23639186]**, **Don't update sex statistic for list of groups**, str)
* **DONOR_OUTDATE_INTERVAL**: (30, **Donor considered outdated if last post was N days ago**, int)
* **STATS_STORING_TIME**: (30, **Statistics storing time in days**, int)
* **NEW_POSTING_INTERVALS_ENABLE**: (True, **New posting intervals logic**, bool)
* **BLOCKS_ACTIVE**: (True, **Are blocks feature active**, bool)
* **IGNORE_DONORS_REPEAT**: (False, **Ignore posting rule, that disable posting from same donor twice**, bool)
* **USE_APP**: (False, **Use app in session creation**, bool)
* **X_TOKEN**: (****, **x1y1z1 token**, str)
