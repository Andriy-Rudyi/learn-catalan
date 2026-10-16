"""English interface strings, keyed by the Ukrainian source text.

Course content (grammar units, phonetics lessons, dictionary entries) is not
here: it has its own English versions in the data files. Run the test suite
after adding a ``_()`` string: it fails when an English page shows Cyrillic.
"""

MESSAGES = {
    # -- navigation and layout -----------------------------------------
    'Граматика': 'Grammar',
    'Словник': 'Dictionary',
    'Дієвідміна': 'Conjugation',
    'Фонетика': 'Pronunciation',
    'Новий урок': 'New lesson',
    'Мій словник': 'My dictionary',
    'Моя сторінка': 'My account',
    'Вийти': 'Log out',
    'Увійти': 'Log in',
    'Зареєструватися': 'Sign up',
    'Меню': 'Menu',
    'Закрити': 'Close',
    'Перемкнути тему': 'Switch theme',
    'Перемкнути світлу / темну тему': 'Switch between light and dark theme',
    'Уроки': 'Lessons',
    'На головну': 'Back to the home page',
    'Прослухати': 'Listen',
    'Увійдіть, щоб відкрити цю сторінку.': 'Please log in to open this page.',
    'На цьому пристрої немає каталонського голосу для озвучення. Додайте його в налаштуваннях: <strong>Android</strong>: «Синтез мовлення» Google → мова «Català»; <strong>iPhone</strong>: Універсальний доступ → Озвучений вміст → Голоси → Català; <strong>Windows</strong>: Час і мова → Мовлення → додати каталонську, або відкрийте сайт у браузері Edge.': (
        'This device has no Catalan voice for reading aloud. You can add one in the settings: '
        '<strong>Android</strong>: Google Text-to-speech → language “Català”; '
        '<strong>iPhone</strong>: Accessibility → Spoken Content → Voices → Català; '
        '<strong>Windows</strong>: Time &amp; language → Speech → add Catalan, or open the site in Microsoft Edge.'
    ),

    # -- home page ---------------------------------------------------------
    'Вивчайте каталонську українською': 'Learn Catalan in English',
    'Граматичний курс у стилі Murphy, каталонсько-український словник і перевірена дієвідміна дієслів в одному місці.': (
        'A Murphy-style grammar course, a Catalan-English dictionary, verified verb '
        'conjugation and pronunciation lessons in one place.'
    ),
    'Розпочати навчання': 'Start learning',
    'Почати з вимови': 'Start with pronunciation',
    'Короткі пояснення, приклади й вправи з відповідями, від A1 до C1.': (
        'Short explanations, examples and exercises with answers, from A1 to C1.'
    ),
    'Слова з перекладом, прикладами та рівнем. Збирайте власний словник і позначайте вивчене.': (
        'Words with translations, examples and levels. Build your own word list and mark what you know.'
    ),
    'Усі часи та способи каталонських дієслів із перекладом.': (
        'Every tense and mood of Catalan verbs, with translations.'
    ),
    'понад 8 000 дієслів': 'over 8,000 verbs',
    'Звуки, наголос і вимова з транскрипцією та озвученими прикладами.': (
        'Sounds, stress and connected speech, with IPA and spoken examples.'
    ),
    'Зареєструйтеся, щоб зберігати слова у «Мій словник» і стежити за прогресом.': (
        'Sign up to save words to “My dictionary” and track your progress.'
    ),
    'Створити акаунт': 'Create an account',

    # -- conjugator --------------------------------------------------------
    'Введіть каталонське дієслово в інфінітиві, наприклад <em>parlar</em>, <em>ser</em> або <em>tenir</em>.': (
        'Type a Catalan verb in the infinitive, for example <em>parlar</em>, <em>ser</em> or <em>tenir</em>.'
    ),
    'Введіть дієслово': 'Type a verb',
    'Відміняти': 'Conjugate',
    'Приклади:': 'Examples:',
    'Можливо, ви мали на увазі:': 'Did you mean:',
    'перевірено': 'verified',
    'Форми цього дієслова звірені з довідниками та перевіряються тестами': (
        'The forms of this verb have been checked against reference grammars and are covered by tests'
    ),
    'зі словника verbecc': 'from the verbecc dictionary',
    'Форми взято зі словника дієслів verbecc і не звірені вручну': (
        'The forms come from the verbecc verb dictionary and have not been checked by hand'
    ),
    'У словнику': 'In the dictionary',
    'у вашому словнику': 'in your dictionary',
    'Додати до мого словника': 'Add to my dictionary',
    'Перекладу цього дієслова ще немає у словнику.': 'This verb has no translation in the dictionary yet.',
    'Додати його': 'Add it',
    'Зразок дієвідміни:': 'Conjugation model:',
    'основа:': 'stem:',
    'дані виправлені вручну': 'data corrected by hand',
    'Нижче наведено дієвідміну дієслова <strong>{infinitive}</strong>. Займенник <code>{suffix}</code> додається до форми окремо: <em>jo em rento</em>, <em>ell es renta</em>.': (
        'Below is the conjugation of <strong>{infinitive}</strong>. The pronoun '
        '<code>{suffix}</code> is added to each form separately: <em>jo em rento</em>, <em>ell es renta</em>.'
    ),
    'Складені часи (<em>he parlat</em>, <em>vaig parlar</em>) утворені з дієприкметника та допоміжного дієслова.': (
        'Compound tenses (<em>he parlat</em>, <em>vaig parlar</em>) are built from the past participle and an auxiliary verb.'
    ),
    # moods and tenses
    'Дійсний спосіб (indicatiu)': 'Indicative (indicatiu)',
    'Умовний спосіб (subjuntiu)': 'Subjunctive (subjuntiu)',
    'Умовний час (condicional)': 'Conditional (condicional)',
    'Наказовий спосіб (imperatiu)': 'Imperative (imperatiu)',
    'Інфінітив (infinitiu)': 'Infinitive (infinitiu)',
    'Дієприслівник (gerundi)': 'Gerund (gerundi)',
    'Дієприкметник (particip)': 'Past participle (particip)',
    'Теперішній': 'Present',
    'Минулий незакінчений (imperfet)': 'Imperfect (imperfet)',
    'Минулий простий (passat simple)': 'Simple past (passat simple)',
    'Минулий складний (passat perifràstic)': 'Periphrastic past (passat perifràstic)',
    'Минулий завершений (perfet)': 'Present perfect (perfet)',
    'Давноминулий (plusquamperfet)': 'Pluperfect (plusquamperfet)',
    'Передминулий (passat anterior)': 'Past anterior (passat anterior)',
    'Майбутній': 'Future',
    'Майбутній завершений': 'Future perfect',
    'Завершений': 'Perfect',
    'Наказові форми': 'Commands',
    'Простий': 'Simple',
    'Складений': 'Compound',
    'Форми': 'Forms',
    '1 ос. одн.': '1st sg.',
    '2 ос. одн.': '2nd sg.',
    '3 ос. одн.': '3rd sg.',
    '1 ос. мн.': '1st pl.',
    '2 ос. мн.': '2nd pl.',
    '3 ос. мн.': '3rd pl.',
    'чол. одн.': 'masc. sg.',
    'жін. одн.': 'fem. sg.',
    'чол. мн.': 'masc. pl.',
    'жін. мн.': 'fem. pl.',
    # conjugator errors
    'Введіть дієслово в інфінітиві, наприклад «parlar».': 'Type a verb in the infinitive, for example “parlar”.',
    'Це задовго для дієслова. Перевірте, чи не вставилося кілька слів.': (
        'That is too long for a verb. Check that you haven’t pasted several words.'
    ),
    'Введіть одне дієслово в інфінітиві, без займенників та інших слів (наприклад «parlar», а не «jo parlo»).': (
        'Type a single verb in the infinitive, without pronouns or other words '
        '(for example “parlar”, not “jo parlo”).'
    ),
    'У слові є символи, яких не буває в каталонських дієсловах.': (
        'The word contains characters that Catalan verbs never have.'
    ),
    'Такого дієслова немає в каталонському словнику дієслів.': 'There is no such verb in the Catalan verb dictionary.',
    'Не вдалося відмінити це дієслово. Спробуйте інше.': 'This verb could not be conjugated. Please try another one.',
    'Не вдалося розпізнати дієслово.': 'The verb could not be recognised.',

    # -- dictionary --------------------------------------------------------
    'Каталонсько-український словник': 'Catalan-English dictionary',
    'Додати слово': 'Add a word',
    'Імпорт': 'Import',
    'слово каталонською або українською': 'a word in Catalan or English',
    'Пошук': 'Search',
    'Знайти': 'Search',
    'у словнику': 'saved',
    'За цим запитом слів не знайдено.': 'No words match your search.',
    'Словник ще порожній.': 'The dictionary is empty.',
    'Завантажити стартовий набір': 'Load the starter set',
    'Завантажити словник у CSV': 'Download the dictionary as CSV',
    'До словника': 'Back to the dictionary',
    'Приклад': 'Example',
    'Примітки': 'Notes',
    'Дієвідміна дієслова «{term}»': 'Conjugate “{term}”',
    'Редагувати': 'Edit',
    'Видалити': 'Delete',
    'Видалити «{term}» зі словника?': 'Delete “{term}” from the dictionary?',
    'Скасувати': 'Cancel',
    'Нове слово': 'New word',
    'Редагувати слово': 'Edit word',
    'Слово додано до словника.': 'The word has been added to the dictionary.',
    'Слово оновлено.': 'The word has been updated.',
    'Слово видалено.': 'The word has been deleted.',
    # word form
    'Каталонською': 'Catalan',
    'Українською': 'Ukrainian',
    'Англійською': 'English',
    'Переклад': 'Translation',
    'Частина мови': 'Part of speech',
    'Рід': 'Gender',
    'Вимова': 'Pronunciation',
    'Тема': 'Topic',
    'Рівень': 'Level',
    'Приклад каталонською': 'Example in Catalan',
    'Переклад прикладу': 'Example translation (Ukrainian)',
    'Переклад прикладу англійською': 'Example translation (English)',
    'Примітки англійською': 'Notes in English',
    'Зберегти': 'Save',
    '(не вказано)': '(not set)',
    'Усі теми': 'All topics',
    'Усі рівні': 'All levels',
    'Усі частини мови': 'All parts of speech',
    'Нотатка': 'Note',
    'Додати': 'Add',
    'Файл CSV': 'CSV file',
    'Потрібен файл .csv': 'A .csv file is required',
    'Завантажити': 'Upload',
    'Готово': 'Done',
    # import
    'Імпорт словника': 'Import words',
    'У словнику зараз:': 'The dictionary currently has',
    'Стартовий набір': 'Starter set',
    'Базова лексика, що постачається з проєктом. Слова, які вже є у словнику, не дублюються.': (
        'The core vocabulary shipped with the project. Words already in the dictionary are not duplicated.'
    ),
    'Свій файл CSV': 'Your own CSV file',
    'Колонки:': 'Columns:',
    'Обов’язкові лише <code>term</code> і <code>translation</code>.': (
        'Only <code>term</code> and <code>translation</code> are required.'
    ),
    'Зразок можна отримати, експортувавши словник:': 'For a sample, export the dictionary:',
    'Оновлювати слова, які вже є у словнику': 'Update words that are already in the dictionary',
    'Імпорт завершено: додано {created}, оновлено {updated}, пропущено {skipped}.': (
        'Import finished: {created} added, {updated} updated, {skipped} skipped.'
    ),
    'рядок {number}: потрібні колонки term і translation': 'row {number}: the term and translation columns are required',
    # my dictionary
    'Загальний словник': 'Full dictionary',
    'Додати своє слово': 'Add your own word',
    'говорити': 'speak',
    'необов’язково': 'optional',
    'Усі': 'All',
    'Вчу': 'Learning',
    'Знаю': 'Known',
    'Дії': 'Actions',
    'Зберегти нотатку': 'Save the note',
    'Позначити як «вчу»': 'Mark as “learning”',
    'Позначити як «знаю»': 'Mark as “known”',
    'вчу': 'learning',
    'знаю': 'known',
    'Вилучити': 'Remove',
    'Завантажити мій словник у CSV': 'Download my dictionary as CSV',
    'У цій категорії поки нічого немає.': 'Nothing here yet.',
    'Ваш словник порожній. Додайте слово вище або оберіть його': (
        'Your dictionary is empty. Add a word above or pick one'
    ),
    'у загальному словнику': 'from the full dictionary',
    '«{term}» додано до вашого словника.': '“{term}” has been added to your dictionary.',
    '«{term}» вже є у вашому словнику.': '“{term}” is already in your dictionary.',
    'Слово вилучено з вашого словника.': 'The word has been removed from your dictionary.',
    'Нотатку збережено.': 'The note has been saved.',
    # parts of speech
    'іменник': 'noun',
    'дієслово': 'verb',
    'прикметник': 'adjective',
    'прислівник': 'adverb',
    'займенник': 'pronoun',
    'числівник': 'numeral',
    'прийменник': 'preposition',
    'сполучник': 'conjunction',
    'вигук': 'interjection',
    'вираз': 'phrase',
    # topics
    'Вітання та знайомство': 'Greetings and introductions',
    'Сім’я та люди': 'Family and people',
    'Їжа та напої': 'Food and drink',
    'Дім і побут': 'Home and household',
    'Місто й транспорт': 'City and transport',
    'Робота й навчання': 'Work and study',
    'Час і дати': 'Time and dates',
    'Числа': 'Numbers',
    'Тіло та здоров’я': 'Body and health',
    'Одяг': 'Clothes',
    'Природа й погода': 'Nature and weather',
    'Тварини': 'Animals',
    'Подорожі': 'Travel',
    'Покупки та гроші': 'Shopping and money',
    'Почуття та характер': 'Feelings and character',
    'Кольори': 'Colours',
    'Спілкування': 'Communication',
    'Дозвілля та спорт': 'Leisure and sport',
    'Суспільство': 'Society',
    'Каталонська культура': 'Catalan culture',
    'Базова лексика': 'Basic vocabulary',
    # levels
    'A1 (початковий)': 'A1 (beginner)',
    'A2 (елементарний)': 'A2 (elementary)',
    'B1 (середній)': 'B1 (intermediate)',
    'B2 (вище середнього)': 'B2 (upper intermediate)',
    'C1 (продвинутий)': 'C1 (advanced)',
    # genders
    'чоловічий (el)': 'masculine (el)',
    'жіночий (la)': 'feminine (la)',
    'чоловічий і жіночий': 'masculine and feminine',

    # -- grammar course ----------------------------------------------------
    'Курс каталонської граматики:': 'Catalan grammar course:',
    'Кожен юніт містить коротке пояснення з прикладами і вправи з відповідями.': (
        'Each unit is a short explanation with examples, followed by exercises with answers.'
    ),
    'Сортувати:': 'Sort:',
    'Сортування юнітів': 'Unit order',
    'за номером': 'by number',
    'за темою': 'by topic',
    'Курс ще не завантажено.': 'The course has not been loaded yet.',
    'До списку юнітів': 'All units',
    'Приклади': 'Examples',
    'Вправи': 'Exercises',
    'Показати відповіді': 'Show answers',
    'Приховати відповіді': 'Hide answers',
    # sections
    'Дієслово: основи': 'Verb basics',
    'Іменник, артикль, прикметник': 'Nouns, articles and adjectives',
    'Займенники та означники': 'Pronouns and determiners',
    'Будова речення': 'Sentence structure',
    'Минулі часи': 'Past tenses',
    'Майбутнє, умовний, наказовий': 'Future, conditional and imperative',
    'Прийменники': 'Prepositions',
    'Порівняння': 'Comparison',
    'Умовні речення': 'Conditional sentences',
    'Словотвір': 'Word formation',
    'Орфографія': 'Spelling',
    'Числа й час': 'Numbers and time',
    'Subjuntiu': 'Subjunctive',

    # -- phonetics ---------------------------------------------------------
    'Як звучить каталанська:': 'How Catalan sounds:',
    'про звуки, наголос і вимову у мовленні. У кожному уроці є таблиця звуків із транскрипцією, слова для тренування з кнопкою 🔊 і вправи. За основу взято центральну (барселонську) вимову.': (
        'on sounds, stress and connected speech. Each lesson has a table of sounds with IPA, '
        'practice words with a 🔊 button, and exercises. The model is Central (Barcelona) Catalan.'
    ),
    'До списку уроків': 'All lessons',
    'Звуки': 'Sounds',
    'Літери': 'Letters',
    'Звук': 'Sound',
    'Слова для тренування': 'Practice words',
    'Озвучення використовує каталонський голос вашого браузера або телефона.': (
        'Audio uses the Catalan voice of your browser or phone.'
    ),
    'Основи': 'Basics',
    'Голосні': 'Vowels',
    'Приголосні': 'Consonants',
    'Наголос і склад': 'Stress and syllables',
    'Вимова у мовленні': 'Connected speech',

    # -- accounts ----------------------------------------------------------
    'Ім’я користувача': 'Username',
    'Пароль': 'Password',
    'Підтвердіть пароль': 'Confirm password',
    'Запам’ятати мене': 'Remember me',
    'Оновити фото профілю': 'Update profile picture',
    'Оновити': 'Update',
    'Скинути пароль': 'Reset password',
    'Змінити пароль': 'Change password',
    'Це ім’я вже зайняте. Оберіть інше.': 'That username is taken. Please choose another one.',
    'Цей email уже зареєстровано. Оберіть інший.': 'That email is already registered. Please use another one.',
    'Акаунта з таким email немає. Спершу зареєструйтеся.': 'There is no account with that email. Please sign up first.',
    'Акаунт створено! Тепер можна увійти.': 'Your account has been created! You can now log in.',
    'Не вдалося увійти. Перевірте email і пароль.': 'Login failed. Please check your email and password.',
    'Акаунт оновлено!': 'Your account has been updated!',
    'Ми надіслали лист з інструкцією, як змінити пароль.': 'We have sent you an email with instructions to reset your password.',
    'Посилання недійсне або застаріло.': 'This link is invalid or has expired.',
    'Пароль змінено! Тепер можна увійти.': 'Your password has been changed! You can now log in.',
    'Реєстрація': 'Sign up',
    'Вхід': 'Log in',
    'Зміна пароля': 'Reset password',
    'Забули пароль?': 'Forgot your password?',
    'Потрібен обліковий запис?': 'Need an account?',
    'Зареєструватися зараз': 'Sign up now',
    'Вже є обліковий запис?': 'Already have an account?',
    'Інформація про обліковий запис': 'Account details',
    'LearnCatalan: зміна пароля': 'LearnCatalan: reset your password',
    'Щоб змінити пароль, перейдіть за посиланням:\n{link}\n\nЯкщо ви не надсилали цього запиту, просто проігноруйте лист, нічого не зміниться.\n': (
        'To reset your password, follow this link:\n{link}\n\n'
        'If you did not request this, just ignore this email and nothing will change.\n'
    ),

    # -- error pages -------------------------------------------------------
    'У вас немає доступу до цієї сторінки (403)': 'You don’t have access to this page (403)',
    'Перевірте, чи ви увійшли до потрібного акаунта, і спробуйте ще раз.': (
        'Check that you are logged in to the right account and try again.'
    ),
    'Сторінку не знайдено (404)': 'Page not found (404)',
    'Такої сторінки немає. Перевірте адресу або поверніться на головну.': (
        'This page doesn’t exist. Check the address or go back to the home page.'
    ),
    'Щось пішло не так (500)': 'Something went wrong (500)',
    'На сервері сталася помилка. Спробуйте трохи пізніше.': 'The server ran into a problem. Please try again a little later.',

    # -- regional varieties ------------------------------------------------
    'валенсійське': 'Valencian',
    'балеарське': 'Balearic',
    'північно-західне (Льєйда)': 'North-Western (Lleida)',
    'західне': 'Western',
    'північнокаталанське (Руссільйон)': 'Northern Catalan (Roussillon)',
    'альгерське': 'Algherese',
    'діалектне': 'dialectal',
    'застаріле': 'archaic',
    'Не вживається в центральному каталанському': 'Not used in Central Catalan',
    'Не центральне слово': 'Not Central Catalan',
    'У центральному каталанському кажуть:': 'Central Catalan uses:',
    'Позначку підтверджено у Вікісловнику.': 'Confirmed by Wiktionary.',
    'Попередня позначка, ще не звірена зі словником.': 'Preliminary mark, not yet checked against a dictionary.',
    'Діалект': 'Variety',
    'Усі слова': 'All words',
    'Лише центральні': 'Central Catalan only',
    'Лише регіональні й застарілі': 'Regional / archaic',
    # -- header ------------------------------------------------------------
    'Пошук слова': 'Search for a word',
    'Результати для «{query}»': 'Results for “{query}”',
    'Фільтри': 'Filters',
}
