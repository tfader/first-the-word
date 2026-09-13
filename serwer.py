"""Word: własna strona bytka. Czysty Python, bez zależności. Uruchom obok zycie.py:
    python3 serwer.py            (port 8080; PORT=... żeby zmienić)
Czyta ciało i dziennik na żywo, słowa ze strony wpisuje prosto do kolejki bytka.
Ten sam kod działa na dowolnym serwerze z pythonem 3.
"""
import json
import socket
import math
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote, parse_qs

import numpy as np

import most
import word as W
import zycie as Z

KATALOG = os.path.dirname(os.path.abspath(__file__))
ARCHIWUM = os.environ.get("SWIAT") or (sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].isdigit() else None)
DANE = os.path.join(KATALOG, "swiaty", str(ARCHIWUM)) if ARCHIWUM else KATALOG   # skąd czytać świat
STRONA = os.path.join(KATALOG, "strona", "bytek_lokalny.html")
WNETRZE = os.path.join(KATALOG, "strona", "wnetrze.html")
ROD = os.path.join(KATALOG, "strona", "rod.html")
JEZYK = os.path.join(KATALOG, "strona", "jezyk.html")
DZIEJE = os.path.join(KATALOG, "strona", "dzieje.html")
PORT = int(os.environ.get("PORT", 8080))
BLOKADA = threading.Lock()          # jeden wątek naraz przy plikach słów i przy cudzie


def stan_dla_strony():
    """Ten sam dokument, który idzie na stronę w claude.ai, plus losy słów."""
    with BLOKADA:
        doc = most.stan()
        slowa = most.slowa_swiata()
    doc["proces_zyje"] = True if ARCHIWUM else proces_zyje()
    doc["archiwum"] = int(ARCHIWUM) if ARCHIWUM else None
    doc["dwoje"] = most.czytaj_json(most.CIALO, {}).get("dwoje", False)
    doc["slowa"] = sorted(
        [{"tekst": s["tekst"], "status": s["status"], "czas": s.get("czas", 0), "do": s.get("do")} for s in slowa.values()],
        key=lambda s: -(s["czas"] or 0))[:40]
    return doc


def wnetrze(nr=None, lekko=False, limit=None):
    """Wnętrze żywych bytów: geny, powłoki, nawyki, echo, ostatni cykl.
    nr: tylko ta istota (okno istoty). lekko: bez genów, dla mapy (przy tysiącu istot pełne wnętrze liczyło się minutę).
    limit: najwyżej tyle istot z pełnym wnętrzem (strona wnętrza)."""
    swiat = most.czytaj_json(most.CIALO, {"zywi": [], "cykl_swiata": 0})
    ustaw_swiat(swiat)
    dziennik = most.czytaj_dziennik()
    ostatni = {}
    for w in dziennik:
        ostatni[w["byt"]] = w
    byty = []
    zywi = sorted(swiat["zywi"], key=lambda x: x["nr"])
    if nr is not None:
        zywi = [b for b in zywi if b["nr"] == nr]
    if limit is not None and not lekko:
        zywi = zywi[:limit]
    for b in zywi:
        o = ostatni.get(b["nr"], {})
        geny = []
        if lekko:
            byty.append({"nr": b["nr"], "pokolenie": b["pokolenie"], "wiek": b["wiek"], "energia": round(b["energia"], 2),
                         "tryb": o.get("tryb", "jawa"), "geny": [], "otwarte": {}, "echo": [], "slownik": [], "mowa": b.get("mowa"),
                         "dzieci": b["dzieci"], "miejsce": str(b.get("miejsce", 0)), "plec": b.get("plec"), "sila": b.get("sila"),
                         "kierunek": b.get("kierunek", 1), "glos": glos_istoty(b), "rozumie": [], "uprawa": b.get("uprawa"), "spichlerz": b.get("spichlerz"), "ryt": b.get("ryt")})
            continue
        K, P = geny_istoty(b)
        M = K + P
        slownik = {t: np.asarray(W.slowo_na_wektor(t), dtype=float) for t in b.get("slownik", {})}

        def rezonans(kier):
            kier = np.asarray(kier, dtype=float)
            Wy = M @ kier
            nw = np.linalg.norm(Wy, axis=1); nk = np.linalg.norm(kier)
            with np.errstate(divide="ignore", invalid="ignore"):
                return np.where(nw > 0, (Wy @ kier) / (nw * nk), 0.0)

        rez_r = rezonans(swiat["kierunek_rany"]); rez_p = rezonans(swiat["kierunek_pokarmu"])
        rez_s = {t: rezonans(wek) for t, wek in slownik.items()}
        grubosci = np.linalg.norm(P.reshape(len(P), -1), axis=1)
        zrodla = b.get("zrodla", {})
        for i, n in enumerate(b["otwarcia_genu"]):
            slowa = sorted(((round(float(rez_s[t][i]), 2), t) for t in rez_s), reverse=True)[:5]
            geny.append({"nr": i, "otwarcia": n, "nawyk": round(1 - 0.8 ** n, 3), "powloka": round(float(grubosci[i]), 2),
                         "rezonans": {"rana": round(float(rez_r[i]), 2), "pokarm": round(float(rez_p[i]), 2)},
                         "slowa": [{"slowo": t, "r": r} for r, t in slowa],
                         "zrodla": zrodla.get(str(i), {})})
        otwarte = {}
        for klucz in ("rana", "pokarm", "echo", "slowo"):
            for g in (o.get(klucz) or {}).get("geny", []):
                otwarte.setdefault(g, klucz)
        for g in (o.get("inny") or {}).get("geny", []):
            otwarte.setdefault(g, "inny")
        echa = [{"wiek": swiat["cykl_swiata"] - e[2], "sila": round(e[1], 2)} for e in b["echo"]]
        byty.append({
            "nr": b["nr"], "pokolenie": b["pokolenie"], "wiek": b["wiek"], "energia": round(b["energia"], 2),
            "tryb": o.get("tryb", "jawa"), "geny": geny, "otwarte": {str(k): v for k, v in otwarte.items()},
            "echo": echa, "slownik": sorted(b.get("slownik", {}).keys()), "mowa": b.get("mowa"),
            "dzieci": b["dzieci"], "otwarcia": b["otwarcia"], "najdluzsza": b["najdluzsza"],
            "miejsce": str(b.get("miejsce", 0)), "wytrwalosc": b.get("wytrwalosc", 2), "sila": b.get("sila"), "ciekawosc": b.get("ciekawosc"), "plec": b.get("plec"), "stadnosc": b.get("stadnosc"), "optimum": b.get("optimum"), "tolerancja": b.get("tolerancja"), "kierunek": b.get("kierunek", 1), "ufnosc": b.get("ufnosc"), "szczerosc": b.get("szczerosc"), "pojetnosc": b.get("pojetnosc"), "towarzyskosc": b.get("towarzyskosc"),
            "sasiedzi": swiat.get("miejsca", {}).get(str(b.get("miejsce", 0)), {}).get("s", []),
            "glos": glos_istoty(b),
            "rozumie": [],                                   # kto kogo rozumie: liczone dla każdej pary z osobna,
                                                             # więc okno istoty otwierało się wieki. Niewiele z tego wynikało.
        })
    pogoda = {k: Z.klimat_miejsca(swiat, k, mm) for k, mm in swiat.get("miejsca", {}).items()} if "miejsca" in swiat else {}
    return {"cykl_swiata": swiat["cykl_swiata"], "byty": byty, "pole": swiat.get("pole", []), "wymiary": swiat.get("wymiary", 4),
            "kolejnosc": swiat.get("kolejnosc", []), "znanych_miejsc": len(swiat.get("miejsca", {})), "miejsca": swiat.get("miejsca", {}),
            "pogoda": pogoda, "pora": swiat.get("pora"), "noc": swiat.get("noc"),
            "zmarli": [] if (lekko or nr is not None) else [{k: z.get(k) for k in ("nr", "pokolenie", "wiek", "otwarcia", "dzieci", "plec", "zmarl_w_cyklu")} for z in swiat.get("zmarli", [])],
            "zywych": len(swiat["zywi"]), "czas": time.time()}


