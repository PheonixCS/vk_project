
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
    'POSTING_BASED_ON_SEX': (False, 'Use sex data to filter best post', bool)
}
