// Aplica o tema salvo (ou a preferência do sistema) antes da renderização.
(function () {
  var CHAVE = 'tema';
  var raiz = document.documentElement;

  function temaInicial() {
    var salvo = null;
    try {
      salvo = localStorage.getItem(CHAVE);
    } catch (e) {}
    if (salvo === 'light' || salvo === 'dark') return salvo;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function aplicar(tema) {
    raiz.setAttribute('data-bs-theme', tema);
    var botao = document.getElementById('botao-tema');
    if (!botao) return;
    var destino = tema === 'dark' ? 'claro' : 'escuro';
    botao.setAttribute('aria-label', 'Mudar para tema ' + destino);
    botao.textContent = (tema === 'dark' ? '☀ ' : '☾ ') + 'Tema ' + destino;
  }

  aplicar(temaInicial());

  document.addEventListener('DOMContentLoaded', function () {
    aplicar(raiz.getAttribute('data-bs-theme'));
    var botao = document.getElementById('botao-tema');
    if (!botao) return;
    botao.addEventListener('click', function () {
      var novo = raiz.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
      try {
        localStorage.setItem(CHAVE, novo);
      } catch (e) {}
      aplicar(novo);
    });
  });
})();
