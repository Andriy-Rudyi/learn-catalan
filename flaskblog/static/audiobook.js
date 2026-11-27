/* The audiobook player (templates/audiobook.html, flaskblog/audiobooks.py).
 *
 * One <audio> element plays the parts one after another. Real audio files
 * keep playing with the screen locked; the Media Session API gives the lock
 * screen, headphones and the car (Bluetooth, CarPlay, Android Auto) their
 * play/pause, previous/next part and seek controls, with the title shown.
 * Where the listener stopped (part, second) and the speed are kept in this
 * browser (localStorage) and offered on the next visit.
 *
 * Below the player the part's text is shown and the word being read lights
 * up: the site gives each sentence's start and end (they are kept when the
 * MP3 is made), and the words of a sentence share its time by their length.
 * Tapping a word plays from there.
 *
 * If the sound cannot be loaded from where it is published (an old Android
 * tablet cannot reach that host), the parts are played through the site
 * (/audio/<file>), and this browser remembers it.
 */
(function () {
  'use strict';

  var configNode = document.getElementById('audiobook-config');
  if (!configNode) { return; }
  var config = JSON.parse(configNode.textContent);
  var S = config.strings;
  var parts = config.parts;
  var audio = document.getElementById('ab-audio');
  var els = {
    title: document.getElementById('ab-title'),
    play: document.getElementById('ab-play'),
    prev: document.getElementById('ab-prev'),
    next: document.getElementById('ab-next'),
    back: document.getElementById('ab-back'),
    forward: document.getElementById('ab-forward'),
    seek: document.getElementById('ab-seek'),
    time: document.getElementById('ab-time'),
    total: document.getElementById('ab-total'),
    rate: document.getElementById('ab-rate'),
    resume: document.getElementById('ab-resume'),
    list: document.getElementById('ab-list')
  };
  var current = 0;
  var seeking = false;
  var PROXY_KEY = 'audiobook:through-site';
  var throughSite = false;
  try { throughSite = window.localStorage.getItem(PROXY_KEY) === '1'; } catch (e) { /* nothing kept */ }
  var wantsToPlay = false;

  function urlOf(index) {
    return throughSite && parts[index].proxy ? parts[index].proxy : parts[index].url;
  }

  function clock(seconds) {
    seconds = Math.max(0, Math.floor(seconds || 0));
    var h = Math.floor(seconds / 3600), m = Math.floor((seconds % 3600) / 60), s = seconds % 60;
    var mm = h ? String(m).padStart(2, '0') : String(m);
    return (h ? h + ':' : '') + mm + ':' + String(s).padStart(2, '0');
  }

  // -- remembering where the listener is ---------------------------------------------------
  function load() {
    try { return JSON.parse(window.localStorage.getItem(config.store) || 'null'); } catch (e) { return null; }
  }
  var lastSave = 0;
  function save(force) {
    var now = Date.now();
    if (!force && now - lastSave < 5000) { return; }
    lastSave = now;
    try {
      window.localStorage.setItem(config.store, JSON.stringify({
        part: current, time: Math.floor(audio.currentTime || 0), rate: audio.playbackRate
      }));
    } catch (e) { /* private window: nothing kept */ }
  }

  // -- parts -----------------------------------------------------------------------------------
  function mark() {
    els.list.querySelectorAll('a[data-part]').forEach(function (link) {
      link.classList.toggle('is-playing', Number(link.getAttribute('data-part')) === current);
    });
  }

  function metadata() {
    if (!('mediaSession' in navigator) || !window.MediaMetadata) { return; }
    navigator.mediaSession.metadata = new MediaMetadata({
      title: parts[current].title,
      artist: config.author,
      album: config.title,
      artwork: [{ src: config.artwork, sizes: '1200x630', type: 'image/png' }]
    });
  }

  function select(index, startAt, autoplay) {
    if (index < 0 || index >= parts.length) { return; }
    var rate = audio.playbackRate;
    current = index;
    audio.src = urlOf(index);
    audio.playbackRate = rate;
    els.title.textContent = parts[index].title;
    els.seek.max = parts[index].seconds || 0;
    els.total.textContent = clock(parts[index].seconds);
    mark();
    metadata();
    showText(index);
    var start = function () {
      if (startAt) { audio.currentTime = startAt; }
      audio.playbackRate = Number(els.rate.value) || 1;
    };
    audio.addEventListener('loadedmetadata', start, { once: true });
    els.resume.classList.remove('text-danger');
    audio.load();
    // play() right away, still inside the tap: Safari on iPhone and iPad
    // refuses to start the sound later (after the file's data has come).
    if (autoplay) { play(); }
    save(true);
  }

  function showPlaying() {
    els.play.classList.add('is-playing');  // the pause icon (SVG: old Android has no ⏸)
    els.play.setAttribute('aria-label', S.pause);
    if ('mediaSession' in navigator) { navigator.mediaSession.playbackState = 'playing'; }
  }
  function showPaused() {
    els.play.classList.remove('is-playing');
    els.play.setAttribute('aria-label', S.play);
    if ('mediaSession' in navigator) { navigator.mediaSession.playbackState = 'paused'; }
  }

  function play() {
    wantsToPlay = true;
    var started = audio.play();
    if (started && started.catch) { started.catch(function () { showPaused(); }); }
  }

  function toggle() {
    if (audio.paused) {
      if (audio.error) { select(current, Math.floor(audio.currentTime || 0), true); return; }
      play();
    } else {
      wantsToPlay = false;
      audio.pause();
    }
  }
  function skip(seconds) {
    var target = Math.max(0, Math.min((audio.duration || parts[current].seconds) - 1, audio.currentTime + seconds));
    audio.currentTime = target;
  }

  // -- the text, with the word being read lit up -----------------------------------------------
  var textBox = document.getElementById('ab-text');
  var followBox = document.getElementById('ab-follow');
  var words = [];       // [{el, sentence, from, to}] in reading order
  var lit = -1;
  var shownFor = -1;
  var scrolledByHand = 0;
  var LETTER = /[A-Za-z0-9À-ɏͰ-ϿЀ-ӿ]/g;

  function weight(word) {
    var letters = (word.match(LETTER) || []).length || word.length;
    // A comma or a full stop is a short silence after the word.
    if (/[,;:]$/.test(word)) { letters += 2; }
    if (/[.!?…»”"]$/.test(word)) { letters += 3; }
    return letters + 1;
  }

  function addWords(holder, text, from, to) {
    var found = [], pattern = /\S+/g, match;
    while ((match = pattern.exec(text))) { found.push(match); }
    var total = 0;
    found.forEach(function (item) { total += weight(item[0]); });
    var at = 0, time = from;
    found.forEach(function (item, position) {
      if (item.index > at) { holder.appendChild(document.createTextNode(text.slice(at, item.index))); }
      var span = document.createElement('span');
      span.className = 'ab-w';
      span.textContent = item[0];
      var length = total ? (to - from) * weight(item[0]) / total : 0;
      span.setAttribute('data-i', String(words.length));
      words.push({ el: span, sentence: holder, from: time, to: time + length });
      time += length;
      holder.appendChild(span);
      at = item.index + item[0].length;
    });
    if (at < text.length) { holder.appendChild(document.createTextNode(text.slice(at))); }
  }

  function renderText(data) {
    textBox.innerHTML = '';
    words = [];
    lit = -1;
    var bySentence = {};
    (data.sentences || []).forEach(function (item) {
      (bySentence[item[0]] = bySentence[item[0]] || []).push(item);
    });
    data.pieces.forEach(function (piece, index) {
      var paragraph = document.createElement('p');
      if (index === 0) { paragraph.className = 'ab-heading'; }
      var at = 0;
      (bySentence[index] || []).sort(function (a, b) { return a[1] - b[1]; }).forEach(function (item) {
        if (item[1] > at) { paragraph.appendChild(document.createTextNode(piece.slice(at, item[1]))); }
        var sentence = document.createElement('span');
        sentence.className = 'ab-s';
        addWords(sentence, piece.slice(item[1], item[2]), item[3], item[4]);
        paragraph.appendChild(sentence);
        at = item[2];
      });
      if (at < piece.length) { paragraph.appendChild(document.createTextNode(piece.slice(at))); }
      textBox.appendChild(paragraph);
    });
    light(audio.currentTime || 0);
  }

  function showText(index) {
    if (!textBox || shownFor === index) { return; }
    shownFor = index;
    words = [];
    lit = -1;
    if (!parts[index].text || !window.fetch) { textBox.textContent = ''; return; }
    textBox.innerHTML = '<p class="text-muted">' + S.loading + '</p>';
    textBox.scrollTop = 0;
    fetch(parts[index].text)
      .then(function (response) { return response.ok ? response.json() : null; })
      .then(function (data) {
        if (shownFor !== index) { return; }
        if (!data || !data.pieces) { textBox.innerHTML = '<p class="text-muted">' + S.no_text + '</p>'; return; }
        renderText(data);
      })
      .catch(function () {
        if (shownFor === index) { textBox.innerHTML = '<p class="text-muted">' + S.no_text + '</p>'; }
      });
  }

  function find(time) {
    // The last word that has started by *time* (binary search).
    var low = 0, high = words.length - 1, found = -1;
    while (low <= high) {
      var middle = (low + high) >> 1;
      if (words[middle].from <= time) { found = middle; low = middle + 1; } else { high = middle - 1; }
    }
    return found;
  }

  function follow(element) {
    if (!followBox || !followBox.checked || Date.now() - scrolledByHand < 4000) { return; }
    var top = element.offsetTop, view = textBox.scrollTop, height = textBox.clientHeight;
    if (top < view + height * 0.15 || top > view + height * 0.7) {
      textBox.scrollTop = Math.max(0, top - height / 3);
    }
  }

  function light(time) {
    if (!words.length) { return; }
    var index = find(time);
    if (index === lit) { return; }
    if (lit >= 0 && words[lit]) {
      words[lit].el.classList.remove('ab-now');
      words[lit].sentence.classList.remove('ab-sentence-now');
    }
    lit = index;
    if (index >= 0) {
      words[index].el.classList.add('ab-now');
      words[index].sentence.classList.add('ab-sentence-now');
      follow(words[index].el);
    }
  }

  var frame = null;
  function tick() {
    frame = null;
    light(audio.currentTime);
    if (!audio.paused && !document.hidden) { frame = window.requestAnimationFrame(tick); }
  }
  function startTicking() {
    if (frame === null && window.requestAnimationFrame) { frame = window.requestAnimationFrame(tick); }
  }

  if (textBox) {
    textBox.addEventListener('click', function (event) {
      var word = event.target.closest ? event.target.closest('.ab-w') : null;
      if (!word) { return; }
      var item = words[Number(word.getAttribute('data-i'))];
      if (!item) { return; }
      scrolledByHand = 0;
      if (audio.readyState < 1) {  // nothing loaded yet: load, go there and play
        select(current, item.from, true);
        light(item.from);
        return;
      }
      audio.currentTime = item.from;
      light(item.from);
      if (audio.paused) { play(); }
    });
    ['wheel', 'touchmove', 'keydown'].forEach(function (name) {
      textBox.addEventListener(name, function () { scrolledByHand = Date.now(); }, { passive: true });
    });
  }
  document.addEventListener('visibilitychange', function () { if (!document.hidden) { light(audio.currentTime); startTicking(); } });

  // -- events ----------------------------------------------------------------------------------
  audio.addEventListener('play', function () { showPlaying(); metadata(); startTicking(); });
  audio.addEventListener('seeked', function () { light(audio.currentTime); });
  audio.addEventListener('error', function () {
    if (!throughSite && parts[current].proxy) {
      // This browser cannot load it from where it is published: through the site.
      throughSite = true;
      try { window.localStorage.setItem(PROXY_KEY, '1'); } catch (e) { /* nothing kept */ }
      select(current, Math.floor(audio.currentTime || 0), wantsToPlay);
      return;
    }
    // Say so instead of a button that does nothing.
    showPaused();
    els.resume.hidden = false;
    els.resume.classList.add('text-danger');
    els.resume.textContent = S.error;
  });
  audio.addEventListener('pause', function () { showPaused(); save(true); });
  audio.addEventListener('ended', function () {
    if (current + 1 < parts.length) {
      select(current + 1, 0, true);  // keeps playing with the screen locked
    } else {
      showPaused();
    }
  });
  audio.addEventListener('timeupdate', function () {
    if (!seeking) { els.seek.value = Math.floor(audio.currentTime); }
    els.time.textContent = clock(audio.currentTime);
    light(audio.currentTime);
    save(false);
    if ('mediaSession' in navigator && navigator.mediaSession.setPositionState && audio.duration) {
      try {
        navigator.mediaSession.setPositionState({
          duration: audio.duration, playbackRate: audio.playbackRate, position: audio.currentTime
        });
      } catch (e) { /* not supported everywhere */ }
    }
  });

  els.play.addEventListener('click', toggle);
  els.prev.addEventListener('click', function () {
    // Like a music player: back to the start first, the previous part on a second press.
    if (audio.currentTime > 5 || current === 0) { audio.currentTime = 0; } else { select(current - 1, 0, !audio.paused); }
  });
  els.next.addEventListener('click', function () { select(current + 1, 0, !audio.paused); });
  els.back.addEventListener('click', function () { skip(-15); });
  els.forward.addEventListener('click', function () { skip(30); });
  els.seek.addEventListener('input', function () { seeking = true; els.time.textContent = clock(els.seek.value); });
  els.seek.addEventListener('change', function () { audio.currentTime = Number(els.seek.value); seeking = false; });
  els.rate.addEventListener('change', function () { audio.playbackRate = Number(els.rate.value) || 1; save(true); });
  els.list.addEventListener('click', function (event) {
    var link = event.target.closest('a[data-part]');
    if (!link) { return; }
    event.preventDefault();
    select(Number(link.getAttribute('data-part')), 0, true);
  });

  if ('mediaSession' in navigator) {
    var handlers = {
      play: function () { play(); },
      pause: function () { audio.pause(); },
      previoustrack: function () { select(Math.max(0, current - 1), 0, true); },
      nexttrack: function () { select(current + 1, 0, true); },
      seekbackward: function (details) { skip(-((details && details.seekOffset) || 15)); },
      seekforward: function (details) { skip((details && details.seekOffset) || 30); },
      seekto: function (details) { if (details && details.seekTime !== undefined) { audio.currentTime = details.seekTime; } }
    };
    Object.keys(handlers).forEach(function (action) {
      try { navigator.mediaSession.setActionHandler(action, handlers[action]); } catch (e) { /* unsupported action */ }
    });
  }

  // -- start: a part asked for in the address, or where the listener stopped -----------------
  var asked = Number(new URLSearchParams(window.location.search).get('part'));
  var saved = load();
  if (asked >= 1 && asked <= parts.length) {
    select(asked - 1, 0, false);
  } else if (saved && saved.part >= 0 && saved.part < parts.length && (saved.part > 0 || saved.time > 10)) {
    if (saved.rate) { els.rate.value = String(saved.rate); }
    select(saved.part, saved.time || 0, false);
    els.resume.hidden = false;
    els.resume.textContent = S.resume.replace('{part}', parts[saved.part].title).replace('{time}', clock(saved.time));
  } else {
    if (throughSite) { audio.src = urlOf(0); }
    mark();
    metadata();
    showText(0);
  }
})();
