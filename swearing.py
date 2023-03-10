from enum import Enum, auto
import random

class Gender(Enum):
    M = auto()
    N = auto()
    F = auto()

class Noun:
    def __init__(self, word, gender):
        self.word = word
        self.gender = gender

class Adjective:
    def __init__(self, word, m, n, f):
        self.word = word
        self.endings = {}
        self.endings[Gender.M] = m
        self.endings[Gender.N] = n
        self.endings[Gender.F] = f

nouns = [
Noun('подонок',     Gender.M),
Noun('пидор',       Gender.M),
Noun('педик',       Gender.M),
Noun('дебил',       Gender.M),
Noun('отстой',      Gender.M),
Noun('выблядок',    Gender.M),
Noun('обмудок',     Gender.M),
Noun('высер',       Gender.M),
Noun('дегенерат',   Gender.M),
Noun('отморозок',   Gender.M),
Noun('сблёв',       Gender.M),
Noun('олень',       Gender.M),
Noun('долбоёб',     Gender.M),
Noun('хуйлан',      Gender.M),

Noun('говно',       Gender.N),
Noun('ничтожество', Gender.N),
Noun('чмо',         Gender.N),
Noun('уебище',      Gender.N),
Noun('быдло',       Gender.N),

Noun('пизда',       Gender.F),
Noun('хуета',       Gender.F),
Noun('чурка',       Gender.F),
Noun('гнида',       Gender.F),
Noun('мразь',       Gender.F),
Noun('скотина',     Gender.F),
Noun('дрянь',       Gender.F),
Noun('проститутка', Gender.F),
]

adjectives = [
Adjective('ничтожн',  'ый', 'ое', 'ая'),
Adjective('пидорск',  'ий', 'ое', 'ая'),  
Adjective('ебан',     'ый', 'ое', 'ая'),
Adjective('суч',      'ий', 'ее', 'ая'),
Adjective('говнян',   'ый', 'ое', 'ая'),  
Adjective('петушин',  'ый', 'ое', 'ая'),   
Adjective('безмозгл', 'ый', 'ое', 'ая'),   
Adjective('конченн',  'ый', 'ое', 'ая'),  
Adjective('амёбн',    'ый', 'ое', 'ая'), 
Adjective('туп',      'ой', 'ое', 'ая'), 
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
            adj = random.choice(adjectives)
            line.insert(i - 1, adj.word + adj.endings[noun.gender])
            i += 1
    return ' '.join(line)

if __name__ == '__main__':
    print(generate_swearline())
