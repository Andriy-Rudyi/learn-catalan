"""What the C1/C2 course pages show: the programme of the course, the topics
of the writing and speaking tasks and the connectors that go with them.

The programme follows the Superior course it prepares for (2nd term,
February to June): spelling review, morphology, vocabulary, an opinion
article of about 410 words and a monologue of about 6 minutes. Each topic
points to the grammar units (by number) and site pages that cover it.

Topic names and labels are Ukrainian source strings (translated by the
interface catalogues); topics, examples and connectors are Catalan and
stay as they are.
"""

ARTICLE_WORDS = 410
MONOLOGUE_MINUTES = 6

# (part, [(topic, unit numbers, page endpoint or None)])
PROGRAMME = [
    ('Орфографія: повторення', [
        ('Наголос на письмі та апостроф', [53, 54], None),
    ]),
    ('Морфологія', [
        ('Однина і множина іменників та прикметників', [7, 8], None),
        ('Жіночий і чоловічий рід іменників та прикметників', [6, 8], None),
        ('Дієслово: неправильні дієслова', [57, 58, 60, 71], 'main.conjugator'),
        ('Слабкі займенники (pronoms febles)', [15, 16, 17, 18, 19, 37, 38], None),
        ('Відносні займенники', [31], None),
        ('Прийменники та сполучники', [27, 28, 48, 67, 68, 69], None),
    ]),
    ('Лексика', [
        ('Сталі вирази (frases fetes)', [], 'course.phrases_page'),
        ('Синоніми', [], 'reader.index'),
        ('Словотвір', [51, 52], None),
    ]),
]

ARTICLE_TOPICS = [
    'Cal prohibir els mòbils a les escoles?',
    'El teletreball: avantatge o trampa?',
    'El turisme fa més bé que mal a les ciutats on vivim?',
    'Hauria de ser gratuït el transport públic?',
    'Les xarxes socials ens acosten o ens aïllen?',
    'Té sentit aprendre idiomes en l’època dels traductors automàtics?',
    'La intel·ligència artificial a l’escola: eina o perill?',
    'Hauríem de menjar menys carn?',
    'Els videojocs també són cultura?',
    'Cal limitar els pisos turístics?',
]

# (group label, [connectors]) — ordered as an article goes.
ARTICLE_CONNECTORS = [
    ('Почати', ['En primer lloc', 'Per començar', 'Avui dia', 'Darrerament']),
    ('Висловити думку', ['Al meu parer', 'Des del meu punt de vista', 'Considero que',
                         'Estic convençut que', 'Pel que fa a']),
    ('Додати', ['A més a més', 'D’altra banda', 'Així mateix', 'També cal tenir en compte que']),
    ('Протиставити', ['Tanmateix', 'No obstant això', 'Ara bé', 'En canvi', 'Tot i que',
                      'Malgrat que']),
    ('Причина', ['Ja que', 'Atès que', 'Perquè', 'Com que']),
    ('Наслідок', ['Per tant', 'En conseqüència', 'Així doncs', 'De manera que']),
    ('Приклад', ['Per exemple', 'Com ara', 'És a dir']),
    ('Завершити', ['En definitiva', 'En resum', 'Per acabar', 'Tot plegat']),
]

ARTICLE_STRUCTURE = [
    ('Заголовок', 'Короткий і чіткий, можна у формі питання.'),
    ('Вступ', 'Тема і ваша теза: що ви думаєте.'),
    ('Аргументи', 'Два-три аргументи, кожен в окремому абзаці, з прикладом.'),
    ('Контраргумент', 'Протилежна думка і чому вона вас не переконує.'),
    ('Висновок', 'Підсумок і пропозиція або запитання до читача.'),
]

MONOLOGUE_TOPICS = [
    ('Un llibre, una pel·lícula o una sèrie que t’hagi marcat',
     ['De què tracta?', 'Per què et va impressionar?', 'La recomanaries? A qui?']),
    ('Viure en una gran ciutat o en un poble',
     ['Avantatges', 'Inconvenients', 'On t’agradaria viure d’aquí a deu anys?']),
    ('Com ha canviat la teva vida des que vius aquí',
     ['Què et va sorprendre al principi?', 'Què trobes a faltar?', 'Què has après?']),
    ('El paper de les xarxes socials en la nostra vida',
     ['Com les fas servir tu?', 'Quins riscos tenen?', 'Com n’hauríem de fer un bon ús?']),
    ('L’escola ideal',
     ['Què hi canviaries?', 'Què hi mantindries?', 'Quin paper hi tenen els idiomes?']),
    ('El turisme al lloc on vius',
     ['Beneficis', 'Problemes', 'Quines solucions proposes?']),
    ('La importància d’aprendre llengües',
     ['Com vas aprendre el català?', 'Què t’ha costat més?', 'Quins consells donaries?']),
    ('Un viatge que no oblidaràs',
     ['On vas anar i amb qui?', 'Què va passar?', 'Què en vas aprendre?']),
    ('El canvi climàtic i els hàbits de cada dia',
     ['Què fas tu?', 'Què haurien de fer les institucions?', 'Ets optimista?']),
    ('Treballar des de casa o a l’oficina',
     ['Avantatges de cada opció', 'La teva experiència', 'Com serà la feina del futur?']),
]

MONOLOGUE_CONNECTORS = [
    'Doncs bé', 'Pel que fa a…', 'En el meu cas', 'Per posar un exemple',
    'Dit d’una altra manera', 'Com deia abans', 'Tornant al tema', 'D’una banda… de l’altra…',
    'Ara bé', 'Per acabar', 'En definitiva',
]

MONOLOGUE_CHECKLIST = [
    'Тему названо, і сказано, про що піде мова.',
    'Є вступ, основна частина і завершення.',
    'Є хоча б один приклад із власного досвіду.',
    'Використано щонайменше п’ять різних сполучних слів.',
    'Ті самі слова не повторюються весь час.',
    'Відкриті й закриті e та o, ненаголошені a та e звучать правильно.',
    'Мовлення тривало всі шість хвилин без довгих пауз.',
]
