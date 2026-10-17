"""Questions and answers for /faq, in Ukrainian and English.

Answers are HTML. ``{name}`` placeholders are filled with the site's links
(see ``links()``), so the same text serves the page and its structured data
for search engines. Each question has a stable ``id`` for links such as
``/faq#sound``; the two languages use the same ids.
"""

from flask import url_for

from flaskblog.i18n import get_locale

SUPPORT_EMAIL = 'support@learn-catalan.com'


def links():
    return {
        'grammar': url_for('grammar.index'),
        'grammar_unit_1': url_for('grammar.unit_by_number', number=1),
        'dictionary': url_for('vocabulary.dictionary'),
        'my_dictionary': url_for('vocabulary.my_dictionary'),
        'conjugator': url_for('main.conjugator'),
        'conjugator_anar': url_for('main.conjugator', verb='anar'),
        'phonetics': url_for('phonetics.index'),
        'register': url_for('users.register'),
        'login': url_for('users.login'),
        'reset': url_for('users.reset_request'),
        'developers': url_for('api_docs.developers'),
        'email': SUPPORT_EMAIL,
    }


UK = [
    {
        'id': 'general',
        'title': 'Загальне',
        'questions': [
            {
                'id': 'about',
                'q': 'Що таке Learn Catalan?',
                'a': """
<p>Learn Catalan — сайт для вивчення каталонської мови українською. Тут є:</p>
<ul>
  <li><a href="{grammar}">Граматика</a>: 70 юнітів від A1 до C1 з поясненнями, прикладами та вправами з відповідями.</li>
  <li><a href="{dictionary}">Словник</a>: понад 3 500 слів із перекладом, прикладами та рівнем.</li>
  <li><a href="{conjugator}">Дієвідміна</a>: усі часи та способи понад 8 000 дієслів.</li>
  <li><a href="{phonetics}">Фонетика</a>: уроки вимови з транскрипцією та озвученими прикладами.</li>
</ul>""",
            },
            {
                'id': 'price',
                'q': 'Скільки це коштує?',
                'a': """
<p>Нічого. Усі розділи сайту зараз відкриті безкоштовно, а для більшості не потрібна навіть реєстрація.</p>""",
            },
            {
                'id': 'start',
                'q': 'З чого почати, якщо я вивчаю каталонську з нуля?',
                'a': """
<ol>
  <li>Пройдіть перші уроки <a href="{phonetics}">фонетики</a>: алфавіт, голосні й наголос. Так ви одразу читатимете слова правильно.</li>
  <li>Почніть <a href="{grammar_unit_1}">граматику з юніту 1</a> і йдіть по порядку: кожен юніт спирається на попередні.</li>
  <li>Нові слова з юнітів шукайте у <a href="{dictionary}">словнику</a> і зберігайте в «Мій словник».</li>
</ol>""",
            },
            {
                'id': 'variety',
                'q': 'Яку каталанську ви вивчаєте?',
                'a': """
<p>Центральну, тобто барселонську: її найчастіше чують у Каталонії й вивчають на курсах.
Слова, які вживаються лише в інших регіонах (Валенсія, Балеарські острови тощо) або вже застаріли,
позначені у словнику, і поруч підказано, як кажуть у центральному варіанті.</p>""",
            },
            {
                'id': 'interface',
                'q': 'Як змінити мову інтерфейсу або увімкнути темну тему?',
                'a': """
<p>Кнопка <strong>EN</strong> / <strong>UA</strong> у верхньому рядку перемикає мову сайту між українською та англійською.
Англійська версія — це окремо адаптований курс для тих, хто говорить англійською, а не дослівний переклад.
Кнопка з місяцем або сонцем перемикає світлу й темну тему. Поки ви її не натиснули, сайт повторює налаштування вашого пристрою.</p>""",
            },
        ],
    },
    {
        'id': 'audio',
        'title': 'Звук і вимова',
        'questions': [
            {
                'id': 'sound',
                'q': 'Як увімкнути звук у розділі «Фонетика»?',
                'a': """
<p>Кнопки 🔊 у фонетиці (а також у словнику, дієвідміні й граматиці) читають каталонські слова
голосом, який уже є на вашому телефоні чи комп’ютері. Сайт нічого не надсилає стороннім
сервісам, тому для звуку на пристрої має бути встановлений <strong>каталонський голос</strong>.</p>
<ol class="faq-steps">
  <li><strong>Перевірте гучність.</strong> Увімкніть звук і збільште гучність медіа.
    На iPhone вимкніть беззвучний режим (перемикач або кнопка дії збоку).</li>
  <li><strong>Встановіть каталонський голос:</strong>
    <ul>
      <li><strong>Android:</strong> Налаштування → Система → Мова та введення → Синтез мовлення.
        Як рушій виберіть «Синтез мовлення Google» (Speech Services by Google), натисніть ⚙ →
        «Встановити голосові дані» → <em>Català</em> і завантажте голос.
        На Samsung спершу замініть рушій Samsung на Google. Назви пунктів у різних телефонів
        трохи відрізняються; найпростіше знайти «Синтез мовлення» пошуком у налаштуваннях.</li>
      <li><strong>iPhone та iPad:</strong> Параметри → Доступність → Озвучений вміст → Голоси →
        <em>Català</em> → завантажте голос (наприклад, Montserrat або Jordi).</li>
      <li><strong>Mac:</strong> Системні параметри → Доступність → Озвучений вміст →
        Системний голос → «Керувати голосами…» → <em>Català</em>.</li>
      <li><strong>Windows:</strong> найпростіше відкрити сайт у браузері <strong>Microsoft Edge</strong>:
        у ньому каталонські голоси вже є. Можна також додати голос у Параметри → Час і мова →
        Мовлення → «Додати голоси» → <em>Català</em>, але Chrome бачить такі голоси не завжди.</li>
    </ul>
  </li>
  <li><strong>Перезавантажте сторінку.</strong> Якщо звуку все ще немає, закрийте браузер
    і відкрийте його знову: деякі браузери бачать новий голос лише після перезапуску.</li>
  <li><strong>Натисніть 🔊</strong> біля прикладу в таблиці звуків або біля слова для тренування.</li>
</ol>""",
            },
            {
                'id': 'sound-trouble',
                'q': 'Звуку все одно немає. Що ще перевірити?',
                'a': """
<ul>
  <li><strong>З’являється жовте повідомлення</strong> «На цьому пристрої немає каталонського голосу»:
    голос ще не встановлено або браузер його не бачить. Повторіть встановлення й перезапустіть браузер.</li>
  <li><strong>Кнопок 🔊 немає зовсім:</strong> ваш браузер не вміє озвучувати текст.
    Відкрийте сайт у Chrome, Safari або Edge.</li>
  <li><strong>Кнопка підсвічується, але тихо:</strong> перевірте гучність саме медіа (не дзвінка)
    і чи не підключені навушники або колонка Bluetooth.</li>
</ul>
<p>Ми навмисно не підставляємо іспанський чи інший голос: він читав би каталанські слова з неправильними звуками.</p>""",
            },
            {
                'id': 'sound-speed',
                'q': 'Чому слова звучать повільніше, ніж у житті?',
                'a': """
<p>Ми трохи сповільнюємо озвучення, щоб було легше розчути кожен звук, особливо ненаголошені голосні.
Як звучить мова в живому темпі, пояснюють уроки розділу «Вимова у мовленні».</p>""",
            },
            {
                'id': 'ipa',
                'q': 'Що означають символи у квадратних дужках, наприклад [ˈɔlə]?',
                'a': """
<p>Це транскрипція за Міжнародним фонетичним алфавітом (МФА): вона показує, як слово звучить, а не як пишеться.
Знак ˈ стоїть перед наголошеним складом. Усі символи пояснені в першому уроці <a href="{phonetics}">фонетики</a>,
а в кожному уроці є таблиця звуків з українськими відповідниками.</p>""",
            },
        ],
    },
    {
        'id': 'learning',
        'title': 'Навчання',
        'questions': [
            {
                'id': 'grammar',
                'q': 'Як влаштований курс граматики?',
                'a': """
<p>Курс складається з 70 юнітів: від A1 до C1. Кожен юніт — це коротке пояснення, таблиця прикладів
із перекладом і вправи. Юніти можна проходити по порядку або <a href="{grammar}?sort=topic">за темами</a>.</p>""",
            },
            {
                'id': 'answers',
                'q': 'Як перевірити відповіді у вправах?',
                'a': """
<p>Під вправами кожного юніту та уроку фонетики є кнопка «Показати відповіді».
Спершу виконайте вправу самостійно, а тоді відкрийте відповіді й порівняйте.</p>""",
            },
            {
                'id': 'dictionary',
                'q': 'Як шукати слова у словнику?',
                'a': """
<p>Вводьте слово каталонською або українською в рядку пошуку вгорі сторінки чи в <a href="{dictionary}">словнику</a>.
Там же можна відфільтрувати слова за темою, рівнем, частиною мови та регіоном.
На сторінці слова є переклад, приклад, озвучення, а для дієслів — посилання на дієвідміну.</p>""",
            },
            {
                'id': 'conjugator',
                'q': 'Як користуватися дієвідміною?',
                'a': """
<p>Введіть дієслово в інфінітиві, наприклад <a href="{conjugator_anar}">anar</a>, і ви побачите
всі часи та способи з особовими формами. Якщо дієслово є у словнику, поруч буде його переклад.
Зворотні дієслова вводьте з -se: <em>rentar-se</em>.</p>""",
            },
            {
                'id': 'api',
                'q': 'Чи можна використати словник і дієвідміну у своєму застосунку?',
                'a': """
<p>Так. Словник і дієвідміна доступні через відкритий API у форматі JSON, без ключа:
їх можна вбудувати у свій сайт, застосунок чи бота. Опис і приклади — на сторінці
<a href="{developers}">API для розробників</a>.</p>""",
            },
        ],
    },
    {
        'id': 'account',
        'title': 'Обліковий запис',
        'questions': [
            {
                'id': 'register',
                'q': 'Чи потрібно реєструватися?',
                'a': """
<p>Ні, уроки, словник і дієвідміна відкриті без реєстрації. Обліковий запис потрібен лише для «Мого словника».
Щоб його створити, відкрийте сторінку <a href="{register}">Зареєструватися</a>, введіть ім’я
(від 2 до 20 символів), електронну пошту й пароль двічі.</p>""",
            },
            {
                'id': 'my-dictionary',
                'q': 'Що таке «Мій словник»?',
                'a': """
<p>Ваш особистий список слів. Додавайте слова кнопкою <strong>+</strong> у словнику або вписуйте власні,
позначайте вивчені як «знаю» і додавайте нотатки. Список можна завантажити у файл CSV.</p>""",
            },
            {
                'id': 'password',
                'q': 'Як відновити пароль?',
                'a': """
<p>На сторінці <a href="{login}">Увійти</a> натисніть «<a href="{reset}">Забули пароль?</a>»,
введіть свою електронну пошту, і ми надішлемо лист із посиланням для зміни пароля.
Якщо листа немає кілька хвилин, перевірте папку «Спам».</p>""",
            },
        ],
    },
    {
        'id': 'contact',
        'title': 'Зв’язок',
        'questions': [
            {
                'id': 'mistake',
                'q': 'Я знайшов помилку. Що робити?',
                'a': """
<p>Напишіть нам на <a href="mailto:{email}?subject=Error on the LearnCatalan">{email}</a>:
вкажіть сторінку (або слово) і що саме не так. Ми виправляємо помилки якомога швидше.</p>""",
            },
            {
                'id': 'contact-us',
                'q': 'Як з вами зв’язатися?',
                'a': """
<p>З будь-якими питаннями та пропозиціями пишіть на <a href="mailto:{email}">{email}</a>.</p>""",
            },
        ],
    },
]


