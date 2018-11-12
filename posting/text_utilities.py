import re


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
