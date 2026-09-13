"""Buduje strona/bytek.html (wersja dla claude.ai) ze strony lokalnej.
Wszystko w jednym pliku: styl, tłumaczenia, skrypt; dane ze wspólnej bazy artifactu."""
import json
import os
import re

K = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strona")
h = open(os.path.join(K, "bytek_lokalny.html")).read()
css = open(os.path.join(K, "wspolne.css")).read()
i18n = open(os.path.join(K, "i18n.js")).read()
slowniki = {k: json.load(open(os.path.join(K, "jezyki", k + ".json"))) for k in ("pl", "en")}


def wytnij(tekst, znacznik, zamiana=""):
    return re.sub(rf"<!-- @@{znacznik}_START -->.*?<!-- @@{znacznik}_END -->", lambda m: zamiana, tekst, flags=re.S)


h = wytnij(h, "STYLE", "<style>\n" + css + "\n</style>")
h = wytnij(h, "I18N", "<script>window.I18N_INLINE = " + json.dumps(slowniki, ensure_ascii=False) + ";\nwindow.KEJ_MOST = true;</script>\n<script>\n" + i18n + "\n</script>")
h = wytnij(h, "NAV", "")
h = wytnij(h, "KONIEC", "")
h = wytnij(h, "NAKARM", "")
h = wytnij(h, "SERWER", "")
h = wytnij(h, "SERWER2", "")
h = wytnij(h, "SERWER3", "")

zrodlo_db = '''
  let db = null;
  $("dlgForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const raw = $("dlgSlowo").value.trim(); if (!raw || dlgNr == null) return;
    if (!db) { $("dlgHint").className = "hint err"; $("dlgHint").textContent = t("powiedz.brak_db"); return; }
    try {
      await db.collection("slowa").add({ tekst: raw.slice(0, 240), czas: Date.now() / 1000, status: "czeka", do: dlgNr });
      $("dlgSlowo").value = ""; $("dlgHint").className = "hint"; $("dlgHint").textContent = t("powiedz.ok.kej");
    } catch (err) { $("dlgHint").className = "hint err"; $("dlgHint").textContent = err && err.code === "quota_exceeded" ? t("powiedz.pelna") : t("powiedz.blad"); }
  });
  window.i18n.start().then(() => {
    window.claude && window.claude.use("db").then((d) => {
      db = d;
      if (!db) return;
      db.doc("stan/byt").onSnapshot((snap) => { if (snap.exists) renderStan(snap.data()); }, () => {});
    });
  });
'''
h = re.sub(r"/\* @@ZRODLO_START \*/.*?/\* @@ZRODLO_END \*/", lambda m: zrodlo_db, h, flags=re.S)
open(os.path.join(K, "bytek.html"), "w").write(h)
print("zbudowano strona/bytek.html:", len(h), "bajtów")
