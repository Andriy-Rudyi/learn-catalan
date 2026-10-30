/* /phonetics/trainer: rounds of self-checking pronunciation tasks
 * (flaskblog/phonetics/trainer.py builds them from the lessons).
 *
 * Task types: transcribe (word -> IPA, typed with the on-screen IPA keys),
 * spell (IPA -> word), sound (how is the marked letter pronounced), stress
 * (click the stressed syllable), spelling (how is [ipa] written) and listen
 * (which word did the device say; skipped without a Catalan voice).
 * Everything is drawn with textContent. The best score of every unit stays
 * in this browser (localStorage).
 */
(function () {
  'use strict';

  var configNode = document.getElementById('trainer-config');
  if (!configNode) { return; }
  var config = JSON.parse(configNode.textContent);
  var S = config.strings;
  var STORE = 'learn-catalan:phonetics-trainer:v1';
  var main = document.getElementById('trainer-main');
  var NUCLEI = /[aəeɛiouɔ]/g;
  var KEYS = ['ə', 'ɛ', 'ɔ', 'ɾ', 'r', 'ʎ', 'ɲ', 'ŋ', 'ʃ', 'ʒ', 'tʃ', 'dʒ', 'dz', 'ɡ', 'j', 'w', 'z', 'ˈ'];
  var SHORTCUTS = { '@': 'ə', 'E': 'ɛ', 'O': 'ɔ', 'R': 'ɾ', 'L': 'ʎ', 'N': 'ɲ', 'G': 'ŋ',
                    'S': 'ʃ', 'Z': 'ʒ', 'C': 'tʃ', 'J': 'dʒ', "'": 'ˈ', '’': 'ˈ' };

  var units = {};
  config.units.forEach(function (unit) { units[unit.slug] = unit; });

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined && text !== null) { node.textContent = text; }
    return node;
  }

  function format(text, values) {
    return text.replace(/\{(\w+)\}/g, function (all, key) { return key in values ? values[key] : all; });
  }

  function shuffle(list) {
    list = list.slice();
    for (var i = list.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = list[i]; list[i] = list[j]; list[j] = t;
    }
    return list;
  }

  // -- best scores -------------------------------------------------------------------------
  function loadBest() {
    try { return JSON.parse(window.localStorage.getItem(STORE) || '{}') || {}; } catch (e) { return {}; }
  }

  function saveBest(unit, pct) {
    var best = loadBest();
    if (!(unit in best) || pct > best[unit]) {
      best[unit] = pct;
      try { window.localStorage.setItem(STORE, JSON.stringify(best)); } catch (e) { /* private window */ }
    }
    showBest();
  }

  function showBest() {
    var best = loadBest();
    document.querySelectorAll('[data-best]').forEach(function (node) {
      var unit = node.getAttribute('data-best');
      node.textContent = unit in best ? best[unit] + '%' : '';
    });
  }

  // -- Catalan voice (the same choice as speak.js) -------------------------------------------
  function hasCatalanVoice() {
    if (!('speechSynthesis' in window)) { return false; }
    return window.speechSynthesis.getVoices().some(function (voice) {
      return voice.lang && voice.lang.toLowerCase().replace('_', '-').indexOf('ca') === 0;
    });
  }
  if ('speechSynthesis' in window) { window.speechSynthesis.getVoices(); }

  function speakButton(text) {
    var button = el('button', 'btn-speak', '🔊');
    button.type = 'button';
    button.setAttribute('data-say', text);
    button.setAttribute('aria-label', S.play + ': ' + text);
    return button;
  }

  // -- checking ----------------------------------------------------------------------------------
  function cleanIpa(text) {
    return (text || '').normalize('NFC').trim()
      .replace(/[\[\]\/.]/g, '')
      .replace(/[͜͡]/g, '')          // tie bars
      .replace(/g/g, 'ɡ').replace(/ʧ/g, 'tʃ').replace(/ʤ/g, 'dʒ').replace(/ʣ/g, 'dz')
      .replace(/[@EORLNGSZCJ’'`]/g, function (c) { return SHORTCUTS[c] || 'ˈ'; }).replace(/ː/g, '')
      .replace(/\s+/g, ' ');
  }

  // Monosyllables need no stress mark: drop it there, keep it elsewhere.
  function stressNeeded(ipa) {
    return ipa.split(' ').map(function (word) {
      return (word.match(NUCLEI) || []).length > 1 ? word : word.replace(/ˈ/g, '');
    }).join(' ');
  }

  function checkIpa(input, answer) {
    var given = cleanIpa(input);
    var right = cleanIpa(answer);
    var flat = function (s) { return s.replace(/[ˈˌ\s]/g, ''); };
    if (flat(given) !== flat(right)) { return 'no'; }
    var g = stressNeeded(given).replace(/\s/g, '');
    var r = stressNeeded(right).replace(/\s/g, '');
    if (g === r) { return 'ok'; }
    if (r.indexOf('ˈ') >= 0 && g.indexOf('ˈ') < 0) { return 'noStress'; }
    return 'badStress';
  }

  function cleanWord(text) {
    return (text || '').normalize('NFC').trim().toLowerCase()
      .replace(/[’`]/g, "'").replace(/l\.l/g, 'l·l').replace(/\s+/g, ' ').replace(/[.!?]+$/, '');
  }

  // -- a round -------------------------------------------------------------------------------------
  var round = null;

  function tasksOf(unitKey) {
    var list = [];
    var slugs = unitKey === '*' ? Object.keys(units) : [unitKey];
    slugs.forEach(function (slug) {
      units[slug].tasks.forEach(function (task) { list.push({ unit: slug, task: task }); });
    });
    return list;
  }

  function start(unitKey) {
    var voice = hasCatalanVoice();
    var all = tasksOf(unitKey);
    var usable = all.filter(function (item) { return voice || item.task.type !== 'listen'; });
    round = {
      unit: unitKey,
      items: shuffle(usable).slice(0, config.perRound),
      index: 0,
      score: 0,
      skippedListening: usable.length < all.length
    };
    document.querySelectorAll('.trainer-unit').forEach(function (button) {
      button.classList.toggle('active', button.getAttribute('data-unit') === unitKey);
    });
    show();
    main.scrollIntoView({ block: 'nearest' });
  }

  function header() {
    var box = el('div', 'trainer-head');
    var title = round.unit === '*' ? S.all : units[round.unit].number + '. ' + units[round.unit].title;
    box.appendChild(el('div', 'trainer-title', title));
    var info = el('div', 'trainer-count small text-muted',
      format(S.question, { n: round.index + 1, total: round.items.length }) + ' · ' +
      format(S.score, { n: round.score }));
    box.appendChild(info);
    var bar = el('div', 'trainer-bar');
    var fill = el('i');
    fill.style.width = (100 * round.index / round.items.length) + '%';
    bar.appendChild(fill);
    box.appendChild(bar);
    return box;
  }

  function show() {
    main.textContent = '';
    if (round.index >= round.items.length) { return finish(); }
    main.appendChild(header());
    if (round.skippedListening && round.index === 0) {
      main.appendChild(el('p', 'small text-muted', S.noVoice));
    }
    var item = round.items[round.index];
    var card = el('div', 'trainer-card');
    main.appendChild(card);
    var draw = { transcribe: drawTranscribe, spell: drawSpell, sound: drawSound,
                 stress: drawStress, spelling: drawSpelling, listen: drawListen }[item.task.type];
    draw(card, item);
  }

  function next() {
    round.index += 1;
    show();
  }

  // Feedback under the task, with the word, its transcription and the lesson.
  function feedback(card, item, status, shown) {
    if (status === 'ok') { round.score += 1; }
    var box = el('div', 'trainer-feedback ' + (status === 'ok' ? 'is-ok' : status === 'no' ? 'is-no' : 'is-half'));
    var message = status === 'ok' ? S.right : status === 'no' ? S.wrong : S[status];
    box.appendChild(el('strong', null, message));
    if (shown) {
      var line = el('div', 'trainer-answer');
      if (shown.word) {
        line.appendChild(speakButton(shown.word));
        line.appendChild(el('span', 'ca', shown.word));
        line.appendChild(document.createTextNode(' '));
      }
      if (shown.ipa) { line.appendChild(el('span', 'ipa', '[' + shown.ipa + ']')); }
      if (shown.extra) { line.appendChild(el('span', 'ms-2', shown.extra)); }
      box.appendChild(line);
    }
    var link = el('a', 'small', S.lesson + ' ' + units[item.unit].number + ': ' + units[item.unit].title + ' →');
    link.href = config.lessonUrls[item.unit];
    box.appendChild(link);
    card.appendChild(box);

    var go = el('button', 'btn btn-info mt-3 trainer-next', round.index + 1 >= round.items.length ? S.finish : S.next);
    go.type = 'button';
    go.addEventListener('click', next);
    card.appendChild(go);
    go.focus();
  }

  function prompt(card, text) { card.appendChild(el('p', 'trainer-prompt', text)); }

  // -- typed answers -----------------------------------------------------------------------------
  function answerForm(card, ipa, onCheck) {
    var form = el('form', 'trainer-answer-form');
    var input = el('input', 'form-control' + (ipa ? ' ipa-input' : ''));
    input.type = 'text';
    input.autocomplete = 'off';
    input.setAttribute('autocapitalize', 'off');
    input.spellcheck = false;
    if (ipa) { input.setAttribute('lang', 'und-fonipa'); } else { input.setAttribute('lang', 'ca'); }
    var button = el('button', 'btn btn-info', S.check);
    button.type = 'submit';
    var row = el('div', 'trainer-input-row');
    if (ipa) { row.appendChild(el('span', 'trainer-bracket', '[')); }
    row.appendChild(input);
    if (ipa) { row.appendChild(el('span', 'trainer-bracket', ']')); }
    row.appendChild(button);
    form.appendChild(row);
    if (ipa) {
      form.appendChild(keyboard(input));
      input.addEventListener('keydown', function (event) {
        var replacement = SHORTCUTS[event.key];
        if (replacement && !event.ctrlKey && !event.metaKey && !event.altKey) {
          event.preventDefault();
          insert(input, replacement);
        }
      });
    }
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      if (!input.value.trim()) {
        input.focus();
        input.placeholder = S.empty;
        return;
      }
      input.disabled = true;
      button.disabled = true;
      var keys = form.querySelector('.trainer-keys');
      if (keys) { keys.remove(); }
      onCheck(input.value);
    });
    card.appendChild(form);
    input.focus();
  }

  function insert(input, text) {
    var start = input.selectionStart == null ? input.value.length : input.selectionStart;
    var end = input.selectionEnd == null ? input.value.length : input.selectionEnd;
    input.value = input.value.slice(0, start) + text + input.value.slice(end);
    var at = start + text.length;
    input.setSelectionRange(at, at);
  }

  function keyboard(input) {
    var box = el('div', 'trainer-keys');
    KEYS.forEach(function (symbol) {
      var key = el('button', 'trainer-key ipa', symbol);
      key.type = 'button';
      key.addEventListener('mousedown', function (event) { event.preventDefault(); });
      key.addEventListener('click', function () { insert(input, symbol); input.focus(); });
      box.appendChild(key);
    });
    var erase = el('button', 'trainer-key trainer-key-wide', '⌫');
    erase.type = 'button';
    erase.setAttribute('aria-label', S.erase);
    erase.addEventListener('mousedown', function (event) { event.preventDefault(); });
    erase.addEventListener('click', function () {
      var start = input.selectionStart, end = input.selectionEnd;
      if (start === end && start > 0) { start -= 1; }
      input.value = input.value.slice(0, start) + input.value.slice(end);
      input.setSelectionRange(start, start);
      input.focus();
    });
    box.appendChild(erase);
    return box;
  }

  function drawTranscribe(card, item) {
    var task = item.task;
    prompt(card, S.transcribe);
    var word = el('div', 'trainer-target');
    word.appendChild(speakButton(task.word));
    word.appendChild(el('span', 'ca', task.word));
    if (task.meaning) { word.appendChild(el('span', 'trainer-meaning', task.meaning)); }
    card.appendChild(word);
    answerForm(card, true, function (value) {
      var status = checkIpa(value, task.answer);
      feedback(card, item, status, { word: task.word, ipa: task.answer });
    });
  }

  function drawSpell(card, item) {
    var task = item.task;
    prompt(card, S.spell);
    var target = el('div', 'trainer-target');
    target.appendChild(el('span', 'ipa', '[' + task.ipa + ']'));
    if (task.meaning) { target.appendChild(el('span', 'trainer-meaning', task.meaning)); }
    card.appendChild(target);
    answerForm(card, false, function (value) {
      var status = cleanWord(value) === cleanWord(task.answer) ? 'ok' : 'no';
      feedback(card, item, status, { word: task.answer, ipa: task.ipa });
    });
  }

  // -- choices --------------------------------------------------------------------------------------
  function choices(card, item, options, isRight, shown, ipaOptions) {
    var box = el('div', 'trainer-options');
    options.forEach(function (option) {
      var label = option === '∅' ? '∅ ' + S.silent : ipaOptions ? '[' + option + ']' : option;
      var button = el('button', 'trainer-option' + (ipaOptions ? ' ipa' : ''), label);
      button.type = 'button';
      button.addEventListener('click', function () {
        var ok = isRight(option);
        box.querySelectorAll('button').forEach(function (other) {
          other.disabled = true;
          if (isRight(other.getAttribute('data-value'))) { other.classList.add('is-right'); }
        });
        if (!ok) { button.classList.add('is-wrong'); }
        feedback(card, item, ok ? 'ok' : 'no', shown);
      });
      button.setAttribute('data-value', option);
      box.appendChild(button);
    });
    card.appendChild(box);
  }

  // The word with the n-th occurrence of the mark highlighted.
  function marked(word, mark, nth) {
    var box = el('span', 'ca');
    var at = -1;
    for (var i = 0; i < (nth || 1); i++) {
      at = word.indexOf(mark, at + 1);
      if (at < 0) { box.textContent = word; return box; }
    }
    box.appendChild(document.createTextNode(word.slice(0, at)));
    box.appendChild(el('mark', 'trainer-mark', mark));
    box.appendChild(document.createTextNode(word.slice(at + mark.length)));
    return box;
  }

  function drawSound(card, item) {
    var task = item.task;
    prompt(card, S.sound);
    var target = el('div', 'trainer-target');
    target.appendChild(marked(task.word, task.mark, task.nth));
    card.appendChild(target);
    choices(card, item, task.options, function (option) { return option === task.answer; },
            { word: task.word, ipa: task.ipa }, true);
  }

  function drawStress(card, item) {
    var task = item.task;
    prompt(card, S.stress);
    var box = el('div', 'trainer-syllables');
    task.syllables.forEach(function (syllable, index) {
      var button = el('button', 'trainer-syllable ca', syllable);
      button.type = 'button';
      button.addEventListener('click', function () {
        box.querySelectorAll('button').forEach(function (other, k) {
          other.disabled = true;
          if (k === task.answer) { other.classList.add('is-right'); }
        });
        if (index !== task.answer) { button.classList.add('is-wrong'); }
        feedback(card, item, index === task.answer ? 'ok' : 'no', { word: task.word, ipa: task.ipa });
      });
      box.appendChild(button);
    });
    card.appendChild(box);
  }

  function drawSpelling(card, item) {
    var task = item.task;
    prompt(card, S.spelling);
    var target = el('div', 'trainer-target');
    target.appendChild(el('span', 'ipa', '[' + task.ipa + ']'));
    card.appendChild(target);
    choices(card, item, shuffle(task.options), function (option) { return option === task.answer; },
            { word: task.answer, ipa: task.ipa }, false);
  }

  function drawListen(card, item) {
    var task = item.task;
    var said = task.options[Math.floor(Math.random() * task.options.length)];
    prompt(card, S.listen);
    var target = el('div', 'trainer-target');
    var play = speakButton(said);
    play.classList.add('btn-speak-lg');
    play.textContent = '🔊 ' + S.play;
    target.appendChild(play);
    card.appendChild(target);
    choices(card, item, shuffle(task.options), function (option) { return option === said; },
            { word: said }, false);
  }

  function finish() {
    var total = round.items.length;
    var pct = total ? Math.round(100 * round.score / total) : 0;
    saveBest(round.unit, pct);
    var box = el('div', 'trainer-done');
    box.appendChild(el('p', 'text-muted mb-1', S.done));
    box.appendChild(el('div', 'trainer-big', round.score + ' / ' + total));
    var best = loadBest()[round.unit];
    box.appendChild(el('p', 'small text-muted', S.best + ': ' + best + '%'));
    var again = el('button', 'btn btn-info me-2', S.again);
    again.type = 'button';
    again.addEventListener('click', function () { start(round.unit); });
    box.appendChild(again);
    if (round.unit !== '*') {
      var lesson = el('a', 'btn btn-outline-secondary', S.lesson + ' ' + units[round.unit].number + ' →');
      lesson.href = config.lessonUrls[round.unit];
      box.appendChild(lesson);
    }
    main.appendChild(box);
  }

  // -- start -------------------------------------------------------------------------------------------
  document.querySelectorAll('[data-unit], [data-start]').forEach(function (button) {
    button.addEventListener('click', function () {
      start(button.getAttribute('data-unit') || button.getAttribute('data-start'));
    });
  });
  showBest();
  // /phonetics/trainer#<lesson slug> (the lesson pages link here) starts that unit.
  function fromHash() {
    var slug = decodeURIComponent((window.location.hash || '').slice(1));
    if (slug && units[slug]) { start(slug); }
  }
  window.addEventListener('hashchange', fromHash);
  fromHash();
})();
