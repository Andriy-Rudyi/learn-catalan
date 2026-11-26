/* The audiobook player (templates/audiobook.html, flaskblog/audiobooks.py).
 *
 * One <audio> element plays the parts one after another. Real audio files
 * keep playing with the screen locked; the Media Session API gives the lock
 * screen, headphones and the car (Bluetooth, CarPlay, Android Auto) their
 * play/pause, previous/next part and seek controls, with the title shown.
 * Where the listener stopped (part, second) and the speed are kept in this
 * browser (localStorage) and offered on the next visit.
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
    audio.src = parts[index].url;
    audio.playbackRate = rate;
    els.title.textContent = parts[index].title;
    els.seek.max = parts[index].seconds || 0;
    els.total.textContent = clock(parts[index].seconds);
    mark();
    metadata();
    var start = function () {
      if (startAt) { audio.currentTime = startAt; }
      audio.playbackRate = Number(els.rate.value) || 1;
      if (autoplay) { audio.play().catch(function () { showPaused(); }); }
    };
    audio.addEventListener('loadedmetadata', start, { once: true });
    audio.load();
    save(true);
  }

  function showPlaying() {
    els.play.textContent = '⏸';
    els.play.setAttribute('aria-label', S.pause);
    if ('mediaSession' in navigator) { navigator.mediaSession.playbackState = 'playing'; }
  }
  function showPaused() {
    els.play.textContent = '▶';
    els.play.setAttribute('aria-label', S.play);
    if ('mediaSession' in navigator) { navigator.mediaSession.playbackState = 'paused'; }
  }

  function toggle() {
    if (audio.paused) {
      audio.play().catch(function () { showPaused(); });
    } else {
      audio.pause();
    }
  }
  function skip(seconds) {
    var target = Math.max(0, Math.min((audio.duration || parts[current].seconds) - 1, audio.currentTime + seconds));
    audio.currentTime = target;
  }

  // -- events ----------------------------------------------------------------------------------
  audio.addEventListener('play', function () { showPlaying(); metadata(); });
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
      play: function () { audio.play(); },
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
    mark();
    metadata();
  }
})();
