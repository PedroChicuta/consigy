// Botão único do menu: em telas largas recolhe/expande a sidebar (escolha lembrada
// por navegador e aplicada antes da renderização); em telas estreitas abre o offcanvas.
(function () {
  var CHAVE = 'menu-recolhido';
  var TELA_LARGA = '(min-width: 768px)';
  var raiz = document.documentElement;

  function recolhidoSalvo() {
    try {
      return localStorage.getItem(CHAVE) === '1';
    } catch (e) {
      return false;
    }
  }

  function salvar(recolhido) {
    try {
      localStorage.setItem(CHAVE, recolhido ? '1' : '0');
    } catch (e) {}
  }

  function telaLarga() {
    return window.matchMedia(TELA_LARGA).matches;
  }

  function atualizarBotao(expandido) {
    var botao = document.getElementById('botao-menu');
    if (botao) botao.setAttribute('aria-expanded', expandido ? 'true' : 'false');
  }

  raiz.classList.toggle('menu-recolhido', recolhidoSalvo());

  document.addEventListener('DOMContentLoaded', function () {
    var botao = document.getElementById('botao-menu');
    var menu = document.getElementById('menu-lateral');
    if (!botao || !menu) return;

    function sincronizar() {
      atualizarBotao(telaLarga() && !raiz.classList.contains('menu-recolhido'));
    }

    botao.addEventListener('click', function () {
      if (telaLarga()) {
        var recolhido = raiz.classList.toggle('menu-recolhido');
        salvar(recolhido);
        sincronizar();
      } else {
        bootstrap.Offcanvas.getOrCreateInstance(menu).toggle();
      }
    });
    menu.addEventListener('shown.bs.offcanvas', function () { atualizarBotao(true); });
    menu.addEventListener('hidden.bs.offcanvas', sincronizar);
    window.matchMedia(TELA_LARGA).addEventListener('change', sincronizar);
    sincronizar();
  });
})();