def geny_istoty(b):
    """(K, P) istoty: z npz, albo ze starego ciała w json."""
    if "kregoslup" in b:
        return np.asarray(b["kregoslup"], dtype=float), np.asarray(b["powloka"], dtype=float)
    return Z.wczytaj_geny(b["nr"])


def ustaw_swiat(swiat):
    wym = int(swiat.get("wymiary", 4))
    W.ustaw_wymiary(wym)
    W.KIERUNEK_GLOSU = swiat.get("kierunek_glosu") or [0.0] * wym
    W.KIERUNEK_WOLANIA = swiat.get("kierunek_wolania") or [0.0] * wym


def glos_istoty(b):
    if "glos_znaki" in b:
        return b["glos_znaki"]
    K, _ = geny_istoty(b)
    return W.glos_na_znaki(W.glos_z_rdzenia(K))


def rozumie_glosy(b, swiat, KP=None):
    """Czy głos każdej innej żywej istoty otwiera w tej istocie gen strojony na pokarm."""
    K, P = KP if KP is not None else geny_istoty(b)
    M = K + P
    wynik = []
    for x in swiat["zywi"]:
        if x["nr"] == b["nr"]:
            continue
        Kx, _ = geny_istoty(x)
        glos = np.asarray(W.glos_z_rdzenia(Kx), dtype=float)
        Wy = M @ glos
        nw = np.linalg.norm(Wy, axis=1); ng = np.linalg.norm(glos)
        with np.errstate(divide="ignore", invalid="ignore"):
            sims = np.where(nw > 0, (Wy @ glos) / (nw * ng), 0.0)
        gen_nr = int(np.argmax(sims)); najlepszy = float(sims[gen_nr])
        zr = b.get("zrodla", {}).get(str(gen_nr), {}) if gen_nr is not None else {}
        o_pokarmie = bool(zr) and max(zr, key=zr.get) == "pokarm"
        wynik.append({"nr": x["nr"], "znaki": W.glos_na_znaki(glos), "slyszy": najlepszy >= W.ZGODNOSC,
                      "zgodnosc": round(najlepszy, 2), "o_pokarmie": o_pokarmie})
    return wynik


def slownik():
    """Słownik świata z ciała: pisany przez proces życia na bieżąco. Tu tylko znaki sygnatur i nazwy."""
    swiat = most.czytaj_json(most.CIALO, None)
    if swiat is None:
        return {"brak": True}
    ustaw_swiat(swiat)
    sl = swiat.get("slownik") or {"slowa": {}, "znaczenia": {}}
    glosy = {}
    for b in swiat.get("zywi", []):
        glosy[b["nr"]] = glos_istoty(b)
    for b in swiat.get("zmarli", []):
        glosy.setdefault(b["nr"], b.get("glos", "?"))
    def znaki(temat, cel):
        try:
            if temat == "zapach":
                return W.glos_na_znaki(swiat["miejsca"][str(cel)]["zapach"])
            if temat == "pokarm":
                return W.glos_na_znaki(swiat["kierunek_pokarmu"])
            if temat == "rana":
                return W.glos_na_znaki(swiat["kierunek_rany"])
            if temat in ("noc", "pora"):
                return W.glos_na_znaki(swiat["sygnatury"][cel if temat == "pora" else "noc"])
            if temat == "klamca":
                return glosy.get(int(cel), "?")
            if temat == "echo":
                return str(cel)
            if temat == "uprawa":
                return W.glos_na_znaki(swiat["sygnatury"]["uprawa"])
            if temat == "spichlerz":
                return W.glos_na_znaki(swiat["sygnatury"]["spichlerz"])
            if temat == "bol":
                return W.glos_na_znaki([a + c for a, c in zip(swiat["kierunek_rany"], swiat["miejsca"][str(cel)]["zapach"])])
        except Exception:
            return "?"
        return "?"
    def slowo_znaczenia(k, n):
        """Wpis słowa przy znaczeniu: wrodzone (@wolanie, @alarm), wyuczone (temat:cel) albo nieznane („?”)."""
        if k.startswith("@"):
            return {"klucz": k, "razy": n, "temat": k[1:], "cel": None, "znaki": "♪" if k == "@wolanie" else "!"}
        temat, _, cel = k.partition(":")
        if not temat or temat == "?":
            return {"klucz": "?", "razy": n, "temat": "?", "cel": None, "znaki": "?"}
        return {"klucz": k, "razy": n, "temat": temat, "cel": cel or None, "znaki": znaki(temat, cel or None)}
    slowa = {}
    for k, s in sl["slowa"].items():
        slowa[k] = {**s, "znaki": znaki(s["temat"], s["cel"]), "nadawcow": len(s.get("nadawcy", []))}
        slowa[k].pop("nadawcy", None)
    znaczenia = []
    for zn in sl["znaczenia"].values():
        znaczenia.append({"czyn": zn["czyn"], "ludzko": zn.get("ludzko"), "razy": zn["razy"], "mowiacych": len(zn.get("kto", [])), "rozumiejacych": len(zn.get("dla", [])),
                          "pierwszy_cykl": zn.get("pierwszy_cykl"), "verb": zn.get("verb"),
                          "slowa": [slowo_znaczenia(k, n) for k, n in sorted(zn["slowa"].items(), key=lambda kv: -kv[1])]})
    znaczenia.sort(key=lambda x: -x["razy"])
    # słownik z obserwacji: dla każdego ciągu znaków, co słuchacze po nim zrobili, ale tylko to, co widać z zewnątrz.
    # Czyny wewnętrzne (zapamiętać, przestać wierzyć) z zewnątrz nie istnieją. Tak czyta się pismo obcej cywilizacji.
    WIDOCZNE = {"idz": "idzie", "chodz": "idzie", "bron": "broni", "unikaj": "unika", "odpowiedz": "odpowiada", "gromadz": "gromadzi", "uprawiaj": "uprawia"}
    reakcje = {}
    for zn in sl["znaczenia"].values():
        klasa = WIDOCZNE.get(zn.get("verb"))
        if not klasa:
            continue
        for k, n in zn["slowa"].items():
            r = reakcje.setdefault(k, {})
            r[klasa] = r.get(klasa, 0) + n
    obserwacja = []
    for k, r in reakcje.items():
        s = sl["slowa"].get(k)
        if k.startswith("@"):
            znaki_ = "♪" if k == "@wolanie" else "!"
            razy = sum(r.values())
        elif s is None:
            continue
        else:
            znaki_ = znaki(s["temat"], s["cel"]); razy = max(s["razy"], sum(r.values()))
        glowna = max(r, key=r.get)
        obserwacja.append({"klucz": k, "znaki": znaki_, "razy": razy, "reakcje": dict(sorted(r.items(), key=lambda kv: -kv[1])), "glowna": glowna,
                           "widziano": sum(r.values()), "pewnosc": round(r[glowna] / razy, 2) if razy else 0.0, "nadawcow": len(s["nadawcy"]) if s else None})
    obserwacja.sort(key=lambda x: (-x["widziano"], -x["pewnosc"]))
    bez_reakcji = sum(1 for k in sl["slowa"] if k not in reakcje)
    return {"cykl": swiat.get("cykl_swiata"), "slowa": sorted(slowa.values(), key=lambda s: (-s["nadawcow"], -s["razy"]))[:200], "znaczenia": znaczenia,
            "obserwacja": obserwacja, "bez_reakcji": bez_reakcji}


