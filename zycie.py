"""Word: życie. Jeden świat w czasie rzeczywistym. Uruchom: python3 zycie.py"""
import json
import os
import random
import sys
import time

import math

import numpy as np

import tlumacz
import word
from word import Byt, ROZMIAR

KATALOG = os.path.dirname(os.path.abspath(__file__))
CIALO = os.path.join(KATALOG, "swiat.json")
GENY_DIR = os.path.join(KATALOG, "cialo")            # geny istot: cialo/<nr>.npz (rdzeń K, powłoka P)
WEJSCIE = os.path.join(KATALOG, "wejscie.txt")
DZIENNIK = os.path.join(KATALOG, "dziennik.jsonl")
CUD = os.path.join(KATALOG, "cud.txt")          # obecność pliku = prośba o nowy cud
KARMA = os.path.join(KATALOG, "karma.txt")      # świat odpowiada na wołanie: dokłada pokarm
ZDARZENIA = os.path.join(KATALOG, "zdarzenia.jsonl")   # narodziny, śmierci, pokarm ze świata, zrozumienia
KORPUS = os.path.join(KATALOG, "korpus.jsonl")         # każde słowo z kontekstem i każda widoczna reakcja: do odczytania języka kiedyś, z zewnątrz
CYKL_SEKUND = float(os.environ.get("CYKL", 60))
GENY = int(os.environ.get("GENY", 64))
WYMIARY = int(os.environ.get("WYMIARY", 4))     # tylko przy tworzeniu świata; potem z ciała
DWOJE = True                                     # zawsze dwoje rodziców
ISTOT = max(2, min(64, int(os.environ.get("ISTOT", "2"))))   # ile istot z cudu na start (co najmniej dwie)
ROZMIAR = os.environ.get("ROZMIAR", "zwykly")    # ciasny / zwykly / rozlegly: miejsc na łąkę i szansa odkryć
JEZYK = os.environ.get("JEZYK", "pl")            # język nazw czynów w tym świecie (pl / en); tylko przy powołaniu
ROZMIARY = {"ciasny": (3, 0.1, 400), "zwykly": (5, 1 / 3, 100000), "rozlegly": (8, 0.5, 100000)}


def _zapisz_npy(p, tab):
    tmp = p + ".tmp.npy"
    np.save(tmp, tab)
    os.replace(tmp, p)


_K_ZAPISANE = set()          # numery istot, których rdzeń zapisano w tym biegu


def zapisz_geny(b):
    """Rdzeń K zapisany raz na bieg (nie zmienia się za życia), powłoka P co cykl.
    Raz na bieg, a nie „gdy brak pliku”: po nagłym zatrzymaniu licznik cofa się do ostatniego zapisu
    i numer może trafić do nowej istoty — wtedy stary plik rdzenia nie jest jej rdzeniem."""
    os.makedirs(GENY_DIR, exist_ok=True)
    pk = os.path.join(GENY_DIR, f"{b.nr}.K.npy")
    if b.nr not in _K_ZAPISANE or not os.path.exists(pk):
        _zapisz_npy(pk, b.K)
        _K_ZAPISANE.add(b.nr)
    _zapisz_npy(os.path.join(GENY_DIR, f"{b.nr}.P.npy"), b.P)


def wczytaj_geny(nr):
    """(K, P) istoty z cialo/; rozumie też starszy zapis <nr>.npz."""
    pk = os.path.join(GENY_DIR, f"{nr}.K.npy")
    if os.path.exists(pk):
        return np.load(pk), np.load(os.path.join(GENY_DIR, f"{nr}.P.npy"))
    pz = os.path.join(GENY_DIR, f"{nr}.npz")
    if not os.path.exists(pz):
        raise FileNotFoundError(f"brak genów istoty nr {nr} w {GENY_DIR}")
    with np.load(pz) as f:
        return f["K"], f["P"]


def byt_do_slownika(b):
    zapisz_geny(b)
    return {
        "nr": b.nr, "pokolenie": b.pokolenie, "geny": int(len(b.K)), "genow_bazowych": int(getattr(b, "genow_bazowych", len(b.K))), "glos_znaki": word.glos_na_znaki(b.glos),
        "otwarcia_genu": b.otwarcia_genu, "echo": b.echo, "energia": b.energia, "wiek": b.wiek,
        "slownik": b.slownik, "mowa": b.mowa, "zrodla": b.zrodla,
        "rodzic": b.rodzic, "rodzic2": b.rodzic2, "urodzony_w_cyklu": getattr(b, "urodzony_w_cyklu", None),
        "miejsce": str(b.miejsce), "poprzednie": b.poprzednie, "kierunek": b.kierunek, "wytrwalosc": b.wytrwalosc, "sila": b.sila, "ciekawosc": b.ciekawosc, "optimum": b.optimum, "tolerancja": b.tolerancja, "staz": b.staz, "nauczone": getattr(b, "nauczone", 0), "plec": b.plec, "stadnosc": b.stadnosc, "dlugowiecznosc": b.dlugowiecznosc, "rozmowy": getattr(b, "rozmowy", 0), "zle": b.zle,
        "ufnosc": b.ufnosc, "szczerosc": b.szczerosc, "deklarowal": b.deklarowal, "przechodzil": b.przechodzil, "klamcy": sorted(b.klamcy), "pojetnosc": b.pojetnosc, "towarzyskosc": b.towarzyskosc, "mapa": b.mapa, "uprawa": b.uprawa, "spichlerz": b.spichlerz, "bliscy": {str(k): v for k, v in b.bliscy.items()}, "unikaj": b.unikaj, "unikani": {str(k): v for k, v in b.unikani.items()}, "bolalo": list(b.bolalo) if b.bolalo else None,
        "przylapala": list(b.przylapala) if b.przylapala else None, "temat": list(b.temat) if b.temat else None, "wypowiedz": b.wypowiedz, "wyszlo": [list(x) for x in b.wyszlo],
        "spala": b.spala, "lownosc": getattr(b, "lownosc", 0.0), "pora": b.pora,
        "idzie": b.idzie, "krokow": b.krokow, "srednio": b.srednio,
        "dobre_miejsce": b.dobre_miejsce, "dobre_ile": b.dobre_ile, "zrozumiane": sorted(b.zrozumiane),
        "poprzednio_zjadl": b.poprzednio_zjadl, "ryt": b.ryt, "zimy": getattr(b, "zimy", 0), "spuscizna": getattr(b, "spuscizna", False), "u_kresu": getattr(b, "u_kresu", False), "wyryte": sorted(getattr(b, "wyryte", set())),
        "ozdoba": b.ozdoba, "gust": b.gust, "troska": b.troska, "odpornosc": b.odpornosc, "chora": list(b.chora) if b.chora else None, "przechorowane": sorted(b.przechorowane),
        "po_slowie": {k: {"n": v["n"], "v": [round(x, 4) for x in v["v"]], "b": round(v["b"], 3)} for k, v in b.po_slowie.items() if "n" in v}, "czeka_skutek": b.czeka_skutek,
        "sen": b.sen, "otwarcia": b.otwarcia, "najdluzsza": b.najdluzsza, "dzieci": b.dzieci,
    }


def byt_ze_slownika(d):
    if "kregoslup" in d:                          # stare ciało: geny w json
        b = Byt(d["kregoslup"], d["energia"], d["pokolenie"])
        b.powloka = d["powloka"]
    else:
        K, P = wczytaj_geny(d["nr"])
        b = Byt(K, d["energia"], d["pokolenie"])
        if P.shape != K.shape:                    # ratunek po awarii: powłoka dopasowana do rdzenia, nadmiar przepada
            Pn = np.zeros_like(K)
            m = min(len(K), len(P))
            Pn[:m] = P[:m]
            P = Pn
        b.P = P
    b.nr = d["nr"]; b.otwarcia_genu = list(d["otwarcia_genu"])[:len(b.K)] + [0] * max(0, len(b.K) - len(d["otwarcia_genu"]))
    b.echo = [tuple(e) for e in d["echo"]]; b.wiek = d["wiek"]; b.sen = d["sen"]
    b.otwarcia = d["otwarcia"]; b.najdluzsza = d["najdluzsza"]; b.dzieci = d["dzieci"]
    b.slownik = d.get("slownik", {}); b.mowa = d.get("mowa", {"krzyk": False, "slowo": None, "glos": False, "wolanie": False})
    b.mowa.setdefault("wolanie", False)
    b.zrodla = d.get("zrodla", {})
    b.rodzic = d.get("rodzic"); b.rodzic2 = d.get("rodzic2"); b.urodzony_w_cyklu = d.get("urodzony_w_cyklu")
    b.miejsce = str(d.get("miejsce", 0)); b.poprzednie = d.get("poprzednie"); b.kierunek = d.get("kierunek", 1)
    b.wytrwalosc = d.get("wytrwalosc", 2); b.sila = d.get("sila", b.sila); b.ciekawosc = d.get("ciekawosc", b.ciekawosc); b.optimum = d.get("optimum", b.optimum); b.tolerancja = d.get("tolerancja", b.tolerancja); b.staz = d.get("staz", 0); b.nauczone = d.get("nauczone", 0); b.plec = d.get("plec", b.plec); b.stadnosc = d.get("stadnosc", b.stadnosc); b.dlugowiecznosc = d.get("dlugowiecznosc", b.dlugowiecznosc); b.rozmowy = d.get("rozmowy", 0); b.zle = d.get("zle", 0)
    b.mapa = d.get("mapa", {}) or {}; b.pojetnosc = d.get("pojetnosc", b.pojetnosc); b.towarzyskosc = d.get("towarzyskosc", b.towarzyskosc); b.uprawa = float(d.get("uprawa", 0.0) or 0.0); b.spichlerz = float(d.get("spichlerz", 0.0) or 0.0); b.przechodzil = d.get("przechodzil", False); b.ryt = float(d.get("ryt", 0.0) or 0.0); b.zimy = int(d.get("zimy", 0) or 0); b.spuscizna = bool(d.get("spuscizna", False)); b.u_kresu = bool(d.get("u_kresu", False)); b.wyryte = set(d.get("wyryte", []) or [])
    b.przylapala = tuple(d["przylapala"]) if d.get("przylapala") else None; b.temat = tuple(d["temat"]) if d.get("temat") else None
    b.wypowiedz = d.get("wypowiedz"); b.wyszlo = d.get("wyszlo", []) or []; b.spala = d.get("spala", False); b.lownosc = d.get("lownosc", 0.0); b.pora = d.get("pora"); b.ufnosc = d.get("ufnosc", b.ufnosc); b.szczerosc = d.get("szczerosc", b.szczerosc); b.deklarowal = d.get("deklarowal", False); b.klamcy = set(d.get("klamcy", [])); b.bliscy = {int(k): v for k, v in (d.get("bliscy") or {}).items()}; b.unikaj = d.get("unikaj") or {}; b.unikani = {int(k): v for k, v in (d.get("unikani") or {}).items()}; b.bolalo = tuple(d["bolalo"]) if d.get("bolalo") else None
    b.idzie = d.get("idzie", False); b.krokow = d.get("krokow", 0); b.srednio = d.get("srednio", 2.0)
    b.dobre_miejsce = d.get("dobre_miejsce"); b.dobre_ile = d.get("dobre_ile", 0.0)
    b.zrozumiane = set(d.get("zrozumiane", []))
    b.poprzednio_zjadl = d.get("poprzednio_zjadl", 0.0)
    b.po_slowie = {k: v for k, v in (d.get("po_slowie") or {}).items() if isinstance(v, dict) and "n" in v}   # skutki z listy (stary zapis) przepadają: teraz skutek jest wektorem; b.czeka_skutek = d.get("czeka_skutek", []) or []
    b.ozdoba = d.get("ozdoba", b.ozdoba); b.gust = d.get("gust", b.gust)
    b.troska = d.get("troska", b.troska)
    b.odpornosc = d.get("odpornosc", b.odpornosc)
    b.chora = tuple(d["chora"]) if d.get("chora") else None
    b.przechorowane = set(d.get("przechorowane", []))
    b.genow_bazowych = int(d.get("genow_bazowych", len(b.K)))     # baza linii: ogon powyżej to duplikaty
    return b


