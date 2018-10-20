#
import re


def replace_russian_with_english_letters(text):

    # replace map goes with russian letter as a key
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
        'М': 'M',
        # 'и': 'u',
        # '1': 'I',
        # 'м': 'm',
        # 'к': 'k',
        # 'Ы': 'bI'
    }
    # Comment because of
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

    result_text = text

    for letter, replacement in replace_map.items():
        result_text = re.sub(letter, replacement, result_text)

    return result_text