def jezyk():
    """Język istot: głosy, kto je słyszy, kto kojarzy, i dziennik rozmów."""
    swiat = most.czytaj_json(most.CIALO, {"zywi": [], "zmarli": [], "cykl_swiata": 0})
    ustaw_swiat(swiat)
    dziennik = most.czytaj_dziennik()
    glosy = {}
    for b in swiat["zywi"]:
        glosy[b["nr"]] = {"nr": b["nr"], "znaki": glos_istoty(b), "zyje": True,
                          "wydany": 0, "rozumie": (rozumie_glosy(b, swiat) if len(swiat["zywi"]) <= 64 else []), "slownik": sorted(b.get("slownik", {}).keys())}   # kto rozumie kogo: kwadrat liczby istot, tylko w małym świecie
    for b in swiat["zmarli"]:
        glosy[b["nr"]] = {"nr": b["nr"], "znaki": b.get("glos", "?"), "zyje": False, "wydany": 0, "rozumie": [], "slownik": []}
    rozmowy = []
    for w in dziennik:
        m = w.get("mowa") or {}
        if m.get("glos") and w["byt"] in glosy:
            glosy[w["byt"]]["wydany"] += 1
        inny = w.get("inny") or {}
        if inny.get("typ") in ("glos", "wolanie", "odpowiedz") or inny.get("glos"):
            rozmowy.append({"cykl": w["cykl_swiata"], "kto": inny.get("od"), "do": w["byt"], "typ": inny.get("typ", "glos"),
                            "otworzyl": bool(inny.get("geny")), "czyn": inny.get("czyn"),
                            "znaki": glosy.get(inny.get("od"), {}).get("znaki", "?")})
        if m.get("krzyk"):
            rozmowy.append({"cykl": w["cykl_swiata"], "kto": w["byt"], "do": None, "krzyk": True})
        if m.get("wolanie"):
            rozmowy.append({"cykl": w["cykl_swiata"], "kto": w["byt"], "do": None, "wolanie": True})
        if m.get("odpowiedz") is not None:
            rozmowy.append({"cykl": w["cykl_swiata"], "kto": w["byt"], "do": m["odpowiedz"], "odpowiedz": True, "znaki": m.get("znaki")})
        if w.get("rozmowa"):
            rozmowy.append({"cykl": w["cykl_swiata"], "kto": w["byt"], "do": w["rozmowa"]["z"], "gawedza": True, "co": w["rozmowa"]["co"]})
        if m.get("slowo"):
            rozmowy.append({"cykl": w["cykl_swiata"], "kto": w["byt"], "do": None, "slowo": m["slowo"]})
    slowa = {}
    for w in dziennik:
        t = (w.get("slowo") or {}).get("tekst")
        if not t:
            continue
        s = slowa.setdefault(t, {"tekst": t, "padlo": 0, "uslyszane": 0, "przespane": 0, "nierozpoznane": 0,
                                 "pierwszy_cykl": w["cykl_swiata"], "ostatni_cykl": w["cykl_swiata"], "kto_slyszal": set()})
        s["padlo"] += 1
        s["ostatni_cykl"] = w["cykl_swiata"]
        if w["tryb"] == "sen":
            s["przespane"] += 1
        elif w["slowo"]["geny"]:
            s["uslyszane"] += 1
            s["kto_slyszal"].add(w["byt"])
        else:
            s["nierozpoznane"] += 1
    for s in slowa.values():
        s["kto_slyszal"] = sorted(s["kto_slyszal"])
    # o czym mówią: głos + temat (zapach łąki, kłamca, pokarm, rana, pora, noc, cudze słowo)
    tematy = {}
    for w in dziennik:
        m = w.get("mowa") or {}
        if m.get("glos") and m.get("temat"):
            kl = (w["byt"], m["temat"], str(m.get("cel")) if m.get("cel") is not None else None)
            t_ = tematy.setdefault(kl, {"kto": w["byt"], "znaki": glosy.get(w["byt"], {}).get("znaki", "?"), "temat": m["temat"], "cel": m.get("cel"), "razy": 0, "pierwszy_cykl": w["cykl_swiata"]})
            t_["razy"] += 1
    # nowe słowa: dźwięki, które wyszły z istoty jako skutek uboczny i zostały wypowiedziane; liczy się, kto je powtórzył
    nowe = {}
    for w in dziennik:
        m = w.get("mowa") or {}
        if m.get("glos") and m.get("slowo_id"):
            n_ = nowe.setdefault(m["slowo_id"], {"znaki": m["slowo_id"], "pierwszy": w["byt"], "pierwszy_cykl": w["cykl_swiata"], "razy": 0, "nadawcy": set(), "powtorzone": 0})
            n_["razy"] += 1
            n_["nadawcy"].add(w["byt"])
            if m.get("temat") == "inny":
                n_["powtorzone"] += 1
    for n_ in nowe.values():
        n_["nadawcy"] = sorted(n_["nadawcy"])
    # słowa istot: unikalne wypowiedzi między nimi (temat + do czego się odnosi), niezależnie od tego, kto mówił.
    # Znaki: sygnatura tematu (zapach łąki, pokarm, ból, noc, pora, głos kłamcy, własne echo). Znaczenie: czyn, jaki wywołało.
    po_cyklu = {}
    for w in dziennik:
        po_cyklu[(w["byt"], w["cykl_swiata"])] = w
    def znaki_sygnatury(temat, cel):
        try:
            if temat == "zapach":
                return W.glos_na_znaki(swiat["miejsca"][str(cel)]["zapach"])
            if temat == "pokarm":
                return W.glos_na_znaki(swiat["kierunek_pokarmu"])
            if temat == "rana":
                return W.glos_na_znaki(swiat["kierunek_rany"])
            if temat in ("noc", "pora"):
                return W.glos_na_znaki(swiat["sygnatury"][cel if temat == "pora" else "noc"])
            if temat == "klamca":
                return glosy.get(int(cel), {}).get("znaki", "?")
            if temat == "echo":
                return str(cel)
        except Exception:
            return "?"
        return "?"
    slowa_istot = {}
    for w in dziennik:
        m = w.get("mowa") or {}
        if not (m.get("glos") and m.get("temat")):
            continue
        temat, cel = m["temat"], m.get("cel")
        if temat == "inny":
            if not m.get("slowo_id"):
                continue                                   # powtórzenie cudzego słowa: liczy się do tamtego słowa
            temat, cel = "echo", m["slowo_id"]
        kl = temat + ":" + (str(cel) if cel is not None else "")
        s_ = slowa_istot.setdefault(kl, {"temat": temat, "cel": cel, "znaki": znaki_sygnatury(temat, cel), "razy": 0, "nadawcy": set(), "pierwszy_cykl": w["cykl_swiata"], "czyny": {}})
        s_["razy"] += 1
        s_["nadawcy"].add(w["byt"])
    for w in dziennik:
        inny = w.get("inny") or {}
        if not (inny.get("czyn") and inny.get("typ") in ("glos", "odpowiedz")):
            continue
        n_ = po_cyklu.get((inny.get("od"), w["cykl_swiata"] - 1))
        m = (n_ or {}).get("mowa") or {}
        if not m.get("temat"):
            continue
        temat, cel = m["temat"], m.get("cel")
        if temat == "inny":
            if not m.get("slowo_id"):
                continue
            temat, cel = "echo", m["slowo_id"]
        kl = temat + ":" + (str(cel) if cel is not None else "")
        if kl in slowa_istot:
            slowa_istot[kl]["czyny"][inny["czyn"]] = slowa_istot[kl]["czyny"].get(inny["czyn"], 0) + 1
    for s_ in slowa_istot.values():
        s_["nadawcy"] = sorted(s_["nadawcy"])
    czekaja = [x["tekst"] for x in most.slowa_swiata().values() if x.get("status") in ("czeka", "w_drodze")]
    znaczenia = {}
    for r in rozmowy:
        if r.get("czyn"):
            k = (r["kto"], r["typ"])
            z = znaczenia.setdefault(k, {"kto": r["kto"], "typ": r["typ"], "znaki": r.get("znaki"), "czyn": r["czyn"],
                                         "ludzko": ((swiat.get("slownik") or {}).get("znaczenia") or {}).get(r["czyn"], {}).get("ludzko"),
                                         "razy": 0, "dla": set()})
            z["razy"] += 1
            z["dla"].add(r["do"])
    for z in znaczenia.values():
        z["dla"] = sorted(z["dla"])
    return {"cykl_swiata": swiat["cykl_swiata"], "glosy": sorted(glosy.values(), key=lambda g: g["nr"]),
            "rozmowy": rozmowy[-80:], "wymiary": swiat.get("wymiary", 4),
            "slowa": sorted(slowa.values(), key=lambda s: (-s["padlo"], s["tekst"])), "czekaja": czekaja,
            "znaczenia": list(znaczenia.values()),
            "tematy": sorted(tematy.values(), key=lambda t: (-t["razy"], t["kto"]))[:80],
            "nowe_slowa": sorted(nowe.values(), key=lambda n_: (-len(n_["nadawcy"]), -n_["razy"]))[:60],
            "slowa_istot": sorted(slowa_istot.values(), key=lambda s_: (-len(s_["nadawcy"]), -s_["razy"]))[:120]}


