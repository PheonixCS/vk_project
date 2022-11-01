# Документация по боту

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
* `pin_best_post.py` - в 1:01 по МСК каждый день
* `sex_statistics_weekly.py` - в 3:30 по МСК каждое воскресенье
* `update_statistics.py` - в 4:03 по МСК каждый день [update_statistics.py](#update_statistics.py)

#### delete_old_ads.py
#### delete_old_blocks.py
Часть функционала, который не был реализован до конца.
#### delete_old_stat.py
#### examine_groups.py
Супер перегруженная функция.

* Берем каждую группу с админом и с is_posting_active=true
* Если в группе были рекламные посты - пропускаем постинг (are_any_ads_posted_recently)
* Проверяем, нужно ли постить в группе, были ли посты за последний период постинга (is_it_time_to_post)
* Далее идет проверка на разные типы групп 
  * is_movies_condition -> Постинг отдельных фильмов (трейлеры) [post_movie.py](#post_movie.py)
  * is_horoscopes_conditions -> Постинг гороскопов [post_horoscope.py](#post_horoscope.py)
  * is_common_condition -> Постинг обычных постов [post_record.py](#post_record.py)


####<a name="pin_best_post.py">pin_best_post.py</a>
####<a name="post_horoscope.py">post_horoscope.py</a>
####<a name="post_movie.py">post_movie.py</a>
####<a name="post_music.py">post_music.py</a>
####<a name="post_record.py">post_record.py</a>
####<a name="sex_statistics_weekly.py">sex_statistics_weekly.py</a>
####<a name="update_statistics.py">update_statistics.py</a>

### Реклама (promotion)


### Скрапинг (scraping)


### Сервисы (services)


### Остальное 

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
