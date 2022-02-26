import json
from pathlib import Path

cwd = Path.cwd()


def reformat_time(time):
    return time.replace('m', 'м').replace('s', 'с').replace('h', 'ч').replace('d', 'д')


def translate_item_name(item: str, lang='ru'):
    with open(Path(cwd, 'src/translation.json'), 'r', encoding='UTF-8') as file, \
            open(Path(cwd, 'src/reversed_translation.json'), 'r', encoding='UTF-8') as rev_file:
        translate_table = json.load(file)
        reversed_table = json.load(rev_file)
        for word in item.split(' '):
            if word.capitalize() in translate_table and lang == 'ru':
                item = item.replace(word, translate_table[word.capitalize()])
            elif word.capitalize() in reversed_table and lang == 'eu':
                item = item.replace(word, reversed_table[word.capitalize()])
        return item


def make_reversed_translation_table():
    with open(Path(cwd, 'src/translation.json'), 'r', encoding='UTF-8') as file:
        translation = json.load(file)
        reversed_translation = inv_map = {v: k for k, v in translation.items()}
        with open(Path(cwd, 'src/reversed_translation.json'), 'w') as rev_file:
            json.dump(reversed_translation, rev_file)


if __name__ == '__main__':
    print(translate_item_name('rhino prime'))