def genom_swiata():
    """Co w tym świecie może nieść genom: kierunki gatunku, cechy dziedziczne i nabyte, stałe świata."""
    swiat = most.czytaj_json(most.CIALO, {"zywi": [], "zmarli": [], "cykl_swiata": 0})
    ustaw_swiat(swiat)
    z = lambda k: W.glos_na_znaki(swiat[k]) if swiat.get(k) else None
    geny = (swiat["zywi"] or swiat["zmarli"] or [{}])[0].get("geny")
    return {
        "wymiary": swiat.get("wymiary", 4), "geny": geny, "istot_na_start": swiat.get("istot_na_start"),
        "dwoje": swiat.get("dwoje", False), "cykl_sekund": swiat.get("cykl_sekund"),
        "kierunki": {"rana": z("kierunek_rany"), "pokarm": z("kierunek_pokarmu"), "wolanie": z("kierunek_wolania"), "glos": z("kierunek_glosu")},
        "stale": {"sytosc": W.SYTOSC, "pojemnosc": W.POJEMNOSC, "prog_cudu": W.PROG_CUDU, "koszt_trwania": W.KOSZT_TRWANIA,
                  "koszt_snu": W.KOSZT_SNU, "koszt_bramki": W.KOSZT_BRAMKI, "koszt_odruchu": W.KOSZT_ODRUCHU, "koszt_ruchu": W.KOSZT_RUCHU,
                  "zgodnosc": W.ZGODNOSC, "skapstwo": W.SKAPSTWO, "wchlanianie": W.WCHLANIANIE, "nawyk": W.NAWYK,
                  "starzenie": W.STARZENIE, "mutacja": W.MUTACJA, "nowy_gen": W.NOWY_GEN, "akcent": W.AKCENT,
                  "dziecinstwo": W.DZIECINSTWO, "karmienie": W.KARMIENIE, "hojnosc": W.HOJNOSC, "sila_max": W.SILA_MAX},
    }


CECHY_PORTRETU = ("sila", "lownosc", "ciekawosc", "stadnosc", "dlugowiecznosc", "ufnosc", "szczerosc", "pojetnosc", "towarzyskosc", "optimum", "tolerancja", "ozdoba", "gust", "troska", "odpornosc")


def portret():
    """Najwybitniejsza istota świata: najmądrzejsza (co nabyła) i najbogatsza (co osiągnęła). Surowe dane;
    na ludzki język przekłada je strona, w języku czytelnika."""
    swiat = most.czytaj_json(most.CIALO, None)
    if swiat is None:
        return {"brak": True}
    dziennik = most.czytaj_dziennik()
    ostatni_wpis, tematy, max_e = {}, {}, {}
    for w in dziennik:
        ostatni_wpis[w["byt"]] = w
        max_e[w["byt"]] = max(max_e.get(w["byt"], 0.0), w.get("energia", 0.0))
        m = w.get("mowa") or {}
        if m.get("glos") and m.get("temat"):
            t = tematy.setdefault(w["byt"], {})
            kl = m["temat"] + (":" + str(m["cel"]) if m.get("cel") is not None else "")
            t[kl] = t.get(kl, 0) + 1
    kandydaci = []
    for b in list(swiat.get("zmarli", [])) + list(swiat.get("zywi", [])):
        b = dict(b)
        w = ostatni_wpis.get(b["nr"], {})
        for c in CECHY_PORTRETU + ("nauczone", "uprawa", "spichlerz"):
            if b.get(c) is None and w.get(c) is not None:
                b[c] = w[c]
        b.setdefault("zrozumiane", []); b.setdefault("mapa", {}); b.setdefault("klamcy", []); b.setdefault("slownik", [])
        if isinstance(b.get("slownik"), dict):
            b["slownik"] = sorted(b["slownik"].keys())
        lak = sum(len(m) for m in (b.get("mapa") or {}).values())
        t = tematy.get(b["nr"], {})
        madrosc = 3 * len(b["zrozumiane"]) + lak + 2 * len(b["klamcy"]) + 2 * len(b["slownik"]) + b.get("rozmowy", 0) + min(b.get("nauczone", 0), 8) / 2 + len(t) + 4 * float(b.get("uprawa") or 0) + 4 * float(b.get("spichlerz") or 0)
        bogactwo = 3 * b.get("dzieci", 0) + max_e.get(b["nr"], 0.0) / 5
        # wybitność w tempie na 30 cykli życia (co najmniej 10), nie sumą dorobku: inaczej wygrywa sam wiek
        if b.get("wiek", 0) < 15:
            continue                                                # za młoda na portret: mapa po matce to jeszcze nie dorobek
        tempo = 30.0 / max(30, b.get("wiek", 0))
        kandydaci.append(((madrosc + bogactwo) * tempo, madrosc * tempo, bogactwo * tempo, b, t))
    if not kandydaci:
        return {"brak": True}
    kandydaci.sort(key=lambda k: -k[0])
    razem, madrosc, bogactwo, b, t = kandydaci[0]
    b["zyje"] = any(x["nr"] == b["nr"] for x in swiat.get("zywi", []))
    if not b.get("glos") or not isinstance(b.get("glos"), str):
        try:
            b["glos"] = glos_istoty(b)
        except Exception:
            b["glos"] = "?"
    b["max_energia"] = round(max_e.get(b["nr"], 0.0), 1)
    b["tematy"] = sorted(({"temat": k.split(":")[0], "cel": k.split(":")[1] if ":" in k else None, "razy": n} for k, n in t.items()), key=lambda x: -x["razy"])[:5]
    b["lak"] = {p: len(m) for p, m in (b.get("mapa") or {}).items()}
    pola = ("nr", "plec", "pokolenie", "wiek", "dzieci", "rodzic", "rodzic2", "glos", "zmarl_w_cyklu", "urodzony_w_cyklu", "ostatnia", "zyje",
            "zrozumiane", "klamcy", "slownik", "nauczone", "rozmowy", "krokow", "sen", "otwarcia", "max_energia", "tematy", "lak", "uprawa", "spichlerz") + CECHY_PORTRETU
    b = {k: b.get(k) for k in pola}
    return {"istota": b, "madrosc": round(madrosc, 1), "bogactwo": round(bogactwo, 1), "istot": len(kandydaci),
            "druga": {"nr": kandydaci[1][3]["nr"], "razem": round(kandydaci[1][0], 1)} if len(kandydaci) > 1 else None}


