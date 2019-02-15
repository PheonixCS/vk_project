
CONSTANCE_CONFIG = {
    'VK_API_VERSION': (5.74, 'VK API version'),
    'MIN_STRING_MATCH_RATIO': (0.85, 'Non documented'),
    'HOROSCOPES_DONOR_ID': ('83815413', 'Horoscopes specific donor id', str),

    'MAX_TEXT_TO_FILL_LENGTH': (70, 'Maximum text length to adding on image'),
    'MIN_QUANTITY_OF_PIXELS':  (700, 'Minimum pixels of any size of image for scraping'),
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
    'TMDB_MIN_TRAILERS_COUNT': (4, 'Minimum count of downloaded youtube trailers', int),
    'FORCE_MOVIE_POST': (False, 'Just for dev. Forcing movie posting', bool),
    'TMDB_SCRAPING_ENABLED': (False, 'Just for dev. Is TMDB scraping enabled', bool),
    'ENABLE_MERGE_IMAGES_MOVIES': (True, 'Enable merging images in movies to one', bool),
    'PUT_TRAILERS_TO_ATTACHMENTS': (True, 'Put trailers to attachments. Otherwise, put link in desc', bool),
    'IMAGE_SIDE_OFFSET_ABS': (10, 'Absolute offset of text and image boarders (all sides)', int)
}
