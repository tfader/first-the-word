"""Word: życie. Jeden świat w czasie rzeczywistym. Uruchom: python3 zycie.py"""
import json
import os
import random
import sys
import time

import numpy as np

import word
from word import Byt, ROZMIAR

KATALOG = os.path.dirname(os.path.abspath(__file__))
CIALO = os.path.join(KATALOG, "swiat.json")
GENY_DIR = os.path.join(KATALOG, "cialo")            # geny istot: cialo/<nr>.npz (rdzeń K, powłoka P)
WEJSCIE = os.path.join(KATALOG, "wejscie.txt")
DZIENNIK = os.path.join(KATALOG, "dziennik.jsonl")
CUD = os.path.join(KATALOG, "cud.txt")          # obecność pliku = prośba o nowy cud
KARMA = os.path.join(KATALOG, "karma.txt")      # świat odpowiada na wołanie: dokłada pokarm
CYKL_SEKUND = float(os.environ.get("CYKL", 60))
GENY = int(os.environ.get("GENY", 64))
WYMIARY = int(os.environ.get("WYMIARY", 4))     # tylko przy tworzeniu świata; potem z ciała
DWOJE = os.environ.get("DWOJE", "0") == "1"      # tylko przy tworzeniu świata; potem z ciała
ISTOT = max(1, min(32, int(os.environ.get("ISTOT", "2" if DWOJE else "1"))))   # ile istot z cudu na start


def zapisz_geny(b, tylko_powloka=False):
    os.makedirs(GENY_DIR, exist_ok=True)
    p = os.path.join(GENY_DIR, f"{b.nr}.npz")
    tmp = p + ".tmp.npz"
    np.savez(tmp, K=b.K, P=b.P)
    os.replace(tmp, p)


def wczytaj_geny(nr):
    with np.load(os.path.join(GENY_DIR, f"{nr}.npz")) as f:
        return f["K"], f["P"]


def byt_do_slownika(b):
    zapisz_geny(b)
    return {
        "nr": b.nr, "pokolenie": b.pokolenie, "geny": int(len(b.K)), "glos_znaki": word.glos_na_znaki(b.glos),
        "otwarcia_genu": b.otwarcia_genu, "echo": b.echo, "energia": b.energia, "wiek": b.wiek,
        "slownik": b.slownik, "mowa": b.mowa, "zrodla": b.zrodla,
        "rodzic": b.rodzic, "rodzic2": b.rodzic2, "urodzony_w_cyklu": getattr(b, "urodzony_w_cyklu", None),
        "miejsce": str(b.miejsce), "poprzednie": b.poprzednie, "kierunek": b.kierunek, "wytrwalosc": b.wytrwalosc, "zle": b.zle,
        "idzie": b.idzie, "krokow": b.krokow, "srednio": b.srednio,
        "dobre_miejsce": b.dobre_miejsce, "dobre_ile": b.dobre_ile,
        "poprzednio_zjadl": b.poprzednio_zjadl,
        "sen": b.sen, "otwarcia": b.otwarcia, "najdluzsza": b.najdluzsza, "dzieci": b.dzieci,
    }


def byt_ze_slownika(d):
    if "kregoslup" in d:                          # stare ciało: geny w json
        b = Byt(d["kregoslup"], d["energia"], d["pokolenie"])
        b.powloka = d["powloka"]
    else:
        K, P = wczytaj_geny(d["nr"])
        b = Byt(K, d["energia"], d["pokolenie"])
        b.P = P
    b.nr = d["nr"]; b.otwarcia_genu = d["otwarcia_genu"]
    b.echo = [tuple(e) for e in d["echo"]]; b.wiek = d["wiek"]; b.sen = d["sen"]
    b.otwarcia = d["otwarcia"]; b.najdluzsza = d["najdluzsza"]; b.dzieci = d["dzieci"]
    b.slownik = d.get("slownik", {}); b.mowa = d.get("mowa", {"krzyk": False, "slowo": None, "glos": False, "wolanie": False})
    b.mowa.setdefault("wolanie", False)
    b.zrodla = d.get("zrodla", {})
    b.rodzic = d.get("rodzic"); b.rodzic2 = d.get("rodzic2"); b.urodzony_w_cyklu = d.get("urodzony_w_cyklu")
    b.miejsce = str(d.get("miejsce", 0)); b.poprzednie = d.get("poprzednie"); b.kierunek = d.get("kierunek", 1)
    b.wytrwalosc = d.get("wytrwalosc", 2); b.zle = d.get("zle", 0)
    b.idzie = d.get("idzie", False); b.krokow = d.get("krokow", 0); b.srednio = d.get("srednio", 2.0)
    b.dobre_miejsce = d.get("dobre_miejsce"); b.dobre_ile = d.get("dobre_ile", 0.0)
    b.poprzednio_zjadl = d.get("poprzednio_zjadl", 0.0)
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