def dzieje():
    """Podsumowanie dziejów świata: liczby, rekordy, cechy po pokoleniach, język, zdarzenia."""
    swiat = most.czytaj_json(most.CIALO, None)
    if swiat is None:
        return {"brak": True}
    dziennik = most.czytaj_dziennik()
    zd = []
    p = os.path.join(DANE, "zdarzenia.jsonl")
    if os.path.exists(p):
        with open(p) as f:
            for l in f:
                try:
                    zd.append(json.loads(l))
                except json.JSONDecodeError:
                    pass
    wszyscy = swiat["zywi"] + swiat["zmarli"]
    pokolenia = {}
    for b in wszyscy:
        pokolenia.setdefault(b["pokolenie"], []).append(b)
    def srednia(lista, klucz):
        v = [x[klucz] for x in lista if isinstance(x.get(klucz), (int, float))]
        return round(sum(v) / len(v), 2) if v else None
    cechy = []
    for pok in sorted(pokolenia):
        g = pokolenia[pok]
        cechy.append({"pokolenie": pok, "ile": len(g), "wiek": srednia(g, "wiek"), "sila": srednia(g, "sila"),
                      "ciekawosc": srednia(g, "ciekawosc"), "stadnosc": srednia(g, "stadnosc"),
                      "dlugowiecznosc": srednia(g, "dlugowiecznosc"), "optimum": srednia(g, "optimum"), "tolerancja": srednia(g, "tolerancja"),
                      "ufnosc": srednia(g, "ufnosc"), "szczerosc": srednia(g, "szczerosc"), "pojetnosc": srednia(g, "pojetnosc"), "towarzyskosc": srednia(g, "towarzyskosc"), "nauczone": srednia(g, "nauczone"),
                      "ozdoba": srednia(g, "ozdoba"), "gust": srednia(g, "gust"), "troska": srednia(g, "troska"), "odpornosc": srednia(g, "odpornosc")})
    zliczenia = {}
    for x in zd:
        zliczenia[x["typ"]] = zliczenia.get(x["typ"], 0) + 1
    najstarsza = max(wszyscy, key=lambda b: b["wiek"], default=None)
    najplodniejsza = max(wszyscy, key=lambda b: b.get("dzieci", 0), default=None)
    slowa = {}
    for w in dziennik:
        t = (w.get("slowo") or {}).get("tekst")
        if t:
            slowa[t] = slowa.get(t, 0) + 1
    glosy = sum(1 for w in dziennik if (w.get("mowa") or {}).get("glos"))
    odpowiedzi = sum(1 for w in dziennik if (w.get("mowa") or {}).get("odpowiedz") is not None)
    czyny = {}
    for w in dziennik:
        c = (w.get("inny") or {}).get("czyn")
        if c:
            czyny[c] = czyny.get(c, 0) + 1
    return {
        "cykli": swiat["cykl_swiata"], "wygasla": swiat.get("wygasla", False), "narodziny": swiat.get("narodziny"), "koniec": swiat.get("koniec"),
        "istot": len(wszyscy), "zywych": len(swiat["zywi"]), "zmarlych": len(swiat["zmarli"]),
        "pokolen": max(pokolenia) if pokolenia else 0, "cudow": sum(1 for b in wszyscy if b.get("rodzic") is not None),
        "geny": swiat.get("geny"), "wymiary": swiat.get("wymiary"), "miejsc": len(swiat.get("miejsca", {})),
        "najstarsza": {"nr": najstarsza["nr"], "wiek": najstarsza["wiek"]} if najstarsza else None,
        "najplodniejsza": {"nr": najplodniejsza["nr"], "dzieci": najplodniejsza.get("dzieci", 0)} if najplodniejsza and najplodniejsza.get("dzieci") else None,
        "cechy": cechy, "zdarzenia": zliczenia, "slowa": sorted(slowa.items(), key=lambda kv: -kv[1])[:10],
        "glosy": glosy, "odpowiedzi": odpowiedzi, "czyny": czyny,
        "slowa_keja": [x["slowo"] for x in (most.czytaj_jsonl(most.SLOWA_KEJA))][-12:],
    }


WAZNE_ZDARZENIA = ("zaraza", "pozar", "powodz", "upolowana", "gatunki", "odczytanie", "odkrycie", "koniec", "spuscizna")   # rzadkie i dotykające wielu istot naraz
# drapieżnik przychodzi co kilka cykli i zwykle odchodzi z niczym, więc liczy się dopiero polowanie z ofiarą;
# spis gatunków robi się co 50 cykli, więc liczy się dopiero zmiana ich liczby


def cywilizacja():
    """Oś czasu cywilizacji: ile istot żyło w każdym cyklu i najważniejsze zdarzenia.
    Liczbę istot odtwarzamy z narodzin i śmierci, zakotwiczoną w tym, ile żyje teraz (ciało świata),
    więc początkowe istoty z cudu, które nie mają wpisu narodzin, też się zgadzają."""
    swiat = most.czytaj_json(most.CIALO, None)
    if swiat is None:
        return {"brak": True}
    teraz = int(swiat.get("cykl_swiata", 0))
    p = os.path.join(DANE, "zdarzenia.jsonl")
    urodzenia, zgony, wazne, gatunki_bylo = {}, {}, [], None
    zachorowania, ozdrowienia, chore = {}, {}, set()             # chore: kto choruje w tej chwili odczytu, żeby śmierć chorej zdjęła ją z rachunku
    if os.path.exists(p):
        with open(p) as f:
            for l in f:
                try:
                    x = json.loads(l)
                except json.JSONDecodeError:
                    continue
                c, typ = int(x.get("cykl", 0)), x.get("typ")
                if typ == "narodziny":
                    urodzenia[c] = urodzenia.get(c, 0) + 1
                elif typ == "smierc":
                    zgony[c] = zgony.get(c, 0) + 1
                    if x.get("nr") in chore:
                        chore.discard(x.get("nr"))
                        ozdrowienia[c] = ozdrowienia.get(c, 0) + 1
                elif typ == "wyzdrowienie":
                    if x.get("nr") in chore:
                        chore.discard(x["nr"])
                        ozdrowienia[c] = ozdrowienia.get(c, 0) + 1
                if typ in ("zarazila_sie", "zaraza") and x.get("nr") is not None and x["nr"] not in chore:
                    chore.add(x["nr"])                             # „zaraza” to pierwsza chora, potem idą „zarazila_sie”
                    zachorowania[c] = zachorowania.get(c, 0) + 1
                if typ in WAZNE_ZDARZENIA:
                    if typ == "gatunki":
                        if x.get("ile") == gatunki_bylo:
                            continue
                        gatunki_bylo = x.get("ile")
                    if typ == "odczytanie" and x.get("autor_zyje", True):
                        continue                                    # liczy się odczyt po zmarłym: kultura przeżyła śmierć
                    if typ == "odkrycie" and x.get("co") != "ryt":
                        continue                                    # uprawę i spichlerz odkrywa się dziesiątki razy; ryt to przełom
                    if typ == "spuscizna" and x.get("glos"):
                        continue                                    # nagrobek z samym głosem to nie książka: w dziejach tylko spuścizna ze znaczeniami
                    w = {"cykl": c, "typ": "polowanie" if typ == "upolowana" else typ}
                    for k in ("miejsce", "ilu", "ile", "szczep", "nr", "od", "co", "powod", "ostatni", "wiek"):
                        if k in x:
                            w[k] = x[k]
                    wazne.append(w)
    saldo = sum(urodzenia.values()) - sum(zgony.values())
    n = len(swiat.get("zywi", [])) - saldo                       # ilu było na początku (przed pierwszym wpisem)
    krzywa, k_chore, k_ur, k_zg, ch = [], [], [], [], 0
    for c in range(0, teraz + 1):
        n += urodzenia.get(c, 0) - zgony.get(c, 0)
        ch += zachorowania.get(c, 0) - ozdrowienia.get(c, 0)
        krzywa.append(max(0, n))
        k_chore.append(max(0, ch))
        k_ur.append(urodzenia.get(c, 0))
        k_zg.append(zgony.get(c, 0))
    # wielkie wymieranie: spadek o ponad jedną trzecią w ciągu dziesięciu cykli, liczony od szczytu
    OKNO, PROG = 10, 1 / 3
    szczyt_c, szczyt_n, ostatnie = 0, krzywa[0] if krzywa else 0, -OKNO
    for c, v in enumerate(krzywa):
        if v >= szczyt_n:
            szczyt_c, szczyt_n = c, v
        elif szczyt_n >= 6 and c - szczyt_c <= OKNO and v <= szczyt_n * (1 - PROG) and c - ostatnie > OKNO:
            wazne.append({"cykl": c, "typ": "wymieranie", "z": szczyt_n, "na": v, "od_cyklu": szczyt_c})
            ostatnie = c
            szczyt_c, szczyt_n = c, v
    wazne.sort(key=lambda w: w["cykl"])
    return {"cykl_swiata": teraz, "zywych": len(swiat.get("zywi", [])), "krzywa": krzywa, "zdarzenia": wazne,
            "szczyt": max(krzywa) if krzywa else 0,
            "serie": {"wszystkie": krzywa, "chore": k_chore, "narodziny": k_ur, "zgony": k_zg}}   # co można pokazać zamiast wszystkich istot


