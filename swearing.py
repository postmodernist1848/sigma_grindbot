from enum import Enum
import random

class Noun:
    def __init__(self, word, ending):
        self.word = word
        self.ending = ending

nouns = [
Noun('падонок',     'ый'),
Noun('пидор',       'ый'),
Noun('педик',       'ый'),
Noun('дебил',       'ый'),
Noun('отстой',      'ый'),

Noun('выблядок' ,   'ый'),
Noun('обмудок'  ,   'ый'),
Noun('высер'    ,   'ый'),
Noun('дегенерат',   'ый'),
Noun('отморозок',   'ый'),
Noun('сблёв'    ,   'ый'),
Noun('олень'    ,   'ый'),

Noun('говно',       'ое'),
Noun('ничтожество', 'ое'),
Noun('чмо',         'ое'),
Noun('уебище',      'ое'),

Noun('пизда',       'ая'),
Noun('хуета',       'ая'),
Noun('чурка',       'ая'),
Noun('гнида',       'ая'),
Noun('мразь',       'ая')
]

adjectives = [
'ничтожн',
'пидорск',
'ебан',
'суч',
'говнян',
'петушин',
'безмозгл',
'конченн',
'амёбн'
]

interjections = [
'блять',
'ты',
'сука'
]

def generate_swearline(length=None):
    line = []
    if (length is None):
        length = random.randint(6, 15)
    i = 0
    while i < length:
        if random.random() < 0.2:
            line.append(random.choice(interjections))
            i += 1
            continue
        noun = random.choice(nouns)
        line.append(noun.word)
        i += 1
        for _ in range(random.randint(0, 2)):
            line.insert(i - 1, random.choice(adjectives) + noun.ending)
            i += 1
    return ' '.join(line)

if __name__ == '__main__':
    print(generate_swearline())
