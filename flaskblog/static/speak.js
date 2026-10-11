/* "Listen" buttons: <button class="btn-speak" data-say="text">.
 *
 * Uses the browser's own speech synthesis with a Catalan voice, so nothing is
 * sent to an outside service. Without a Catalan voice on the device we do not
 * fall back to another language (a Spanish voice reading Catalan teaches the
 * wrong sounds); instead we explain how to install one.
 */
(function () {
  var buttons = document.querySelectorAll('.btn-speak');
  if (!buttons.length) { return; }
  if (!('speechSynthesis' in window)) {
    buttons.forEach(function (button) { button.classList.add('d-none'); });
    return;
  }

  function catalanVoice() {
    var voices = window.speechSynthesis.getVoices();
    var catalan = voices.filter(function (voice) {
      return voice.lang && voice.lang.toLowerCase().replace('_', '-').indexOf('ca') === 0;
    });
    // Prefer voices installed on the device (they work offline).
    catalan.sort(function (a, b) { return (b.localService ? 1 : 0) - (a.localService ? 1 : 0); });
    return catalan[0] || null;
  }

  // Chrome fills the voice list asynchronously; asking early starts loading.
  window.speechSynthesis.getVoices();

  function showHint() {
    var hint = document.getElementById('speak-hint');
    if (!hint) {
      hint = document.createElement('div');
      hint.id = 'speak-hint';
      hint.className = 'alert alert-warning alert-dismissible fade show speak-hint';
      hint.setAttribute('role', 'status');
      hint.innerHTML =
        'На цьому пристрої немає каталонського голосу для озвучення. ' +
        'Додайте його в налаштуваннях: <strong>Android</strong> — «Синтез мовлення» Google → мова «Català»; ' +
        '<strong>iPhone</strong> — Універсальний доступ → Озвучений вміст → Голоси → Català; ' +
        '<strong>Windows</strong> — Час і мова → Мовлення → додати каталонську, або відкрийте сайт у браузері Edge.' +
        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Закрити"></button>';
      document.body.appendChild(hint);
    }
  }

  buttons.forEach(function (button) {
    button.addEventListener('click', function () {
      var voice = catalanVoice();
      if (!voice) { showHint(); return; }
      window.speechSynthesis.cancel();
      var utterance = new SpeechSynthesisUtterance(button.getAttribute('data-say'));
      utterance.voice = voice;
      utterance.lang = voice.lang;
      utterance.rate = 0.85;
      button.classList.add('speaking');
      utterance.onend = utterance.onerror = function () { button.classList.remove('speaking'); };
      window.speechSynthesis.speak(utterance);
    });
  });
})();