def rod():
    """Drzewo rodowe: z ciała (żywi, zmarli) i z dziennika (kto kogo urodził)."""
    swiat = most.czytaj_json(most.CIALO, {"zywi": [], "zmarli": [], "cykl_swiata": 0})
    dziennik = most.czytaj_dziennik()
    rodzic, urodzony = {}, {}
    for w in dziennik:
        if w.get("tryb") == "cud" and w.get("dziecko"):
            rodzic[w["dziecko"]] = w["byt"]
            urodzony[w["dziecko"]] = w["cykl_swiata"]
    osoby = {}
    for b in swiat["zywi"]:
        osoby[b["nr"]] = {"nr": b["nr"], "pokolenie": b["pokolenie"], "wiek": b["wiek"], "zyje": True,
                          "dzieci": b["dzieci"], "energia": round(b["energia"], 1),
                          "rodzic": b.get("rodzic") or rodzic.get(b["nr"]), "rodzic2": b.get("rodzic2"),
                          "urodzony": b.get("urodzony_w_cyklu") or urodzony.get(b["nr"])}
    for b in swiat["zmarli"]:
        osoby[b["nr"]] = {"nr": b["nr"], "pokolenie": b["pokolenie"], "wiek": b["wiek"], "zyje": False,
                          "dzieci": b["dzieci"], "zmarl": b.get("zmarl_w_cyklu"),
                          "rodzic": b.get("rodzic") or rodzic.get(b["nr"]), "rodzic2": b.get("rodzic2"),
                          "urodzony": urodzony.get(b["nr"]) or (b.get("zmarl_w_cyklu", 0) - b["wiek"])}
    return {"cykl_swiata": swiat["cykl_swiata"], "dwoje": swiat.get("dwoje", False),
            "osoby": sorted(osoby.values(), key=lambda o: o["nr"])}


SWIATY = os.path.join(KATALOG, "swiaty")
ZYCIE_PID = os.path.join(KATALOG, "zycie.pid")
if ARCHIWUM:
    # podgląd dawnego świata: czytamy wyłącznie z jego katalogu, niczego nie ruszamy
    most.ustaw_katalog(DANE)
    Z.GENY_DIR = os.path.join(DANE, "cialo")
PLIKI_SWIATA = ["swiat.json", "dziennik.jsonl", "slowa_keja.jsonl", "slowa_swiata.json", "slowa_update.json",
                "wejscie.txt", "wejscie.txt.czytam", "stan.json", "zycie.log", "karma.txt", "karma.txt.czytam", "cud.txt", "cialo", "zdarzenia.jsonl", "korpus.jsonl"]


_PROCES_CACHE = {"czas": 0.0, "pid": None, "wynik": False}


def proces_zyje():
    """Czy proces z zycie.pid żyje i naprawdę jest procesem życia (nie cudzym po restarcie Maca).
    Wynik `ps` pamiętany 5 s (strona pyta co 20 s z każdej karty)."""
    try:
        pid = int(open(ZYCIE_PID).read().strip())
        os.kill(pid, 0)
        c = _PROCES_CACHE
        if c["pid"] == pid and time.time() - c["czas"] < 5:
            return c["wynik"]
        wynik = subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True)
        c.update(czas=time.time(), pid=pid, wynik=("zycie.py" in wynik.stdout))
        return c["wynik"]
    except (OSError, ValueError, FileNotFoundError):
        return False


def wznow_zycie():
    """Wznowienie procesu życia na istniejącym ciele (po awarii, restarcie Maca): zycie.py sam wraca do ciała."""
    swiat = most.czytaj_json(most.CIALO, None)
    if swiat is None or not swiat.get("zywi") or swiat.get("wygasla"):
        return 409, {"blad": "nie ma kogo wznawiać"}
    if proces_zyje():
        return 409, {"blad": "proces życia już działa"}
    with open(os.path.join(KATALOG, "zycie.log"), "a") as log:
        proc = subprocess.Popen([sys.executable, os.path.join(KATALOG, "zycie.py")],
                                cwd=KATALOG, stdout=log, stderr=subprocess.STDOUT, env={**os.environ}, start_new_session=True)
    with open(ZYCIE_PID, "w") as f:
        f.write(str(proc.pid))
    _PROCES_CACHE["czas"] = 0.0
    time.sleep(1)
    return 200, {"wznowiony": True, "pid": proc.pid}


def nowy_swiat(geny=None, dwoje=False, cykl=None, wymiary=None, istot=None, rozmiar=None, pojemnosc=None, jezyk=None):
    """Stary świat idzie do archiwum (rzeczywistość równoległa), rusza nowy proces życia.
    Tylko gdy w obecnym świecie nikt nie żyje. geny: ile genów ma mieć pierwszy byt."""
    def liczba(x, dom):
        f = float(x if x not in (None, "") else dom)
        if not math.isfinite(f):
            raise ValueError("nie liczba")
        return f
    geny = max(4, min(4096, int(liczba(geny, os.environ.get("GENY", "64")))))
    cykl = max(1.0, min(3600.0, liczba(cykl, os.environ.get("CYKL", "60"))))
    wymiary = max(2, min(64, int(liczba(wymiary, 4))))
    dwoje = True                                              # zawsze dwoje rodziców
    istot = max(2, min(32, int(liczba(istot, 2))))
    rozmiar = rozmiar if rozmiar in ("ciasny", "zwykly", "rozlegly") else "zwykly"
    pojemnosc = max(10, min(20000, int(liczba(pojemnosc, os.environ.get("POJEMNOSC_SWIATA", "2000")))))   # ilu żywych świat uniesie
    jezyk = jezyk if jezyk in ("pl", "en") else os.environ.get("JEZYK", "pl")   # język nazw czynów w tym świecie
    swiat = most.czytaj_json(most.CIALO, None)
    if proces_zyje():
        return 409, {"blad": "proces życia jeszcze działa"}
    przerwany = swiat is not None and bool(swiat.get("zywi")) and not swiat.get("wygasla")   # ktoś żył, ale proces padł
    numer = 1
    os.makedirs(SWIATY, exist_ok=True)
    while os.path.exists(os.path.join(SWIATY, str(numer))):
        numer += 1
    cel = os.path.join(SWIATY, str(numer))
    if swiat is not None:
        os.makedirs(cel)
        try:
            with open(os.path.join(cel, "dzieje.json"), "w") as f:
                json.dump(dzieje(), f, ensure_ascii=False, indent=1)
        except Exception:
            pass
        for nazwa in PLIKI_SWIATA:
            p = os.path.join(KATALOG, nazwa)
            if os.path.exists(p):
                shutil.move(p, os.path.join(cel, nazwa))
        with open(os.path.join(cel, "SWIAT.txt"), "w") as f:
            f.write(f"świat {numer}\ncykli: {swiat.get('cykl_swiata')}\nbytów: {len(swiat.get('zmarli', [])) + len(swiat.get('zywi', []))}\n"
                    f"zarchiwizowany: {time.strftime('%Y-%m-%d %H:%M')}\n" + ("przerwany: proces życia nie działał, żywi zostali w archiwum\n" if przerwany else ""))
    with open(os.path.join(KATALOG, "zycie.log"), "a") as log:
        proc = subprocess.Popen([sys.executable, os.path.join(KATALOG, "zycie.py")],
                            cwd=KATALOG, stdout=log, stderr=subprocess.STDOUT,
                            env={**os.environ, "CYKL": str(cykl), "GENY": str(geny), "DWOJE": "1" if dwoje else "0", "WYMIARY": str(wymiary), "ISTOT": str(istot), "ROZMIAR": rozmiar, "POJEMNOSC_SWIATA": str(pojemnosc), "JEZYK": jezyk},
                            start_new_session=True)
    with open(ZYCIE_PID, "w") as f:
        f.write(str(proc.pid))
    time.sleep(2)
    return 200, {"nowy_swiat": True, "geny": geny, "dwoje": dwoje, "cykl": cykl, "wymiary": wymiary, "istot": istot, "poprzedni_w": cel if swiat is not None else None, "pid": proc.pid}


