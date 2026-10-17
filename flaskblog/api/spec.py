"""OpenAPI 3.0 description of /api/v1, served at /api/v1/openapi.json."""


def _param(name, description, schema=None, required=False, location='query'):
    return {
        'name': name, 'in': location, 'required': required,
        'description': description, 'schema': schema or {'type': 'string'},
    }


def _error():
    return {'description': 'Error', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/Error'}}}}


def spec(server, topics, levels, parts_of_speech, languages, regions):
    lang_param = _param(
        'lang', 'Comma-separated language codes of the translations to return (default: all).',
        {'type': 'string', 'example': 'en,fr'},
    )
    return {
        'openapi': '3.0.3',
        'info': {
            'title': 'Learn Catalan open API',
            'version': '1.0',
            'description': (
                'Read-only access to the Learn Catalan dictionary (Catalan words with translations '
                'into several languages) and to the Catalan verb conjugator. No key is needed; '
                'every origin may call it (CORS). Each client may make a limited number of requests '
                'a minute; over the limit the answer is 429 with a Retry-After header. '
                'Regional labels come partly from Wiktionary (CC BY-SA 4.0); conjugations are made '
                'with verbecc from Verbiste/catverbs data (GPL-2.0-or-later). The API index lists '
                'the sources.'
            ),
        },
        'servers': [{'url': server}],
        'paths': {
            '/languages': {'get': {
                'summary': 'Languages the dictionary is translated into, with word counts',
                'responses': {'200': {'description': 'Languages'}},
            }},
            '/words': {'get': {
                'summary': 'Search and list dictionary words',
                'parameters': [
                    _param('q', 'Text to look for in the Catalan word, its translations or the Catalan example.'),
                    lang_param,
                    _param('topic', 'Topic code.', {'type': 'string', 'enum': topics}),
                    _param('level', 'CEFR level.', {'type': 'string', 'enum': levels}),
                    _param('part_of_speech', 'Part of speech.', {'type': 'string', 'enum': parts_of_speech}),
                    _param('variety', '"central" hides regional and archaic words, "regional" shows only them.',
                           {'type': 'string', 'enum': ['central', 'regional']}),
                    _param('page', 'Page number.', {'type': 'integer', 'minimum': 1, 'default': 1}),
                    _param('per_page', 'Words per page.', {'type': 'integer', 'minimum': 1, 'maximum': 100, 'default': 20}),
                ],
                'responses': {
                    '200': {'description': 'A page of words', 'content': {'application/json': {'schema': {
                        'type': 'object',
                        'properties': {
                            'data': {'type': 'array', 'items': {'$ref': '#/components/schemas/Word'}},
                            'meta': {'type': 'object'},
                            'links': {'type': 'object'},
                        },
                    }}}},
                    '400': _error(),
                },
            }},
            '/words/{slug}': {'get': {
                'summary': 'One dictionary word, by slug or by the Catalan word itself',
                'parameters': [_param('slug', 'Slug or Catalan word, e.g. "anar".', required=True, location='path'), lang_param],
                'responses': {
                    '200': {'description': 'The word', 'content': {'application/json': {'schema': {
                        'type': 'object', 'properties': {'data': {'$ref': '#/components/schemas/Word'}},
                    }}}},
                    '404': _error(),
                },
            }},
            '/conjugations/{verb}': {'get': {
                'summary': 'Every tense and mood of a Catalan verb',
                'parameters': [_param('verb', 'Infinitive, e.g. "anar" or "rentar-se".', required=True, location='path')],
                'responses': {
                    '200': {'description': 'The conjugation', 'content': {'application/json': {'schema': {
                        'type': 'object', 'properties': {'data': {'$ref': '#/components/schemas/Conjugation'}},
                    }}}},
                    '400': _error(),
                    '404': _error(),
                },
            }},
            '/verbs': {'get': {
                'summary': 'Infinitives that start with the given letters (for autocomplete)',
                'parameters': [
                    _param('q', 'Beginning of the verb.', required=True),
                    _param('limit', 'How many.', {'type': 'integer', 'minimum': 1, 'maximum': 50, 'default': 10}),
                ],
                'responses': {'200': {'description': 'Infinitives'}},
            }},
            '/dictionary.csv': {'get': {
                'summary': 'The whole dictionary as CSV, every language',
                'responses': {'200': {'description': 'CSV file', 'content': {'text/csv': {}}}},
            }},
        },
        'components': {'schemas': {
            'Translation': {'type': 'object', 'properties': {
                'translation': {'type': 'string'},
                'example': {'type': 'string', 'nullable': True, 'description': 'The Catalan example in this language.'},
                'notes': {'type': 'string', 'nullable': True},
                'reviewed': {'type': 'boolean', 'description': 'False for a draft (machine) translation nobody has checked yet.'},
            }},
            'Word': {'type': 'object', 'properties': {
                'term': {'type': 'string', 'example': 'anar'},
                'slug': {'type': 'string'},
                'language': {'type': 'string', 'example': 'ca'},
                'part_of_speech': {'type': 'string', 'nullable': True, 'enum': parts_of_speech + [None]},
                'gender': {'type': 'string', 'nullable': True, 'enum': ['m', 'f', 'mf', None]},
                'pronunciation': {'type': 'string', 'nullable': True,
                                  'description': 'IPA typed in by an editor, if any.'},
                'transcription': {'$ref': '#/components/schemas/Transcription'},
                'topic': {'type': 'string', 'nullable': True},
                'level': {'type': 'string', 'nullable': True},
                'example': {'type': 'string', 'nullable': True, 'description': 'Example sentence in Catalan.'},
                'regional': {'type': 'array', 'items': {'type': 'string', 'enum': regions},
                             'description': 'Where the word is used instead of Central Catalan (empty for standard words).'},
                'central_alternative': {'type': 'string', 'nullable': True},
                'translations': {'type': 'object', 'description': 'By language code: ' + ', '.join(languages) + '.',
                                 'additionalProperties': {'$ref': '#/components/schemas/Translation'}},
                'senses': {'type': 'array', 'description': 'The meanings of the word in order, each with its '
                           'translation per language (the meanings follow the English translation). '
                           '"translation" above is these joined with ";".',
                           'items': {'$ref': '#/components/schemas/Sense'}},
                'conjugation': {'type': 'string', 'nullable': True, 'format': 'uri'},
                'url': {'type': 'string', 'format': 'uri'},
                'api_url': {'type': 'string', 'format': 'uri'},
            }},
            'Transcription': {'type': 'object', 'nullable': True, 'properties': {
                'ipa': {'type': 'string', 'example': 'ˈkazə',
                        'description': 'Central Catalan, broad IPA, ˈ before the stressed syllable.'},
                'cyrillic': {'type': 'string', 'example': 'ка́зə',
                             'description': 'The same in Ukrainian letters, the stressed vowel marked.'},
                'certain': {'type': 'boolean',
                            'description': 'False when the rules had to guess (open or closed e/o, a final -r).'},
                'source': {'type': 'string', 'enum': ['editor', 'lessons', 'rules']},
            }},
            'Sense': {'type': 'object', 'properties': {
                'position': {'type': 'integer', 'example': 1},
                'translations': {'type': 'object', 'additionalProperties': {'type': 'object', 'properties': {
                    'text': {'type': 'string'},
                    'reviewed': {'type': 'boolean'},
                }}},
            }},
            'Conjugation': {'type': 'object', 'properties': {
                'infinitive': {'type': 'string'},
                'base_infinitive': {'type': 'string'},
                'pronominal': {'type': 'boolean'},
                'model': {'type': 'string', 'description': 'Conjugation model the verb follows.'},
                'verified': {'type': 'boolean', 'description': 'Checked by hand against a reference.'},
                'moods': {'type': 'object', 'description': 'mood → tense → list of {person, form}. '
                          'Persons: 1s 2s 3s 1p 2p 3p; imperative from 2s; participle ms fs mp fp; '
                          'infinitive and gerund have no person.'},
                'url': {'type': 'string', 'format': 'uri'},
            }},
            'Error': {'type': 'object', 'properties': {'error': {'type': 'object', 'properties': {
                'code': {'type': 'string'}, 'message': {'type': 'string'},
            }}}},
        }},
    }
