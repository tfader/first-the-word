"""Word: most między ciałem bytka (Mac) a stroną (claude.ai). Obsługuje go Kej.

  python3 most.py stan                 -> pisze stan.json (dokument stan/byt dla strony)
  python3 most.py slowa <katalog_db>   -> bierze słowa "czeka" z plików db, wpisuje do kolejki,
                                          pisze slowa_update.json (statusy do odesłania na stronę)
  python3 most.py kej <cykl> <słowo>   -> dopisuje słowo Keja do slowa_keja.jsonl
"""
import glob
import json
import os
import sys
import time

KATALOG = os.path.dirname(os.path.abspath(__file__))
CIALO = os.path.join(KATALOG, "swiat.json")
DZIENNIK = os.path.join(KATALOG, "dziennik.jsonl")
WEJSCIE = os.path.join(KATALOG, "wejscie.txt")
SLOWA_KEJA = os.path.join(KATALOG, "slowa_keja.jsonl")
SLOWA_SWIATA = os.path.join(KATALOG, "slowa_swiata.json")   # id -> {tekst, status, od_cyklu}
STAN = os.path.join(KATALOG, "stan.json")
SLOWA_UPDATE = os.path.join(KATALOG, "slowa_update.json")


def ustaw_katalog(k):
    """Przestawia wszystkie ścieżki na inny katalog świata (podgląd świata z archiwum)."""
    global KATALOG, CIALO, DZIENNIK, WEJSCIE, SLOWA_KEJA, SLOWA_SWIATA, STAN, SLOWA_UPDATE
    KATALOG = k
    CIALO = os.path.join(k, "swiat.json")
    DZIENNIK = os.path.join(k, "dziennik.jsonl")
    WEJSCIE = os.path.join(k, "wejscie.txt")
    SLOWA_KEJA = os.path.join(k, "slowa_keja.jsonl")
    SLOWA_SWIATA = os.path.join(k, "slowa_swiata.json")
    STAN = os.path.join(k, "stan.json")
    SLOWA_UPDATE = os.path.join(k, "slowa_update.json")

SYTOSC, POJEMNOSC = 10.0, 30.0


import threading
_DZ = {"rozmiar": 0, "inode": None, "wpisy": [], "ogon": ""}
_DZ_LOCK = threading.Lock()
OKNO_CYKLI = 40              # tyle ostatnich cykli dziennika trzymamy w pamięci (przy 1000 istot pełny dziennik to gigabajty)
OGON_PLIKU = 40 * 1024 * 1024   # przy pierwszym czytaniu dużego pliku bierzemy tylko tyle bajtów z końca


def czytaj_dziennik():
    """Dziennik rośnie tylko na końcu, więc czyta się go przyrostowo: pamięć + nowe linie od ostatniego rozmiaru.
    Nowy świat (inny plik, mniejszy rozmiar) czyści pamięć. Brak pliku: pusta lista."""
    with _DZ_LOCK:
        try:
            st = os.stat(DZIENNIK)
        except FileNotFoundError:
            _DZ.update(rozmiar=0, inode=None, wpisy=[], ogon="")
            return []
        if st.st_ino != _DZ["inode"] or st.st_size < _DZ["rozmiar"]:
            _DZ.update(rozmiar=0, inode=st.st_ino, wpisy=[], ogon="")
        if st.st_size > _DZ["rozmiar"]:
            try:
                with open(DZIENNIK, "rb") as f:
                    start = _DZ["rozmiar"]
                    if start == 0 and st.st_size > OGON_PLIKU:
                        start = st.st_size - OGON_PLIKU          # duży plik: tylko ogon; pierwsza (ucięta) linia odpadnie
                        f.seek(start)
                        f.readline()
                        start = f.tell()
                    f.seek(start)
                    dane = f.read()
            except FileNotFoundError:
                return list(_DZ["wpisy"])
            tekst = _DZ["ogon"] + dane.decode("utf-8", "replace")
            linie = tekst.split("\n")
            _DZ["ogon"] = linie.pop()                        # niedokończona linia czeka na resztę
            for l in linie:
                if l.strip():
                    try:
                        _DZ["wpisy"].append(json.loads(l))
                    except ValueError:
                        pass
            _DZ["rozmiar"] = st.st_size
            if _DZ["wpisy"]:
                prog = _DZ["wpisy"][-1]["cykl_swiata"] - OKNO_CYKLI
                if _DZ["wpisy"][0]["cykl_swiata"] < prog:
                    _DZ["wpisy"] = [w for w in _DZ["wpisy"] if w["cykl_swiata"] >= prog]
        return list(_DZ["wpisy"])