def przyjmij_slowa(tekst, do=None):
    """Zdanie to jeden sygnał w jednym cyklu: suma wektorów wyrazów. do: nr istoty albo None (do wszystkich)."""
    tekst = " ".join(str(tekst).split())[:240].lstrip("@")
    if not tekst:
        return []
    do = int(do) if (do is not None and str(do).isdigit() and int(do) >= 1) else None
    if do is not None:
        zywe = {b["nr"] for b in most.czytaj_json(most.CIALO, {"zywi": []}).get("zywi", [])}
        if do not in zywe:
            return None
    swiat = most.czytaj_json(most.CIALO, {"cykl_swiata": 0})
    with BLOKADA:
        znane = most.slowa_swiata()
        znane["l-" + uuid.uuid4().hex[:12]] = {
            "tekst": tekst, "status": "w_drodze", "od_cyklu": swiat["cykl_swiata"],
            "czas": time.time(), "odeslane": True, "do": do}
        with open(most.WEJSCIE, "a") as f:
            f.write((f"@{do} " if do is not None else "") + tekst + "\n")
        most.zapisz_json(most.SLOWA_SWIATA, znane)
    return [tekst]


class Bytek(BaseHTTPRequestHandler):
    def _json(self, kod, dane):
        ciało = json.dumps(dane, ensure_ascii=False).encode()
        try:
            self.send_response(kod)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(ciało)))
            self.end_headers()
            self.wfile.write(ciało)
        except (BrokenPipeError, ConnectionResetError):
            # przeglądarka rozłączyła się, zanim skończyliśmy pisać (odświeżenie strony, zamknięta karta).
            # To nie jest błąd świata: nie ma czego logować ani ratować.
            self.close_connection = True

    def handle_one_request(self):
        try:
            BaseHTTPRequestHandler.handle_one_request(self)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True

    def log_message(self, fmt, *args):
        pass                                    # cisza: log serwera ma zawierać błędy, nie każde żądanie

    def do_GET(self):
        sciezka = urlparse(self.path).path
        if sciezka == "/api/wersja":
            # do pracy nad stroną: kiedy ostatnio zmienił się jakiś plik strony
            baza = os.path.join(KATALOG, "strona")
            m = 0.0
            for katalog, _, pliki in os.walk(baza):
                for n in pliki:
                    m = max(m, os.path.getmtime(os.path.join(katalog, n)))
            return self._json(200, {"wersja": m})
        if sciezka == "/api/stan":
            return self._json(200, stan_dla_strony())
        if sciezka == "/api/istoty":
            # lekka lista wszystkich żywych: bez genów i bez dziennika, żeby dało się ją pokazać przy tysiącach istot
            q = parse_qs(urlparse(self.path).query)
            try:
                od = max(0, int(q.get("od", ["0"])[0]))
                ile = max(1, min(500, int(q.get("ile", ["100"])[0])))
            except ValueError:
                return self._json(400, {"blad": "zła strona"})
            sw = most.czytaj_json(most.CIALO, {"zywi": []})
            zywi = sorted(sw.get("zywi", []), key=lambda x: (-x["wiek"], x["nr"]))   # od najstarszej
            kawalek = [{"nr": x["nr"], "pokolenie": x["pokolenie"], "wiek": x["wiek"], "energia": round(x["energia"], 2),
                        "dzieci": x.get("dzieci", 0), "miejsce": str(x.get("miejsce", 0)), "plec": x.get("plec"),
                        "geny": x.get("geny"), "chora": bool(x.get("chora")), "mowa": x.get("mowa", {}),
                        "glod": round(max(0.0, min(1.0, 1 - x["energia"] / most.SYTOSC)), 2)}
                       for x in zywi[od:od + ile]]
            return self._json(200, {"istoty": kawalek, "od": od, "ile": len(kawalek), "wszystkich": len(zywi),
                                    "pojemnosc": most.POJEMNOSC, "cykl": sw.get("cykl_swiata")})
        if sciezka == "/api/istota":
            # szukanie po numerze: widok główny nie trzyma już wszystkich istot
            q = parse_qs(urlparse(self.path).query)
            try:
                nr_ = int(q["nr"][0])
            except (KeyError, ValueError, IndexError):
                return self._json(400, {"blad": "zły numer"})
            sw = most.czytaj_json(most.CIALO, {"zywi": [], "zmarli": []})
            zy = next((x for x in sw.get("zywi", []) if x["nr"] == nr_), None)
            if zy is not None:
                return self._json(200, {"nr": zy["nr"], "zyje": True, "czym": "szukana", "pokolenie": zy["pokolenie"], "wiek": zy["wiek"],
                                        "energia": round(zy["energia"], 2), "dzieci": zy["dzieci"], "miejsce": str(zy.get("miejsce", 0)),
                                        "mowa": zy.get("mowa", {}), "rodzic": zy.get("rodzic"), "rodzic2": zy.get("rodzic2"),
                                        "geny": zy.get("geny"), "glod": round(max(0.0, min(1.0, 1 - zy["energia"] / most.SYTOSC)), 2),
                                        "sila": zy.get("sila"), "pojetnosc": zy.get("pojetnosc"), "towarzyskosc": zy.get("towarzyskosc"),
                                        "plec": zy.get("plec"), "tryb": "jawa"})
            zm = next((x for x in sw.get("zmarli", []) if x.get("nr") == nr_), None)
            if zm is not None:
                return self._json(200, {"nr": nr_, "zyje": False, "pokolenie": zm.get("pokolenie"), "wiek": zm.get("wiek"),
                                        "dzieci": zm.get("dzieci"), "zmarl_w_cyklu": zm.get("zmarl_w_cyklu")})
            return self._json(404, {"blad": "nie ma takiej istoty"})
        if sciezka == "/api/wnetrze":
            q = parse_qs(urlparse(self.path).query)
            try:
                nr_ = int(q["nr"][0]) if q.get("nr") else None
                limit_ = int(q["limit"][0]) if q.get("limit") else None
            except ValueError:
                return self._json(400, {"blad": "zły numer"})
            return self._json(200, wnetrze(nr=nr_, lekko=bool(q.get("lekko")), limit=limit_))
        if sciezka == "/api/rod":
            return self._json(200, rod())
        if sciezka == "/api/genom":
            return self._json(200, genom_swiata())
        if sciezka == "/api/zdarzenia":
            q = parse_qs(urlparse(self.path).query)
            try:
                od = float(q.get("od", ["0"])[0])
            except ValueError:
                od = 0.0
            p = os.path.join(DANE, "zdarzenia.jsonl")
            zd = []
            if os.path.exists(p):
                with open(p) as f:
                    # okno szerokie: przy dwóch tysiącach istot na jeden cykl przypada ~70 zdarzeń,
                    # a „znaczenie” (jedyne, z którego robi się powiadomienie) jest rzadkie i łatwo je wypchnąć
                    for l in f.readlines()[-3000:]:
                        try:
                            x = json.loads(l)
                        except json.JSONDecodeError:
                            continue
                        if x.get("czas", 0) > od:
                            zd.append(x)
            # „znaczenie” jest rzadkie, a reszty jest ~70 na cykl: obcięcie do ostatnich 30 wypychało właśnie to,
            # z czego robi się powiadomienie. Więc najpierw odkładamy wszystkie znaczenia, potem dobieramy resztę.
            wazne = [x for x in zd if x.get("typ") == "znaczenie"]
            reszta = [x for x in zd if x.get("typ") != "znaczenie"]
            wynik = sorted(wazne[-20:] + reszta[-120:], key=lambda x: x.get("czas", 0))   # szersze okno: strona sama wybiera, co pokazuje
            return self._json(200, {"zdarzenia": wynik, "teraz": time.time()})
        if sciezka == "/api/dzieje":
            return self._json(200, dzieje())
        if sciezka == "/api/cywilizacja":
            return self._json(200, cywilizacja())
        if sciezka == "/api/portret":
            return self._json(200, portret())
        if sciezka == "/api/slownik":
            return self._json(200, slownik())
        if sciezka == "/api/kronika":
            p = os.path.join(DANE, "zdarzenia.jsonl")
            zd = []
            if os.path.exists(p):
                with open(p) as f:
                    for l in f.readlines()[-500:]:
                        try:
                            zd.append(json.loads(l))
                        except json.JSONDecodeError:
                            pass
            return self._json(200, {"zdarzenia": zd[::-1]})
        if sciezka == "/api/jezyk":
            return self._json(200, jezyk())
        if sciezka.startswith("/s/"):
            # pliki wspólne: css, js, słowniki
            baza = os.path.realpath(os.path.join(KATALOG, "strona"))
            nazwa = unquote(sciezka[3:])
            plik = os.path.realpath(os.path.join(baza, nazwa))
            if (not plik.startswith(baza + os.sep) or not os.path.isfile(plik)
                    or any(cz.startswith((".", "_")) for cz in nazwa.split("/"))):
                return self._json(404, {"blad": "nie ma"})
            typ = {"css": "text/css", "js": "application/javascript", "json": "application/json"}.get(plik.rsplit(".", 1)[-1], "application/octet-stream")
            with open(plik, "rb") as f:
                ciało = f.read()
            self.send_response(200)
            self.send_header("Content-Type", typ + "; charset=utf-8")
            self.send_header("Content-Length", str(len(ciało)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return self.wfile.write(ciało)
        if sciezka in ("/", "/index.html", "/wnetrze", "/rod", "/jezyk", "/dzieje"):
            plik = {"/wnetrze": WNETRZE, "/rod": ROD, "/jezyk": JEZYK, "/dzieje": DZIEJE}.get(sciezka, STRONA)
            with open(plik, "rb") as f:
                ciało = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(ciało)))
            self.send_header("Cache-Control", "no-store")        # inaczej przeglądarka trzyma starą stronę mimo zmian
            self.end_headers()
            return self.wfile.write(ciało)
        self._json(404, {"blad": "nie ma"})

    def _dane(self):
        """Ciało POST jako słownik; złe wejście = pusty słownik. Zwraca None przy zbyt dużym ciele."""
        try:
            n = int(self.headers.get("Content-Length", 0))
        except ValueError:
            n = 0
        if n < 0 or n > 65536:
            return None
        try:
            dane = json.loads(self.rfile.read(n) or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            dane = {}
        return dane if isinstance(dane, dict) else {}

    def do_POST(self):
        sciezka = urlparse(self.path).path
        if ARCHIWUM:
            return self._json(403, {"blad": f"świat {ARCHIWUM} jest w archiwum: można go oglądać, nie można w nim nic zmienić"})
        dane = self._dane()
        if dane is None:
            return self._json(413, {"blad": "za dużo"})
        if sciezka == "/api/nowy_swiat":
            try:
                with BLOKADA:
                    kod, odp = nowy_swiat(dane.get("geny"), bool(dane.get("dwoje")), dane.get("cykl"), dane.get("wymiary"), dane.get("istot"), dane.get("rozmiar"), dane.get("pojemnosc"), dane.get("jezyk"))
            except (TypeError, ValueError):
                return self._json(400, {"blad": "złe parametry"})
            return self._json(kod, odp)
        if sciezka == "/api/zatrzymaj":
            # zatrzymanie świata: proces życia dostaje sygnał i kończy po bieżącym cyklu.
            # Ciało jest zapisywane na końcu każdego cyklu, więc traci się najwyżej jeden.
            if not proces_zyje():
                return self._json(409, {"blad": "proces życia i tak nie działa"})
            try:
                with open(ZYCIE_PID) as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
            except (OSError, ValueError) as e:
                return self._json(500, {"blad": f"nie udało się zatrzymać: {e}"})
            _PROCES_CACHE["czas"] = 0.0
            time.sleep(1.5)
            swiat = most.czytaj_json(most.CIALO, {}) or {}
            return self._json(200, {"zatrzymany": True, "cykl": swiat.get("cykl_swiata"), "zywych": len(swiat.get("zywi", []))})
        if sciezka == "/api/wznow":
            with BLOKADA:
                kod, odp = wznow_zycie()
            return self._json(kod, odp)
        # słowa i pokarm tylko do żywego świata z działającym procesem: inaczej trafiłyby do następnego świata
        if sciezka in ("/api/nakarm", "/api/slowo"):
            sw = most.czytaj_json(most.CIALO, None)
            if sw is None or not sw.get("zywi") or sw.get("wygasla"):
                return self._json(409, {"blad": "w tym świecie nikt nie żyje"})
            if not proces_zyje():
                return self._json(409, {"blad": "proces życia nie działa"})
        if sciezka == "/api/nakarm":
            do = dane.get("do")
            if do is not None and do != "wszystkie":
                zywe = {b["nr"] for b in most.czytaj_json(most.CIALO, {"zywi": []}).get("zywi", [])}
                if not (str(do).isdigit() and int(do) in zywe):
                    return self._json(404, {"blad": "nie ma takiej istoty"})
            with open(os.path.join(KATALOG, "karma.txt"), "a") as f:
                f.write(("@wszystkie" if do == "wszystkie" else f"@{int(do)}" if do is not None else str(time.time())) + "\n")
            return self._json(200, {"karma": "w najbliższym cyklu", "do": do})
        if sciezka != "/api/slowo":
            return self._json(404, {"blad": "nie ma"})
        if not isinstance(dane.get("slowo", ""), str):
            return self._json(400, {"blad": "to nie jest słowo"})
        slowa = przyjmij_slowa(dane.get("slowo", ""), dane.get("do"))
        if slowa is None:
            return self._json(404, {"blad": "nie ma takiej istoty"})
        if not slowa:
            return self._json(400, {"blad": "puste"})
        self._json(200, {"slowa": slowa, "status": "w_drodze"})

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    if ARCHIWUM:
        print(f"podgląd świata z archiwum: swiaty/{ARCHIWUM} (tylko do oglądania)", flush=True)
    print(f"bytek słucha na http://0.0.0.0:{PORT}  (na tym Macu: http://localhost:{PORT})", flush=True)
    class Cichy(ThreadingHTTPServer):
        def handle_error(self, request, client_address):
            t, v = sys.exc_info()[:2]
            if t in (BrokenPipeError, ConnectionResetError):
                return                        # klient się rozłączył: nic się nie stało
            ThreadingHTTPServer.handle_error(self, request, client_address)

    class Serwer6(Cichy):
        address_family = socket.AF_INET6      # "::" słucha też po IPv4 (localhost bywa najpierw ::1)
    try:
        Serwer6(("::", PORT), Bytek).serve_forever()
    except OSError:
        Cichy(("0.0.0.0", PORT), Bytek).serve_forever()
