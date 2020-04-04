import logging
import re

log = logging.getLogger('services.text_utilities')


def replace_words(match_obj):
    replace_map = {
        'а': 'a',
        'с': 'c',
        'о': 'o',
        'е': 'e',
        'у': 'y',
        'х': 'x',
        'р': 'p',
        'Е': 'E',
        'Н': 'H',
        'О': 'O',
        'Х': 'X',
        'А': 'A',
        'С': 'C',
        'В': 'B',
        'Р': 'P',
        'М': 'M'
    }
    # result_text = ''
    # replaced = False
    #
    # for word in re.findall(r'\s*\S+\s*', text):
    #     if not replaced:
    #         for letter in word:
    #             if letter in replace_map.keys():
    #                 word = word.replace(letter, replace_map[letter], 1)
    #                 replaced = True
    #                 break
    #     else:
    #         replaced = False
    #     result_text += word

    word = match_obj.group(0)

    for letter, replacement in replace_map.items():
        word = re.sub(letter, replacement, word)

    return word


def replace_russian_with_english_letters(text):
    result_text = re.sub(r'((?<!#)\b\w+)', replace_words, text)

    return result_text


def delete_double_spaces_from_text(text):
    text = re.sub(' +', ' ', text)
    return text


def delete_hashtags_from_text(text):
    # link hashtag looks like '#hello@user', common looks like '#hello'
    text_without_link_hashtags = re.sub(r'(@\w*)', '', text)
    text_without_double_spaces = delete_double_spaces_from_text(text_without_link_hashtags)
    return text_without_double_spaces


def delete_emoji_from_text(text):
    log.debug('delete_emoji_from_text called. Text: "{}"'.format(text))
    # text_without_emoji = re.sub(u'[\u0000-\u052F]+', ' ', text)
    last_char_code = 1279  # 04FF
    text_without_emoji = ''.join(letter for letter in text if ord(letter) <= last_char_code)
    log.debug('text after deleting "{}"'.format(text_without_emoji))
    text_without_double_spaces = delete_double_spaces_from_text(text_without_emoji)
    return text_without_double_spaces
