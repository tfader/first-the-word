"""Word: tłumacz znaczeń. Znaki skutku (▲▼·) to zapis wektora przeżycia;
tutaj rozkłada się go na rzeczy, które świat zna z nazwy, i mówi po ludzku.
Uruchom: python3 tlumacz.py [ile]"""
import json
import os
import sys
import collections
import math

KATALOG = os.path.dirname(os.path.abspath(__file__))
CIALO = os.path.join(KATALOG, "swiat.json")
PROG = 0.3                     # poniżej tego podobieństwa składnik nie wchodzi do zdania
PROG_LAKI = 0.8                # zapachów łąk są tysiące i są losowe: taki składnik musi pasować dużo mocniej
JEZYK = "pl"                   # język świata; ustawiany przy wznowieniu z ciała

SLOWA = {
    "pl": {"jedzenie": "jedzenie", "bol": "ból", "glos": "cudzy głos", "wolanie": "wołanie",
           "uprawa": "praca na łące", "spichlerz": "zapas", "noc": "noc", "choroba": "gorączka",
           "drapieznik": "drapieżnik", "zima": "zima", "wiosna": "wiosna", "lato": "lato", "jesien": "jesień",
           "laka": "zapach jakiejś łąki", "bez_nazwy": "coś, czego świat nie nazwał",
           "domieszka": " z domieszką: ", "przeciw": "przeciwieństwo: ",
           "duzo": "i zostało dużo sił", "plus": "i wyszło na plus", "zero": "i wyszło na zero", "minus": "i ubyło sił",
           "idz": "idź", "unikaj": "unikaj", "zapamietaj": "zapamiętaj", "odpowiedz": "odpowiedz",
           "zdanie": "{cz}, bo {opis} — {ile}"},
    "en": {"jedzenie": "food", "bol": "pain", "glos": "another's voice", "wolanie": "a mating call",
           "uprawa": "work on the meadow", "spichlerz": "stored food", "noc": "night", "choroba": "fever",
           "drapieznik": "a predator", "zima": "winter", "wiosna": "spring", "lato": "summer", "jesien": "autumn",
           "laka": "the smell of some meadow", "bez_nazwy": "something the world has no name for",
           "domieszka": " mixed with: ", "przeciw": "the opposite of: ",
           "duzo": "and plenty of strength was left", "plus": "and it came out ahead",
           "zero": "and it came out even", "minus": "and strength was lost",
           "idz": "go", "unikaj": "avoid", "zapamietaj": "remember", "odpowiedz": "answer",
           "zdanie": "{cz}, because {opis} — {ile}"},
}


def sl(k):
    return SLOWA.get(JEZYK, SLOWA["pl"]).get(k, k)


def znaki(wektor):
    d = math.sqrt(sum(x * x for x in wektor)) or 1.0
    return "".join("▲" if x / d > 0.3 else ("▼" if x / d < -0.3 else "·") for x in wektor)


_SKLADNIKI = {}              # cache: budowanie listy zapachów co wpis byłoby drogie przy tysiącu istot


def skladniki(swiat):
    """Wszystko, co w tym świecie ma nazwę i kierunek: z tego składa się każde przeżycie."""
    klucz = swiat.get("cykl_swiata")
    if _SKLADNIKI.get("cykl") == klucz:
        return _SKLADNIKI["co"]
    z = {sl("jedzenie"): swiat["kierunek_pokarmu"], sl("bol"): swiat["kierunek_rany"],
         sl("glos"): swiat["kierunek_glosu"], sl("wolanie"): swiat["kierunek_wolania"]}
    for n, v in (swiat.get("sygnatury") or {}).items():
        z[sl(n)] = v
    zajete = {str(b.get("miejsce")) for b in swiat.get("zywi", [])}
    for k, m in (swiat.get("miejsca") or {}).items():
        if m.get("zapach") and k in zajete:          # tylko łąki, na których ktoś stoi: reszta to tysiące losowych kierunków,
            z[sl("laka")] = m["zapach"]              # a wśród setek zawsze trafi się jakiś podobny przez przypadek;
                                                     # numer łąki nic nie mówi, sam zapach owszem
    _SKLADNIKI["cykl"], _SKLADNIKI["co"] = klucz, z
    return z


def cos(a, b):
    da = math.sqrt(sum(x * x for x in a)) or 1.0
    db = math.sqrt(sum(x * x for x in b)) or 1.0
    return sum(x * y for x, y in zip(a, b)) / (da * db)


def na_ludzki(wektor, bilans, czasownik, swiat):
    """Zdanie o jednym znaczeniu: z czego było zrobione przeżycie i czy się opłaciło.
    czasownik: znacznik („idz”, „unikaj”, „zapamietaj”) albo gotowe słowo ze starego zapisu."""
    sk = skladniki(swiat)
    laka = sl("laka")
    pod = sorted(((cos(wektor, v), n) for n, v in sk.items()), key=lambda x: -abs(x[0]))
    czesci = []
    for c, n in pod:
        prog = PROG_LAKI if n == laka else PROG      # zapach łąki musi pasować dużo mocniej: łąk są setki i są losowe
        if abs(c) < prog:
            continue
        if c < 0 and n == laka:
            continue                                  # „przeciwieństwo zapachu łąki” nic nie znaczy
        czesci.append(((sl("przeciw") if c < 0 else "") + n, abs(c)))
        if len(czesci) == 3:
            break
    if not czesci:
        opis = sl("bez_nazwy")
    else:
        opis = czesci[0][0]
        if len(czesci) > 1:
            opis += sl("domieszka") + ", ".join(n for n, _ in czesci[1:])
    if bilans > 0.5:
        ile = sl("duzo")
    elif bilans > 0.0:
        ile = sl("plus")
    elif bilans > -0.5:
        ile = sl("zero")
    else:
        ile = sl("minus")
    cz = SLOWA.get(JEZYK, SLOWA["pl"]).get(czasownik, czasownik)
    return SLOWA.get(JEZYK, SLOWA["pl"])["zdanie"].format(cz=cz, opis=opis, ile=ile)


def zbierz(swiat):
    """Znaczenia żyją w istotach: sumuje ich skojarzenia po znaku skutku."""
    agg = collections.defaultdict(lambda: {"n": 0, "b": 0.0, "v": None, "slowa": set(), "kto": set()})
    for z in swiat.get("zywi", []):
        for kl, v in (z.get("po_slowie") or {}).items():
            if not isinstance(v, dict) or "n" not in v:
                continue
            a = agg[znaki(v["v"])]
            a["n"] += v["n"]; a["b"] += v["b"]; a["slowa"].add(kl); a["kto"].add(z["nr"])
            a["v"] = list(v["v"]) if a["v"] is None else [x + y for x, y in zip(a["v"], v["v"])]
    return agg


def main():
    ile = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    swiat = json.load(open(CIALO))
    agg = zbierz(swiat)
    print(f"cykl {swiat['cykl_swiata']}, żywych {len(swiat['zywi'])}, znaczeń w obiegu {len(agg)}\n")
    for zn, a in sorted(agg.items(), key=lambda x: -x[1]["n"])[:ile]:
        sr = a["b"] / max(1, a["n"])
        czas = "idź" if sr > 0.3 else ("unikaj" if sr < -0.3 else "zapamiętaj")
        print(f"{zn}   {a['n']:>5} obserwacji, {len(a['kto'])} istot, {len(a['slowa'])} słów")
        print(f"    {na_ludzki(a['v'], sr, czas, swiat)}\n")


if __name__ == "__main__":
    main()