EN = [
    {
        'id': 'general',
        'title': 'General',
        'questions': [
            {
                'id': 'about',
                'q': 'What is Learn Catalan?',
                'a': """
<p>Learn Catalan is a website for learning Catalan. It has:</p>
<ul>
  <li><a href="{grammar}">Grammar</a>: 70 units from A1 to C1 with explanations, examples and exercises with answers.</li>
  <li>A <a href="{dictionary}">dictionary</a> of over 3,500 words with translations, examples and levels.</li>
  <li>A <a href="{conjugator}">conjugator</a> with every tense and mood of over 8,000 verbs.</li>
  <li><a href="{phonetics}">Pronunciation</a> lessons with phonetic transcription and audio examples.</li>
</ul>""",
            },
            {
                'id': 'price',
                'q': 'How much does it cost?',
                'a': """
<p>Nothing. Every section of the site is currently free, and most of them don’t even need an account.</p>""",
            },
            {
                'id': 'start',
                'q': 'Where should I start if I am a complete beginner?',
                'a': """
<ol>
  <li>Go through the first <a href="{phonetics}">pronunciation</a> lessons: the alphabet, vowels and stress. Then you will read words correctly from the start.</li>
  <li>Start the <a href="{grammar_unit_1}">grammar at unit 1</a> and follow the order: each unit builds on the earlier ones.</li>
  <li>Look up new words from the units in the <a href="{dictionary}">dictionary</a> and save them to “My dictionary”.</li>
</ol>""",
            },
            {
                'id': 'variety',
                'q': 'Which Catalan do you teach?',
                'a': """
<p>Central (Barcelona) Catalan: the variety you hear most in Catalonia and learn on most courses.
Words used only in other regions (Valencia, the Balearic Islands and so on) or no longer in use are marked
in the dictionary, with the Central Catalan word shown next to them.</p>""",
            },
            {
                'id': 'interface',
                'q': 'How do I change the interface language or switch to dark mode?',
                'a': """
<p>The <strong>EN</strong> / <strong>UA</strong> button in the top bar switches the site between English and Ukrainian.
The English version is a course adapted for English speakers, not a word-for-word translation.
The moon or sun button switches between light and dark mode. Until you press it, the site follows your device’s setting.</p>""",
            },
        ],
    },
    {
        'id': 'audio',
        'title': 'Audio and pronunciation',
        'questions': [
            {
                'id': 'sound',
                'q': 'How do I turn on audio in the Pronunciation section?',
                'a': """
<p>The 🔊 buttons in the pronunciation lessons (and in the dictionary, conjugation and grammar)
read Catalan words aloud with a voice that is already on your phone or computer. The site sends
nothing to outside services, so your device needs a <strong>Catalan voice</strong> installed.</p>
<ol class="faq-steps">
  <li><strong>Check the volume.</strong> Turn the sound on and raise the media volume.
    On an iPhone, turn off Silent mode (the switch or Action button on the side).</li>
  <li><strong>Install a Catalan voice:</strong>
    <ul>
      <li><strong>Android:</strong> Settings → System → Languages &amp; input → Text-to-speech output.
        Choose “Speech Services by Google” as the engine, tap ⚙ → “Install voice data” →
        <em>Català</em> and download the voice. On Samsung phones switch the engine from Samsung
        to Google first. Menu names vary between phones; searching the settings for
        “Text-to-speech” is the quickest way.</li>
      <li><strong>iPhone and iPad:</strong> Settings → Accessibility → Spoken Content → Voices →
        <em>Català</em> → download a voice (for example Montserrat or Jordi).</li>
      <li><strong>Mac:</strong> System Settings → Accessibility → Spoken Content →
        System voice → “Manage Voices…” → <em>Català</em>.</li>
      <li><strong>Windows:</strong> the easiest way is to open the site in <strong>Microsoft Edge</strong>,
        which already has Catalan voices. You can also add one in Settings → Time &amp; language →
        Speech → “Add voices” → <em>Català</em>, but Chrome does not always see these voices.</li>
    </ul>
  </li>
  <li><strong>Reload the page.</strong> If there is still no sound, close the browser and open it
    again: some browsers only see a new voice after a restart.</li>
  <li><strong>Press 🔊</strong> next to an example in the table of sounds or next to a practice word.</li>
</ol>""",
            },
            {
                'id': 'sound-trouble',
                'q': 'There is still no sound. What else can I check?',
                'a': """
<ul>
  <li><strong>A yellow message appears</strong> saying “This device has no Catalan voice”:
    the voice is not installed yet or the browser cannot see it. Install it again and restart the browser.</li>
  <li><strong>There are no 🔊 buttons at all:</strong> your browser cannot read text aloud.
    Open the site in Chrome, Safari or Edge.</li>
  <li><strong>The button lights up but you hear nothing:</strong> check the media volume (not the ringer)
    and whether headphones or a Bluetooth speaker are connected.</li>
</ul>
<p>We deliberately don’t fall back to a Spanish or other voice: it would read Catalan words with the wrong sounds.</p>""",
            },
            {
                'id': 'sound-speed',
                'q': 'Why are words read more slowly than in real life?',
                'a': """
<p>We slow the audio down a little so every sound is easier to hear, especially unstressed vowels.
The lessons in “Connected speech” explain how Catalan sounds at natural speed.</p>""",
            },
            {
                'id': 'ipa',
                'q': 'What do the symbols in square brackets, such as [ˈɔlə], mean?',
                'a': """
<p>This is a transcription in the International Phonetic Alphabet (IPA): it shows how a word sounds, not how it is spelt.
The mark ˈ comes before the stressed syllable. Every symbol is explained in the first <a href="{phonetics}">pronunciation</a>
lesson, and each lesson has a table of sounds with English comparisons.</p>""",
            },
        ],
    },
    {
        'id': 'learning',
        'title': 'Learning',
        'questions': [
            {
                'id': 'grammar',
                'q': 'How is the grammar course organised?',
                'a': """
<p>The course has 70 units from A1 to C1. Each unit has a short explanation, a table of examples
with translations, and exercises. You can follow the units in order or <a href="{grammar}?sort=topic">by topic</a>.</p>""",
            },
            {
                'id': 'answers',
                'q': 'How do I check my answers to the exercises?',
                'a': """
<p>Below the exercises of every grammar unit and pronunciation lesson there is a “Show answers” button.
Do the exercise on your own first, then open the answers and compare.</p>""",
            },
            {
                'id': 'dictionary',
                'q': 'How do I search the dictionary?',
                'a': """
<p>Type a word in Catalan or English in the search box at the top of the page or in the <a href="{dictionary}">dictionary</a>.
There you can also filter words by topic, level, part of speech and region.
A word’s page has its translation, an example, audio and, for verbs, a link to the conjugation.</p>""",
            },
            {
                'id': 'conjugator',
                'q': 'How do I use the conjugator?',
                'a': """
<p>Enter a verb in the infinitive, for example <a href="{conjugator_anar}">anar</a>, to see every tense and mood
with all the personal forms. If the verb is in the dictionary, its translation is shown too.
Enter reflexive verbs with -se: <em>rentar-se</em>.</p>""",
            },
            {
                'id': 'api',
                'q': 'Can I use the dictionary and conjugator in my own app?',
                'a': """
<p>Yes. The dictionary and conjugator are available through an open JSON API with no key:
build them into your site, app or bot. See <a href="{developers}">API for developers</a>
for the details and examples.</p>""",
            },
        ],
    },
    {
        'id': 'account',
        'title': 'Your account',
        'questions': [
            {
                'id': 'register',
                'q': 'Do I need to sign up?',
                'a': """
<p>No, the lessons, dictionary and conjugator are open to everyone. You only need an account for “My dictionary”.
To create one, open <a href="{register}">Sign up</a> and enter a username (2 to 20 characters),
your email and your password twice.</p>""",
            },
            {
                'id': 'my-dictionary',
                'q': 'What is “My dictionary”?',
                'a': """
<p>Your own word list. Add words with the <strong>+</strong> button in the dictionary or type in your own,
mark the ones you have learnt as “known” and add notes. You can download the list as a CSV file.</p>""",
            },
            {
                'id': 'password',
                'q': 'How do I reset my password?',
                'a': """
<p>On the <a href="{login}">Log in</a> page, press “<a href="{reset}">Forgot your password?</a>”,
enter your email, and we will send you a link to set a new password.
If the email hasn’t arrived after a few minutes, check your spam folder.</p>""",
            },
        ],
    },
    {
        'id': 'contact',
        'title': 'Contact',
        'questions': [
            {
                'id': 'mistake',
                'q': 'I found a mistake. What should I do?',
                'a': """
<p>Write to <a href="mailto:{email}?subject=Error on the LearnCatalan">{email}</a>
with the page (or word) and what is wrong. We fix mistakes as quickly as we can.</p>""",
            },
            {
                'id': 'contact-us',
                'q': 'How can I contact you?',
                'a': """
<p>For any questions or suggestions, write to <a href="mailto:{email}">{email}</a>.</p>""",
            },
        ],
    },
]

_SECTIONS = {'uk': UK, 'en': EN}


def sections(lang=None):
    """The FAQ for a language, with the links filled in."""
    urls = links()
    return [
        dict(section, questions=[
            dict(question, a=question['a'].strip().format(**urls))
            for question in section['questions']
        ])
        for section in _SECTIONS.get(lang or get_locale(), UK)
    ]


def structured_data(sections):
    """schema.org FAQPage, so search engines can show the answers."""
    return {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [
            {
                '@type': 'Question',
                'name': question['q'],
                'acceptedAnswer': {'@type': 'Answer', 'text': question['a']},
            }
            for section in sections
            for question in section['questions']
        ],
    }
