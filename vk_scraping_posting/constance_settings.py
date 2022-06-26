# Our settings that can be changed on air w/o process reload
from collections import OrderedDict

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

CONSTANCE_CONFIG = {
    'VK_API_VERSION': ('5.131', 'VK API version', str),
    'MIN_STRING_MATCH_RATIO': (0.85, 'Non documented'),
    'HOROSCOPES_DONOR_ID': ('83815413', 'Horoscopes specific donor id', str),
    'MAX_TEXT_TO_FILL_LENGTH': (70, 'Maximum text length to adding on image'),
    'MIN_QUANTITY_OF_PIXELS': (700, 'Minimum pixels of any size of image for scraping'),
    'PIXELS_TO_CUT_FROM_BOTTOM': (10, 'Pixels to cut from bottom'),
    'PERCENTAGE_TO_CROP_FROM_EDGES': (0.05, 'Non documented'),
    'FONT_NAME': ('SFUIDisplay-Regular.otf', 'Font name for filling', str),
    'FONT_SIZE_PERCENT': (6, 'Font size percent of all image'),
    'THE_SAME_SIZE_FACTOR': (0.03, 'allowable size divergence', float),
    'WALL_RECORD_COUNT_TO_PIN': (50, 'How many records analise to pin post'),
    'OLD_RECORDS_HOURS': (24, 'Time for records expiring'),
    'OLD_AD_RECORDS_HOURS': (30, 'Time for advertising records expiring'),
    'OLD_HOROSCOPES_HOURS': (48, 'Time for horoscope records expiring'),
    'OLD_MODERATION_TRANSACTIONS_HOURS': (48, 'Time for moderation transactions expiring'),
    'IS_DEV': (False, 'Is server role for development?', bool),
    'SIX_IMAGES_OFFSET': (6, 'Offset between two images in merging', int),
    'SIX_IMAGES_WIDTH': (2560, 'Default width of image after merging', int),
    'POSTING_BASED_ON_SEX': (False, 'Use sex data to filter best post', bool),
    'RECORDS_SELECTION_PERCENT': (20, 'Percent of best records using in posting based on sex', int),
    'HOROSCOPES_TO_IMAGE_ENABLED': (False, 'Is transport horoscopes to image enabled?', bool),
    'HOROSCOPES_POSTING_INTERVAL': (3, 'Horoscopes posting interval', int),
    'HOROSCOPES_FONT_TITLE': (80, 'Text in horoscopes font size', int),
    'HOROSCOPES_FONT_BODY': (60, 'Text in horoscopes font size', int),
    'TMDB_API_KEY': ('', 'The movie db api key', str),
    'TMDB_SEARCH_START_YEAR': (1998, 'Discover movies starts with given year', int),
    'TMDB_NEW_MOVIES_OFFSET': (2, 'Number of years for searching new movies', int),
    'TMDB_MIN_TRAILERS_COUNT': (4, 'Minimum count of downloaded youtube trailers', int),
    'FORCE_MOVIE_POST': (False, 'Just for dev. Forcing movie posting', bool),
    'TMDB_SCRAPING_ENABLED': (False, 'Just for dev. Is TMDB scraping enabled', bool),
    'ENABLE_MERGE_IMAGES_MOVIES': (True, 'Enable merging images in movies to one', bool),
    'PUT_TRAILERS_TO_ATTACHMENTS': (True, 'Put trailers to attachments. Otherwise, put link in desc', bool),
    'IMAGE_SIDE_OFFSET_ABS': (10, 'Absolute offset of text and image boarders (all sides)', int),
    'IMAGE_SPACING_ABS': (5, 'Absolute spacing between lines of text', int),
    'TMDB_MOVIE_INTERVALS': ('[(60, 65), (65, 70), (70, 75), (75, 80), (80, 101)]',
                             'Intervals for posting. Note that values must be integers',
                             str),
    'OLD_MOVIES_TIME_THRESHOLD': (7, 'Number of days when movie become old', int),
    'TMDB_NUMBER_OF_STORED_TRAILERS': (3, 'Number of movie trailers to store in db', int),
    'FORCE_USE_ABSTRACTION': (False, 'Forcing using of abstraction in music', bool),
    'COMMON_RECORDS_COUNT_FOR_DONOR': (80, 'Number of records that we need to rate donor', int),
    'NEW_RECORD_MATURITY_MINUTES': (120, 'How old must be a record when we rate it', int),
    'CUT_ONE_AUDIO_ATTACHMENT': (False, 'Cut one random audio attachment from posts'),
    'EXCLUDE_GROUPS_FROM_SEX_STATISTICS_UPDATE': ('[42440233, 28446706, 23639186]',
                                                  'Don\'t update sex statistic for list of groups',
                                                  str),
    'DONOR_OUTDATE_INTERVAL': (30, 'Donor considered outdated if last post was N days ago', int),
    'STATS_STORING_TIME': (30, 'Statistics storing time in days', int),
    'NEW_POSTING_INTERVALS_ENABLE': (True, 'New posting intervals logic', bool),
    'BLOCKS_ACTIVE': (True, 'Are blocks feature active', bool),
    'IGNORE_DONORS_REPEAT': (False, 'Ignore posting rule, that disable posting from same donor twice', bool),
    'USE_APP': (False, 'Use app in session creation', bool),
    'X_TOKEN': (None, 'x1y1z1 token', str),
}

