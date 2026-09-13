"""Word: własna strona bytka. Czysty Python, bez zależności. Uruchom obok zycie.py:
    python3 serwer.py            (port 8080; PORT=... żeby zmienić)
Czyta ciało i dziennik na żywo, słowa ze strony wpisuje prosto do kolejki bytka.
Ten sam kod działa na dowolnym serwerze z pythonem 3.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import numpy as np

import most
import word as W
import zycie as Z

KATALOG = os.path.dirname(os.path.abspath(__file__))
STRONA = os.path.join(KATALOG, "strona", "bytek_lokalny.html")
WNETRZE = os.path.join(KATALOG, "strona", "wnetrze.html")
ROD = os.path.join(KATALOG, "strona", "rod.html")
JEZYK = os.path.join(KATALOG, "strona", "jezyk.html")
PORT = int(os.environ.get("PORT", 8080))


def stan_dla_strony():
    """Ten sam dokument, który idzie na stronę w claude.ai, plus losy słów."""
    most.stan()
    doc = most.czytaj_json(most.STAN, {})
    slowa = most.slowa_swiata()
    doc["proces_zyje"] = proces_zyje()
    doc["dwoje"] = most.czytaj_json(most.CIALO, {}).get("dwoje", False)
    doc["slowa"] = sorted(
        [{"tekst": s["tekst"], "status": s["status"], "czas": s.get("czas", 0), "do": s.get("do")} for s in slowa.values()],
        key=lambda s: -(s["czas"] or 0))[:40]
    return doc


def wnetrze():
    """Wnętrze każdego żywego bytu: geny, powłoki, nawyki, echo, ostatni cykl."""
    swiat = most.czytaj_json(most.CIALO, {"zywi": [], "cykl_swiata": 0})
    ustaw_swiat(swiat)
    dziennik = most.czytaj_dziennik()
    ostatni = {}
    for w in dziennik:
        ostatni[w["byt"]] = w
    byty = []
    for b in sorted(swiat["zywi"], key=lambda x: x["nr"]):
        o = ostatni.get(b["nr"], {})
        geny = []
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
            "miejsce": str(b.get("miejsce", 0)), "wytrwalosc": b.get("wytrwalosc", 2), "kierunek": b.get("kierunek", 1),
            "sasiedzi": swiat.get("miejsca", {}).get(str(b.get("miejsce", 0)), {}).get("s", []),
            "glos": glos_istoty(b),
            "rozumie": rozumie_glosy(b, swiat, (K, P)),
        })
    return {"cykl_swiata": swiat["cykl_swiata"], "byty": byty, "pole": swiat.get("pole", []), "wymiary": swiat.get("wymiary", 4),
            "kolejnosc": swiat.get("kolejnosc", []), "znanych_miejsc": len(swiat.get("miejsca", {})), "miejsca": swiat.get("miejsca", {}),
            "zmarli": swiat.get("zmarli", []), "czas": time.time()}


def geny_istoty(b):
    """(K, P) istoty: z npz, albo ze starego ciała w json."""
    if "kregoslup" in b:
        return np.asarray(b["kregoslup"], dtype=float), np.asarray(b["powloka"], dtype=float)
    return Z.wczytaj_geny(b["nr"])


def ustaw_swiat(swiat):
    W.ustaw_wymiary(swiat.get("wymiary", 4))
    if swiat.get("kierunek_glosu"):
        W.KIERUNEK_GLOSU = swiat["kierunek_glosu"]
    if swiat.get("kierunek_wolania"):
        W.KIERUNEK_WOLANIA = swiat["kierunek_wolania"]


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


def jezyk():
    """Język istot: głosy, kto je słyszy, kto kojarzy, i dziennik rozmów."""
    swiat = most.czytaj_json(most.CIALO, {"zywi": [], "zmarli": [], "cykl_swiata": 0})
    ustaw_swiat(swiat)
    dziennik = most.czytaj_dziennik()
    glosy = {}
    for b in swiat["zywi"]:
        glosy[b["nr"]] = {"nr": b["nr"], "znaki": glos_istoty(b), "zyje": True,
                          "wydany": 0, "rozumie": rozumie_glosy(b, swiat), "slownik": sorted(b.get("slownik", {}).keys())}
    for b in swiat["zmarli"]:
        glosy[b["nr"]] = {"nr": b["nr"], "znaki": b.get("glos", "?"), "zyje": False, "wydany": 0, "rozumie": [], "slownik": []}
    rozmowy = []
    for w in dziennik:
        m = w.get("mowa") or {}
        if m.get("glos") and w["byt"] in glosy:
            glosy[w["byt"]]["wydany"] += 1
        inny = w.get("inny") or {}
        if inny.get("typ") in ("glos", "wolanie") or inny.get("glos"):
            rozmowy.append({"cykl": w["cykl_swiata"], "kto": inny.get("od"), "do": w["byt"], "typ": inny.get("typ", "glos"),
                            "otworzyl": bool(inny.get("geny")), "czyn": inny.get("czyn"),
                            "znaki": glosy.get(inny.get("od"), {}).get("znaki", "?")})
        if m.get("krzyk"):
            rozmowy.append({"cykl": w["cykl_swiata"], "kto": w["byt"], "do": None, "krzyk": True})
        if m.get("wolanie"):
            rozmowy.append({"cykl": w["cykl_swiata"], "kto": w["byt"], "do": None, "wolanie": True})
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
    czekaja = [x["tekst"] for x in most.slowa_swiata().values() if x.get("status") in ("czeka", "w_drodze")]
    znaczenia = {}
    for r in rozmowy:
        if r.get("czyn"):
            k = (r["kto"], r["typ"])
            z = znaczenia.setdefault(k, {"kto": r["kto"], "typ": r["typ"], "znaki": r.get("znaki"), "czyn": r["czyn"], "razy": 0, "dla": set()})
            z["razy"] += 1
            z["dla"].add(r["do"])
    for z in znaczenia.values():
        z["dla"] = sorted(z["dla"])
    return {"cykl_swiata": swiat["cykl_swiata"], "glosy": sorted(glosy.values(), key=lambda g: g["nr"]),
            "rozmowy": rozmowy[-80:], "wymiary": swiat.get("wymiary", 4),
            "slowa": sorted(slowa.values(), key=lambda s: (-s["padlo"], s["tekst"])), "czekaja": czekaja,
            "znaczenia": list(znaczenia.values())}


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
PLIKI_SWIATA = ["swiat.json", "dziennik.jsonl", "slowa_keja.jsonl", "slowa_swiata.json",
                "wejscie.txt", "stan.json", "zycie.log", "karma.txt", "cud.txt", "cialo"]


def proces_zyje():
    try:
        pid = int(open(ZYCIE_PID).read().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError, FileNotFoundError):
        return False


def nowy_swiat(geny=None, dwoje=False, cykl=None, wymiary=None, istot=None):
    """Stary świat idzie do archiwum (rzeczywistość równoległa), rusza nowy proces życia.
    Tylko gdy w obecnym świecie nikt nie żyje. geny: ile genów ma mieć pierwszy byt."""
    geny = max(4, min(4096, int(geny or os.environ.get("GENY", "64"))))
    cykl = max(1.0, min(3600.0, float(cykl or os.environ.get("CYKL", "60"))))
    wymiary = max(2, min(64, int(wymiary or 4)))
    istot = max(1, min(32, int(istot or (2 if dwoje else 1))))
    swiat = most.czytaj_json(most.CIALO, None)
    if swiat is not None and swiat.get("zywi") and not swiat.get("wygasla"):
        return 409, {"blad": "w tym świecie ktoś jeszcze żyje"}
    if proces_zyje():
        return 409, {"blad": "proces życia jeszcze działa"}
    numer = 1
    os.makedirs(SWIATY, exist_ok=True)
    while os.path.exists(os.path.join(SWIATY, str(numer))):
        numer += 1
    cel = os.path.join(SWIATY, str(numer))
    if swiat is not None:
        os.makedirs(cel)
        for nazwa in PLIKI_SWIATA:
            p = os.path.join(KATALOG, nazwa)
            if os.path.exists(p):
                shutil.move(p, os.path.join(cel, nazwa))
        with open(os.path.join(cel, "SWIAT.txt"), "w") as f:
            f.write(f"świat {numer}\ncykli: {swiat.get('cykl_swiata')}\nbytów: {len(swiat.get('zmarli', [])) + len(swiat.get('zywi', []))}\n"
                    f"zarchiwizowany: {time.strftime('%Y-%m-%d %H:%M')}\n")
    log = open(os.path.join(KATALOG, "zycie.log"), "a")
    proc = subprocess.Popen([sys.executable, os.path.join(KATALOG, "zycie.py")],
                            cwd=KATALOG, stdout=log, stderr=subprocess.STDOUT,
                            env={**os.environ, "CYKL": str(cykl), "GENY": str(geny), "DWOJE": "1" if dwoje else "0", "WYMIARY": str(wymiary), "ISTOT": str(istot)},
                            start_new_session=True)
    with open(ZYCIE_PID, "w") as f:
        f.write(str(proc.pid))
    time.sleep(2)
    return 200, {"nowy_swiat": True, "geny": geny, "dwoje": dwoje, "cykl": cykl, "wymiary": wymiary, "istot": istot, "poprzedni_w": cel if swiat is not None else None, "pid": proc.pid}


def przyjmij_slowa(tekst, do=None):
    """Zdanie to jeden sygnał w jednym cyklu: suma wektorów wyrazów. do: nr istoty albo None (do wszystkich)."""
    tekst = " ".join(str(tekst).split())[:240]
    if not tekst:
        return []
    do = int(do) if (do is not None and str(do).isdigit()) else None
    swiat = most.czytaj_json(most.CIALO, {"cykl_swiata": 0})
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
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(ciało)))
        self.end_headers()
        self.wfile.write(ciało)

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
        if sciezka == "/api/wnetrze":
            return self._json(200, wnetrze())
        if sciezka == "/api/rod":
            return self._json(200, rod())
        if sciezka == "/api/genom":
            return self._json(200, genom_swiata())
        if sciezka == "/api/jezyk":
            return self._json(200, jezyk())
        if sciezka.startswith("/s/"):
            # pliki wspólne: css, js, słowniki
            baza = os.path.join(KATALOG, "strona")
            plik = os.path.normpath(os.path.join(baza, sciezka[3:]))
            if not plik.startswith(baza) or not os.path.isfile(plik):
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
        if sciezka in ("/", "/index.html", "/wnetrze", "/rod", "/jezyk"):
            plik = {"/wnetrze": WNETRZE, "/rod": ROD, "/jezyk": JEZYK}.get(sciezka, STRONA)
            with open(plik, "rb") as f:
                ciało = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(ciało)))
            self.end_headers()
            return self.wfile.write(ciało)
        self._json(404, {"blad": "nie ma"})

    def do_POST(self):
        sciezka = urlparse(self.path).path
        if sciezka == "/api/nowy_swiat":
            n = int(self.headers.get("Content-Length", 0))
            try:
                dane = json.loads(self.rfile.read(n) or b"{}")
            except json.JSONDecodeError:
                dane = {}
            kod, dane = nowy_swiat(dane.get("geny"), bool(dane.get("dwoje")), dane.get("cykl"), dane.get("wymiary"), dane.get("istot"))
            return self._json(kod, dane)
        if sciezka == "/api/nakarm":
            n = int(self.headers.get("Content-Length", 0))
            try:
                dane = json.loads(self.rfile.read(n) or b"{}")
            except json.JSONDecodeError:
                dane = {}
            do = dane.get("do")
            with open(os.path.join(KATALOG, "karma.txt"), "a") as f:
                f.write(("@wszystkie" if do == "wszystkie" else f"@{int(do)}" if do is not None and str(do).isdigit() else str(time.time())) + "\n")
            return self._json(200, {"karma": "w najbliższym cyklu", "do": do})
        if sciezka != "/api/slowo":
            return self._json(404, {"blad": "nie ma"})
        n = int(self.headers.get("Content-Length", 0))
        try:
            dane = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._json(400, {"blad": "to nie jest słowo"})
        slowa = przyjmij_slowa(dane.get("slowo", ""), dane.get("do"))
        if not slowa:
            return self._json(400, {"blad": "puste"})
        self._json(200, {"slowa": slowa, "status": "w_drodze"})

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print(f"bytek słucha na http://0.0.0.0:{PORT}  (na tym Macu: http://localhost:{PORT})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Bytek).serve_forever()