def zapisz(swiat):
    tmp = CIALO + ".tmp"
    with open(tmp, "w") as f:
        json.dump(swiat, f)
    os.replace(tmp, CIALO)


def wczytaj():
    if not os.path.exists(CIALO):
        return None
    with open(CIALO) as f:
        return json.load(f)


def zdarzenie(swiat, typ, **dane):
    swiat.setdefault("_zdarzenia", []).append({"cykl": swiat["cykl_swiata"], "czas": time.time(), "typ": typ, **dane})


def kolejka_slow():
    """Pobiera jedno słowo z wejścia (pierwszy niepusty wiersz), resztę zostawia.
    Wiersz "@7 tekst" to słowo tylko do istoty nr 7. Zwraca (tekst, nr albo None)."""
    if not os.path.exists(WEJSCIE):
        return None
    czytam = WEJSCIE + ".czytam"
    try:
        os.rename(WEJSCIE, czytam)          # serwer dopisuje od tej chwili do nowego pliku
    except FileNotFoundError:
        return None
    with open(czytam) as f:
        wiersze = [w.strip() for w in f]
    os.remove(czytam)
    wiersze = [w for w in wiersze if w]
    if not wiersze:
        return None
    if wiersze[1:]:
        with open(WEJSCIE, "a") as f:        # reszta wraca na początek kolejki (append: nic nie ginie)
            f.write("\n".join(wiersze[1:]) + "\n")
    w = wiersze[0]
    if w.startswith("@"):
        czesci = w[1:].split(None, 1)
        if len(czesci) == 2 and czesci[0].isdigit():
            return czesci[1], int(czesci[0])
        if len(czesci) == 2 and czesci[0] == "wszystkie":
            return czesci[1], None
        print(f"słowo z niezrozumiałym adresem pominięte: {w!r}", flush=True)
        return None
    return w, None


SASIADOW = 3               # tyle sąsiadów może mieć miejsce
ROK = 480                  # cykli w roku (pory roku): rok krótszy nie dawał młodej cywilizacji czasu na odkrycie spichlerza przed pierwszą zimą
DOBA = 24                  # cykli w dobie; noc to ostatnia trzecia
KLESKA = 1 / 20000         # szansa pożaru albo powodzi w miejscu na cykl
WYBUCH = 1 / 120           # szansa, że w świecie pojawi się nowy szczep choroby (na cykl świata)
ZARAZLIWOSC = 0.07         # na jednego chorego obok, przy zerowej odporności
CHORUJE_MIN = 6            # tyle cykli choroba trwa, zanim w ogóle można wyzdrowieć
OGNISKO = (25, 70)         # ile cykli choroba utrzymuje się w skażonym miejscu
ROZWLEKA = 0.10            # szansa, że chora istota skazi łąkę, na której stoi (nowe ognisko)
ROZLEWA = 0.02             # szansa na cykl, że ognisko przenosi się na sąsiednią łąkę samo (woda, padlina, owady)
OGNISK_MAX = 0.05          # zaraza nie zajmuje więcej niż tyle części świata naraz: nawet epidemia ma swoją granicę
DRAPIEZNIK = 0.1           # szansa na cykl, że na którejś zamieszkanej łące zjawia się drapieżnik (było 0,25: w 147 cyklach 21 wizyt i 50 szarpnięć na 32 istoty)
DRAPIEZNIK_MIN = 3         # nie opłaca mu się polować tam, gdzie stoi mniej niż tyle istot
LOWY = 0.5                 # szansa, że drapieżnik w danym cyklu w ogóle kogoś dopadnie (jedna ofiara na cykl)
POSTOJ = (3, 8)            # ile cykli drapieżnik zostaje


def klimat_miejsca(swiat, k, m):
    """Pogoda w miejscu w tym cyklu: temperatura, deszcz, wiatr (0..1) i noc.
    Pory roku przesunięte w fazie zależnie od szerokości (lat): różne w różnych częściach świata."""
    t = swiat["cykl_swiata"]
    lat = m.get("lat", 0.5)
    faza = 2 * math.pi * t / ROK + math.pi * lat
    temp = 0.5 + 0.45 * math.sin(faza) - 0.25 * lat
    deszcz = 0.5 + 0.5 * math.sin(faza + math.pi / 2 + 1.5 * lat)
    wiatr = 0.35 + 0.3 * math.sin(3 * faza + 5 * lat) + 0.15 * math.sin(t / 7.0 + 2 * lat)
    noc = (t % DOBA) >= DOBA * 2 // 3
    return {"temp": max(0.0, min(1.0, temp)), "deszcz": max(0.0, min(1.0, deszcz)), "wiatr": max(0.0, min(1.0, wiatr)), "noc": noc}


def uzupelnij_tlumaczenia(swiat):
    """Znaczenia zapisane wcześniej mają same znaki. Tłumaczy je z pamięci żywych istot:
    wektor skutku odtwarza się z ich skojarzeń, po tym samym znaku."""
    zn = ((swiat.get("slownik") or {}).get("znaczenia") or {})
    braki = [k for k, v in zn.items() if (v.get("skutek") or ", bo " in k) and not v.get("ludzko")]
    if not braki:
        return
    agg = tlumacz.zbierz(swiat)
    ile = 0
    for k in braki:
        wpis = zn[k]
        if wpis.get("skutek"):
            czasownik, skutek = wpis.get("verb") or k.split(",", 1)[0], wpis["skutek"]
        else:
            czasownik, skutek = k.split(", bo ", 1)          # stare światy: czasownik i skutek z samego napisu
        a = agg.get(skutek)
        if not a or not a["n"]:
            continue
        zn[k]["ludzko"] = tlumacz.na_ludzki(a["v"], a["b"] / a["n"], czasownik, swiat)
        ile += 1
    if ile:
        print(f"przetłumaczono starych znaczeń: {ile} z {len(braki)}.", flush=True)


def do_slownika(swiat, b):
    """Słownik świata, pisany na bieżąco: unikalne słowa (temat + odniesienie) i znaczenia (czyn, jakie słowa go niosły).
    Zamiast liczyć z całego dziennika przy każdym otwarciu okna."""
    sl = swiat.setdefault("slownik", {"slowa": {}, "znaczenia": {}})
    m = b.mowa or {}
    if m.get("glos") and m.get("temat"):
        k = word.klucz_slowa(m.get("temat"), m.get("cel"), m.get("slowo_id"))
        if k:
            temat, cel = k.split(":", 1)
            gen = getattr(b, "gen_slowa", None)                       # z którego genu wypadł ten dźwięk
            baza = getattr(b, "genow_bazowych", len(b.K))
            z_nowego = gen is not None and gen >= baza                # gen z duplikacji: dźwięk, którego linia wcześniej nie miała
            if k not in sl["slowa"] and z_nowego:
                zdarzenie(swiat, "dzwiek_z_nowego_genu", nr=b.nr, slowo=k, gen=int(gen), geny=int(len(b.K)))
                print(f"nowy dźwięk z genu {gen}: byt {b.nr} mówi {k}.", flush=True)
            s = sl["slowa"].setdefault(k, {"temat": temat, "cel": cel or None, "razy": 0, "nadawcy": [], "pierwszy": b.nr, "pierwszy_cykl": swiat["cykl_swiata"], "gen": int(gen) if gen is not None else None, "z_nowego_genu": bool(z_nowego)})
            s["razy"] += 1
            if b.nr not in s["nadawcy"]:
                s["nadawcy"].append(b.nr)
    if b.czyn and b.czyn_do is not None:
        if b.czyn not in sl["znaczenia"]:
            # nowe znaczenie w świecie: pierwszy raz ktoś zrobił ten czyn po usłyszeniu słowa. Jedyne powiadomienie na stronie.
            ludzko = None
            if getattr(b, "czyn_skutek", None):
                n_ = (b.po_slowie.get(b.czyn_slowo) or {})
                if n_.get("n"):
                    ludzko = tlumacz.na_ludzki(n_["v"], n_["b"] / n_["n"], getattr(b, "czyn_verb", None) or b.czyn.split(",", 1)[0], swiat)
            zdarzenie(swiat, "znaczenie", nr=b.nr, od=b.czyn_do, czyn=b.czyn, slowo=b.czyn_slowo, ludzko=ludzko)
        zn = sl["znaczenia"].setdefault(b.czyn, {"czyn": b.czyn, "razy": 0, "slowa": {}, "kto": [], "dla": [], "pierwszy_cykl": swiat["cykl_swiata"],
                                                 "verb": getattr(b, "czyn_verb", None), "skutek": getattr(b, "czyn_skutek", None)})
        if "ludzko" not in zn and getattr(b, "czyn_skutek", None):
            # znaki skutku to zapis wektora; obok zapisujemy, co ten wektor znaczy po ludzku (raz na znaczenie)
            nauka = (b.po_slowie.get(b.czyn_slowo) or {})
            if nauka.get("n"):
                zn["ludzko"] = tlumacz.na_ludzki(nauka["v"], nauka["b"] / nauka["n"], getattr(b, "czyn_verb", None) or b.czyn.split(",", 1)[0], swiat)
        zn["razy"] += 1
        k = b.czyn_slowo or "?"
        zn["slowa"][k] = zn["slowa"].get(k, 0) + 1
        if getattr(b, "czyn_skutek", None):
            # słowo ma własne, wyuczone znaczenie — zapis przeżycia, które zapowiada.
            # Rośnie przy słowie, nie na liście czynów.
            w = sl["slowa"].get(b.czyn_slowo)
            if w is not None:
                skutek = b.czyn_skutek
                w.setdefault("znaczy", {})
                w["znaczy"][skutek] = w["znaczy"].get(skutek, 0) + 1
        if b.czyn_do not in zn["kto"]:
            zn["kto"].append(b.czyn_do)
        if b.nr not in zn["dla"]:
            zn["dla"].append(b.nr)