CONSTANCE_CONFIG_FIELDSETS = OrderedDict([
    ('General', (
        'VK_API_VERSION', 'WALL_RECORD_COUNT_TO_PIN', 'OLD_RECORDS_HOURS',
        'OLD_AD_RECORDS_HOURS', 'OLD_HOROSCOPES_HOURS', 'OLD_MODERATION_TRANSACTIONS_HOURS',
        'IS_DEV', 'POSTING_BASED_ON_SEX', 'RECORDS_SELECTION_PERCENT', 'FORCE_USE_ABSTRACTION',
        'MIN_STRING_MATCH_RATIO', 'COMMON_RECORDS_COUNT_FOR_DONOR',
        'NEW_RECORD_MATURITY_MINUTES', 'EXCLUDE_GROUPS_FROM_SEX_STATISTICS_UPDATE', 'STATS_STORING_TIME',
        'DONOR_OUTDATE_INTERVAL', 'NEW_POSTING_INTERVALS_ENABLE', 'BLOCKS_ACTIVE', 'IGNORE_DONORS_REPEAT', 'USE_APP'
    )),
    ('Horoscopes', (
        'HOROSCOPES_DONOR_ID', 'HOROSCOPES_TO_IMAGE_ENABLED', 'HOROSCOPES_POSTING_INTERVAL',
        'HOROSCOPES_FONT_TITLE', 'HOROSCOPES_FONT_BODY', 'X_TOKEN',
    )),
    ('Movies', (
        'TMDB_API_KEY', 'TMDB_SEARCH_START_YEAR', 'TMDB_NEW_MOVIES_OFFSET', 'TMDB_MIN_TRAILERS_COUNT',
        'FORCE_MOVIE_POST', 'TMDB_SCRAPING_ENABLED', 'ENABLE_MERGE_IMAGES_MOVIES', 'PUT_TRAILERS_TO_ATTACHMENTS',
        'TMDB_MOVIE_INTERVALS', 'OLD_MOVIES_TIME_THRESHOLD', 'TMDB_NUMBER_OF_STORED_TRAILERS'
    )),
    ('Images', (
        'MAX_TEXT_TO_FILL_LENGTH', 'MIN_QUANTITY_OF_PIXELS', 'SIX_IMAGES_OFFSET', 'SIX_IMAGES_WIDTH',
        'THE_SAME_SIZE_FACTOR', 'FONT_NAME', 'FONT_SIZE_PERCENT', 'PERCENTAGE_TO_CROP_FROM_EDGES',
        'PIXELS_TO_CUT_FROM_BOTTOM', 'IMAGE_SIDE_OFFSET_ABS', 'IMAGE_SPACING_ABS'
    )),
    ('Music', (
        'CUT_ONE_AUDIO_ATTACHMENT',
    )),
])