def czytaj_jsonl(p):
    """Plik z jednym JSON-em na linię; puste i zepsute linie pomijane."""
    if not os.path.exists(p):
        return []
    out = []
    with open(p) as f:
        for l in f:
            if l.strip():
                try:
                    out.append(json.loads(l))
                except ValueError:
                    pass
    return out


MIESIACE = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca", "sierpnia", "września", "października", "listopada", "grudnia"]


def czytaj_json(p, domyslne):
    if not os.path.exists(p):
        return domyslne
    try:
        with open(p) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return domyslne


def slowa_swiata():
    return czytaj_json(SLOWA_SWIATA, {})


def zapisz_json(p, dane):
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(dane, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def uaktualnij_losy(slowa, dziennik):
    """Słowo, które już przeszło przez cykl, dostaje los: spal / uslyszal / nie_rozpoznal.
    Słowo adresowane: liczy się wpis adresata. Do wszystkich: usłyszane, gdy ktokolwiek usłyszał,
    przespane, gdy wszyscy spali, inaczej nierozpoznane. Wpisy z jednego cyklu liczone razem."""
    wg_cyklu = {}
    for wpis in dziennik:
        tekst = (wpis.get("slowo") or {}).get("tekst")
        if tekst:
            wg_cyklu.setdefault((tekst, wpis["cykl_swiata"]), []).append(wpis)
    for (tekst, cykl), wpisy in sorted(wg_cyklu.items(), key=lambda kv: kv[0][1]):
        for sid, s in sorted(slowa.items(), key=lambda kv: kv[1].get("od_cyklu", 0)):
            if s["status"] not in ("czeka", "w_drodze") or s["tekst"] != tekst or cykl <= s["od_cyklu"]:
                continue
            do = s.get("do")
            w = [x for x in wpisy if do is None or x["byt"] == do]
            if not w:
                continue
            if any(x["tryb"] == "jawa" and x["slowo"]["geny"] for x in w):
                s["status"] = "uslyszal"
            elif all(x["tryb"] != "jawa" for x in w):
                s["status"] = "spal"
            else:
                s["status"] = "nie_rozpoznal"
            s["cykl"] = cykl
            break
    return slowa


WYROZNIENIA = [("najstarsza", lambda x: x["wiek"]),                 # klucze, nie napisy: nazwę dobiera strona w swoim języku
               ("najplodniejsza", lambda x: x.get("dzieci", 0)),
               ("najgadatliwsza", lambda x: x.get("rozmowy", 0)),
               ("najpojetniejsza", lambda x: x.get("pojetnosc", 0) or 0),
               ("najglodniejsza", lambda x: -x["energia"]),
               ("najmlodsza", lambda x: -x["wiek"])]


def wyroznione(zywi):
    """Kilka istot, na które warto spojrzeć. Przy dwóch tysiącach lista wszystkich nic nie mówi."""
    wziete, out = set(), []
    for nazwa, klucz in WYROZNIENIA:
        kand = [x for x in zywi if x["nr"] not in wziete]
        if not kand:
            break
        b = max(kand, key=klucz)
        wziete.add(b["nr"])
        out.append((nazwa, b))
    return out


def populacja(zywi):
    """Puls świata zamiast listy istot."""
    if not zywi:
        return {"zywych": 0}
    miejsca = {}
    for x in zywi:
        m = str(x.get("miejsce", 0))
        miejsca[m] = miejsca.get(m, 0) + 1
    najl = max(miejsca.items(), key=lambda kv: kv[1])
    geny = [x.get("geny") or 0 for x in zywi]
    baza = [x.get("genow_bazowych") or 0 for x in zywi]
    chorych = sum(1 for x in zywi if x.get("chora"))
    return {"zywych": len(zywi), "chorych": chorych,
            "odpornosc": round(sum((x.get("odpornosc") or 0) for x in zywi) / len(zywi), 2),
            "ozdoba": round(sum((x.get("ozdoba") or 0) for x in zywi) / len(zywi), 3),
            "gust": round(sum((x.get("gust") or 0) for x in zywi) / len(zywi), 3),
            "wiek_sredni": round(sum(x["wiek"] for x in zywi) / len(zywi), 1),
            "wiek_max": max(x["wiek"] for x in zywi),
            "pokolenia": [min(x["pokolenie"] for x in zywi), max(x["pokolenie"] for x in zywi)],
            "miejsc_zajetych": len(miejsca), "najludniejsze": {"miejsce": najl[0], "ilu": najl[1]},
            "genow_srednio": round(sum(geny) / len(geny), 1), "genow_max": max(geny),
            "z_duplikacji": sum(1 for g, b in zip(geny, baza) if b and g > b),
            "dzieci_lacznie": sum(x.get("dzieci", 0) for x in zywi)}


def stan():
    swiat = czytaj_json(CIALO, None)
    if swiat is None:
        doc = {"zyje": False, "brak_ciala": True, "zywych": 0, "zmarlych": 0, "byty": [], "cykle": [], "pole": [],
               "cykl_swiata": 0, "slowa_keja": [], "slowo_keja": None, "most_czas": time.time()}
        zapisz_json(STAN, doc)
        return doc
    dziennik = czytaj_dziennik()
    slowa = uaktualnij_losy(slowa_swiata(), dziennik)
    zapisz_json(SLOWA_SWIATA, slowa)
    keja = czytaj_jsonl(SLOWA_KEJA)
    # pierwszy żywy byt (najstarszy) jako "bytek"; jeśli linia wygasła, ostatni zmarły
    zywi = swiat["zywi"]
    ostatni_wpis = {}
    for w in dziennik:
        ostatni_wpis[w["byt"]] = w                        # raz, nie dla każdej istoty osobno (1000 istot × dziennik = minuty)
    if zywi:
        b = min(zywi, key=lambda x: x["nr"])
        ost = ostatni_wpis.get(b["nr"], {})
        ostatni = [w for w in dziennik if w["byt"] == b["nr"]]   # cykle najstarszej: do wykresu
    else:
        b = None
        ost = dziennik[-1] if dziennik else {}
        ostatni = dziennik
    cykle = []
    for w in ostatni[-40:]:
        cykle.append({
            "cykl": w["cykl_swiata"], "tryb": w["tryb"], "energia": w["energia"],
            "zjedzone": w.get("zjedzone", 0), "rana": bool(w["rana"]["geny"]),
            "echo": bool(w["echo"]["geny"]), "slowo": (w.get("slowo") or {}).get("tekst"),
            "uslyszal": bool((w.get("slowo") or {}).get("geny")), "dziecko": w.get("dziecko"),
            "inny": (w.get("inny") or {}).get("od"), "inny_geny": bool((w.get("inny") or {}).get("geny")),
            "krzyk": (w.get("mowa") or {}).get("krzyk", False), "mowi": (w.get("mowa") or {}).get("slowo"),
            "znaki": (w.get("mowa") or {}).get("znaki"), "inny_glos": bool((w.get("inny") or {}).get("glos")),
            "odpowiedz": (w.get("mowa") or {}).get("odpowiedz"), "alarm": (w.get("mowa") or {}).get("alarm", False), "rozmowa": w.get("rozmowa"),
            "wolanie": (w.get("mowa") or {}).get("wolanie", False), "czyn": (w.get("inny") or {}).get("czyn"),
            "miejsce": str(w.get("miejsce")), "ruszyl": w.get("ruszyl", False), "karmione": w.get("karmione", 0),
        })
    doc = {
        "zyje": bool(zywi), "wiek": (b or {}).get("wiek", ost.get("wiek")),
        "energia": (b or {}).get("energia", 0.0), "sytosc": SYTOSC, "pojemnosc": POJEMNOSC,
        "glod": ost.get("glod", 0.0), "tryb": ost.get("tryb", "jawa"),
        "pokolenie": (b or {}).get("pokolenie", 1), "dzieci": (b or {}).get("dzieci", 0),
        "zywych": len(zywi), "zmarlych": len(swiat.get("zmarli", [])), "cykl_swiata": swiat["cykl_swiata"], "czas": ost.get("czas"),
        "narodziny": swiat["narodziny"], "koniec": swiat.get("koniec"),
        "narodziny_tekst": (lambda lt: f"{lt.tm_mday} {MIESIACE[lt.tm_mon - 1]} {lt.tm_year}, {lt.tm_hour:02d}:{lt.tm_min:02d}")(time.localtime(swiat["narodziny"])),
        "most_czas": time.time(),
        "mowa": (b or {}).get("mowa", {"krzyk": False, "slowo": None}),
        "miejsce": str((b or {}).get("miejsce", "0")), "wytrwalosc": (b or {}).get("wytrwalosc"),
        "geny": (b or {}).get("geny") or len((b or {}).get("kregoslup", [])) or (swiat["zmarli"][-1].get("geny") if swiat["zmarli"] else None),
        "dwoje": swiat.get("dwoje", False), "cykl_sekund": swiat.get("cykl_sekund", 60), "wymiary": swiat.get("wymiary", 4),
        "pole": [round(x, 2) for x in swiat.get("pole", [])],
        "kolejnosc": swiat.get("kolejnosc", [str(i) for i in range(len(swiat.get("pole", [])))]),
        "znanych_miejsc": len(swiat.get("miejsca", {})) or len(swiat.get("pole", [])),
        "pora": swiat.get("pora"), "noc": swiat.get("noc"),
        "miejsca": {str(x["nr"]): str(x.get("miejsce", 0)) for x in zywi},
        "slownik": sorted((b or {}).get("slownik", {}).keys()),
        "populacja": dict(populacja(zywi),
                          znaczen=sum(1 for k in ((swiat.get("slownik") or {}).get("znaczenia") or {}) if ", bo " in k),
                          slow=len(((swiat.get("slownik") or {}).get("slowa") or {})),
                          gatunkow=swiat.get("gatunkow"), drapiezniki=len(swiat.get("drapiezniki") or {}),
                          ogniska=len(swiat.get("ogniska") or {})),
        "byty": [{"czym": czym, "nr": x["nr"], "pokolenie": x["pokolenie"], "wiek": x["wiek"],
                  "energia": round(x["energia"], 2), "dzieci": x["dzieci"],
                  "miejsce": str(x.get("miejsce", 0)), "mowa": x.get("mowa", {}),
                  "rodzic": x.get("rodzic"), "rodzic2": x.get("rodzic2"), "geny": x.get("geny") or len(x.get("kregoslup", [])),
                  "glod": round(max(0.0, min(1.0, 1 - x["energia"] / SYTOSC)), 2),
                  "lownosc": x.get("lownosc", (ostatni_wpis.get(x["nr"]) or {}).get("lownosc")),
                  "chora": bool(x.get("chora")), "odpornosc": x.get("odpornosc"),
                  "sila": x.get("sila"), "ciekawosc": x.get("ciekawosc"), "plec": x.get("plec"), "stadnosc": x.get("stadnosc"), "dlugowiecznosc": x.get("dlugowiecznosc"), "optimum": x.get("optimum"), "tolerancja": x.get("tolerancja"), "ufnosc": x.get("ufnosc"), "szczerosc": x.get("szczerosc"), "pojetnosc": x.get("pojetnosc"), "towarzyskosc": x.get("towarzyskosc"),
                  "tryb": (ostatni_wpis.get(x["nr"]) or {}).get("tryb", "jawa")}
                 for czym, x in wyroznione(zywi)],
        "slowo_keja": keja[-1]["slowo"] if keja else None,
        "slowa_keja": keja[-30:], "cykle": cykle,
    }
    zapisz_json(STAN, doc)
    zmiany = {sid: s for sid, s in slowa.items() if s.get("status") not in ("czeka",) and not s.get("odeslane")}
    zapisz_json(SLOWA_UPDATE, zmiany)
    if __name__ == "__main__":
        print(f"stan: cykl {doc['cykl_swiata']}, {'żyje' if doc['zyje'] else 'umarł'}, E={doc['energia']:.2f}, tryb {doc['tryb']}, słowo Keja: {doc['slowo_keja']!r}")
        print(f"do odesłania na stronę: {len(zmiany)} słów")
    return doc


def slowa(katalog_db):
    """Pliki <katalog_db>/slowa/<id>.json z read_db. Nowe 'czeka' idą do kolejki."""
    znane = slowa_swiata()
    swiat = czytaj_json(CIALO, {"cykl_swiata": 0})
    nowe = []
    for p in sorted(glob.glob(os.path.join(katalog_db, "slowa", "*.json"))):
        sid = os.path.splitext(os.path.basename(p))[0]
        d = czytaj_json(p, {})
        dane = d.get("data", d)
        if sid in znane or dane.get("status") != "czeka":
            continue
        tekst = " ".join(str(dane.get("tekst", "")).split())[:240]
        if not tekst:
            continue
        znane[sid] = {"tekst": tekst, "status": "w_drodze", "od_cyklu": swiat["cykl_swiata"], "czas": dane.get("czas")}
        nowe.append((sid, tekst))
    if nowe:
        with open(WEJSCIE, "a") as f:
            for _, t in nowe:
                f.write(t + "\n")
    zapisz_json(SLOWA_SWIATA, znane)
    zapisz_json(SLOWA_UPDATE, {sid: znane[sid] for sid, _ in nowe})
    print(f"do kolejki: {[t for _, t in nowe]}")


def kej(cykl, slowo):
    with open(SLOWA_KEJA, "a") as f:
        f.write(json.dumps({"cykl": int(cykl), "slowo": slowo, "czas": time.time()}, ensure_ascii=False) + "\n")
    print(f"Kej ({cykl}): {slowo}")


def odeslane(ids):
    z = slowa_swiata()
    for i in ids:
        if i in z:
            z[i]["odeslane"] = True
    zapisz_json(SLOWA_SWIATA, z)


if __name__ == "__main__":
    co = sys.argv[1] if len(sys.argv) > 1 else "stan"
    if co == "stan":
        stan()
    elif co == "slowa":
        slowa(sys.argv[2])
    elif co == "kej":
        kej(sys.argv[2], " ".join(sys.argv[3:]))
    elif co == "odeslane":
        odeslane(sys.argv[2:])