def daleka(swiat, b, tu, pora):
    """Łąka z pamięci istoty (na tę porę roku, poza obecną) i jej zapach: o niej może powiedzieć głodnemu, który jej nie widzi."""
    m = b.najlepsze_z_mapy(pora, poza=tu)
    return (m, zapach(swiat, m)) if m is not None and str(m) in swiat["miejsca"] else None


def do_korpusu(swiat, b, tu, blisko, zywi):
    """Korpus języka: każde słowo z kontekstem (kto, komu, gdzie, pora, kto słyszał) i każda reakcja słuchacza
    (co zrobił po jakim słowie). Bez zaglądania do wnętrza: tylko to, co widać z zewnątrz. Z tego kiedyś
    odczyta się ich pismo, jak pismo obcej cywilizacji."""
    k = swiat.setdefault("_korpus", [])
    c = swiat["cykl_swiata"]
    m = b.mowa or {}
    if m.get("glos") or m.get("krzyk") or m.get("wolanie") or m.get("alarm"):
        if m.get("glos"):
            klucz, znaki = word.klucz_slowa(m.get("temat"), m.get("cel"), m.get("slowo_id")), m.get("znaki")
        else:
            klucz = "@alarm" if m.get("alarm") else "@wolanie" if m.get("wolanie") else "@krzyk"
            znaki = {"@alarm": "!", "@wolanie": "♪", "@krzyk": "!!"}[klucz]
        k.append({"c": c, "r": "mowa", "kto": b.nr, "znaki": znaki, "klucz": klucz, "do": m.get("odpowiedz"),
                  "miejsce": tu, "pora": swiat.get("pora"), "noc": bool(swiat.get("noc")),
                  "slyszy": [x.nr for x in zywi if x.nr != b.nr and x.zyje() and str(x.miejsce) in blisko][:32]})
    if b.czyn and b.czyn_do is not None:
        k.append({"c": c, "r": "reakcja", "kto": b.nr, "od": b.czyn_do, "klucz": b.czyn_slowo, "czyn": getattr(b, "czyn_verb", None),
                  "obiekt": getattr(b, "czyn_obiekt", None), "cel": b.czyn_cel, "miejsce": tu})


def wpis_zmarlej(b, swiat, ostatnia=False):
    """Co zostaje po istocie: liczby, cechy z genów i to, co nabyła. Z tego powstaje portret."""
    return {"nr": b.nr, "pokolenie": b.pokolenie, "wiek": b.wiek, "geny": len(b.kregoslup),
            "glos": word.glos_na_znaki(b.glos), "plec": b.plec, "ostatnia": ostatnia,
            "otwarcia": b.otwarcia, "dzieci": b.dzieci, "rodzic": b.rodzic, "rodzic2": b.rodzic2,
            "zmarl_w_cyklu": swiat["cykl_swiata"], "urodzony_w_cyklu": getattr(b, "urodzony_w_cyklu", None),
            "sila": b.sila, "lownosc": getattr(b, "lownosc", None), "ciekawosc": b.ciekawosc, "wytrwalosc": b.wytrwalosc,
            "stadnosc": b.stadnosc, "dlugowiecznosc": b.dlugowiecznosc, "optimum": b.optimum, "tolerancja": b.tolerancja, "towarzyskosc": b.towarzyskosc,
            "ufnosc": b.ufnosc, "szczerosc": b.szczerosc, "pojetnosc": b.pojetnosc, "uprawa": b.uprawa, "spichlerz": b.spichlerz,
            "zrozumiane": sorted(b.zrozumiane), "mapa": b.mapa, "klamcy": sorted(b.klamcy), "nauczone": getattr(b, "nauczone", 0),
            "rozmowy": getattr(b, "rozmowy", 0), "slownik": sorted(b.slownik.keys()), "krokow": b.krokow, "sen": b.sen}


POJEMNOSC_SWIATA = int(os.environ.get("POJEMNOSC_SWIATA", "2000"))   # tylu żywych świat uniesie: powyżej nie ma urodzeń


def sygnatura(swiat, nazwa):
    """Sygnatura rzeczy w świecie (noc, pory roku): losowy kierunek, stały dla świata. Powstaje przy pierwszym użyciu."""
    s = swiat.setdefault("sygnatury", {})
    if nazwa not in s:
        s[nazwa] = word.losowy_kierunek()
    return s[nazwa]


def zapach(swiat, k):
    """Zapach miejsca: jego sygnatura. Każda łąka pachnie inaczej; tak można o niej mówić."""
    m = swiat["miejsca"][str(k)]
    if "zapach" not in m or len(m["zapach"]) != word.ROZMIAR:
        m["zapach"] = word.losowy_kierunek()
    return m["zapach"]


def pora_roku(swiat):
    """Pora roku w środku świata (lat 0,5), do pokazania."""
    f = ((swiat["cykl_swiata"] / ROK) + 0.25) % 1.0
    return ["wiosna", "lato", "jesien", "zima"][int(f * 4)]