def kolejka_slow():
    """Pobiera jedno słowo z wejścia (pierwszy niepusty wiersz), resztę zostawia.
    Wiersz "@7 tekst" to słowo tylko do istoty nr 7. Zwraca (tekst, nr albo None)."""
    if not os.path.exists(WEJSCIE):
        return None
    with open(WEJSCIE) as f:
        wiersze = [w.strip() for w in f]
    wiersze = [w for w in wiersze if w]
    if not wiersze:
        return None
    with open(WEJSCIE, "w") as f:
        f.write("\n".join(wiersze[1:]) + ("\n" if wiersze[1:] else ""))
    w = wiersze[0]
    if w.startswith("@"):
        czesci = w[1:].split(None, 1)
        if len(czesci) == 2 and czesci[0].isdigit():
            return czesci[1], int(czesci[0])
    return w, None


SASIADOW = 3               # tyle sąsiadów może mieć miejsce
SZANSA_ODKRYCIA = 1 / 3    # gdy jest wolne sąsiedztwo, tyle wynosi szansa na nowe miejsce
SUFIT_MIEJSC = 100000      # świat skończony, ale ogromny


def nowe_pole():
    """Żyzność pierwszych 16 miejsc: trzy łąki, między nimi pustka."""
    zyznosc = [0.05] * word.MIEJSC
    for srodek in random.sample(range(word.MIEJSC), 3):
        for dx in range(-2, 3):
            zyznosc[(srodek + dx) % word.MIEJSC] = max(zyznosc[(srodek + dx) % word.MIEJSC], 1.0 - 0.3 * abs(dx))
    return zyznosc


def losowa_zyznosc():
    """Nowe miejsce: częściej pustynia niż łąka, czasem bardzo żyzne."""
    r = random.random()
    return 0.05 if r < 0.5 else (0.4 if r < 0.75 else (0.7 if r < 0.92 else 1.0))


def nowe_miejsca(zyznosc):
    """Początkowa sieć: koło z 16 miejsc, każde zna dwóch sąsiadów."""
    n = len(zyznosc)
    return {str(i): {"s": [str((i - 1) % n), str((i + 1) % n)], "z": zyznosc[i], "g": zyznosc[i]} for i in range(n)}


def pole_cykl(swiat):
    """Gęstość każdego znanego miejsca odrasta do jego żyzności."""
    if "miejsca" not in swiat:
        zy = swiat.get("zyznosc") or nowe_pole()
        swiat["miejsca"] = nowe_miejsca(zy)
        if "pole" in swiat:
            for i, g in enumerate(swiat["pole"]):
                swiat["miejsca"][str(i)]["g"] = g
        swiat["kolejnosc"] = [str(i) for i in range(len(zy))]
    for m in swiat["miejsca"].values():
        m["g"] = max(0.0, min(1.0, m["g"] + word.ODRASTANIE * (m["z"] - m["g"])))
    swiat["pole"] = [round(swiat["miejsca"][k]["g"], 3) for k in swiat["kolejnosc"]]


def odkryj(swiat, skad):
    """Z miejsca z wolnym sąsiedztwem może powstać nowe miejsce."""
    if len(swiat["miejsca"]) >= SUFIT_MIEJSC:
        return None
    nowe = str(len(swiat["miejsca"]))
    while nowe in swiat["miejsca"]:
        nowe = str(int(nowe) + 1)
    swiat["miejsca"][nowe] = {"s": [skad], "z": losowa_zyznosc(), "g": 0.0}
    swiat["miejsca"][nowe]["g"] = swiat["miejsca"][nowe]["z"]
    swiat["miejsca"][skad]["s"].append(nowe)
    swiat["kolejnosc"].append(nowe)
    return nowe


