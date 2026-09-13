/* Word · tłumaczenia. Nowy język = nowy plik w jezyki/<kod>.json i wpis w JEZYKI. */
(function () {
  const JEZYKI = ["pl", "en"];
  const slowniki = {};
  let kod = "pl";
  const nasluch = [];

  function podstaw(wzor, vars) {
    return String(wzor).replace(/\{(\w+)\}/g, (m, k) => (vars && k in vars) ? vars[k] : m);
  }
  function t(klucz, vars) {
    const d = slowniki[kod] || {};
    const w = (klucz in d) ? d[klucz] : ((slowniki.pl || {})[klucz] ?? klucz);
    return podstaw(w, vars);
  }
  function zastosuj(root) {
    (root || document).querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.getAttribute("data-i18n")); });
    (root || document).querySelectorAll("[data-i18n-placeholder]").forEach((el) => { el.placeholder = t(el.getAttribute("data-i18n-placeholder")); });
    (root || document).querySelectorAll("[data-i18n-aria]").forEach((el) => { el.setAttribute("aria-label", t(el.getAttribute("data-i18n-aria"))); });
    (root || document).querySelectorAll("[data-i18n-title]").forEach((el) => { document.title = t(el.getAttribute("data-i18n-title")); });
    document.documentElement.lang = kod;
    const sel = document.getElementById("lang");
    if (sel) { sel.value = kod; sel.setAttribute("aria-label", t("lang")); }
  }
  async function wczytaj(k) {
    if (slowniki[k]) return slowniki[k];
    if (window.I18N_INLINE && window.I18N_INLINE[k]) { slowniki[k] = window.I18N_INLINE[k]; return slowniki[k]; }
    try {
      const r = await fetch("/s/jezyki/" + k + ".json", { cache: "no-store" });
      slowniki[k] = await r.json();
    } catch (e) { slowniki[k] = {}; }
    return slowniki[k];
  }
  async function ustaw(k) {
    if (!JEZYKI.includes(k)) k = "pl";
    await wczytaj("pl");
    await wczytaj(k);
    kod = k;
    try { localStorage.setItem("jezyk", k); } catch (e) {}
    zastosuj();
    nasluch.forEach((f) => { try { f(k); } catch (e) {} });
  }
  function start() {
    let k = "pl";
    try { k = localStorage.getItem("jezyk") || ((navigator.language || "pl").startsWith("pl") ? "pl" : "en"); } catch (e) {}
    const sel = document.getElementById("lang");
    if (sel) {
      sel.innerHTML = JEZYKI.map((j) => `<option value="${j}">${j.toUpperCase()}</option>`).join("");
      sel.addEventListener("change", () => ustaw(sel.value));
    }
    return ustaw(k);
  }
  window.i18n = { t, ustaw, start, zastosuj, onChange: (f) => nasluch.push(f), get kod() { return kod; }, JEZYKI };
})();

/* praca nad stroną: przeładuj, gdy pliki strony się zmienią (tylko z lokalnego serwera) */
(function () {
  if (location.protocol !== "http:" || !(/^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname) || /[?&]dev\b/.test(location.search))) return;
  let znana = null;
  setInterval(async () => {
    try {
      const r = await fetch("/api/wersja", { cache: "no-store" });
      const w = (await r.json()).wersja;
      if (znana === null) znana = w;
      else if (w !== znana) location.reload();
    } catch (e) {}
  }, 2000);
})();
