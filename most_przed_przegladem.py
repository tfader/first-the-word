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

SYTOSC, POJEMNOSC = 10.0, 30.0


def czytaj_dziennik():
    if not os.path.exists(DZIENNIK):
        return []
    with open(DZIENNIK) as f:
        return [json.loads(l) for l in f if l.strip()]


def czytaj_json(p, domyslne):
    if not os.path.exists(p):
        return domyslne
    with open(p) as f:
        return json.load(f)


def slowa_swiata():
    return czytaj_json(SLOWA_SWIATA, {})


def zapisz_json(p, dane):
    with open(p, "w") as f:
        json.dump(dane, f, ensure_ascii=False, indent=1)


def uaktualnij_losy(slowa, dziennik):
    """Słowo, które już przeszło przez cykl, dostaje los: spal / uslyszal / nie_rozpoznal."""
    for wpis in dziennik:
        tekst = (wpis.get("slowo") or {}).get("tekst")
        if not tekst:
            continue
        for sid, s in slowa.items():
            if s["status"] in ("czeka", "w_drodze") and s["tekst"] == tekst and wpis["cykl_swiata"] > s["od_cyklu"]:
                if wpis["tryb"] == "sen":
                    s["status"] = "spal"
                elif wpis["slowo"]["geny"]:
                    s["status"] = "uslyszal"
                else:
                    s["status"] = "nie_rozpoznal"
                s["cykl"] = wpis["cykl_swiata"]
                break
    return slowa


def stan():
    swiat = czytaj_json(CIALO, None)
    if swiat is None:
        print("brak ciała", file=sys.stderr)
        sys.exit(1)
    dziennik = czytaj_dziennik()
    slowa = uaktualnij_losy(slowa_swiata(), dziennik)
    zapisz_json(SLOWA_SWIATA, slowa)
    keja = [json.loads(l) for l in open(SLOWA_KEJA)] if os.path.exists(SLOWA_KEJA) else []
    # pierwszy żywy byt (najstarszy) jako "bytek"; jeśli linia wygasła, ostatni zmarły
    zywi = swiat["zywi"]
    if zywi:
        b = min(zywi, key=lambda x: x["nr"])
        ostatni = [w for w in dziennik if w["byt"] == b["nr"]]
    else:
        b = None
        ostatni = dziennik
    ost = ostatni[-1] if ostatni else {}
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
            "wolanie": (w.get("mowa") or {}).get("wolanie", False), "czyn": (w.get("inny") or {}).get("czyn"),
            "miejsce": str(w.get("miejsce")), "ruszyl": w.get("ruszyl", False), "karmione": w.get("karmione", 0),
        })
    doc = {
        "zyje": bool(zywi), "wiek": (b or {}).get("wiek", ost.get("wiek")),
        "energia": (b or {}).get("energia", 0.0), "sytosc": SYTOSC, "pojemnosc": POJEMNOSC,
        "glod": ost.get("glod", 0.0), "tryb": ost.get("tryb", "jawa"),
        "pokolenie": (b or {}).get("pokolenie", 1), "dzieci": (b or {}).get("dzieci", 0),
        "zywych": len(zywi), "zmarlych": len(swiat.get("zmarli", [])), "cykl_swiata": swiat["cykl_swiata"], "czas": ost.get("czas"),
        "narodziny": swiat["narodziny"],
        "narodziny_tekst": time.strftime("%-d %B %Y, %H:%M", time.localtime(swiat["narodziny"]))
            .replace("September", "września"),
        "most_czas": time.time(),
        "mowa": (b or {}).get("mowa", {"krzyk": False, "slowo": None}),
        "miejsce": str((b or {}).get("miejsce", "0")), "wytrwalosc": (b or {}).get("wytrwalosc"),
        "geny": (b or {}).get("geny") or len((b or {}).get("kregoslup", [])) or (swiat["zmarli"][-1].get("geny") if swiat["zmarli"] else None),
        "dwoje": swiat.get("dwoje", False), "cykl_sekund": swiat.get("cykl_sekund", 60), "wymiary": swiat.get("wymiary", 4),
        "pole": [round(x, 2) for x in swiat.get("pole", [])],
        "kolejnosc": swiat.get("kolejnosc", [str(i) for i in range(len(swiat.get("pole", [])))]),
        "znanych_miejsc": len(swiat.get("miejsca", {})) or len(swiat.get("pole", [])),
        "miejsca": {str(x["nr"]): str(x.get("miejsce", 0)) for x in zywi},
        "slownik": sorted((b or {}).get("slownik", {}).keys()),
        "byty": [{"nr": x["nr"], "pokolenie": x["pokolenie"], "wiek": x["wiek"],
                  "energia": round(x["energia"], 2), "dzieci": x["dzieci"],
                  "miejsce": str(x.get("miejsce", 0)), "mowa": x.get("mowa", {}),
                  "rodzic": x.get("rodzic"), "rodzic2": x.get("rodzic2"), "geny": x.get("geny") or len(x.get("kregoslup", [])),
                  "glod": round(max(0.0, min(1.0, 1 - x["energia"] / SYTOSC)), 2),
                  "tryb": next((w["tryb"] for w in reversed(dziennik) if w["byt"] == x["nr"]), "jawa")}
                 for x in sorted(zywi, key=lambda x: x["nr"])],
        "slowo_keja": keja[-1]["slowo"] if keja else None,
        "slowa_keja": keja[-30:], "cykle": cykle,
    }
    zapisz_json(STAN, doc)
    print(f"stan: cykl {doc['cykl_swiata']}, {'żyje' if doc['zyje'] else 'umarł'}, E={doc['energia']:.2f}, tryb {doc['tryb']}, słowo Keja: {doc['slowo_keja']!r}")
    zmiany = {sid: s for sid, s in slowa.items() if s.get("status") not in ("czeka",) and not s.get("odeslane")}
    zapisz_json(SLOWA_UPDATE, zmiany)
    print(f"do odesłania na stronę: {len(zmiany)} słów")


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