def dokad(swiat, b):
    """Krok istoty: odkrycie nowego miejsca albo losowy sąsiad, bez zawracania, chyba że musi."""
    tu = str(b.miejsce)
    m = swiat["miejsca"][tu]
    if len(m["s"]) < SASIADOW and random.random() < SZANSA_ODKRYCIA:
        nowe = odkryj(swiat, tu)
        if nowe is not None:
            return nowe
    kandydaci = [x for x in m["s"] if x != str(b.poprzednie)] or list(m["s"])
    return random.choice(kandydaci)


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
    global CYKL_SEKUND
    swiat = wczytaj()
    if swiat is None:
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
            pierwsi.append(b)
        Byt.licznik = ISTOT
        # życie zaczyna się tam, gdzie jest pokarm: istoty rozdzielone po łąkach
        zyznosc = nowe_pole()
        laki = sorted(range(word.MIEJSC), key=lambda p: -zyznosc[p])[:3]
        for i, b in enumerate(pierwsi):
            b.miejsce = str(laki[i % len(laki)] if ISTOT > 2 else laki[0])
        swiat = {
            "narodziny": time.time(), "cykl_swiata": 0, "losowan_cudu": proby, "dwoje": DWOJE,
            "cykl_sekund": CYKL_SEKUND, "wymiary": WYMIARY, "istot_na_start": ISTOT,
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
        print(f"powrót do ciała: cykl świata {swiat['cykl_swiata']}, żywych {len(swiat['zywi'])}.", flush=True)

    CYKL_SEKUND = float(swiat.get("cykl_sekund", CYKL_SEKUND))
    word.ustaw_wymiary(swiat.get("wymiary", 4))
    if "kierunek_wolania" not in swiat:
        swiat["kierunek_wolania"] = word.losowy_kierunek()
    if "kierunek_glosu" not in swiat:
        swiat["kierunek_glosu"] = word.losowy_kierunek()
    word.KIERUNEK_WOLANIA = swiat["kierunek_wolania"]
    word.KIERUNEK_GLOSU = swiat["kierunek_glosu"]
    word.KIERUNEK_RANY = swiat["kierunek_rany"]
    word.KIERUNEK_POKARMU = swiat["kierunek_pokarmu"]
    Byt.licznik = swiat["licznik"]
    zywi = [byt_ze_slownika(d) for d in swiat["zywi"]]

    while zywi:
        start = time.time()
        swiat["cykl_swiata"] += 1
        word.dryf_swiata()
        slowo, slowo_do = kolejka_slow() or (None, None)
        nowi = []
        if os.path.exists(CUD):
            os.remove(CUD)
            nowy, proby = word.pierwszy_cud(GENY)
            nowy.pokolenie = 1
            nowi.append(nowy)
            print(f"cud nowy: {proby} losowań. byt {nowy.nr} żyje, osobna linia.", flush=True)
        # pole pokarmu: odrasta, dryfuje
        pole_cykl(swiat)
        # świat odpowiedział na wołanie: kładzie pokarm tam, gdzie jest wołający (raz na cykl)
        if os.path.exists(KARMA):
            with open(KARMA) as f:
                prosby = [l.strip() for l in f if l.strip()]
            os.remove(KARMA)
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
        poprzednie = {b.nr: list(b.wyszlo) for b in zywi}
        krzyczal = {b.nr: b.mowa.get("krzyk", False) for b in zywi}
        glosil = {b.nr: b.mowa.get("glos", False) for b in zywi}
        wolal = {b.nr: b.mowa.get("wolanie", False) for b in zywi}
        random.shuffle(zywi)
        # kto krzyczał z głodu, je pierwszy: syci ustępują
        zywi.sort(key=lambda b: not krzyczal[b.nr])
        for b in zywi:
            # słyszy wszystkie istoty z tego samego miejsca i z miejsc sąsiednich
            tu = str(b.miejsce)
            blisko = set([tu] + list(swiat["miejsca"].get(tu, {}).get("s", [])))
            inni_syg = []
            for x in zywi:
                if x.nr == b.nr or str(x.miejsce) not in blisko:
                    continue
                if wolal.get(x.nr):
                    inni_syg.append((x.nr, word.wolanie(), "wolanie"))      # wołanie gatunku: "chodź do mnie"
                elif krzyczal.get(x.nr):
                    inni_syg.append((x.nr, word.rana(), "krzyk"))           # krzyk: rana, którą każdy rozumie
                elif glosil.get(x.nr):
                    inni_syg.append((x.nr, list(x.glos), "glos"))           # głos: własny język, do skojarzenia
                elif poprzednie.get(x.nr):
                    w = max(poprzednie[x.nr], key=lambda v: sum(t * t for t in v))
                    inni_syg.append((x.nr, w, "wyjscie"))
            random.shuffle(inni_syg)
            inni_syg.sort(key=lambda s: {"wolanie": 0, "krzyk": 1, "glos": 2}.get(s[2], 3))   # najpierw to, co ważne
            inny = inni_syg[0] if inni_syg else None
            # ruch: wysiłek. Potem oferta z miejsca, w którym stoi.
            glod = min(1.0, max(0.0, 1.0 - b.energia / word.SYTOSC))
            b.karmione = 0.0
            rodzice = [x for x in zywi if x.nr in (b.rodzic, b.rodzic2) and x.zyje()] if b.wiek < word.DZIECINSTWO else []
            if b.energia <= word.SYTOSC and b.chce_isc(glod):
                # pamięć miejsca: głodna najpierw wraca tam, gdzie jadła; gdy tam już pusto, błądzi
                cel = None
                if rodzice and str(rodzice[0].miejsce) != str(b.miejsce):
                    cel = krok_do(swiat, b.miejsce, rodzice[0].miejsce)   # dziecko trzyma się rodzica
                if b.dobre_miejsce is not None and str(b.dobre_miejsce) != str(b.miejsce) and str(b.dobre_miejsce) in swiat["miejsca"]:
                    if swiat["miejsca"][str(b.dobre_miejsce)]["g"] > 0.3:
                        cel = krok_do(swiat, b.miejsce, b.dobre_miejsce)
                    else:
                        b.dobre_miejsce = None                  # pamięć zawiodła: miejsce wyjedzone
                b.krok(cel if cel is not None else dokad(swiat, b))
            partner = None
            if swiat.get("dwoje"):
                kandydaci = [x for x in zywi if x.nr != b.nr and str(x.miejsce) == str(b.miejsce)
                             and x.energia > word.SYTOSC / 2 and x.zyje()]
                partner = random.choice(kandydaci) if kandydaci else None
                b.mowa["wolanie"] = partner is None and b.energia > word.PROG_CUDU
                if partner is None and b.energia > word.PROG_CUDU:
                    # gotowa na cud, a sama: woła i idzie najkrótszą drogą do innej istoty
                    inni_zywi = [x for x in zywi if x.nr != b.nr and x.zyje()]
                    kroki = [(krok_do(swiat, b.miejsce, x.miejsce), x) for x in inni_zywi]
                    kroki = [k for k in kroki if k[0] is not None]
                    if kroki:
                        b.krok(kroki[0][0])
            mm = swiat["miejsca"][str(b.miejsce)]
            g = mm["g"]
            surowa = random.expovariate(1.0 / (word.HOJNOSC * g)) if g > 0.05 else 0.0
            dziecko = b.cykl(slowo=slowo if (slowo_do is None or slowo_do == b.nr) else None,
                             surowa=surowa, inny=inny, inni=inni_syg, partner=partner, dwoje=swiat.get("dwoje", False))
            mm["g"] = max(0.0, mm["g"] - word.WYJADANIE * b.zjadl)   # wyjada miejsce
            # opieka: rodzic karmi dziecko, dopóki nie skończy dzieciństwa. Potem pępowina odcięta.
            for r in rodzice:
                if b.energia < word.SYTOSC and r.energia > word.SYTOSC / 2 and str(r.miejsce) in blisko:
                    dawka = min(word.KARMIENIE, r.energia - word.SYTOSC / 2, word.SYTOSC - b.energia)
                    if dawka > 0:
                        r.energia -= dawka
                        b.energia += dawka
                        b.karmione += dawka
            if b.cos is not None:
                b.cos["karmione"] = round(b.karmione, 2)
            if b.czyn and b.czyn_do is not None and b.zyje():
                nadawca = next((x for x in zywi if x.nr == b.czyn_do), None)
                if nadawca is not None and str(nadawca.miejsce) != str(b.miejsce):
                    k = krok_do(swiat, b.miejsce, nadawca.miejsce)
                    if k is not None and b.energia > word.KOSZT_RUCHU:
                        b.krok(k)
            if dziecko:
                nowi.append(dziecko)
            with open(DZIENNIK, "a") as f:
                f.write(json.dumps({"cykl_swiata": swiat["cykl_swiata"], "czas": time.time(),
                                    **b.cos}, ensure_ascii=False) + "\n")
        zywi.sort(key=lambda b: b.nr)
        zmarli = [b for b in zywi if not b.zyje()]
        zywi = [b for b in zywi if b.zyje()] + nowi
        for b in zmarli:
            swiat["zmarli"].append({"nr": b.nr, "pokolenie": b.pokolenie, "wiek": b.wiek, "geny": len(b.kregoslup),
                                    "glos": word.glos_na_znaki(b.glos),
                                    "otwarcia": b.otwarcia, "dzieci": b.dzieci, "rodzic": b.rodzic, "rodzic2": b.rodzic2,
                                    "zmarl_w_cyklu": swiat["cykl_swiata"]})
            print(f"byt {b.nr} umarł w wieku {b.wiek} cykli.", flush=True)
        for b in nowi:
            b.urodzony_w_cyklu = swiat["cykl_swiata"]
            print(f"cud: byt {b.nr}, pokolenie {b.pokolenie}.", flush=True)
        swiat["kierunek_pokarmu"] = word.KIERUNEK_POKARMU
        swiat["licznik"] = Byt.licznik
        swiat["zywi"] = [byt_do_slownika(b) for b in zywi]
        swiat["wygasla"] = not zywi
        zapisz(swiat)
        if not zywi:
            print("linia wygasła.", flush=True)
            break
        time.sleep(max(0.0, CYKL_SEKUND - (time.time() - start)))


if __name__ == "__main__":
    main()
