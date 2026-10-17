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
    'Інші мови — колонки <code>translation_fr</code>, <code>example_fr</code>, <code>notes_fr</code> (і так само для it, es, pl, de, ar, zh).': (
        'Other languages: columns <code>translation_fr</code>, <code>example_fr</code>, <code>notes_fr</code> '
        '(and the same for it, es, pl, de, ar, zh).'
    ),
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
    'Показати пароль': 'Show password',
    'Раді бачити вас знову! Увійдіть, щоб відкрити «Мій словник».': 'Welcome back! Log in to open “My dictionary”.',
    'Створіть акаунт, щоб зберігати слова в «Мій словник» і позначати вивчені.': (
        'Create an account to save words to “My dictionary” and mark the ones you know.'
    ),
    'Від 2 до 20 символів.': '2 to 20 characters.',
    'Введіть email, з яким ви реєструвалися, і ми надішлемо посилання для зміни пароля.': (
        'Enter the email you signed up with and we will send you a link to reset your password.'
    ),
    'Назад до входу': 'Back to log in',
    'Придумайте новий пароль для свого акаунта.': 'Choose a new password for your account.',
    'Редактор сайту': 'Site editor',
    'усього слів': 'words in total',
    'Ім’я редактора сайту змінити не можна.': 'The site editor’s username cannot be changed.',
    'Виберіть фото (JPG або PNG)': 'Choose a photo (JPG or PNG)',
    'Слова, які ви вчите. Позначайте вивчені й додавайте нотатки.': 'Words you are learning. Mark the ones you know and add notes.',
    'Фільтр': 'Filter',
    'Відкрити словник': 'Open the dictionary',
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
    'Мова сайту': 'Site language',
    'Машинний переклад, ще не перевірений редактором.': 'Machine translation, not yet checked by an editor.',
    # -- design switch and FAQ ----------------------------------------------
    'Часті запитання': 'Frequently asked questions',
    'Відповіді на найчастіші запитання про сайт. Не знайшли свого? Напишіть нам:': (
        'Answers to the most common questions about the site. Didn’t find yours? Write to us:'
    ),
    'Пошук у запитаннях': 'Search the questions',
    'Зміст': 'Contents',
    'До змісту': 'Back to contents',
    'Посилання на це запитання': 'Link to this question',
    'Нічого не знайдено. Спробуйте інше слово або напишіть нам:': 'Nothing found. Try another word or write to us:',

    # -- developers page (open API) ------------------------------------------
    'API для розробників': 'API for developers',
    'Відкритий API Learn Catalan: каталонський словник із перекладами кількома мовами та дієвідміна дієслів у форматі JSON, без ключа.': (
        'The Learn Catalan open API: a Catalan dictionary with translations into several languages '
        'and verb conjugation as JSON, no key needed.'
    ),
    'Словник і дієвідміна відкриті: їх можна вбудувати у свій сайт, застосунок або бота. Відповіді у форматі JSON, ключ не потрібен, запити дозволені з будь-якого домену (CORS).': (
        'The dictionary and the conjugator are open: build them into your site, app or bot. '
        'Answers are JSON, no key is needed, and requests are allowed from any domain (CORS).'
    ),
    'Швидкий старт': 'Quick start',
    'Запити': 'Endpoints',
    'Пошук і список слів. Параметри: q, lang, topic, level, part_of_speech, variety, page, per_page (до 100).': (
        'Search and list words. Parameters: q, lang, topic, level, part_of_speech, variety, page, per_page (up to 100).'
    ),
    'Одне слово: переклади, приклад, рівень, тема, регіональні позначки.': (
        'One word: translations, example, level, topic, regional marks.'
    ),
    'Усі часи та способи дієслова, зокрема зворотних (rentar-se).': 'Every tense and mood of a verb, reflexive ones too (rentar-se).',
    'Дієслова, що починаються з цих літер (для автодоповнення).': 'Verbs starting with these letters (for autocomplete).',
    'Мови перекладів і кількість слів у кожній.': 'Translation languages and how many words each has.',
    'Увесь словник одним файлом CSV, усіма мовами.': 'The whole dictionary as one CSV file, in every language.',
    'Адреса всіх запитів:': 'Base address:',
    'Повний опис у форматі OpenAPI:': 'Full description in OpenAPI format:',
    'Приклад відповіді': 'Example answer',
    'Мови': 'Languages',
    'Параметр <code>lang</code> вибирає мови перекладів, наприклад <code>lang=fr,uk</code>; без нього приходять усі.': (
        'The <code>lang</code> parameter picks the translation languages, e.g. <code>lang=fr,uk</code>; without it you get all of them.'
    ),
    'Коди:': 'Codes:',
    'Мови, для яких перекладів ще немає, з’являться у відповідях, щойно їх додадуть.': (
        'Languages without translations yet will appear in the answers as soon as they are added.'
    ),
    'Правила': 'Rules',
    'До {limit} запитів на хвилину з однієї адреси. Більше — відповідь 429 і заголовок Retry-After.': (
        'Up to {limit} requests a minute from one address. Beyond that the answer is 429 with a Retry-After header.'
    ),
    'Відповіді можна кешувати: вони змінюються рідко (Cache-Control: 1 година).': (
        'Answers may be cached: they change rarely (Cache-Control: 1 hour).'
    ),
    'Будь ласка, вказуйте джерело з посиланням на Learn Catalan.': 'Please credit the source with a link to Learn Catalan.',
    'Помилки приходять як': 'Errors look like',

    # -- search engines and link previews ------------------------------------
    'каталонська мова українською': 'grammar, dictionary and pronunciation',
    '{verb}: дієвідміна дієслова': '{verb} conjugation',
    '{term}: переклад з каталонської': '{term}: Catalan to English translation',
    'Вивчайте каталонську українською: курс граматики від A1 до C1, каталонсько-український словник, дієвідміна понад 8 000 дієслів і уроки вимови з озвученням.': (
        'Learn Catalan online: a grammar course from A1 to C1, a Catalan dictionary with English '
        'translations, a conjugator for over 8,000 verbs and pronunciation lessons with audio.'
    ),
    'Відповіді на часті запитання про Learn Catalan: як увімкнути звук у фонетиці, з чого почати вивчення каталонської, як користуватися словником і дієвідміною.': (
        'Answers to common questions about Learn Catalan: how to turn on audio in the pronunciation '
        'lessons, where to start learning Catalan, and how to use the dictionary and conjugator.'
    ),
    'Курс каталонської граматики українською: {count} юнітів від A1 до C1 з поясненнями, прикладами та вправами з відповідями.': (
        'A Catalan grammar course in English: {count} units from A1 to C1 with explanations, '
        'examples and exercises with answers.'
    ),
    'Юніт {number} курсу каталонської граматики ({level}): пояснення, приклади та вправи з відповідями.': (
        'Unit {number} of the Catalan grammar course ({level}): explanation, examples and exercises with answers.'
    ),
    'Каталонська вимова для українців: звуки, наголос і вимова у мовленні з транскрипцією, озвученими прикладами та вправами.': (
        'Catalan pronunciation for English speakers: sounds, stress and connected speech with IPA, '
        'audio examples and exercises.'
    ),
    'Урок каталонської вимови: звуки з транскрипцією, слова для тренування з озвученням і вправи.': (
        'A Catalan pronunciation lesson: sounds with IPA, practice words with audio, and exercises.'
    ),
    'Каталонсько-український словник: {words} з перекладом, прикладами, рівнем і озвученням. Пошук каталонською та українською.': (
        'Catalan dictionary: {words} with English translations, examples, levels and audio. '
        'Search in Catalan or English.'
    ),
    'Переклад, приклад і вимова в каталонсько-українському словнику.': (
        'Translation, example and pronunciation in the Catalan dictionary.'
    ),
    'Дієвідміна каталонського дієслова {verb}: усі часи та способи, особові форми й переклад.': (
        'Conjugation of the Catalan verb {verb}: every tense and mood, all personal forms and the translation.'
    ),
    'Дієвідміна каталонських дієслів: усі часи та способи понад 8 000 дієслів з перекладом.': (
        'Catalan verb conjugation: every tense and mood of over 8,000 verbs, with translations.'
    ),
    'Не чути звуку?': 'No sound?',
    'Як увімкнути звук': 'How to turn on audio',
    'Докладна інструкція': 'Step-by-step instructions',
    'Результати для «{query}»': 'Results for “{query}”',
    'Фільтри': 'Filters',
    # Translation platform (/translate), data sources
    'Допоможіть перекласти словник та інтерфейс сайту своєю мовою.': 'Help translate the dictionary and the site itself into your language.',
    'Виберіть мову': 'Choose a language',
    'Словник перекладають за значеннями: у слова «tocar» їх два, і кожне перекладається окремо. Поруч показано англійський переклад як орієнтир.': 'The dictionary is translated meaning by meaning: “tocar” has two meanings, and each is translated on its own. The English translation is shown alongside as a guide.',
    'Запропонуйте переклад': 'Suggest a translation',
    'Кожен, хто увійшов, може запропонувати переклад. Інші бачать пропозиції, тож одну роботу не роблять двічі.': 'Anyone who is logged in can suggest a translation. Suggestions are visible to everyone, so nobody does the same work twice.',
    'Перекладач перевіряє': 'A translator checks it',
    'Перекладач мови приймає пропозиції, виправляє машинні переклади й позначає їх перевіреними. Кожну зміну видно в історії, її можна скасувати.': 'The language’s translator accepts suggestions, fixes machine translations and marks them as checked. Every change shows in the history and can be undone.',
    'Щоб пропонувати переклади,': 'To suggest translations,',
    'увійдіть': 'log in',
    'Ви можете перекладати й перевіряти всі мови.': 'You can translate and check every language.',
    'Ви перекладач:': 'You translate:',
    'Ваші переклади йдуть як пропозиції. Хочете стати перекладачем мови? Напишіть адміністраторові.': 'Your translations are sent as suggestions. Would you like to become a translator for a language? Write to the administrator.',
    'пропозицій: {count}': 'suggestions: {count}',
    '{done}% перекладено, {checked}% перевірено': '{done}% translated, {checked}% checked',
    'перевірено {checked}%': '{checked}% checked',
    'чернетки': 'drafts',
    'Інтерфейс': 'Interface',
    '{done}% перекладено': '{done}% translated',
    'Інтерфейс сайту написано цією мовою.': 'The site is written in this language.',
    'Історія змін': 'History',
    'Останні зміни': 'Recent changes',
    'інтерфейс': 'interface',
    'позначено як перевірене': 'marked as checked',
    'видалено': 'removed',
    'Допомогти з перекладом': 'Help translate',
    'До роботи': 'To do',
    'Без перекладу': 'Untranslated',
    'Чернетки': 'Drafts',
    'Пропозиції': 'Suggestions',
    'Усі мови': 'All languages',
    'Перекладайте кожне значення слова окремо. Англійською показано, яке це значення.': 'Translate each meaning of a word on its own. The English shows which meaning it is.',
    'Тут нічого немає. Спробуйте інший фільтр.': 'Nothing here. Try another filter.',
    'Усе перевірено': 'All checked',
    'приклад': 'example',
    'примітка': 'note',
    'Сторінки': 'Pages',
    'Назад': 'Back',
    'Далі': 'Next',
    'Джерела даних': 'Data sources',
    'Регіональні позначки слів частково взяті з Вікісловника (англійського й каталонського), ліцензія CC BY-SA 4.0.': 'Regional labels on words come partly from Wiktionary (English and Catalan editions), licensed CC BY-SA 4.0.',
    'Добір слів і дієслів спирався на частотний список FrequencyWords (Hermit Dave) з корпусу OpenSubtitles 2018, ліцензія CC BY-SA 4.0.': 'The choice of words and verbs drew on the FrequencyWords list (Hermit Dave) from the OpenSubtitles 2018 corpus, licensed CC BY-SA 4.0.',
    'Дієвідміну будує бібліотека verbecc (LGPL-3.0) на даних Verbiste і catverbs з нашими виправленнями; ці дані поширюються за ліцензією GPL-2.0-or-later.': 'Conjugations are built by the verbecc library (LGPL-3.0) from Verbiste and catverbs data with our corrections; that data is under GPL-2.0-or-later.',
    'Публікуючи ці дані, вказуйте й ці джерела. Перелік є і в корені API.': 'If you publish this data, credit these sources too. The API root lists them as well.',
    'зміна': 'edit',
    'прийнято пропозицію': 'suggestion accepted',
    'скасування': 'undo',
    'Останні 200 змін. Перекладач мови може скасувати будь-яку з них.': 'The last 200 changes. The language’s translator can undo any of them.',
    'Змін ще не було.': 'No changes yet.',
    'Перекладені': 'Translated',
    'Меню, кнопки й підказки сайту. Текст у фігурних дужках, як {count}, і HTML-теги залишайте як є.': 'The site’s menus, buttons and hints. Leave text in curly brackets, like {count}, and HTML tags as they are.',
    'Цієї мови ще немає в меню мов сайту: її вмикають у коді, коли інтерфейс перекладено.': 'This language is not in the site’s language menu yet: it is switched on in the code once the interface is translated.',
    'немає': 'missing',
    'на сайті': 'on the site',
    'з файлу': 'from the file',
    'Машинний або неперевірений переклад': 'Machine or unchecked translation',
    'чернетка': 'draft',
    'Запропонувати': 'Suggest',
    'Прийняти': 'Accept',
    'Відхилити': 'Reject',
    'Задовгий текст.': 'The text is too long.',
    'Залиште ті самі заповнювачі у фігурних дужках, що й в оригіналі: {items}.': 'Keep the same placeholders in curly brackets as the original: {items}.',
    'Залиште ті самі HTML-теги, що й в оригіналі, і не додавайте нових.': 'Keep the same HTML tags as the original and do not add new ones.',
    'Крапка з комою розділяє значення слова. Синоніми розділяйте комою.': 'A semicolon separates the meanings of a word. Separate synonyms with a comma.',
    'Переклад словника: {language}': 'Translating the dictionary: {language}',
    '«{term}»: позначено як перевірене.': '“{term}”: marked as checked.',
    'Переклад інтерфейсу: {language}': 'Translating the interface: {language}',
    'Порожню пропозицію не збережено.': 'An empty suggestion was not saved.',
    'У вас забагато пропозицій, що чекають перевірки. Дочекайтеся, поки їх розглянуть.': 'You have too many suggestions waiting to be checked. Please wait until they are reviewed.',
    'Дякуємо! Пропозицію перевірить перекладач цієї мови.': 'Thank you! A translator of this language will check your suggestion.',
    'Поки ви редагували, хтось уже змінив цей переклад: «{text}». Подивіться на нього й збережіть ще раз, якщо ваш кращий.': 'While you were editing, someone else changed this translation: “{text}”. Have a look at it and save again if yours is better.',
    'Збережено.': 'Saved.',
    'Пропозицію прийнято.': 'Suggestion accepted.',
    'Пропозицію відхилено.': 'Suggestion rejected.',
    'Історія перекладів: {language}': 'Translation history: {language}',
    'Цього вже немає у словнику.': 'This is no longer in the dictionary.',
    'Зміну скасовано.': 'Change undone.',
    # Text page (/text)
    'Текст': 'Text',
    'Вставте каталонський текст і натисніть будь-яке слово: початкова форма, переклад і синоніми в тій самій формі.': 'Paste a Catalan text and click any word: its base form, translation and synonyms in the same form.',
    'Робота з текстом': 'Working with a text',
    'Текст каталонською': 'Text in Catalan',
    'Розібрати': 'Analyse',
    'Змінити текст': 'Edit the text',
    'Копіювати текст': 'Copy the text',
    'Текст: натисніть слово або виберіть його стрілками й натисніть Enter': 'Text: click a word, or pick it with the arrow keys and press Enter',
    'Натисніть слово. З клавіатури: стрілки ← → і Enter.': 'Click a word. With the keyboard: arrows ← → and Enter.',
    'Тут з’являться переклад, форма й синоніми слова, яке ви натиснете.': 'The translation, form and synonyms of the word you click will appear here.',
    'Синоніми: тезаурус Softcatalà (CC BY 4.0). Форми дієслів: verbecc. Ідея й правила множини: ReeeWriter.': 'Synonyms: Softcatalà thesaurus (CC BY 4.0). Verb forms: verbecc. Idea and plural rules: ReeeWriter.',
    'Шукаю…': 'Looking it up…',
    'Не вдалося розібрати слово. Спробуйте ще раз.': 'The word could not be analysed. Please try again.',
    'Цього слова немає ні в словнику, ні в тезаурусі.': 'This word is neither in the dictionary nor in the thesaurus.',
    'Синоніми в тій самій формі': 'Synonyms in the same form',
    'Синонімів не знайдено.': 'No synonyms found.',
    'Замінити на «{text}»': 'Replace with “{text}”',
    'У вашому словнику': 'In your dictionary',
    'Повернутися сюди': 'Go back to this step',
    'Початковий текст': 'Original text',
    'Скопійовано': 'Copied',
    'Текст задовгий: до {count} знаків.': 'The text is too long: up to {count} characters.',
    'множина': 'plural',
    'жіночий рід': 'feminine',
    'Синоніми на сторінці «Текст» взято з тезауруса Softcatalà (sinonims-cat), ліцензія CC BY 4.0.': 'Synonyms on the Text page come from the Softcatalà thesaurus (sinonims-cat), licensed CC BY 4.0.',
}
