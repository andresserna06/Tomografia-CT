/* ============================================================
   Simulador CT — Selector de tema (claro/oscuro + paletas)
   Dash carga este archivo automaticamente por estar en assets/.
   Es JS puro de navegador: no necesita callbacks de Python.
   Construye los swatches y el boton claro/oscuro dentro de
   los contenedores #swatches y #mode-toggle que crea layout.py,
   y recuerda la eleccion en localStorage.
   ============================================================ */
(function () {
  var THEMES = [
    { name: "Clinico cian",   dark:{ accent:"oklch(0.80 0.115 210)", accentD:"oklch(0.64 0.10 210)", hot:"oklch(0.80 0.12 68)" },  light:{ accent:"oklch(0.55 0.13 220)",  accentD:"oklch(0.46 0.11 220)", hot:"oklch(0.58 0.13 52)" } },
    { name: "Osciloscopio",   dark:{ accent:"oklch(0.84 0.16 150)",  accentD:"oklch(0.66 0.13 150)", hot:"oklch(0.82 0.11 95)" },  light:{ accent:"oklch(0.52 0.15 152)",  accentD:"oklch(0.43 0.13 152)", hot:"oklch(0.56 0.13 88)" } },
    { name: "Ambar / cobre",  dark:{ accent:"oklch(0.80 0.13 70)",   accentD:"oklch(0.64 0.11 70)",  hot:"oklch(0.78 0.10 205)" }, light:{ accent:"oklch(0.55 0.14 55)",   accentD:"oklch(0.46 0.12 55)",  hot:"oklch(0.52 0.12 232)" } },
    { name: "Violeta",        dark:{ accent:"oklch(0.72 0.16 300)",  accentD:"oklch(0.58 0.13 300)", hot:"oklch(0.76 0.14 18)" },  light:{ accent:"oklch(0.53 0.18 300)",  accentD:"oklch(0.44 0.15 300)", hot:"oklch(0.56 0.16 22)" } },
    { name: "Indigo clinico", dark:{ accent:"oklch(0.70 0.15 262)",  accentD:"oklch(0.56 0.12 262)", hot:"oklch(0.80 0.12 68)" },  light:{ accent:"oklch(0.50 0.16 262)",  accentD:"oklch(0.42 0.14 262)", hot:"oklch(0.58 0.13 52)" } }
  ];

  var curTheme = 0, curMode = "dark";

  function alpha(s, a) { return s.replace(/\)$/, " / " + a + ")"); }

  function apply() {
    var set = THEMES[curTheme][curMode];
    var r = document.documentElement.style;
    r.setProperty("--accent", set.accent);
    r.setProperty("--accent-d", set.accentD);
    r.setProperty("--accent-bg", alpha(set.accent, curMode === "light" ? ".11" : ".12"));
    r.setProperty("--hot", set.hot);
    document.body.classList.toggle("light", curMode === "light");

    var sw = document.querySelectorAll("#swatches .swatch");
    for (var i = 0; i < sw.length; i++) sw[i].classList.toggle("active", i === curTheme);

    var mb = document.getElementById("mode-toggle");
    if (mb) mb.textContent = curMode === "dark" ? "\u263e Oscuro" : "\u2600 Claro";

    try { localStorage.setItem("ct-theme", curTheme); localStorage.setItem("ct-mode", curMode); } catch (e) {}
  }

  function build() {
    var wrap = document.getElementById("swatches");
    if (!wrap || wrap.dataset.ready) return false;   // aun no existe en el DOM
    wrap.dataset.ready = "1";

    THEMES.forEach(function (t, i) {
      var b = document.createElement("button");
      b.className = "swatch";
      b.title = t.name;
      b.style.background = t.dark.accent;
      b.style.color = t.dark.accent;
      b.addEventListener("click", function () { curTheme = i; apply(); });
      wrap.appendChild(b);
    });

    var mb = document.getElementById("mode-toggle");
    if (mb) mb.addEventListener("click", function () { curMode = curMode === "dark" ? "light" : "dark"; apply(); });

    try {
      curTheme = parseInt(localStorage.getItem("ct-theme")) || 0;
      curMode = localStorage.getItem("ct-mode") || "dark";
    } catch (e) {}
    apply();
    return true;
  }

  // Dash monta el layout de forma asincrona: reintenta hasta que exista #swatches.
  var iv = setInterval(function () { if (build()) clearInterval(iv); }, 120);
  document.addEventListener("DOMContentLoaded", build);
})();