def nowe_pole(istot=1):
    """Żyzność pierwszych miejsc: łąk tyle, ile trzeba dla istot na start (co najmniej 3,
    jedna na dwie istoty), koło rośnie razem z liczbą łąk (5 miejsc na łąkę, co najmniej 16)."""
    laki = max(4, -(-istot // 4))                                   # co najmniej cztery łąki: cztery grupy na start, daleko od siebie
    na_lake = ROZMIARY.get(ROZMIAR, ROZMIARY["zwykly"])[0]
    n = max(word.MIEJSC if na_lake >= 5 else 9, na_lake * laki)
    zyznosc = [0.05] * n
    srodki = [int(i * n / laki + n / (2 * laki)) % n for i in range(laki)]   # równo rozłożone
    for srodek in srodki:
        for dx in range(-2, 3):
            zyznosc[(srodek + dx) % n] = max(zyznosc[(srodek + dx) % n], 1.0 - 0.3 * abs(dx))
    return zyznosc


def losowa_zyznosc():
    """Nowe miejsce: częściej pustynia niż łąka, czasem bardzo żyzne."""
    r = random.random()
    return 0.05 if r < 0.5 else (0.4 if r < 0.75 else (0.7 if r < 0.92 else 1.0))


def cechy_miejsca():
    """Twardość (ile siły trzeba) i przyswajalność (ile z pokarmu da się wziąć) miejsca."""
    h = round(0.8 * random.random() ** 2, 2)
    return {"h": h, "h0": h, "a": round(random.uniform(0.7, 1.0), 2)}


def nowe_miejsca(zyznosc):
    """Początkowa sieć: koło z 16 miejsc, każde zna dwóch sąsiadów."""
    n = len(zyznosc)
    return {str(i): {"s": [str((i - 1) % n), str((i + 1) % n)], "z": zyznosc[i], "g": zyznosc[i],
                     "lat": round(0.5 + 0.5 * math.sin(2 * math.pi * i / n), 3), **cechy_miejsca()} for i in range(n)}


def pole_cykl(swiat):
    """Gęstość każdego znanego miejsca odrasta do jego żyzności."""
    if "miejsca" not in swiat:
        zy = swiat.get("zyznosc") or nowe_pole(1)
        swiat["miejsca"] = nowe_miejsca(zy)
        if "pole" in swiat:
            for i, g in enumerate(swiat["pole"]):
                swiat["miejsca"][str(i)]["g"] = g
        swiat["kolejnosc"] = [str(i) for i in range(len(zy))]
    for k, m in swiat["miejsca"].items():
        m.setdefault("h", 0.2); m.setdefault("a", 1.0); m.setdefault("h0", m["h"])   # stare światy
        m.setdefault("lat", 0.5)
        p = klimat_miejsca(swiat, k, m)
        cieplo = max(0.0, min(1.0, (p["temp"] - 0.2) / 0.4))       # poniżej 0,2 łąka nie rośnie wcale: zima zatrzymuje wzrost
        odr = word.ODRASTANIE * (0.2 + 1.6 * p["deszcz"]) * cieplo
        m["g"] = max(0.0, min(1.0, m["g"] + odr * (m["z"] - m["g"])))
        if p["temp"] < 0.12:
            m["g"] = max(0.0, m["g"] * 0.995)                      # mróz zabiera i to, co zostało
        if m.get("zapas"):
            m["zapas"] = max(0.0, m["zapas"] * (0.997 if p["temp"] < 0.2 else 0.99))   # mróz konserwuje: zimą zapas psuje się wolniej
        if m.get("ryty"):
            for r in m["ryty"]:
                r["sila"] = r.get("sila", 1.0) - word.RYT_BLEDNIE       # ryt blednie, chyba że ktoś go odnowi
            for r in [r for r in m["ryty"] if r["sila"] <= 0.0]:
                m["ryty"].remove(r)
                zdarzenie(swiat, "ryt_zatarty", miejsce=k, nr=r.get("nr"), co=r.get("kl"))
        if p["deszcz"] < 0.2:
            m["h"] = min(0.95, m["h"] + 0.01)                     # susza: pokarm twardnieje
        else:
            m["h"] = m["h"] + 0.01 * (m["h0"] - m["h"]) if abs(m["h"] - m["h0"]) > 0.01 else m["h0"]
        h = m.setdefault("hist", [])                                 # historia miejsca: gęstość i temperatura, ostatni rok
        h.append([round(m["g"], 3), round(p["temp"], 2), round(p["deszcz"], 2)])
        if len(h) > ROK:
            del h[:-ROK]
        r = random.random()
        if r < KLESKA:
            m["g"] = 0.0; zdarzenie(swiat, "pozar", miejsce=k)      # pożar: łąka znika, odrośnie
        elif r < 2 * KLESKA:
            m["h"] = round(m["h"] * 0.3, 2); m["g"] *= 0.5; zdarzenie(swiat, "powodz", miejsce=k)
    swiat["pole"] = [round(swiat["miejsca"][k]["g"], 3) for k in swiat["kolejnosc"]]


def odkryj(swiat, skad):
    """Z miejsca z wolnym sąsiedztwem może powstać nowe miejsce."""
    if len(swiat["miejsca"]) >= ROZMIARY.get(swiat.get("rozmiar", "zwykly"), ROZMIARY["zwykly"])[2]:
        return None
    nowe = str(len(swiat["miejsca"]))
    while nowe in swiat["miejsca"]:
        nowe = str(int(nowe) + 1)
    swiat["miejsca"][nowe] = {"s": [skad], "z": losowa_zyznosc(), "g": 0.0,
                              "lat": round(max(0.0, min(1.0, swiat["miejsca"][skad].get("lat", 0.5) + random.gauss(0, 0.05))), 3),
                              **cechy_miejsca()}
    swiat["miejsca"][nowe]["g"] = swiat["miejsca"][nowe]["z"]
    swiat["miejsca"][skad]["s"].append(nowe)
    swiat["kolejnosc"].append(nowe)
    return nowe


def towarzystwo(swiat, b, k, zywi):
    """Kto stoi w miejscu k: swoi (po akcencie) liczą się dodatnio, obcy ujemnie."""
    swoi = obcy = 0
    for x in zywi:
        if x is not b and x.zyje() and str(x.miejsce) == str(k):
            if b.swoj(x):
                swoi += 1
            else:
                obcy += 1
    return swoi, obcy


def wech(swiat, b, k, zywi=None):
    """Jak dobrze pachnie sąsiednie miejsce: pokarm (gęstość, przyswajalność, czy da radę go wziąć)
    razy komfort (temperatura bliska optimum istoty), plus szum. Zimne, bogate miejsce może pachnieć
    gorzej niż ciepłe, uboższe: to jest migracja za klimatem."""
    m = swiat["miejsca"][k]
    sila_wobec = max(0.2, 1.0 - 1.5 * max(0.0, m.get("h", 0.2) - b.sila))
    p = klimat_miejsca(swiat, k, m)
    poza = max(0.0, abs(max(0.0, p["temp"] - 0.15 * p["deszcz"]) - b.optimum) - b.tolerancja)
    komfort = 1.0 / (1.0 + 1.2 * poza)
    zapach = m["g"] * m.get("a", 1.0) * sila_wobec * komfort
    if zywi is not None:
        swoi, obcy = towarzystwo(swiat, b, k, zywi)
        # stadność: swoi przyciągają (malejąco: trzeci mniej niż pierwszy), obcy odpychają
        zapach *= 1.0 + b.stadnosc * (0.5 * min(swoi, 4) ** 0.5) - 0.3 * min(obcy, 3)
    return zapach + random.gauss(0, 0.08)


def dokad(swiat, b, zwiad=False, zywi=None):
    """Krok istoty: odkrycie nowego miejsca albo sąsiad, który najlepiej pachnie (zwiad węchem).
    Bez zawracania, chyba że musi. zwiad=True: syta rusza, bo gdzie indziej pachnie lepiej niż tu."""
    tu = str(b.miejsce)
    m = swiat["miejsca"][tu]
    if len(m["s"]) < SASIADOW and random.random() < ROZMIARY.get(swiat.get("rozmiar", "zwykly"), ROZMIARY["zwykly"])[1]:
        nowe = odkryj(swiat, tu)
        if nowe is not None:
            return nowe
    kandydaci = [x for x in m["s"] if x != str(b.poprzednie)] or list(m["s"])
    kandydaci = [x for x in kandydaci if not b.omija(x)] or ([] if zwiad else kandydaci)   # „uwaga”: omija łąki, o których słyszała, że tam boli
    if not kandydaci:
        return None
    najlepszy = max(kandydaci, key=lambda k: wech(swiat, b, k, zywi))
    if zwiad and wech(swiat, b, najlepszy, zywi) <= wech(swiat, b, tu, zywi) + 0.1:
        return None                                                    # nigdzie nie pachnie lepiej: zostaje
    return najlepszy


def odleglosc(swiat, skad, cel):
    """Liczba kroków po znanych miejscach (BFS); None, gdy nie ma drogi."""
    skad, cel = str(skad), str(cel)
    if skad == cel:
        return 0
    odw = {skad: 0}
    kolejka = [skad]
    while kolejka:
        x = kolejka.pop(0)
        for y in swiat["miejsca"][x]["s"]:
            if y not in odw:
                odw[y] = odw[x] + 1
                if y == cel:
                    return odw[y]
                kolejka.append(y)
    return None


def krok_do(swiat, skad, cel):
    """Pierwszy krok najkrótszej drogi po znanych miejscach (BFS)."""
    skad, cel = str(skad), str(cel)
    if skad == cel:
        return None
    poprz = {skad: None}
    kolejka = [skad]
    while kolejka:
        x = kolejka.pop(0)
        for y in swiat["miejsca"][x]["s"]:
            if y not in poprz:
                poprz[y] = x
                if y == cel:
                    while poprz[y] != skad:
                        y = poprz[y]
                    return y
                kolejka.append(y)
    return None


def main():
    global CYKL_SEKUND, POJEMNOSC_SWIATA
    swiat = wczytaj()
    if swiat is None:
        word.ustaw_jezyk(JEZYK)
        tlumacz.JEZYK = JEZYK
        word.ustaw_wymiary(WYMIARY)
        word.KIERUNEK_RANY = word.losowy_kierunek()
        word.KIERUNEK_POKARMU = word.losowy_kierunek()
        word.KIERUNEK_WOLANIA = word.losowy_kierunek()
        word.KIERUNEK_GLOSU = word.losowy_kierunek()
        pierwsi, proby = [], 0
        for i in range(ISTOT):
            Byt.licznik = 0
            b, p = word.pierwszy_cud(GENY)
            proby += p
            b.nr = i + 1
            b.plec = "n" if i % 2 == 0 else "d"                     # na start po równo
            pierwsi.append(b)
        Byt.licznik = ISTOT
        # życie zaczyna się tam, gdzie jest pokarm: istoty rozdzielone po łąkach
        zyznosc = nowe_pole(ISTOT)
        laki = [p for p in range(len(zyznosc)) if zyznosc[p] >= 0.99]   # środki łąk, równo po kole
        # cztery grupy na start, rozrzucone po świecie: co czwarta łąka z równo rozłożonych, czyli najdalej, jak się da
        grup = min(4, len(laki), max(1, ISTOT // 2))
        wybrane = [laki[int(k * len(laki) / grup)] for k in range(grup)]
        for i, b in enumerate(pierwsi):
            b.miejsce = str(wybrane[i % grup])
        swiat = {
            "narodziny": time.time(), "cykl_swiata": 0, "losowan_cudu": proby, "dwoje": DWOJE,
            "cykl_sekund": CYKL_SEKUND, "wymiary": WYMIARY, "istot_na_start": ISTOT, "geny": GENY, "rozmiar": ROZMIAR,
            "pojemnosc_swiata": POJEMNOSC_SWIATA, "jezyk": JEZYK,
            "miejsca": nowe_miejsca(zyznosc), "kolejnosc": [str(i) for i in range(len(zyznosc))],
            "pole": list(zyznosc),
            "kierunek_rany": word.KIERUNEK_RANY, "kierunek_pokarmu": word.KIERUNEK_POKARMU,
            "kierunek_wolania": word.KIERUNEK_WOLANIA, "kierunek_glosu": word.KIERUNEK_GLOSU,
            "licznik": Byt.licznik, "zywi": [byt_do_slownika(b) for b in pierwsi], "zmarli": [],
            "wygasla": False,
        }
        zapisz(swiat)
        print(f"cud: {proby} losowań. istot {ISTOT}. {GENY} genów, {WYMIARY} wymiary."
              f"{' Dwoje rodziców.' if DWOJE else ''}", flush=True)
    elif swiat["wygasla"]:
        print("linia wygasła. to jest grób. nic go nie wskrzesi.", flush=True)
        sys.exit(1)
    else:
        POJEMNOSC_SWIATA = int(swiat.get("pojemnosc_swiata", POJEMNOSC_SWIATA))   # ilu żywych uniesie TEN świat
        print(f"powrót do ciała: cykl świata {swiat['cykl_swiata']}, żywych {len(swiat['zywi'])}, pojemność {POJEMNOSC_SWIATA}.", flush=True)
        uzupelnij_tlumaczenia(swiat)

    CYKL_SEKUND = float(swiat.get("cykl_sekund", CYKL_SEKUND))
    word.ustaw_wymiary(swiat.get("wymiary", 4))
    if "kierunek_wolania" not in swiat:
        swiat["kierunek_wolania"] = word.losowy_kierunek()
    if "kierunek_glosu" not in swiat:
        swiat["kierunek_glosu"] = word.losowy_kierunek()
    word.KIERUNEK_WOLANIA = swiat["kierunek_wolania"]
    word.KIERUNEK_GLOSU = swiat["kierunek_glosu"]
    word.ustaw_jezyk(swiat.get("jezyk", "pl"))               # świat mówi w języku, w którym go powołano
    tlumacz.JEZYK = word.JEZYK
    word.PROG_GATUNKU = float(swiat.get("prog_gatunku", 0.0) or 0.0)     # bariera dojrzewa ze światem, nie zaczyna się od zera
    word.KIERUNEK_RANY = swiat["kierunek_rany"]
    word.KIERUNEK_POKARMU = swiat["kierunek_pokarmu"]
    zywi = [byt_ze_slownika(d) for d in swiat["zywi"]]
    Byt.licznik = max(swiat["licznik"], max((b.nr for b in zywi), default=0), max((z["nr"] for z in swiat["zmarli"]), default=0))

    while zywi:
        start = time.time()
        swiat["cykl_swiata"] += 1
        word.dryf_swiata()
        slowo, slowo_do = kolejka_slow() or (None, None)
        if slowo_do is not None and slowo_do not in {b.nr for b in zywi}:
            print(f"słowo {slowo!r} do istoty nr {slowo_do}, której nie ma; przepada", flush=True)
            slowo, slowo_do = None, None
        nowi = []
        if os.path.exists(CUD):
            os.remove(CUD)
            nowy, proby = word.pierwszy_cud(swiat.get("geny", GENY))
            nowy.pokolenie = 1
            nowy.miejsce = max(swiat["miejsca"], key=lambda k: swiat["miejsca"][k]["z"])
            nowy.staz = 2
            nowi.append(nowy)
            print(f"cud nowy: {proby} losowań. byt {nowy.nr} żyje, osobna linia.", flush=True)
        # pole pokarmu: odrasta, dryfuje
        pole_cykl(swiat)
        # świat odpowiedział na wołanie: kładzie pokarm tam, gdzie jest wołający (raz na cykl)
        if os.path.exists(KARMA):
            czytam = KARMA + ".czytam"
            try:
                os.rename(KARMA, czytam)
                with open(czytam) as f:
                    prosby = [l.strip() for l in f if l.strip()]
                os.remove(czytam)
            except FileNotFoundError:
                prosby = []
            for prosba in prosby[:8]:
                cele = []
                if prosba == "@wszystkie":
                    cele = list(zywi)
                elif prosba.startswith("@") and prosba[1:].isdigit():
                    cele = [b for b in zywi if b.nr == int(prosba[1:])]
                if not cele:
                    cele = ([b for b in zywi if b.mowa.get("krzyk")] or zywi)[:1]
                for b in cele:
                    mm = swiat["miejsca"][str(b.miejsce)]
                    mm["g"] = min(1.0, mm["g"] + 0.5)   # pokarm ląduje tam, gdzie stoi
                zdarzenie(swiat, "pokarm", nr=[b.nr for b in cele], wszystkie=(prosba == "@wszystkie"))
        poprzednie = {b.nr: list(b.wyszlo) for b in zywi}
        krzyczal = {b.nr: b.mowa.get("krzyk", False) for b in zywi}
        alarmowal = {b.nr: b.mowa.get("alarm", False) for b in zywi}
        glosil = {b.nr: b.mowa.get("glos", False) for b in zywi}
        # migawka brzmienia i tematu sprzed cyklu: słuchacz słyszy to, co nadawca wydał w poprzednim cyklu, nie w trakcie tego
        mowy = {b.nr: (list(b.wypowiedz or b.glos), b.mowa.get("odpowiedz"), b.mowa.get("temat"), b.mowa.get("cel"), b.mowa.get("slowo_id"), b.mowa.get("uprawa"), b.mowa.get("spichlerz")) for b in zywi}
        cykl_istoty = list(zywi)
        wolal = {b.nr: b.mowa.get("wolanie", False) for b in zywi}
        random.shuffle(zywi)
        # kto krzyczał z głodu, je pierwszy: syci ustępują
        zywi.sort(key=lambda b: not krzyczal[b.nr])
        wpisy = []
        for b in zywi:
            # ruch: wysiłek. Najpierw krok, potem słuchanie i jedzenie tam, gdzie stanęła.
            glod = min(1.0, max(0.0, 1.0 - b.energia / word.SYTOSC))
            tu_start = str(b.miejsce)
            b.karmione = 0.0
            b.ruszyl = False                    # najwyżej jeden krok na cykl, liczony od tej chwili
            b.przechodzi = False                # przejście: idzie dalej, tu nie je i nie zostaje
            b.deklaruje = False                 # „tylko przechodzę”: prawda przechodnia albo kłamstwo przybysza
            dalej = None                        # cel wędrówki, gdy jest dalej niż jeden krok
            rodzice = [x for x in zywi if x.nr in (b.rodzic, b.rodzic2) and x.zyje()] if b.wiek < word.DZIECINSTWO else []
            unikana_obok = any(b.unika(x.nr) for x in zywi if x.nr != b.nr and x.zyje() and str(x.miejsce) == str(b.miejsce)) if b.unikani else False
            if unikana_obok and b.energia > word.KOSZT_RUCHU * 2 and random.random() < 0.5:
                b.krok(random.choice(swiat["miejsca"][str(b.miejsce)]["s"]))     # „unikaj istoty”: nie stoi z nią na jednej łące
            elif b.energia <= word.SYTOSC and b.chce_isc(glod):
                cel = None
                if rodzice and str(rodzice[0].miejsce) != str(b.miejsce):
                    cel = krok_do(swiat, b.miejsce, rodzice[0].miejsce)   # dziecko trzyma się rodzica
                    dalej = str(rodzice[0].miejsce)
                elif b.najlepsze_z_mapy(pora_roku(swiat), poza=b.miejsce) in swiat["miejsca"] and swiat["miejsca"][b.najlepsze_z_mapy(pora_roku(swiat), poza=b.miejsce)]["g"] > 0.3:
                    dalej = b.najlepsze_z_mapy(pora_roku(swiat), poza=b.miejsce)
                    cel = krok_do(swiat, b.miejsce, dalej)                 # mapa pór roku: idzie tam, gdzie o tej porze się jada
                elif b.dobre_miejsce is not None and str(b.dobre_miejsce) != str(b.miejsce) and str(b.dobre_miejsce) in swiat["miejsca"]:
                    if swiat["miejsca"][str(b.dobre_miejsce)]["g"] > 0.3:
                        cel = krok_do(swiat, b.miejsce, b.dobre_miejsce)  # pamięć: wraca, gdzie jadła
                        dalej = str(b.dobre_miejsce)
                    else:
                        b.dobre_miejsce = None                          # pamięć zawiodła: miejsce wyjedzone
                dk = cel if cel is not None else dokad(swiat, b, zywi=zywi)
                if dk is not None:
                    b.krok(dk)
                    b.przechodzi = dalej is not None and str(dk) != dalej   # cel dalej: tu tylko przechodzi
                    b.energia -= word.KOSZT_RUCHU * 0.5 * klimat_miejsca(swiat, tu_start, swiat["miejsca"][tu_start])["wiatr"]   # pod wiatr
            elif b.energia > word.SYTOSC and not b.ruszyl and random.random() < 0.14 * b.ciekawosc:   # zwiad: syta czasem sprawdza, czy obok nie jest lepiej
                # zwiad: syta czasem rusza, gdy obok pachnie lepiej. Ryzyko, ale i szansa na lepsze miejsce.
                dk = dokad(swiat, b, zwiad=True, zywi=zywi)
                if dk is not None and b.energia > word.KOSZT_RUCHU * 2:
                    b.krok(dk)
            partner = None
            if swiat.get("dwoje"):
                def moze_byc_partnerem(x):
                    return (x.nr != b.nr and x.zyje() and x.plec != b.plec and str(x.miejsce) == str(b.miejsce)
                            and x.energia > word.SYTOSC / 2 and x.wiek >= word.DZIECINSTWO * (1 + 0.5 * x.dlugowiecznosc)
                            and b.wiek >= word.DZIECINSTWO * (1 + 0.5 * b.dlugowiecznosc)
                            and x.nr not in (b.rodzic, b.rodzic2) and b.nr not in (x.rodzic, x.rodzic2)
                            and b.zgodna_z(x))                       # bariera gatunkowa: za odległe rdzenie nie dają potomstwa
                kandydaci = [x for x in zywi if moze_byc_partnerem(x)]
                # dobór płciowy: nosząca wybiera najatrakcyjniejszego z obecnych dających; dający nie wybiera
                # dobór płciowy: do siły i kondycji dochodzi ozdoba, ważona własnym gustem wybierającej.
                # Gust jest dziedziczny tak samo jak ozdoba, więc jedno może pociągnąć drugie w górę.
                partner = (max(kandydaci, key=lambda x: x.atrakcyjnosc() + 2.0 * b.gust * x.ozdoba) if kandydaci else None) if b.plec == "n" else None
                if partner is not None and len(zywi) + len(nowi) >= POJEMNOSC_SWIATA:
                    partner = None                                        # świat pełny: pojemność środowiska, bez urodzeń
                dorosla = b.wiek >= word.DZIECINSTWO * (1 + 0.5 * b.dlugowiecznosc)
                gotowa = b.plec == "n" and b.energia > word.PROG_CUDU and dorosla
                szuka = b.plec == "d" and b.energia > word.SYTOSC and not kandydaci and dorosla
                b.mowa["wolanie"] = (gotowa and partner is None) or szuka
                if szuka and b.wiek >= word.DZIECINSTWO and not b.ruszyl:
                    # wędruje tylko jedna płeć: gotowa ♀ zostaje i woła, syty ♂ bez ♀ obok idzie na wołanie
                    # (najbliższa wołająca ♀; gdy żadna nie woła, najbliższa dorosła ♀). Obie płcie naraz goniły się po świecie.
                    cele = [(odleglosc(swiat, b.miejsce, x.miejsce), x) for x in zywi
                            if x.nr != b.nr and x.zyje() and x.plec != b.plec and x.wiek >= word.DZIECINSTWO
                            and x.nr not in (b.rodzic, b.rodzic2) and b.nr not in (x.rodzic, x.rodzic2)]
                    cele = [c for c in cele if c[0] is not None and c[0] > 0]
                    wolajace = [c for c in cele if wolal.get(c[1].nr)]
                    if wolajace:
                        cele = wolajace
                    if cele:
                        cel = min(cele, key=lambda c: c[0])[1]
                        k = krok_do(swiat, b.miejsce, cel.miejsce)
                        if k is not None:
                            b.krok(k)
                            b.przechodzi = str(k) != str(cel.miejsce)    # do ♀ jeszcze daleko: tu tylko przechodzi
            if b.ruszyl:
                # znak przejścia: przechodzień mówi prawdę; przybysz, który chce zostać, czasem kłamie (gen szczerości)
                b.deklaruje = b.przechodzi or random.random() > b.szczerosc
            # słyszy wszystkie istoty z miejsca, w którym stoi, i z miejsc sąsiednich
            tu = str(b.miejsce)
            pog = klimat_miejsca(swiat, tu, swiat["miejsca"][tu])
            blisko = set([tu] + list(swiat["miejsca"].get(tu, {}).get("s", [])))
            if pog["wiatr"] < 0.7:                                          # silny wiatr zagłusza: słychać tylko sąsiadów
                for s1 in list(blisko):                                     # inaczej słychać na dwa miejsca
                    blisko.update(swiat["miejsca"].get(s1, {}).get("s", []))
            inni_syg = []
            for x in zywi:
                if x.nr == b.nr or str(x.miejsce) not in blisko:
                    continue
                if alarmowal.get(x.nr):
                    inni_syg.append((x.nr, word.rana(), "alarm", b.swoj(x)))   # alarm: ból swojego, wrodzony
                elif wolal.get(x.nr):
                    inni_syg.append((x.nr, word.wolanie(), "wolanie", x.plec != b.plec))   # wołanie: "chodź do mnie" (dla przeciwnej płci)
                elif krzyczal.get(x.nr):
                    inni_syg.append((x.nr, word.rana(), "krzyk"))           # krzyk: rana, którą każdy rozumie
                elif glosil.get(x.nr):
                    # głos: własny język, do skojarzenia. Odpowiedź brzmi tak samo, ale na nią już się nie odpowiada.
                    # Brzmienie = głos + temat; metadane mówią, do czego temat się odnosi (łąka, kłamca): to „wskazanie”.
                    brzm, odp, tem, cel_t, sid, upr, spi = mowy[x.nr]
                    inni_syg.append((x.nr, brzm, "odpowiedz" if odp is not None else "glos", None, {"temat": tem, "cel": cel_t, "slowo_id": sid, "uprawa": upr, "spichlerz": spi, "swoj": b.swoj(x)}))
                elif poprzednie.get(x.nr):
                    w = max(poprzednie[x.nr], key=lambda v: sum(t * t for t in v))
                    inni_syg.append((x.nr, w, "wyjscie"))
            random.shuffle(inni_syg)
            inni_syg.sort(key=lambda s: {"alarm": 0, "wolanie": 1, "krzyk": 2, "glos": 3, "odpowiedz": 3}.get(s[2], 4))   # najpierw to, co ważne
            inny = inni_syg[0] if inni_syg else None
            mm = swiat["miejsca"][tu]
            g = mm["g"]
            # twardy pokarm wymaga siły: brak siły odejmuje od tego, co da się wziąć; przyswajalność miejsca mnoży
            sila_wobec = max(0.2, 1.0 - 1.5 * max(0.0, mm.get("h", 0.2) - b.sila))
            surowa = random.expovariate(1.0 / (word.HOJNOSC * g)) * mm.get("a", 1.0) * sila_wobec if g > 0.05 else 0.0
            if pog["noc"]:
                surowa *= 0.5                                                # w nocy oferta słabsza
            # deszcz wychładza: odczuwalna temperatura spada do 0,15 przy ulewie; w ulewie trudniej żerować
            odczuwalna = max(0.0, pog["temp"] - 0.15 * pog["deszcz"])
            if pog["deszcz"] > 0.8:
                surowa *= 0.8
            if b.przechodzi:
                surowa = 0.0                                                 # tylko przechodzi: nie bierze pokarmu z tej łąki
            pora_teraz = pora_roku(swiat)
            klimat = {"temp": odczuwalna, "noc": pog["noc"], "pora": pora_teraz,          # koszt liczy istota wg swojego optimum i tolerancji
                      "zapach": zapach(swiat, tu), "pora_syg": sygnatura(swiat, pora_teraz), "noc_syg": sygnatura(swiat, "noc"), "uprawa_syg": sygnatura(swiat, "uprawa"), "spichlerz_syg": sygnatura(swiat, "spichlerz"), "choroba_syg": sygnatura(swiat, "choroba"), "drapieznik_syg": sygnatura(swiat, "drapieznik"),
                      "drapieznik": str(tu) in (swiat.get("drapiezniki") or {}), "ognisko": str(tu) in (swiat.get("ogniska") or {}), "zapas": swiat["miejsca"][tu].get("zapas", 0.0),
                      "towarzystwo": sum(1 for x in zywi if x.nr != b.nr and x.zyje() and str(x.miejsce) in blisko),
                      "daleka": daleka(swiat, b, tu, pora_teraz)}
            dziecko = b.cykl(slowo=slowo if (slowo_do is None or slowo_do == b.nr) else None,
                             surowa=surowa, inny=inny, inni=inni_syg, partner=partner, dwoje=swiat.get("dwoje", False),
                             klimat=klimat)
            mm["g"] = max(0.0, mm["g"] - word.WYJADANIE * b.zjadl)   # wyjada miejsce
            if b.uprawiala:
                mm["g"] = min(1.0, mm["g"] + word.UPRAWA_ODROST * b.uprawa)   # uprawia: łąka odrasta szybciej
                mm["uprawiana"] = swiat["cykl_swiata"]
            if getattr(b, "odkryla_uprawe", False):
                b.odkryla_uprawe = False
                zdarzenie(swiat, "odkrycie", nr=b.nr, miejsce=tu, co="uprawa")
            if getattr(b, "odkryla_spichlerz", False):
                b.odkryla_spichlerz = False
                zdarzenie(swiat, "odkrycie", nr=b.nr, miejsce=tu, co="spichlerz")
            if getattr(b, "odkryla_ryt", False):
                b.odkryla_ryt = False
                zdarzenie(swiat, "odkrycie", nr=b.nr, miejsce=tu, co="ryt")
            # ryt: istota wyryła znaczenie w miejscu (odnawia, jeśli takie tu już jest); pamięć poza ciałem
            if getattr(b, "ryje", None):
                kl, d = b.ryje
                ryty = mm.setdefault("ryty", [])
                stary = next((r for r in ryty if r.get("kl") == kl), None)
                if stary is not None:
                    stary.update({"n": d["n"], "v": d["v"], "b": d["b"], "sila": 1.0, "nr": b.nr, "cykl": swiat["cykl_swiata"]})
                elif len(ryty) < word.RYTOW_NA_LACE:
                    ryty.append({"kl": kl, "n": d["n"], "v": d["v"], "b": d["b"], "sila": 1.0, "nr": b.nr, "cykl": swiat["cykl_swiata"]})
                else:
                    stary = min(ryty, key=lambda r: r.get("sila", 1.0))                 # nie ma miejsca: najbledszy ustępuje
                    zdarzenie(swiat, "ryt_zatarty", miejsce=tu, nr=stary.get("nr"), co=stary.get("kl"))
                    ryty.remove(stary)
                    ryty.append({"kl": kl, "n": d["n"], "v": d["v"], "b": d["b"], "sila": 1.0, "nr": b.nr, "cykl": swiat["cykl_swiata"]})
                zdarzenie(swiat, "ryt", nr=b.nr, miejsce=tu, co=kl, odnowiony=stary is not None and stary.get("kl") == kl)
            # spuścizna: u kresu ryje jeden wpis na cykl, od najważniejszego, póki żyje. Nagrobek albo książka.
            if getattr(b, "spuscizna_teraz", None):
                kl, d, rodzaj = b.spuscizna_teraz
                ryty = mm.setdefault("ryty", [])
                wpis = {"kl": kl, "rodzaj": rodzaj, "sila": 1.0, "nr": b.nr, "cykl": swiat["cykl_swiata"], "spuscizna": True}
                if d is not None:
                    wpis.update(d)
                else:
                    wpis["znaki"] = word.glos_na_znaki(b.glos)
                stary = next((r for r in ryty if r.get("kl") == kl), None)
                if stary is not None:
                    stary.update(wpis)
                elif len(ryty) < word.RYTOW_NA_LACE:
                    ryty.append(wpis)
                else:
                    najslabszy = min(ryty, key=lambda r: r.get("sila", 1.0))
                    zdarzenie(swiat, "ryt_zatarty", miejsce=tu, nr=najslabszy.get("nr"), co=najslabszy.get("kl"))
                    ryty.remove(najslabszy)
                    ryty.append(wpis)
                zdarzenie(swiat, "spuscizna", nr=b.nr, miejsce=tu, co=kl, rodzaj=rodzaj, glos=rodzaj == "glos", wiek=b.wiek, ile=len(b.wyryte))
                b.spuscizna_teraz = None
            # odczyt: kto zostaje na łące z rytami i ma dość ciekawości, znajduje jeden, którego jeszcze nie zna
            elif mm.get("ryty") and not b.ruszyl and b.zyje() and random.random() < word.ODCZYT * b.ciekawosc:
                nieznane = [r for r in mm["ryty"] if r.get("rodzaj", "znaczenie") != "glos" and r.get("kl") not in b.po_slowie and r.get("kl") not in b.wyryte]
                if nieznane:
                    r = random.choice(nieznane)
                    if b.odczytaj(r):
                        autor_zyje = any(x.nr == r.get("nr") and x.zyje() for x in zywi)
                        zdarzenie(swiat, "odczytanie", nr=b.nr, miejsce=tu, od=r.get("nr"), co=r.get("kl"), autor_zyje=autor_zyje, sila=round(r.get("sila", 1.0), 2))
            # spichlerz łąki: odłożone (ze stratą) i pobrane
            if b.odklada > 0.0:
                mm["zapas"] = mm.get("zapas", 0.0) + b.odklada * (1.0 - word.STRATA_SPICHLERZA)
            if b.pobiera > 0.0:
                dawka = min(b.pobiera, mm.get("zapas", 0.0))
                mm["zapas"] = mm.get("zapas", 0.0) - dawka
                b.energia += dawka
                b.pobiera = dawka
            # opieka: rodzic karmi żywe dziecko, dopóki nie skończy dzieciństwa. Potem pępowina odcięta.
            if b.zyje():
                for r in rodzice:
                    if b.energia < word.SYTOSC and r.energia > word.SYTOSC / 2 and str(r.miejsce) in blisko:
                        dawka = min(word.KARMIENIE, r.energia - word.SYTOSC / 2, word.SYTOSC - b.energia)
                        if dawka > 0:
                            r.energia -= dawka
                            b.energia += dawka
                            b.karmione += dawka
            # kultura: dziecko przy rodzicu uczy się tego, co rodzic nabył (słowa, głosy, dobre miejsce)
            if b.zyje() and rodzice:
                for r in rodzice:
                    if str(r.miejsce) in blisko:
                        b.ucz_sie_od(r)
            if b.cos is not None:
                b.cos["karmione"] = round(b.karmione, 2)
                b.cos["energia"] = round(b.energia, 2)
                b.cos["nauczone"] = getattr(b, "nauczone", 0)
            do_slownika(swiat, b)
            do_korpusu(swiat, b, tu, blisko, zywi)
            if b.czyn and b.czyn_do is not None and b.zyje():
                if b.czyn not in b.zrozumiane:
                    b.zrozumiane.add(b.czyn)
                    zdarzenie(swiat, "zrozumienie", nr=b.nr, od=b.czyn_do, czyn=b.czyn, cel=b.czyn_cel)
                # wykonanie czynu: czasownik × przedmiot (składane znaczenia) albo czyny wrodzone (chodź do mnie, bronić)
                cz = b.czyn
                v = getattr(b, "czyn_verb", None)        # świat wykonuje czyn po znaczniku, nie po napisie:
                if v is None:                            # dzięki temu nazwy mogą być w dowolnym języku
                    v = ("idz" if cz.startswith("idź") or cz in ("chodź do mnie", "bronić", "chodź, tu pokarm")
                         else "unikaj" if cz.startswith("unikaj") or cz == "uwaga"
                         else "zapamietaj" if cz.startswith("zapamiętaj")
                         else "odpowiedz" if cz.startswith("odpowiedz") else None)   # stare światy: czasownik z napisu
                ob, cel = getattr(b, "czyn_obiekt", None), b.czyn_cel
                if v in ("idz", "chodz", "bron"):
                    if ob == "laka" and str(cel) in swiat["miejsca"]:
                        m_ = b.mapa.setdefault(pora_roku(swiat), {})          # usłyszana łąka wchodzi do mapy (z drugiej ręki)
                        m_[str(cel)] = max(m_.get(str(cel), 0.0), word.KOSZT_TRWANIA * 2)
                        dokad_ = str(cel)
                    else:
                        kto = next((x for x in zywi if x.nr == (cel if ob == "istota" else b.czyn_do) and x.zyje()), None)
                        dokad_ = str(kto.miejsce) if kto is not None else None
                    if dokad_ is not None and dokad_ != str(b.miejsce) and not b.ruszyl:
                        k_ = krok_do(swiat, b.miejsce, dokad_)
                        if k_ is not None and b.energia > word.KOSZT_RUCHU:
                            b.krok(k_)
                elif v == "unikaj":
                    if ob == "laka":
                        b.unikaj[str(cel)] = b.wiek + word.UNIKANIE
                    else:
                        kogo = int(cel) if ob == "istota" else int(b.czyn_do)
                        b.unikani[kogo] = b.wiek + word.UNIKANIE
                        tam = next((x for x in zywi if x.nr == kogo and x.zyje()), None)
                        if tam is not None and str(tam.miejsce) == str(b.miejsce) and not b.ruszyl and b.energia > word.KOSZT_RUCHU:
                            b.krok(random.choice(swiat["miejsca"][str(b.miejsce)]["s"]))   # odsuwa się od unikanej
                elif v == "zapamietaj":
                    if ob == "laka" and str(cel) in swiat["miejsca"]:
                        m_ = b.mapa.setdefault(pora_roku(swiat), {})
                        m_[str(cel)] = max(m_.get(str(cel), 0.0), word.KOSZT_TRWANIA * 2)
                    else:
                        kogo = int(cel) if ob == "istota" else int(b.czyn_do)
                        b.bliscy[kogo] = b.bliscy.get(kogo, 0) + 1              # zapamiętana istota: krok do bliskości
                elif v == "odpowiedz":
                    b.odpowiada = b.czyn_do                                     # odpowie własnym głosem (w tym cyklu już wydała mowę: od następnego)
                    b.bliscy[int(b.czyn_do)] = b.bliscy.get(int(b.czyn_do), 0) + 1
            if dziecko:
                nowi.append(dziecko)
        zywi.sort(key=lambda b: b.nr)
        # rozmowy sytych: dorośli swoi w jednym miejscu, nie jedzący i nie śpiący, wymieniają nabyte
        wg_m = {}
        for b in zywi:
            if b.zyje() and b.energia > word.SYTOSC * 0.8 and b.wiek >= word.DZIECINSTWO and b.zjadl < word.KOSZT_TRWANIA and (b.cos or {}).get("tryb") == "jawa":
                wg_m.setdefault(str(b.miejsce), []).append(b)
        for k, grupa in wg_m.items():
            random.shuffle(grupa)
            for b in grupa:
                # swoi wymieniają drobiazgi; w czasie wolnym gawędzi się też z obcym (nie z kłamcą), i z gawęd rodzi się bliskość
                partnerzy = [x for x in grupa if x is not b and (b.swoj(x) or (b.gawedzi and x.nr not in b.klamcy))]
                if partnerzy and random.random() < 0.2 + 0.6 * b.towarzyskosc:   # towarzyska zagaduje częściej
                    x = random.choice(partnerzy)
                    co = b.rozmowa_z(x) if b.swoj(x) else None
                    if co is None and (b.gawedzi or x.gawedzi):
                        co = "gaweda"
                        b.bliscy[x.nr] = b.bliscy.get(x.nr, 0) + (2 if b.towarzyskosc > 0.7 else 1)   # bardzo towarzyska zbliża się w dwa razy mniej gawęd
                        x.bliscy[b.nr] = x.bliscy.get(b.nr, 0) + (2 if x.towarzyskosc > 0.7 else 1)
                        if b.bliscy[x.nr] == word.BLISKOSC and not b.swoj_z_rdzenia(x):
                            zdarzenie(swiat, "bliskosc", nr=b.nr, z=x.nr, miejsce=k)
                    if co:
                        b.rozmowy = getattr(b, "rozmowy", 0) + 1
                        if b.cos is not None:
                            b.cos["rozmowa"] = {"z": x.nr, "co": co}
        # terytorium: kto stoi na cudzej łące, musi się zmierzyć z obroną albo odejść
        for b in zywi:
            b.staz += 1
            b.mowa["alarm"] = False
        wg_miejsca = {}
        for b in zywi:
            if b.zyje():
                wg_miejsca.setdefault(str(b.miejsce), []).append(b)
        for k, grupa in wg_miejsca.items():
            if len(grupa) < 2 or swiat["miejsca"][k]["g"] < 0.3:
                continue
            # przybysz: stanął tu w tym cyklu. Zdemaskowany: cykl temu mówił „tylko przechodzę”, a został.
            przybysze = [b for b in grupa if b.staz <= 1 or (b.staz == 2 and b.deklarowal)]
            for intruz in przybysze:
                obroncy = [x for x in grupa if x is not intruz and x.staz > 1 and not x.swoj(intruz) and x.energia > word.SYTOSC / 3]
                if not obroncy:
                    continue
                if intruz.staz == 2 and intruz.przechodzil:
                    pass                                                   # uczciwy przechodzień, który utknął: zwykły przybysz, bez wiary
                elif intruz.staz == 2:
                    # kłamstwo wyszło na jaw: obrońcy zapamiętują kłamcę (nabyte), już mu nie uwierzą. Dalej jak z intruzem.
                    for x in obroncy:
                        x.klamcy.add(intruz.nr)
                        x.przylapala = (intruz.nr, list(intruz.glos))         # jutro będzie o tym mówić: głos kłamcy w swoim głosie
                    zdarzenie(swiat, "klamstwo", nr=intruz.nr, miejsce=k, obroncy=[x.nr for x in obroncy])
                elif intruz.deklaruje:
                    # „tylko przechodzę”: każdy obrońca wierzy albo nie (gen ufności); znanemu kłamcy nikt nie wierzy
                    wierza = all(intruz.nr not in x.klamcy and random.random() < x.ufnosc for x in obroncy)
                    if wierza:
                        zdarzenie(swiat, "przejscie", nr=intruz.nr, miejsce=k, obroncy=[x.nr for x in obroncy], prawda=intruz.przechodzi)
                        continue
                obrona = sum(x.sila * x.kondycja() for x in obroncy)
                atak = intruz.sila * intruz.kondycja()
                for x in obroncy:
                    x.mowa["alarm"] = True                            # obrońcy alarmują swoich
                if atak < obrona * word.ODWROT:
                    # obcy jest słabszy: odchodzi bez walki (gołąb)
                    cel = str(intruz.poprzednie) if intruz.poprzednie is not None and str(intruz.poprzednie) in swiat["miejsca"] else random.choice(swiat["miejsca"][k]["s"])
                    intruz.krok(cel)
                    intruz.bolalo = (k, zapach(swiat, k), 2)
                    zdarzenie(swiat, "odwrot", nr=intruz.nr, miejsce=k, obroncy=[x.nr for x in obroncy])
                else:
                    # starcie: obie strony płacą; słabsza strona ustępuje (jastrząb)
                    intruz.energia -= 0.5 + 0.5 * obrona
                    for x in obroncy:
                        x.energia -= (0.3 + 0.3 * atak) / len(obroncy)
                    if atak > obrona:
                        for x in obroncy:
                            if x.zyje():
                                x.krok(random.choice(swiat["miejsca"][k]["s"]))
                                x.bolalo = (k, zapach(swiat, k), 2)
                        zdarzenie(swiat, "starcie", nr=intruz.nr, miejsce=k, obroncy=[x.nr for x in obroncy], wygral="intruz")
                    else:
                        if intruz.zyje():
                            intruz.krok(random.choice(swiat["miejsca"][k]["s"]))
                            intruz.bolalo = (k, zapach(swiat, k), 2)
                        zdarzenie(swiat, "starcie", nr=intruz.nr, miejsce=k, obroncy=[x.nr for x in obroncy], wygral="obrona")
        for b in zywi:
            b.deklarowal = b.deklaruje and b.zyje()     # do wykrycia kłamstwa w następnym cyklu
            b.przechodzil = b.przechodzi
        # dziennik dopiero teraz: po rozmowach i starciach, z energią i losem po wszystkim
        for b in cykl_istoty:
            if b.cos is not None:
                b.cos["energia"] = round(b.energia, 2)
                b.cos["zyje"] = b.energia > 0
                b.cos["miejsce"] = b.miejsce
                wpisy.append(json.dumps({"cykl_swiata": swiat["cykl_swiata"], "czas": time.time(), **b.cos}, ensure_ascii=False))
        if zywi and swiat["cykl_swiata"] % 50 == 0 and len(zywi) > 8:
            # bariera gatunkowa i liczba gatunków, liczone z populacji: próg to piąta część typowego
            # podobieństwa rdzeni. Rozjazd musi być wyraźny na tle tego, jak spójna jest reszta.
            probka = random.sample(zywi, min(80, len(zywi)))
            m_ = min(len(x.K) for x in probka)
            wek = [x.rdzen_wektor(m_) for x in probka]
            pary = [float(np.dot(wek[i], wek[j])) for i in range(len(wek)) for j in range(i + 1, len(wek))]
            pary.sort()
            mediana = pary[len(pary) // 2] if pary else 0.0
            word.PROG_GATUNKU = max(0.0, 0.2 * mediana)
            swiat["prog_gatunku"] = round(word.PROG_GATUNKU, 4)
            grupy = []
            for v in wek:
                if not any(float(np.dot(v, g)) >= word.PROG_GATUNKU for g in grupy):
                    grupy.append(v)
            swiat["gatunkow"] = len(grupy)
            zdarzenie(swiat, "gatunki", ile=len(grupy), probka=len(probka), prog=swiat["prog_gatunku"])
        # drapieżnik: druga siła selekcji obok głodu. Przychodzi tam, gdzie ktoś jest, zostaje kilka cykli i poluje.
        # W gromadzie bezpieczniej (rozcieńczenie i czujność), samotnik ginie — dopiero teraz stado ma sens.
        drap = swiat.setdefault("drapiezniki", {})
        for k in list(drap):
            drap[k] -= 1
            if drap[k] <= 0:
                del drap[k]
                zdarzenie(swiat, "drapieznik_odszedl", miejsce=k)
        if zywi and random.random() < DRAPIEZNIK:
            gdzie = {}
            for b in zywi:
                gdzie[str(b.miejsce)] = gdzie.get(str(b.miejsce), 0) + 1
            gdzie = {k: v for k, v in gdzie.items() if v >= DRAPIEZNIK_MIN}       # pustkowia go nie interesują
            cel = random.choices(list(gdzie), weights=list(gdzie.values()))[0] if gdzie else None
            if cel is not None and cel not in drap:
                drap[cel] = random.randint(*POSTOJ)
                zdarzenie(swiat, "drapieznik", miejsce=cel, ilu=gdzie[cel])
                print(f"drapieżnik na łące {cel} ({gdzie[cel]} istot).", flush=True)
        if drap:
            w_miejscu = {}
            for b in zywi:
                if str(b.miejsce) in drap and b.zyje():
                    w_miejscu.setdefault(str(b.miejsce), []).append(b)
            for k, stado in w_miejscu.items():
                czujni = sum(1 for x in stado if (x.mowa or {}).get("alarm") or (x.mowa or {}).get("krzyk"))
                if random.random() >= LOWY * (0.5 if czujni else 1.0):
                    continue                                              # czujne stado częściej odstrasza
                # jeden drapieżnik bierze jedną ofiarę na cykl: w gromadzie ryzyko rozkłada się na wszystkich
                # (efekt rozcieńczenia), a wybiera raczej słabą, chorą albo głodną
                wagi = [(1.2 - 0.6 * x.sila) * (1.6 if x.chora else 1.0) * (1.4 if x.energia < word.SYTOSC / 2 else 1.0)
                        * (1.0 + x.ozdoba) for x in stado]                      # ozdobna rzuca się w oczy: płaci za to dwa razy
                b = random.choices(stado, weights=wagi)[0]
                b.energia -= 0.2 * b.energia + 0.3                        # szarpnięcie: rana i utrata sił, nie cios w serce.
                                                                          # Koniec zawsze jest brakiem energii: ginie tylko ta, która już była na granicy
                b.bolalo = (str(b.miejsce), zapach(swiat, b.miejsce), 2)
                b.mowa["alarm"] = True                                    # krzyczy; kto usłyszy, ten wie
                if b.zyje():
                    zdarzenie(swiat, "atak", nr=b.nr, miejsce=k, ilu=len(stado))
                else:
                    zdarzenie(swiat, "upolowana", nr=b.nr, miejsce=k, ilu=len(stado))
                    print(f"drapieżnik dopadł byt {b.nr}; nie starczyło mu sił (łąka {k}, {len(stado)} istot).", flush=True)
        # choroby: rzadki wybuch nowego szczepu, zarażanie przez bliskość, przebieg i odporność nabyta.
        # Cena życia w tłumie: kto stoi w gromadzie, ten je bezpieczniej, ale choruje częściej.
        if zywi and random.random() < WYBUCH:
            # każdy szczep jest inny: zaraźliwość, ciężkość i długość losowane z rozkładów o długim ogonie,
            # więc większość jest łagodna, ale raz na jakiś czas trafi się coś, co wygarnie połowę łąki
            szczep = int(swiat.get("szczep_nr", 0)) + 1
            swiat["szczep_nr"] = szczep
            zar = round(min(0.35, 0.03 * math.exp(random.expovariate(1.6))), 3)
            koszt = round(min(2.5, 0.2 * math.exp(random.expovariate(1.5))), 2)
            dlugo = random.randint(3, 14)
            zdrowienie = round(random.uniform(0.04, 0.22), 3)
            swiat.setdefault("szczepy", {})[str(szczep)] = {"zarazliwosc": zar, "koszt": koszt, "dlugo": dlugo, "zdrowienie": zdrowienie}
            pierwszy = random.choice(zywi)
            pierwszy.chora = (szczep, 0, koszt)
            swiat.setdefault("ogniska", {})[str(pierwszy.miejsce)] = {"szczep": szczep, "do": swiat["cykl_swiata"] + random.randint(*OGNISKO)}
            zdarzenie(swiat, "zaraza", nr=pierwszy.nr, szczep=szczep, miejsce=str(pierwszy.miejsce),
                      zarazliwosc=zar, koszt=koszt, dlugo=dlugo, zdrowienie=zdrowienie)
            ostrosc = "łagodny" if koszt < 0.6 and zar < 0.1 else ("ostry" if koszt > 1.5 or zar > 0.25 else "zwykły")
            print(f"zaraza: szczep {szczep} ({ostrosc}: zaraźliwość {zar}, ciężkość {koszt}, {dlugo} cykli) od bytu {pierwszy.nr}.", flush=True)
        ogniska = swiat.setdefault("ogniska", {})
        for k in list(ogniska):
            if ogniska[k]["do"] <= swiat["cykl_swiata"]:
                zdarzenie(swiat, "ognisko_wygaslo", miejsce=k, szczep=ogniska[k]["szczep"])
                del ogniska[k]
        limit_ognisk = max(3, int(OGNISK_MAX * len(swiat.get("miejsca") or {1: 1})))
        for k in list(ogniska):                               # ognisko rozlewa się na sąsiednie łąki samo
            if len(ogniska) < limit_ognisk and random.random() < ROZLEWA:
                sasiedzi = (swiat["miejsca"].get(k) or {}).get("s") or []
                wolne = [x for x in sasiedzi if str(x) not in ogniska]
                if wolne:
                    n = str(random.choice(wolne))
                    ogniska[n] = {"szczep": ogniska[k]["szczep"], "do": swiat["cykl_swiata"] + random.randint(*OGNISKO)}
                    zdarzenie(swiat, "ognisko", miejsce=n, szczep=ogniska[k]["szczep"], od=None)
        chorzy_tu = {}
        for b in zywi:
            if b.chora:
                chorzy_tu.setdefault(str(b.miejsce), []).append(b.chora[0])
                # chora roznosi zarazę: łąka, na której stoi, może stać się nowym ogniskiem
                if str(b.miejsce) not in ogniska and len(ogniska) < limit_ognisk and random.random() < ROZWLEKA:
                    ogniska[str(b.miejsce)] = {"szczep": b.chora[0], "do": swiat["cykl_swiata"] + random.randint(*OGNISKO)}
                    zdarzenie(swiat, "ognisko", miejsce=str(b.miejsce), szczep=b.chora[0], od=b.nr)
        for b in zywi:
            if b.chora:
                sz, ile = b.chora[0], b.chora[1] + 1
                opis = (swiat.get("szczepy") or {}).get(str(sz), {})
                if ile >= opis.get("dlugo", CHORUJE_MIN) and random.random() < opis.get("zdrowienie", 0.06) + 0.30 * b.odpornosc:
                    b.przechorowane.add(sz)
                    b.chora = None
                    zdarzenie(swiat, "wyzdrowienie", nr=b.nr, szczep=sz, cykli=ile)
                else:
                    b.chora = (sz, ile, opis.get("koszt", word.KOSZT_CHOROBY))
                continue
            tu = list(chorzy_tu.get(str(b.miejsce)) or [])
            ogn = ogniska.get(str(b.miejsce))
            if ogn:
                tu += [ogn["szczep"]] * 2                      # skażona łąka zaraża sama: rezerwuar liczy się jak dwoje chorych
            if not tu:
                continue
            for sz in set(tu):
                if sz in b.przechorowane:
                    continue                                   # przechorowana: tego szczepu już się nie boi
                zar = ((swiat.get("szczepy") or {}).get(str(sz), {})).get("zarazliwosc", ZARAZLIWOSC)
                p = 1.0 - (1.0 - zar * (1.0 - b.odpornosc)) ** tu.count(sz)
                if random.random() < min(0.95, p):
                    b.chora = (sz, 0, ((swiat.get("szczepy") or {}).get(str(sz), {})).get("koszt", word.KOSZT_CHOROBY))
                    zdarzenie(swiat, "zarazila_sie", nr=b.nr, szczep=sz, miejsce=str(b.miejsce))
                    break
        zmarli = [b for b in zywi if not b.zyje()]
        zywi = [b for b in zywi if b.zyje()] + nowi
        for b in zmarli:
            swiat["zmarli"].append(wpis_zmarlej(b, swiat))
            print(f"byt {b.nr} umarł w wieku {b.wiek} cykli.", flush=True)
            zdarzenie(swiat, "smierc", nr=b.nr, wiek=b.wiek, pokolenie=b.pokolenie)
        for b in nowi:
            b.urodzony_w_cyklu = swiat["cykl_swiata"]
            print(f"cud: byt {b.nr}, pokolenie {b.pokolenie}, genów {len(b.K)}.", flush=True)
            zdarzenie(swiat, "narodziny", nr=b.nr, pokolenie=b.pokolenie, rodzic=b.rodzic, rodzic2=b.rodzic2, geny=int(len(b.K)))
            przybylo = getattr(b, "przybylo_genow", 0)
            if przybylo:                                   # kręgosłup dłuższy albo krótszy niż u matki
                zdarzenie(swiat, "duplikacja" if przybylo > 0 else "utrata_genu", nr=b.nr, rodzic=b.rodzic, geny=int(len(b.K)), zmiana=int(przybylo))
                print(f"{'duplikacja' if przybylo > 0 else 'utrata genu'}: byt {b.nr} ma {len(b.K)} genów.", flush=True)
        # bez przyszłości: gdy została jedna płeć (albo jedna istota), dzieci już nie będzie.
        # Taki świat kończy bieg od razu; ostatnie istoty zostają zapisane jako „ostatnie”, nie umarły z głodu.
        plcie = {b.plec for b in zywi}
        if zywi and len(plcie) < 2:
            ostatni = [b.nr for b in zywi]
            swiat["koniec"] = {"powod": "jedna_plec", "plec": zywi[0].plec, "ostatni": ostatni, "cykl": swiat["cykl_swiata"]}
            zdarzenie(swiat, "koniec", powod="jedna_plec", plec=zywi[0].plec, ostatni=ostatni)
            for b in zywi:
                swiat["zmarli"].append(wpis_zmarlej(b, swiat, ostatnia=True))
            print(f"świat bez przyszłości: została jedna płeć ({', '.join(map(str, ostatni))}). koniec.", flush=True)
            zywi = []
        swiat["kierunek_pokarmu"] = word.KIERUNEK_POKARMU
        swiat["licznik"] = Byt.licznik
        swiat["zywi"] = [byt_do_slownika(b) for b in zywi]
        swiat["wygasla"] = not zywi
        swiat["pora"] = pora_roku(swiat)
        swiat["noc"] = (swiat["cykl_swiata"] % DOBA) >= DOBA * 2 // 3
        zd = swiat.pop("_zdarzenia", [])
        zapisz(swiat)
        with open(DZIENNIK, "a") as f:
            f.write("\n".join(wpisy) + ("\n" if wpisy else ""))
        if zd:
            with open(ZDARZENIA, "a") as f:
                f.write("\n".join(json.dumps(x, ensure_ascii=False) for x in zd) + "\n")
        kp = swiat.pop("_korpus", [])
        if kp:
            with open(KORPUS, "a") as f:
                f.write("\n".join(json.dumps(x, ensure_ascii=False) for x in kp) + "\n")
        if not zywi:
            print("linia wygasła.", flush=True)
            break
        time.sleep(max(0.0, CYKL_SEKUND - (time.time() - start)))


if __name__ == "__main__":
    main()
