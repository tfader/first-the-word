"""Word: prawa świata i byt. Symulacja wielu światów: python3 word.py. Życie: zycie.py."""
import os
import random

import numpy as np
import warnings

warnings.filterwarnings("ignore", message="overflow encountered in matmul")   # fałszywy alarm Accelerate w numpy 2.0 na Macu

ILE_GENOW = int(os.environ.get("GENY", 8))
ROZMIAR = int(os.environ.get("WYMIARY", 4))


def ustaw_wymiary(n):
    """Wymiary świata ustala się raz, przy cudzie. Wczytywane z ciała świata."""
    global ROZMIAR
    ROZMIAR = int(n)
CYKLE_SWIATA = int(os.environ.get("CYKLE", 300))

# --- prawa świata ---
SYTOSC = 10.0                # poniżej tej energii zaczyna się głód
START = 1.4                  # pierwsze istoty z cudu rodzą się z zapasem: 1,4 sytości
KOSZT_TRWANIA = 1.0          # każdy cykl kosztuje
KOSZT_SNU = 0.5              # spoczynek to złudzenie: też kosztuje, tylko mniej
SEN_SZUM = 0.35              # sen zniekształca mocniej niż echo na jawie: stąd bierze się to, czego nie było
BUDZET_SNU = 0.6             # ile energii wolno przepalić na marzenie (bramki we śnie kosztują połowę)
STARZENIE = 0.002            # o tyle maleje zdolność absorpcji co cykl (po 250 cyklach połowa)
KOSZT_BRAMKI = 0.15          # otwarcie bramki kosztuje
NAWYK = 0.8                  # każde kolejne otwarcie tego samego genu kosztuje tyle razy mniej
KOSZT_ODRUCHU = 0.03         # ale nigdy mniej niż tyle
ZGODNOSC = 0.9               # jak bardzo sygnał musi "pasować" do genu
SLUCH = 0.7                  # słuch społeczny: cudzy głos otwiera bramkę przy niższym progu (wrodzony wzorzec głosu gatunku); było 0,75
TEMAT_W_GLOSIE = 0.6         # ile siły głosu ma sygnatura tematu w wypowiedzi: głos dominuje, żeby wrodzony słuch go poznawał
BUDZET_SLUCHU = 0.3          # uwaga na innych: tyle budżetu ma zawsze słuchanie, choćby kaskady zjadły resztę (gatunek społeczny)
GAWEDA = 0.6                 # czas wolny: syta w dzień, z kimś obok, zamiast drzemać gawędzi z takim prawdopodobieństwem
BLISKOSC = 3                 # tyle gawęd z obcym czyni go swoim (nabyta bliskość, obok pokrewieństwa z rdzenia)
UNIKANIE = 12                # „uwaga”: tyle cykli słuchacz omija łąkę, o której usłyszał, że tam boli
SKAPSTWO = 0.3               # najwyżej taką część energii byt wyda w cyklu na bramki
BUDZET_MAX = 0.6             # ...i nigdy więcej niż tyle: mózg nie pali więcej niż pół tego, co ciało
WCHLANIANIE = 0.2            # ile sygnału powłoka wchłania przy otwarciu (× (0,5 + pojętność))
KULTURA = 0.15               # ile powłoki rodzica dziecko przejmuje w jednym cyklu nauki (× (0,5 + pojętność))
KOSZT_NAUKI = 0.25           # tyle energii kosztuje rodzica jeden cykl uczenia (× troska): kultura nie jest darmowa
KOSZT_POJETNOSCI = 0.1       # pojętny mózg jest drogi: tyle więcej kosztuje trwanie przy pojętności 1
ODKRYCIE_UPRAWY = 0.05       # odkrycie uprawy na cykl: × ciekawość × (0,5 + pojętność); geny odkrywcy to ciekawość i pojętność (było 0,02)
KOSZT_UPRAWY = 0.2           # praca na łące: tyle energii na cykl przy umiejętności 1
UPRAWA_ODROST = 0.02         # o tyle rośnie gęstość łąki na cykl pracy przy umiejętności 1 (mniej więcej tyle, ile zjada jedna istota)
PRAKTYKA = 0.02              # o tyle rośnie umiejętność za cykl pracy (było 0,01)
PRZEKAZ = 0.8                # ile poziomu nauczyciela dostaje uczeń ze słowa (było 0,6: umiejętność gasła z każdym przekazem)
ODKLADANIE = 0.3             # spichlerz: tyle nadwyżki ponad sytość odkłada na cykl przy umiejętności 1 (najwyżej 3)
STRATA_SPICHLERZA = 0.1      # tyle ginie przy odkładaniu (część pokarmu się psuje)
POBOR = 2.0                  # tyle na cykl bierze ze spichlerza głodna przy umiejętności 1
APETYT_JESIENI = 0.9         # jesienne tuczenie: taki apetyt co najmniej, żeby wejść w zimę z zapasem
SKUPIENIE = 1                # ile genów naraz może odpowiedzieć na jeden sygnał
SZUM_RANY = 0.1              # rana zawsze boli tak samo, z lekkim szumem
SZUM_POKARMU = 0.3           # pokarm smakuje podobnie, ale bardziej zmiennie
HOJNOSC = 18.0               # średnia oferta świata (4,5 → 9 → 18: łąki cztery razy wydajniejsze niż na początku); byt bierze z niej tylko część
POWROT_ECHA = 0.3            # szansa, że dane echo wróci w tym cyklu
ECHA_NA_CYKL = 2             # najwyżej tyle ech wraca w jednym cyklu
ZNIEKSZTALCENIE = 0.15       # szum echa rośnie o tyle na każdy cykl czekania
SLABNIECIE = 0.8             # siła echa maleje tyle razy na cykl czekania
SILA_MIN = 0.1               # ale nigdy do zera
SILA_MAX = 10.0              # sygnał się nasyca: nic nie rośnie bez końca
SUFIT_ECHA = 100             # praktyczny sufit kolejki
PROG_CUDU = 1.4 * SYTOSC     # przy takiej nadwyżce byt powołuje potomka (dobra kondycja, nie podwójny zapas)
POJEMNOSC = 3.0 * SYTOSC     # więcej byt nie zmieści, nadmiar przepada
BUDZENIE = 0.5               # syty budzi się na ofertę > HOJNOSC * (BUDZENIE + 2 * pełność)
DRYFT = float(os.environ.get("DRYFT", 0.03))                 # o tyle na cykl świata przesuwa się smak pokarmu
MUTACJA = 0.1                # jak mocno potomek odchyla się od rodzica
MIEJSC = 16                  # świat to koło z tylu miejsc
DZIECINSTWO = 8              # tyle cykli potomek jest karmiony przez rodziców; potem pępowina odcięta
KARMIENIE = 0.8              # tyle energii rodzic oddaje dziecku na cykl, jeśli sam nie głoduje
KOSZT_RUCHU = 0.3            # przejście do sąsiedniego miejsca
GLOD_RUCHU = 0.25            # poniżej takiego głodu byt nie rusza się z miejsca
ODRASTANIE = 0.06           # gęstość pokarmu wraca do żyzności o tyle na cykl (stada ogryzały swoje łąki szybciej, niż odrastały)
WYJADANIE = 0.0015           # o tyle maleje gęstość łąki na jednostkę zjedzonego (było 0,006: plon urósł 4×, wyjadanie musi zmaleć 4×, inaczej tłum zjada łąkę w kilkanaście cykli)
KOSZT_SILY = 0.25            # silna istota płaci za trwanie do tyle więcej (mięśnie kosztują)
KREWNY = 0.2                 # tak podobne rdzenie to swoi (dziecko–rodzic ≈ 0,5, rodzeństwo ≈ 0,5, wnuk ≈ 0,25, obcy ≈ 0); po głosie obcy wychodzili krewnymi
ODWROT = 0.8                 # obcy odpuszcza bez walki, gdy jest słabszy niż tyle razy obrona (jastrząb i gołąb)
NOWY_GEN = 0.02              # szansa, że gen potomka jest całkiem nowy, losowy
DUPLIKACJA = 0.03            # szansa, że u potomka jeden gen kopiuje się na koniec kręgosłupa (duplikacja genu)
MUTACJA_KOPII = 3.0          # kopia mutuje tyle razy mocniej: oryginał trzyma funkcję, kopia szuka nowej
USUNIECIE = 0.015            # szansa, że potomek traci jeden gen z ogona (nigdy z części bazowej)
KULTURA_ZNACZEN = 0.5        # z jaką siłą dziecko przejmuje znaczenia rodzica (wiedza z drugiej ręki)
PAMIEC_SLOW = 64             # tyle słów naraz istota trzyma w skojarzeniach (co po nich następowało)
PROG_GATUNKU = 0.0           # bariera gatunkowa: ustawiana przez świat co jakiś czas jako ułamek tego,
                             # jak podobne są do siebie rdzenie w populacji. W świeżym świecie rdzenie są losowe
                             # i nikt nie pasuje do nikogo, więc bariery nie ma; dojrzewa razem ze światem.
KOSZT_OZDOBY = 0.35          # ozdoba nie służy niczemu: kosztuje trwanie i rzuca się w oczy drapieżnikowi.
                             # Właśnie dlatego jest uczciwym sygnałem — stać na nią tylko tego, komu starcza sił.
KOSZT_ODPORNOSCI = 0.08      # utrzymanie odporności kosztuje trwanie (układ odpornościowy nie jest darmowy)
KOSZT_CHOROBY = 1.2          # chora płaci tyle dodatkowo za każdy cykl gorączki (podwójne trwanie)
KOSZT_GENU = 0.02            # o tyle droższe trwanie za każdy gen ponad bazę: nadmiar genów kosztuje


def losowy_kierunek():
    k = [random.gauss(0, 1) for _ in range(ROZMIAR)]
    d = sum(x * x for x in k) ** 0.5 or 1.0
    return [x / d for x in k]


def losowa_macierz():
    return [[random.gauss(0, 1) for _ in range(ROZMIAR)] for _ in range(ROZMIAR)]


def podobienstwo(a, b):
    ab = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return ab / (na * nb) if na and nb else 0.0


KIERUNEK_RANY = losowy_kierunek()     # stały: uszczypnięcie zawsze boli tak samo
KIERUNEK_POKARMU = losowy_kierunek()  # dryfuje: świat się zmienia
KIERUNEK_WOLANIA = losowy_kierunek()  # wołanie gatunku: "chodź do mnie", receptor wrodzony
KIERUNEK_GLOSU = losowy_kierunek()    # głos gatunku "jem": wspólny, ale bez receptora wrodzonego, trzeba go skojarzyć
SZUM_WOLANIA = 0.15
AKCENT = 0.2                          # ile w głosie jest własnego rdzenia, reszta to głos gatunku


def szum(s):
    """Szum na składową skalowany tak, żeby kąt odchylenia nie rósł z liczbą wymiarów (4 = jak dotąd)."""
    return s * (4.0 / ROZMIAR) ** 0.5


def wolanie():
    return [k + random.gauss(0, szum(SZUM_WOLANIA)) for k in KIERUNEK_WOLANIA]


def dryf_swiata():
    global KIERUNEK_POKARMU
    k = [x + random.gauss(0, DRYFT) for x in KIERUNEK_POKARMU]
    d = sum(x * x for x in k) ** 0.5 or 1.0
    KIERUNEK_POKARMU = [x / d for x in k]


def slowo_na_wektor(slowo, sila=1.0):
    """To samo słowo zawsze ten sam kierunek. Obcy dla rdzenia.
    Zdanie to suma wektorów wyrazów: blisko każdego z nich, ale żadnym z nich nie jest.
    Jak melodia i nuty."""
    k = [0.0] * ROZMIAR
    for wyraz in slowo.strip().lower().split():
        r = random.Random(wyraz)
        for i in range(ROZMIAR):
            k[i] += r.gauss(0, 1)
    d = sum(x * x for x in k) ** 0.5 or 1.0
    return [x / d * sila for x in k]


ZNAKI = "▲▼◆◇●○■□"


def glos_z_rdzenia(kregoslup):
    """Głos istoty: głos gatunku ("jem") z akcentem z własnego rdzenia.
    Wspólny na tyle, że nauka jednego głosu przenosi się na inne; różny na tyle, że istoty da się rozróżnić."""
    k = [0.0] * ROZMIAR
    for gen in kregoslup[:8]:
        for i in range(ROZMIAR):
            k[i] += gen[0][i]
    d = sum(x * x for x in k) ** 0.5 or 1.0
    akcent = [x / d for x in k]
    g = [(1.0 - AKCENT) * KIERUNEK_GLOSU[i] + AKCENT * akcent[i] for i in range(ROZMIAR)]
    d = sum(x * x for x in g) ** 0.5 or 1.0
    return [x / d for x in g]


JEZYK = "pl"                 # język nazw czynów w TYM świecie; ustawiany raz, przy cudzie, i zapisany w ciele


def ustaw_jezyk(k):
    global JEZYK
    JEZYK = k if k in NAZWY else "pl"


# Nazwy czynów: to, co widać w słowniku świata. Mechanika ich nie czyta — świat wykonuje czyn po znaczniku
# czasownika (czyn_verb), nie po napisie. Dlatego język można wybrać przy powołaniu świata, nic nie psując.
NAZWY = {
    "pl": {
        "bron": "bronić", "chodz": "chodź do mnie", "nie_wierz": "nie wierzyć",
        "gromadz": "gromadzić", "uprawiaj": "uprawiać",
        ("idz", "laka"): "idź do łąki", ("unikaj", "laka"): "unikaj łąki", ("zapamietaj", "laka"): "zapamiętaj łąkę",
        ("idz", "istota"): "idź do istoty", ("unikaj", "istota"): "unikaj istoty", ("zapamietaj", "istota"): "zapamiętaj istotę",
        ("idz", "nadawca"): "idź do nadawcy", ("unikaj", "nadawca"): "unikaj nadawcy",
        ("zapamietaj", "nadawca"): "zapamiętaj nadawcę", ("odpowiedz", "nadawca"): "odpowiedz nadawcy",
        "@idz": "idź", "@unikaj": "unikaj", "@zapamietaj": "zapamiętaj", "@odpowiedz": "odpowiedz",
        "@bo": "{cz}, bo {s}",
    },
    "en": {
        "bron": "defend", "chodz": "come to me", "nie_wierz": "distrust",
        "gromadz": "store", "uprawiaj": "till",
        ("idz", "laka"): "go to the meadow", ("unikaj", "laka"): "avoid the meadow", ("zapamietaj", "laka"): "remember the meadow",
        ("idz", "istota"): "go to the being", ("unikaj", "istota"): "avoid the being", ("zapamietaj", "istota"): "remember the being",
        ("idz", "nadawca"): "go to the speaker", ("unikaj", "nadawca"): "avoid the speaker",
        ("zapamietaj", "nadawca"): "remember the speaker", ("odpowiedz", "nadawca"): "answer the speaker",
        "@idz": "go", "@unikaj": "avoid", "@zapamietaj": "remember", "@odpowiedz": "answer",
        "@bo": "{cz}, because {s}",
    },
}


def nazwa_czynu(verb, obiekt=None):
    """Nazwa czynu w języku tego świata. Bez obiektu: czyn wrodzony."""
    d = NAZWY.get(JEZYK, NAZWY["pl"])
    return d.get((verb, obiekt)) if obiekt else d.get(verb)


def nazwa_bo(verb, skutek):
    """„zapamiętaj, bo ▲▼·▲” — czasownik plus zapis przeżycia, które słowo zapowiada."""
    d = NAZWY.get(JEZYK, NAZWY["pl"])
    return d["@bo"].format(cz=d["@" + verb], s=skutek)


def klucz_slowa(temat, cel=None, slowo_id=None):
    """Klucz słowa w słowniku świata: temat i to, do czego się odnosi. Powtórzone cudze słowo liczy się do tamtego słowa
    (po identyfikatorze nowego dźwięku); powtórzenie bez identyfikatora nie jest osobnym słowem."""
    if not temat:
        return None
    if temat == "inny":
        return ("echo:" + str(slowo_id)) if slowo_id else None
    if temat == "echo":
        return "echo:" + str(cel)
    return temat + ":" + (str(cel) if cel is not None else "")


def znak_slowa(wektor):
    """Krótka nazwa nowego dźwięku (dla ludzi): znaki z unormowanego wektora. Podobne dźwięki dostają tę samą nazwę."""
    d = sum(x * x for x in wektor) ** 0.5 or 1.0
    return glos_na_znaki([x / d for x in wektor])


def znak_skutku(wektor):
    """Zgrubna nazwa skutku: dla każdego wymiaru tylko mocno na plus, mocno na minus albo nijak.
    Zgrubnie, żeby podobne przeżycia trafiały do jednego kubełka — inaczej każdy skutek byłby jednorazowy."""
    d = sum(x * x for x in wektor) ** 0.5 or 1.0
    return "".join("▲" if x / d > 0.3 else ("▼" if x / d < -0.3 else "·") for x in wektor)


def glos_na_znaki(glos):
    """Cztery znaki z ośmiu: znak i wielkość każdej składowej. Bez tłumaczenia."""
    out = []
    for x in glos:
        i = (0 if x >= 0 else 4) + min(3, int(abs(x) * 4))
        out.append(ZNAKI[i])
    return "".join(out)


def rana():
    return [(k + random.gauss(0, szum(SZUM_RANY))) * KOSZT_TRWANIA for k in KIERUNEK_RANY]


def oferta_swiata(wiek):
    surowa = random.expovariate(1.0 / HOJNOSC)
    absorpcja = max(0.0, 1.0 - STARZENIE * wiek)
    ilosc = surowa * absorpcja
    return [(k + random.gauss(0, szum(SZUM_POKARMU))) * ilosc for k in KIERUNEK_POKARMU], ilosc


def wziete(oferta, otwarcia, nawyk):
    """Bierze tylko otwarta bramka. Znany pokarm trawi się lepiej:
    nawyk 0 = jak dotąd (pierwsza bramka bierze połowę), nawyk 1 = prawie wszystko."""
    strata = 0.5 * (1.0 - nawyk) + 0.05 * nawyk
    return oferta * (1.0 - strata ** otwarcia) if otwarcia else 0.0


class Byt:
    licznik = 0

    def __init__(self, kregoslup, energia, pokolenie):
        Byt.licznik += 1
        self.nr = Byt.licznik
        self.pokolenie = pokolenie
        self.K = np.asarray(kregoslup, dtype=float)                  # rdzeń: stały (N, R, R)
        self.P = np.zeros_like(self.K)                               # powłoka: zmienna
        self.otwarcia_genu = [0] * len(kregoslup)
        self.genow_bazowych = len(kregoslup)                         # ile genów miała linia na starcie; ogon powyżej to duplikaty (dziedziczone)
        self.echo = []
        self.energia = energia
        self.wiek = 0
        self.sen = 0
        self.otwarcia = 0
        self.najdluzsza = 0
        self.dzieci = 0
        self.cos = None                     # zapis ostatniego cyklu dla Keja
        self.wyszlo = []                    # co wyszło w ostatnim cyklu (inni to słyszą)
        self.zjadl = 0.0
        self.slownik = {}                   # słowa, które do niego dotarły: tekst -> wektor
        self.zrodla = {}                    # nr genu -> {"rana": n, "pokarm": n, "echo": n, "slowo": n, "inny": n}
        self.rodzic = None                  # nr rodzica; None = z cudu
        self.rodzic2 = None                 # drugi rodzic, gdy świat ma dwoje rodziców
        self.miejsce = 0                    # id miejsca w świecie
        self.poprzednie = None              # skąd przyszła (nie zawraca, chyba że musi)
        self.kierunek = random.choice((-1, 1))
        self.wytrwalosc = 2                 # ile gorszych cykli zniesie, zanim skręci (dziedziczne)
        self.sila = random.uniform(0.4, 0.8)   # siła: ile twardego pokarmu potrafi wziąć (dziedziczna, kosztuje)
        self.ciekawosc = random.uniform(0.2, 0.8)   # zwiad (rzadki) i odkrycia: gen ciekawości (dziedziczny); było 0,1..0,6
        self.optimum = random.uniform(0.3, 0.7)     # temperatura, w której trwanie kosztuje najmniej (dziedziczna)
        self.tolerancja = random.uniform(0.1, 0.3)  # jak szeroko wokół optimum nic nie kosztuje; szeroka kosztuje sama w sobie
        self.zle = 0
        self.idzie = False
        self.krokow = 0
        self.srednio = KOSZT_TRWANIA * 2            # na start ufa miejscu, w którym się urodził
        self.dobre_miejsce = None                   # pamięć: gdzie ostatnio najadła się porządnie
        self.dobre_ile = 0.0
        self.mapa = {}                              # nabyte: pora roku -> {miejsce: ile tam zwykle jadła}; kultura ją przekazuje
        self.towarzystwo_bylo = None                # ilu było obok w poprzednim cyklu
        self.snil = None                            # co zostało po ostatnim śnie (wektor), do opowiedzenia na jawie
        self.co_zaszlo = None                       # wektor tego, co weszło w istotę w poprzednim cyklu
        self.bilans = 0.0                           # ile energii po tym zostało (dodatnio: opłaciło się)
        self.po_slowie = {}                         # NABYTE: klucz słowa -> co zwykle po nim następowało {"pokarm": n, "bol": n, "nic": n}
        self.czeka_skutek = []                      # słowa usłyszane w tym cyklu: skutek oceni się w następnym
        self.skad_wyjscia = {}                      # wektor wyjścia -> gen, z którego wypadł (czyszczone co cykl)
        self.gen_slowa = None                       # gen, z którego wyszedł nowy dźwięk w tym cyklu
        self.temat = None                           # o czym mówi: (nazwa, wektor sygnatury, cel) — to, co w tym cyklu brzmiało najgłośniej
        self.wypowiedz = None                       # co wydaje z siebie: własny głos + sygnatura tematu
        self.przylapala = None                      # (nr, głos) kłamcy przyłapanego w poprzednim cyklu: temat na dziś
        self.czyn_cel = None                        # do czego odnosi się zrozumiany czyn (miejsce albo nr istoty)
        self.pora = None                            # pora roku w tym cyklu (od świata)
        self.poprzednio_zjadl = 0.0
        self.ruszyl = False
        self.mowa = {"krzyk": False, "slowo": None, "glos": False, "wolanie": False, "odpowiedz": None, "alarm": False}   # co mówi światu po tym cyklu
        self.odpowiada = None
        self.czyn = None                    # nazwa czynu (w języku świata) — do słownika i dla oczu
        self.czyn_verb = None               # znacznik czasownika: po nim świat wykonuje czyn, nie po napisie
        self.czyn_skutek = None             # znaki przeżycia, jeśli czyn wziął się z wyuczonego znaczenia
        self.czyn_do = None                 # do której istoty iść
        self.lownosc = 0.0                  # jakość receptora pokarmu (0..1)
        self.zrozumiane = set()             # znaczenia, które już raz wywołały czyn
        self.staz = 0                       # ile cykli stoi w tym miejscu (kto był pierwszy, ten broni)
        self.spala = False                  # czy poprzedni cykl przespała (sen najwyżej jeden cykl z rzędu)
        self.plec = random.choice(("n", "d"))   # n: nosi i wybiera; d: daje geny, woła i konkuruje
        self.stadnosc = random.uniform(0.0, 0.6)   # jak bardzo ciągnie do swoich (dziedziczna): grupa broni, ale dzieli pokarm
        self.pojetnosc = random.uniform(0.3, 0.7)  # dziedziczna: jak szybko powłoka się uczy (i od rodzica, i ze świata); droższe trwanie
        self.towarzyskosc = random.uniform(0.2, 0.8)   # dziedziczna: zdolności społeczne: chęć gawędy, uwaga na innych, tempo bliskości; droższe trwanie
        self.uprawa = 0.0                          # NABYTE, nie dziedziczne: umiejętność uprawy łąki (0..1); odkrycie albo nauka ze słowa
        self.uprawiala = False                     # czy w tym cyklu pracowała na łące
        self.spichlerz = 0.0                       # NABYTE: umiejętność odkładania pokarmu na łące (0..1); odkrycie jesienią albo nauka ze słowa
        self.odklada = 0.0                         # ile w tym cyklu odłożyła do spichlerza (świat dopisuje do łąki)
        self.pobiera = 0.0                         # ile chce wziąć ze spichlerza (świat daje, ile jest)
        self.gromadzila = False                    # czy w tym cyklu miała do czynienia ze spichlerzem (temat mowy)
        self.ufnosc = random.uniform(0.3, 0.9)     # dziedziczna: z jakim prawdopodobieństwem wierzy obcemu „tylko przechodzę”
        self.szczerosc = random.uniform(0.5, 1.0)  # dziedziczna: z jakim prawdopodobieństwem mówi prawdę, gdy przychodzi zostać
        self.przechodzi = False                    # w tym cyklu tylko przechodzi (nie je, nie zostaje)
        self.deklaruje = False                     # w tym cyklu powiedziała „tylko przechodzę” (prawda albo kłamstwo)
        self.deklarowal = False                    # to samo w poprzednim cyklu (do wykrycia kłamstwa)
        self.przechodzil = False                   # czy w poprzednim cyklu naprawdę tylko przechodziła
        self.klamcy = set()                        # nabyte: kogo przyłapała na kłamstwie; temu już nie wierzy
        self.bliscy = {}                           # nabyte: nr -> ile razy gawędziły; od BLISKOSC obcy staje się swoim
        self.gawedzi = False                       # w tym cyklu ma czas wolny: mówi dla samego mówienia
        self.bolalo = None                         # (miejsce, zapach, ile cykli jeszcze): po starciu mówi o bólu i o tej łące
        self.unikaj = {}                           # nabyte: miejsce -> do którego cyklu je omija („uwaga” zrozumiana)
        self.unikani = {}                          # nabyte: nr istoty -> do którego cyklu jej unika (składane znaczenie „unikaj istoty”)
        self.czyn_obiekt = None                    # rodzaj przedmiotu czynu: "laka", "istota", "nadawca"
        self.ozdoba = random.uniform(0.0, 0.15)     # dziedziczna: bezużyteczna ozdoba, kosztowna i widoczna
        self.gust = random.uniform(0.0, 0.5)        # dziedziczny: ile wybierająca waży cudzą ozdobę
        self.troska = random.uniform(0.2, 0.8)      # dziedziczna: ile sił oddaje na uczenie dziecka (i ile mu przekazuje)
        self.odpornosc = random.uniform(0.2, 0.8)   # dziedziczna: jak trudno ją zarazić i jak szybko zdrowieje; kosztuje trwanie
        self.chora = None                           # (szczep, ile cykli już choruje) albo None
        self.przechorowane = set()                  # szczepy, na które ma już odporność nabytą
        self.dlugowiecznosc = random.uniform(0.3, 0.7)   # 0: szybko się starzeje, tanio żyje; 1: wolno, ale trwanie droższe i dojrzewa później
        self.glos = glos_z_rdzenia(kregoslup)   # własny głos: z rdzenia, więc dziedziczny

    # --- geny (numpy: wszystkie geny naraz) ---
    @property
    def kregoslup(self):
        return self.K.tolist()

    @kregoslup.setter
    def kregoslup(self, v):
        self.K = np.asarray(v, dtype=float)

    @property
    def powloka(self):
        return self.P.tolist()

    @powloka.setter
    def powloka(self, v):
        self.P = np.asarray(v, dtype=float)

    def przez_gen(self, nr, s):
        """Sygnał przechodzi przez rdzeń i powłokę razem."""
        return ((self.K[nr] + self.P[nr]) @ np.asarray(s, dtype=float)).tolist()

    def wchlon(self, nr, s):
        """Powłoka wchłania sygnał: gen staje się do niego podobny (rezonuje łatwiej)."""
        k = np.asarray(s, dtype=float)
        d = float(np.linalg.norm(k)) or 1.0
        k = k / d
        self.P[nr] += WCHLANIANIE * (0.5 + self.pojetnosc) * np.outer(k, k)

    def jakosc(self, kierunek):
        """Jak dokładnie najlepszy gen (rdzeń + powłoka) pasuje do kierunku: 0..1.
        Dla pokarmu to łowność: dziedziczna przez rdzeń, doskonalona przez powłokę."""
        sv = np.asarray(kierunek, dtype=float)
        W = (self.K + self.P) @ sv
        nw = np.linalg.norm(W, axis=1)
        ns = float(np.linalg.norm(sv)) or 1.0
        with np.errstate(divide="ignore", invalid="ignore"):
            sims = np.where(nw > 0, (W @ sv) / (nw * ns), 0.0)
        return float(max(0.0, min(1.0, sims.max() if sims.size else 0.0)))

    def koszt_bramki(self, nr):
        return max(KOSZT_ODRUCHU, KOSZT_BRAMKI * NAWYK ** self.otwarcia_genu[nr])

    def zgodne_geny(self, s, pomin=(), prog=ZGODNOSC):
        sv = np.asarray(s, dtype=float)
        ns = float(np.linalg.norm(sv))
        if ns == 0.0:
            return []
        W = (self.K + self.P) @ sv                                   # (N, R)
        nw = np.linalg.norm(W, axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            sims = np.where(nw > 0, (W @ sv) / (nw * ns), 0.0)
        if pomin:
            sims[list(pomin)] = -2.0
        idx = np.nonzero(sims >= prog)[0]
        if idx.size == 0:
            return []
        kandydaci = sorted(((self.otwarcia_genu[int(i)], float(sims[i]), int(i)) for i in idx), reverse=True)
        return [nr for _, _, nr in kandydaci[:SKUPIENIE]]

    def kaskada(self, sygnal, budzet, prog=ZGODNOSC, zrodlo=None):
        otwarte, wyjscie, koszt = [], [], 0.0
        fala = [(sygnal, None)]                      # każdy sygnał w fali niesie numer genu, z którego wypadł
        while fala:
            nastepna = []
            for s, skad in fala:
                trafione = self.zgodne_geny(s, pomin=otwarte, prog=prog)
                if not trafione:
                    wyjscie.append(s)
                    self.skad_wyjscia[tuple(s)] = skad
                for nr in trafione:
                    c = self.koszt_bramki(nr)
                    if budzet < c:
                        wyjscie.append(s)
                        self.skad_wyjscia[tuple(s)] = skad
                        return otwarte, wyjscie, koszt
                    budzet -= c
                    koszt += c
                    otwarte.append(nr)
                    self.otwarcia_genu[nr] += 1
                    if zrodlo:
                        z = self.zrodla.setdefault(str(nr), {})
                        z[zrodlo] = z.get(zrodlo, 0) + 1
                    wyn = np.asarray(self.przez_gen(nr, s))
                    d = float(np.linalg.norm(wyn))
                    if d > SILA_MAX:
                        wyn = wyn / d * SILA_MAX          # nasycenie: kaskada nie wybucha
                    nastepna.append((wyn.tolist(), nr))
                    self.wchlon(nr, s)
            fala = nastepna
        return otwarte, wyjscie, koszt

    # --- echo ---
    def do_echa(self, wektory):
        for w in wektory:
            d = sum(x * x for x in w) ** 0.5
            if d > 0 and d == d and d != float("inf"):
                self.echo.append(([x / d for x in w], min(d, SILA_MAX), self.wiek))   # echo nasyca się
        del self.echo[:-SUFIT_ECHA]

    def wracajace_echa(self):
        wroci, zostaje = [], []
        for kierunek, sila, kiedy in self.echo:
            if len(wroci) < ECHA_NA_CYKL and random.random() < POWROT_ECHA:
                w = self.wiek - kiedy
                s = max(SILA_MIN, sila * SLABNIECIE ** w)
                wroci.append([(k + random.gauss(0, ZNIEKSZTALCENIE * w)) * s for k in kierunek])
            else:
                zostaje.append((kierunek, sila, kiedy))
        self.echo = zostaje
        return wroci

    # --- ruch: wysiłek, żeby zdobyć pokarm ---
    def chce_isc(self, glod):
        """Jak bakteria. Gdzie się najada, tam zostaje. Gdy kilka cykli z rzędu (wytrwałość)
        nie najadła się choć na trwanie, rusza i idzie, aż znów się naje.
        Zwraca True, gdy w tym cyklu chce zrobić krok. Sam krok robi świat (zna sąsiadów)."""
        self.ruszyl = False
        if self.spala:
            return self.idzie                            # po śnie nie ocenia łąki: nie żerowała, więc nic nie wie
        self.srednio = 0.7 * self.srednio + 0.3 * self.zjadl
        glodno_tu = self.srednio < KOSZT_TRWANIA
        if not self.idzie:
            self.zle = self.zle + 1 if glodno_tu else 0
            if glod >= GLOD_RUCHU and self.zle >= self.wytrwalosc:
                self.idzie, self.krokow = True, 0
        else:
            if self.zjadl >= KOSZT_TRWANIA:
                self.idzie, self.zle = False, 0          # tu jest jedzenie: zostaje
                self.srednio = self.zjadl
        if self.idzie and self.dobre_miejsce is not None and str(self.dobre_miejsce) == str(self.miejsce):
            self.dobre_miejsce, self.dobre_ile = None, 0.0                   # pamięć zawiodła: tu już nie karmi
        self.poprzednio_zjadl = self.zjadl
        return self.idzie and self.energia > KOSZT_RUCHU

    def rdzen_wektor(self, ile=None):
        """Rdzeń jako jeden wektor jednostkowy (stały, więc liczony raz): do rozpoznawania swoich.
        ile: liczyć tylko z pierwszych tylu genów — po duplikacjach kręgosłupy mają różną długość,
        a homologiczny jest wspólny początek."""
        ile = len(self.K) if ile is None else min(ile, len(self.K))
        pamiec = getattr(self, "_kw", None)
        if not isinstance(pamiec, dict):
            pamiec = self._kw = {}
        kw = pamiec.get(ile)
        if kw is None:
            f = self.K[:ile].reshape(-1)
            kw = f / (float(np.linalg.norm(f)) or 1.0)
            pamiec[ile] = kw
        return kw

    def swoj(self, inna):
        """Rozpoznanie swoich po rdzeniu, jak po zapachu (dopasowanie fenotypu): dziecko dzieli z rodzicem połowę genów,
        obcy prawie nic. Głos (akcent z 8 genów) był za mało pojemny: w 4 wymiarach połowa obcych brzmiała jak krewni."""
        if self.bliscy.get(inna.nr, 0) >= BLISKOSC:
            return True                                              # nabyta bliskość: gawędzili dość razy
        wspolne = min(len(self.K), len(inna.K))
        a, b = self.rdzen_vektor_bezpieczny(wspolne), inna.rdzen_vektor_bezpieczny(wspolne)
        if a is None or b is None or a.shape != b.shape:
            return podobienstwo(self.glos, inna.glos) >= 0.98
        return float(np.sum(a * b)) >= KREWNY      # bez matmul: Accelerate na Macu rzuca fałszywe ostrzeżenia

    def swoj_z_rdzenia(self, inna):
        """Tylko pokrewieństwo, bez nabytej bliskości."""
        wspolne = min(len(self.K), len(inna.K))
        a, b = self.rdzen_vektor_bezpieczny(wspolne), inna.rdzen_vektor_bezpieczny(wspolne)
        if a is None or b is None or a.shape != b.shape:
            return podobienstwo(self.glos, inna.glos) >= 0.98
        return float(np.sum(a * b)) >= KREWNY      # bez matmul: Accelerate na Macu rzuca fałszywe ostrzeżenia

    def zgodna_z(self, inna):
        """Bariera gatunkowa: rdzenie, które rozeszły się za daleko, nie dają potomstwa.
        Nikt tego nie ogłasza — linie po prostu przestają się ze sobą łączyć."""
        wspolne = min(len(self.K), len(inna.K))
        a, b = self.rdzen_vektor_bezpieczny(wspolne), inna.rdzen_vektor_bezpieczny(wspolne)
        if a is None or b is None or a.shape != b.shape:
            return True
        return float(np.sum(a * b)) >= PROG_GATUNKU

    def rdzen_vektor_bezpieczny(self, ile=None):
        try:
            return self.rdzen_wektor(ile)
        except Exception:
            return None

    def ucz_sie_od(self, rodzic):
        """Kultura: dziecko przy rodzicu przejmuje to, co nabyte, powoli, cykl po cyklu.
        Nauka kosztuje rodzica energię (× jego troska): głodny nie uczy, a kto uczy dużo, ten sam słabnie.
        Słowa i głosy, które rodzic zna, wchodzą do powłoki dziecka w te geny, które u dziecka
        rezonują z pokarmem (skojarzenie przez naśladowanie), dobre miejsce dziecko zapamiętuje."""
        # kultura głęboka: powłoka dziecka zbliża się do powłoki rodzica (te same geny po indeksie, bo rdzeń
        # dziedziczony gen po genie), z nią skojarzenia głosów i znaczeń; dziecko przejmuje też, co gen rodzica
        # znaczył (pokarm, rana, głos innego) i część nawyków. Tempo zależy od pojętności dziecka.
        troska = getattr(rodzic, "troska", 0.5)
        if rodzic.energia <= SYTOSC * 0.6 or troska <= 0.05:
            return                                                    # głodny rodzic nie uczy: najpierw przetrwać
        rodzic.energia -= KOSZT_NAUKI * troska
        sila_przekazu = 0.4 + 1.2 * troska                            # ile z tego, co wie, naprawdę przekazuje
        if rodzic.P.shape[1:] == self.P.shape[1:]:
            m = min(len(rodzic.P), len(self.P))                      # kręgosłupy bywają różnej długości: uczy się z części wspólnej
            self.P[:m] += KULTURA * sila_przekazu * (0.5 + self.pojetnosc) * (rodzic.P[:m] - self.P[:m])
            for nr, z in list(rodzic.zrodla.items())[:64]:
                if z:
                    glowne = max(z, key=z.get)
                    moje = self.zrodla.setdefault(str(nr), {})
                    moje[glowne] = moje.get(glowne, 0) + 1
            self.klamcy |= rodzic.klamcy                                       # dziecko wie, komu rodzic nie wierzy
            for p, m in rodzic.mapa.items():                                   # i zna mapę łąk rodzica, słabiej
                moja = self.mapa.setdefault(p, {})
                for k, v in m.items():
                    moja[k] = max(moja.get(k, 0.0), v * 0.7)
            nawykowe = sorted(range(len(rodzic.otwarcia_genu)), key=lambda i: -rodzic.otwarcia_genu[i])[:8]
            for i in nawykowe:
                if rodzic.otwarcia_genu[i] >= 3 and i < len(self.otwarcia_genu):
                    self.otwarcia_genu[i] += 1
        for kl, d in list(rodzic.po_slowie.items())[:16]:
            # tradycja: znaczenia rodzica przechodzą na dziecko, słabiej (wiedza z drugiej ręki, nie własne przeżycie).
            # Dzięki temu znaczenie słowa przeżywa tego, kto je zrozumiał.
            if kl in self.po_slowie or len(self.po_slowie) >= PAMIEC_SLOW or not isinstance(d, dict) or "n" not in d:
                continue
            waga = KULTURA_ZNACZEN * sila_przekazu * (0.5 + self.pojetnosc)
            self.po_slowie[kl] = {"n": max(1, int(round(d["n"] * waga))), "v": [x * waga for x in d["v"]], "b": d["b"] * waga}
        for tekst, wek in list(rodzic.slownik.items())[:4]:
            if tekst in self.slownik:
                continue
            self.slownik[tekst] = wek
            # naśladowanie: gen dziecka strojony na pokarm wchłania słowo, jakby je usłyszało przy jedzeniu
            geny = self.zgodne_geny(KIERUNEK_POKARMU, prog=0.5)
            for nr in geny[:1]:
                self.wchlon(nr, wek)
        if rodzic.dobre_miejsce is not None and self.dobre_miejsce is None:
            self.dobre_miejsce, self.dobre_ile = rodzic.dobre_miejsce, rodzic.dobre_ile * 0.5
        self.nauczone = getattr(self, "nauczone", 0) + 1

    def atrakcyjnosc(self):
        """Co widzi wybierająca: siła, kondycja, łowność. Z odrobiną przypadku."""
        return 0.5 * self.sila + 0.3 * self.kondycja() + 0.2 * getattr(self, "lownosc", 0.5) + random.gauss(0, 0.05)

    def zapamietaj_posilek(self):
        """Pamięć miejsca, w chwili jedzenia (nie cykl później i nie pod cudzym miejscem).
        Dobre miejsce: gdzie najadła się porządnie. Mapa pór roku: ile zwykle je tu o tej porze; chude wpisy wypadają."""
        if self.zjadl >= KOSZT_TRWANIA * 2 and self.zjadl >= self.dobre_ile * 0.7:
            self.dobre_miejsce, self.dobre_ile = self.miejsce, self.zjadl
        if self.pora is not None and self.miejsce is not None:
            m = self.mapa.setdefault(self.pora, {})
            k = str(self.miejsce)
            m[k] = 0.7 * m.get(k, self.zjadl) + 0.3 * self.zjadl
            if m[k] < KOSZT_TRWANIA * 0.5:
                m.pop(k, None)

    def najlepsze_z_mapy(self, pora, poza=None):
        """Najlepsze zapamiętane miejsce na tę porę roku (poza podanym). None, gdy nic nie pamięta."""
        m = self.mapa.get(pora) or {}
        kand = [(v, k) for k, v in m.items() if k != str(poza) and v >= KOSZT_TRWANIA * 1.5 and not self.omija(k)]
        return max(kand)[1] if kand else None

    def unika(self, nr):
        """Czy unika tej istoty (zrozumiane „unikaj istoty”, jeszcze nie wygasło)."""
        do = self.unikani.get(int(nr))
        if do is None:
            return False
        if do < self.wiek:
            self.unikani.pop(int(nr), None)
            return False
        return True

    def omija(self, miejsce):
        """Czy omija to miejsce („uwaga” w pamięci, jeszcze nie wygasła)."""
        do = self.unikaj.get(str(miejsce))
        if do is None:
            return False
        if do < self.wiek:
            self.unikaj.pop(str(miejsce), None)
            return False
        return True

    def rozmowa_z(self, inna):
        """Uczenie społeczne dorosłych: syci swoi w jednym miejscu wymieniają po jednym drobiazgu na cykl.
        Przez zachowanie, nie przez telepatię: z szumem, więc czasem błędnie. Swoi, bo obcym się nie ufa."""
        wybor = []
        if inna.slownik:
            wybor.append("slowo")
        if inna.dobre_miejsce is not None and inna.dobre_miejsce != self.dobre_miejsce:
            wybor.append("miejsce")
        if not wybor:
            return None
        co = random.choice(wybor)
        if co == "slowo":
            tekst, wek = random.choice(list(inna.slownik.items()))
            if tekst not in self.slownik:
                zaszum = [x + random.gauss(0, 0.05) for x in wek]      # przekaz z błędem
                self.slownik[tekst] = zaszum
                for nr in self.zgodne_geny(KIERUNEK_POKARMU, prog=0.5)[:1]:
                    self.wchlon(nr, zaszum)
                return "slowo:" + tekst
            return None
        if co == "miejsce" and random.random() < 0.5:                # nie każdą wskazówkę się przyjmuje
            self.dobre_miejsce, self.dobre_ile = inna.dobre_miejsce, inna.dobre_ile * 0.6
            return "miejsce"
        return None

    def kondycja(self):
        return max(0.0, min(1.0, self.energia / POJEMNOSC))

    def krok(self, dokad):
        self.poprzednie = self.miejsce
        self.miejsce = dokad
        self.staz = 0
        self.energia -= KOSZT_RUCHU
        self.ruszyl = True
        self.krokow += 1

    # --- cud ---
    def potomek(self, partner=None):
        """Rdzeń dziedziczony z przypadkiem. Powłoka, nawyki, echo: puste.
        Z partnerem: każdy gen losowo od jednego z dwojga rodziców."""
        nowy = self.K.copy()
        baza = getattr(self, "genow_bazowych", len(nowy))
        if partner is not None and partner.K.shape[1:] == self.K.shape[1:]:
            m = min(len(nowy), len(partner.K))                    # wspólne, homologiczne geny: bazowe i te same duplikaty
            od_partnera = np.random.random(m) < 0.5
            nowy[:m][od_partnera] = partner.K[:m][od_partnera]
            if len(partner.K) > len(nowy) and random.random() < 0.5:
                nowy = np.concatenate([nowy, partner.K[len(nowy):]])   # dłuższy kręgosłup partnera: duplikat wchodzi do linii
        if random.random() < DUPLIKACJA:                           # duplikacja: kopia genu na końcu, mutuje mocniej
            zrodlo_g = random.randrange(len(nowy))
            kopia = nowy[zrodlo_g] + np.random.normal(0.0, MUTACJA * MUTACJA_KOPII, nowy[zrodlo_g].shape)
            nowy = np.concatenate([nowy, kopia[None, ...]])
        elif len(nowy) > baza and random.random() < USUNIECIE:      # albo gen z ogona wypada zupełnie
            nowy = np.delete(nowy, random.randrange(baza, len(nowy)), axis=0)
        nowy = nowy + np.random.normal(0.0, MUTACJA, nowy.shape)
        for i in np.nonzero(np.random.random(len(nowy)) < NOWY_GEN)[0]:
            nowy[i] = np.asarray(losowa_macierz())
        oddane = self.energia / 3                    # poród: matka oddaje trzecią część, resztę dziecko dostaje przez karmienie
        self.energia -= oddane
        self.dzieci += 1
        d = Byt(nowy, oddane, self.pokolenie + 1)
        d.genow_bazowych = baza                     # baza linii się nie zmienia; różnica to ogon z duplikacji
        d.przybylo_genow = len(nowy) - len(self.K)  # +1 duplikacja, -1 utrata, 0 bez zmiany (do kroniki)
        d.rodzic = self.nr
        d.rodzic2 = partner.nr if partner is not None else None
        d.plec = random.choice(("n", "d"))
        zrodlo_st = partner if (partner is not None and random.random() < 0.5) else self
        d.stadnosc = max(0.0, min(1.0, zrodlo_st.stadnosc + random.gauss(0, 0.06)))   # gen stadności
        zrodlo_d = partner if (partner is not None and random.random() < 0.5) else self
        d.dlugowiecznosc = max(0.0, min(1.0, zrodlo_d.dlugowiecznosc + random.gauss(0, 0.06)))   # gen starzenia
        zrodlo_t = partner if (partner is not None and random.random() < 0.5) else self
        d.towarzyskosc = max(0.0, min(1.0, zrodlo_t.towarzyskosc + random.gauss(0, 0.06)))   # gen towarzyskości
        zrodlo_oz = partner if (partner is not None and random.random() < 0.5) else self
        d.ozdoba = max(0.0, min(1.0, zrodlo_oz.ozdoba + random.gauss(0, 0.06)))              # gen ozdoby
        zrodlo_g = partner if (partner is not None and random.random() < 0.5) else self
        d.gust = max(0.0, min(1.0, zrodlo_g.gust + random.gauss(0, 0.06)))                   # gen gustu (co się podoba)
        zrodlo_t2 = partner if (partner is not None and random.random() < 0.5) else self
        d.troska = max(0.0, min(1.0, zrodlo_t2.troska + random.gauss(0, 0.06)))              # gen troski
        zrodlo_o = partner if (partner is not None and random.random() < 0.5) else self
        d.odpornosc = max(0.0, min(1.0, zrodlo_o.odpornosc + random.gauss(0, 0.06)))          # gen odporności
        zrodlo_p = partner if (partner is not None and random.random() < 0.5) else self
        d.pojetnosc = max(0.0, min(1.0, zrodlo_p.pojetnosc + random.gauss(0, 0.06)))          # gen pojętności
        zrodlo_u = partner if (partner is not None and random.random() < 0.5) else self
        d.ufnosc = max(0.0, min(1.0, zrodlo_u.ufnosc + random.gauss(0, 0.06)))                 # gen ufności
        zrodlo_sz = partner if (partner is not None and random.random() < 0.5) else self
        d.szczerosc = max(0.0, min(1.0, zrodlo_sz.szczerosc + random.gauss(0, 0.06)))          # gen szczerości
        d.miejsce = self.miejsce
        d.poprzednie = None
        d.staz = max(2, self.staz)                  # rodzi się u siebie, nie jako przybysz
        zrodlo = partner if (partner is not None and random.random() < 0.5) else self
        d.wytrwalosc = max(1, zrodlo.wytrwalosc + random.choice((-1, 0, 0, 1)))   # gen ruchu, z mutacją
        zrodlo_s = partner if (partner is not None and random.random() < 0.5) else self
        d.sila = max(0.0, min(1.0, zrodlo_s.sila + random.gauss(0, 0.08)))       # gen siły, z mutacją
        zrodlo_c = partner if (partner is not None and random.random() < 0.5) else self
        d.ciekawosc = max(0.0, min(1.0, zrodlo_c.ciekawosc + random.gauss(0, 0.08)))   # gen zwiadu
        zrodlo_k = partner if (partner is not None and random.random() < 0.5) else self
        d.optimum = max(0.0, min(1.0, zrodlo_k.optimum + random.gauss(0, 0.05)))       # gen klimatu: optimum
        d.tolerancja = max(0.02, min(0.6, zrodlo_k.tolerancja + random.gauss(0, 0.04)))  # gen klimatu: tolerancja
        if partner is not None:
            partner.dzieci += 1
        return d

    # --- cykl ---
    def cykl(self, slowo=None, surowa=None, inny=None, partner=None, dwoje=False, inni=None, klimat=None):
        """klimat: {"koszt": mnożnik kosztu trwania (zimno/gorąco), "noc": bool} albo None."""
        klimat = klimat or {}
        noc = bool(klimat.get("noc", False))
        self.pora = klimat.get("pora", self.pora)
        if "temp" in klimat:
            # odporność na klimat: poza pasem tolerancji wokół optimum trwanie drożeje; szeroka tolerancja też kosztuje
            poza = max(0.0, abs(float(klimat["temp"]) - self.optimum) - self.tolerancja)
            mnoznik = 1.0 + 1.2 * poza + 0.25 * self.tolerancja
        else:
            mnoznik = float(klimat.get("koszt", 1.0))
        self.klimat_poprzedni = getattr(self, "klimat_koszt", 1.0)     # jak drogo było w poprzednim cyklu (do oceny skutku słów)
        self.klimat_koszt = round(mnoznik, 3)
        """Zwraca potomka, jeśli w tym cyklu nastąpił cud.
        slowo: sygnał ze świata. surowa: wspólna oferta świata (ilość), gdy bytów jest wielu.
        inny: (nr, wektor, czy_glos) — to, co wyszło z innego bytu, albo jego głos."""
        self.wiek += 1
        self.energia_start = self.energia           # do bilansu: czy po tym cyklu zostało jej więcej, czy mniej
        self.slyszy = False
        self.zjadl = 0.0
        self.czyn, self.czyn_do, self.czyn_cel, self.odpowiada = None, None, None, None   # nic z poprzedniego cyklu nie zostaje
        self.czyn_verb = self.czyn_skutek = None
        self.czyn_slowo = None                      # jakie słowo (klucz) wywołało czyn: do słownika świata
        self.czyn_obiekt = None
        self.gawedzi = False
        ilu_teraz = klimat.get("towarzystwo")
        if self.czeka_skutek:
            # warunkowanie: słowo znaczy to, co po nim nastąpiło. Skutek nie jest z listy — to wektor tego,
            # co naprawdę weszło w istotę w następnym cyklu (ile zjadła, czy bolało, czyje głosy), plus bilans energii.
            # Sumy rosną, więc długość sumy podzielona przez liczbę obserwacji mówi, jak powtarzalny jest skutek.
            v = np.asarray(getattr(self, "co_zaszlo", None) or [0.0] * ROZMIAR, dtype=float)
            dl = float(np.linalg.norm(v))
            if dl > 0:
                v = (v / dl).tolist()
                bil = getattr(self, "bilans", 0.0)
                for kl in self.czeka_skutek:
                    d = self.po_slowie.setdefault(kl, {"n": 0, "v": [0.0] * ROZMIAR, "b": 0.0})
                    d["n"] += 1
                    d["v"] = [a + b for a, b in zip(d["v"], v)]
                    d["b"] += bil
            self.czeka_skutek = []
            if len(self.po_slowie) > PAMIEC_SLOW:                 # pamięć skończona: najrzadsze skojarzenia blakną
                for kl in sorted(self.po_slowie, key=lambda k: self.po_slowie[k].get("n", 0))[:len(self.po_slowie) - PAMIEC_SLOW]:
                    del self.po_slowie[kl]
        if ilu_teraz is not None:
            self.towarzystwo_bylo = ilu_teraz                     # ilu było obok: do wykrycia, że ktoś przyszedł albo odszedł
        self.skad_wyjscia = {}                      # wektor wyjścia -> gen, z którego wypadł (do narodzin nowego dźwięku)
        self.gen_slowa = None                       # z którego genu wyszedł dźwięk, o którym mówi
        if surowa is None:
            oferta, ilosc = oferta_swiata(self.wiek)
        else:
            absorpcja = max(0.0, 1.0 - STARZENIE * (1.5 - self.dlugowiecznosc) * self.wiek)   # gen starzenia
            ilosc = surowa * absorpcja
            oferta = [(k + random.gauss(0, szum(SZUM_POKARMU))) * ilosc for k in KIERUNEK_POKARMU]
        nadmiar_genow = max(0, len(self.K) - getattr(self, "genow_bazowych", len(self.K)))   # geny z duplikacji: każdy kosztuje trwanie
        koszt_czuwania = KOSZT_TRWANIA * (1.0 + KOSZT_SILY * self.sila + 0.15 * self.dlugowiecznosc + KOSZT_POJETNOSCI * self.pojetnosc + 0.05 * self.towarzyskosc + KOSZT_GENU * nadmiar_genow + KOSZT_ODPORNOSCI * self.odpornosc + KOSZT_OZDOBY * self.ozdoba + ((self.chora[2] if len(self.chora) > 2 else KOSZT_CHOROBY) if self.chora else 0.0)) * mnoznik   # silna, zmarznięta, długowieczna, pojętna, towarzyska i obrośnięta genami płacą więcej

        def spij():
            self.spala = True
            self.energia -= KOSZT_SNU * mnoznik * (0.7 if noc else 1.0)   # śpi: oferta za mała albo noc
            self.sen += 1
            # marzenie senne: echa wracają i mieszają się ze sobą, a szum dokłada resztę. Powstaje sygnał,
            # którego nigdy nie było — a powłoka uczy się z niego tak samo jak z pokarmu czy z bólu.
            # Śpiąca budzi się zmieniona przez coś, co się nie zdarzyło. Bramki we śnie kosztują połowę.
            echa_snu = self.wracajace_echa()
            if echa_snu and self.energia > KOSZT_ODRUCHU:
                v = np.zeros(ROZMIAR)
                for e in echa_snu[:2]:
                    a = np.asarray(e, dtype=float)
                    v = v + a / (float(np.linalg.norm(a)) or 1.0)
                v = v + np.random.normal(0.0, SEN_SZUM, ROZMIAR)
                o_sn, w_sn, k_sn = self.kaskada(v.tolist(), BUDZET_SNU, zrodlo="sen")
                self.energia -= k_sn * 0.5
                self.do_echa(w_sn)                            # sen rodzi kolejne echa: marzenie wraca
                if w_sn:
                    self.snil = w_sn[0]                       # to, co zostało po śnie: rano można o tym mówić
            self.mowa = {"krzyk": False, "slowo": None, "glos": False, "wolanie": self.mowa.get("wolanie", False)}
            self.wyszlo = []                         # śpiąca nic nie wydaje
            self.cos = self.zapis("sen", ilosc, [], [], [], [], 0, slowo=slowo)

        if self.energia > SYTOSC:
            if self.energia > PROG_CUDU and (not dwoje or partner is not None):
                dziecko = self.potomek(partner)
                self.wyszlo = []
                self.cos = self.zapis("cud", ilosc, [], [], [], [], 0, dziecko=dziecko.nr, slowo=slowo)
                return dziecko
            pelnosc = (self.energia - SYTOSC) / (POJEMNOSC - SYTOSC)
            # gromadzenie na potomstwo: syta, ale poniżej progu cudu, nie śpi, gdy jest co jeść (hiperfagia przed rozrodem)
            gromadzi = self.energia < PROG_CUDU and ilosc >= KOSZT_TRWANIA and not noc
            # sen najwyżej jeden cykl z rzędu: potem musi wstać, choćby na chwilę
            if (ilosc <= HOJNOSC * (BUDZENIE + 2 * pelnosc) or noc) and not gromadzi and not self.spala:
                # czas wolny: syta, w dzień, z kimś w zasięgu słuchu, zamiast drzemać gawędzi (płaci za czuwanie, jak za wszystko)
                if not noc and klimat.get("towarzystwo", 0) > 0 and random.random() < GAWEDA * (0.4 + 1.2 * self.towarzyskosc):   # towarzyska gawędzi chętniej
                    self.gawedzi = True
                else:
                    spij()
                    return None
            # duża oferta budzi sytego: wstaje i je, gromadzi
        elif noc and ilosc < koszt_czuwania and not self.spala:
            # noc: głodna też odpoczywa, gdy żerowanie nie zwróci kosztu czuwania. Zwierzęta nie żerują nocą;
            # sen pali o połowę mniej. Bez tego pierwsza noc zabijała stado (24 z 32 zgonów jednej nocy).
            spij()
            return None
        self.spala = False
        self.energia -= koszt_czuwania
        # budżet na myślenie: część energii, ale nigdy więcej niż BUDZET_MAX na cykl.
        # Bez sufitu tańsze bramki oznaczały tyle samo wydatku: więcej otwarć za te same 30% zapasu.
        budzet = max(KOSZT_BRAMKI, min(BUDZET_MAX, SKAPSTWO * self.energia))
        glod = min(1.0, max(0.0, 1.0 - self.energia / SYTOSC))
        # apetyt zależy od zapasu, nie tylko od głodu: poniżej progu cudu syta je łapczywie (hiperfagia przed rozrodem),
        # dopiero z pełnym zapasem wybrzydza. Bez tego w 8 wymiarach syta przepuszczała 4 na 10 ofert.
        apetyt = max(glod, min(1.0, max(0.0, (PROG_CUDU - self.energia) / (PROG_CUDU - SYTOSC))))
        if self.pora == "jesien":
            apetyt = max(apetyt, APETYT_JESIENI)        # jesienne tuczenie: przed zimą je łapczywie, jak niedźwiedź
        smak = ZGODNOSC - apetyt * (ZGODNOSC - 0.5)
        s_rany = rana()
        if self.chora:
            s_rany = [x * 1.5 for x in s_rany]      # choroba boli: rana mocniejsza, więc częściej otwiera bramki
        if random.random() < apetyt:
            o_p, w_p, k_p = self.kaskada(oferta, budzet, prog=smak, zrodlo="pokarm"); budzet -= k_p
            o_r, w_r, k_r = self.kaskada(s_rany, budzet, zrodlo="rana"); budzet -= k_r
        else:
            o_r, w_r, k_r = self.kaskada(s_rany, budzet, zrodlo="rana"); budzet -= k_r
            o_p, w_p, k_p = self.kaskada(oferta, budzet, prog=smak, zrodlo="pokarm"); budzet -= k_p
        o_e, w_e, k_e = [], [], 0.0
        for e in self.wracajace_echa():
            o, w, k = self.kaskada(e, budzet, zrodlo="echo")
            budzet -= k; o_e += o; w_e += w; k_e += k
        # słowo ze świata: obcy sygnał
        o_s, w_s, k_s = [], [], 0.0
        if slowo is not None:
            s = slowo_na_wektor(slowo)
            self.slownik[slowo.strip().lower()] = s
            o_s, w_s, k_s = self.kaskada(s, budzet, zrodlo="slowo")
            budzet -= k_s
            self.slyszy = bool(o_s)
            if not o_s:
                # skojarzenie: geny otwarte przez to, co byt czuje, wchłaniają też słowo
                for nr in set(o_r + o_p + o_e):
                    self.wchlon(nr, s)
        # inne istoty: to, co z nich wyszło, jest dla mnie sygnałem. Słyszę wszystkie obok.
        o_i, w_i, k_i = [], [], 0.0
        sygnaly = list(inni) if inni else ([inny] if inny is not None else [])
        if sygnaly:
            budzet = max(budzet, BUDZET_SLUCHU * (0.5 + self.towarzyskosc))   # uwaga na innych rośnie z towarzyskością; słuch nie żyje z resztek
        self.czyn = None
        self.czyn_verb = self.czyn_skutek = None
        self.czyn_do = None
        otwarte_przez = {}
        wektory_od = {}
        slowa_od = {}                               # od kogo: identyfikator nowego dźwięku, jeśli to było takie słowo
        self.odpowiada = None                       # komu odpowiada własnym głosem
        self.czyn_cel = None
        for syg in sygnaly:
            if budzet < KOSZT_ODRUCHU:
                break
            typ_s = syg[2] if len(syg) > 2 else "wyjscie"
            o, w, k = self.kaskada(syg[1], budzet, prog=(SLUCH if typ_s in ("glos", "odpowiedz") else ZGODNOSC), zrodlo="inny")
            budzet -= k; k_i += k; w_i += w
            if o:
                o_i += o
                otwarte_przez.setdefault(syg[0], []).extend(o)
                wektory_od[syg[0]] = syg[1]
                if len(syg) > 4 and isinstance(syg[4], dict) and syg[4].get("slowo_id"):
                    slowa_od[syg[0]] = syg[4]["slowo_id"]
                if len(syg) > 4 and isinstance(syg[4], dict):
                    kl_ = klucz_slowa(syg[4].get("temat"), syg[4].get("cel"), syg[4].get("slowo_id"))
                    if kl_ and kl_ not in self.czeka_skutek and len(self.czeka_skutek) < 4:
                        self.czeka_skutek.append(kl_)             # usłyszane: skutek oceni następny cykl
                typ = syg[2] if len(syg) > 2 else "wyjscie"
                if typ == "glos" and self.odpowiada is None:
                    self.odpowiada = syg[0]                         # usłyszała głos: odpowiada swoim
                if self.czyn is None:
                    if typ == "alarm" and self.energia > SYTOSC / 2 and len(syg) > 3 and syg[3]:
                        self.czyn, self.czyn_verb, self.czyn_do, self.czyn_slowo = nazwa_czynu("bron"), "bron", syg[0], "@alarm"   # alarm swojego: idzie bronić
                    elif typ == "wolanie" and self.plec == "d" and self.energia > SYTOSC / 2 and (len(syg) < 4 or syg[3]):
                        self.czyn, self.czyn_verb, self.czyn_do, self.czyn_slowo = nazwa_czynu("chodz"), "chodz", syg[0], "@wolanie"   # wrodzone, przeciwna płeć
                    elif typ in ("glos", "odpowiedz"):
                        meta = syg[4] if len(syg) > 4 and isinstance(syg[4], dict) else {}
                        zr = self.zrodla.get(str(o[0]), {})
                        kl = klucz_slowa(meta.get("temat"), meta.get("cel"), meta.get("slowo_id"))
                        nauka = self.po_slowie.get(kl) if kl else None
                        nauczony, bilans_n = None, 0.0
                        if nauka and nauka.get("n", 0) >= 3:
                            pewnosc = float(np.linalg.norm(np.asarray(nauka["v"], dtype=float))) / nauka["n"]
                            if pewnosc >= 0.6:                    # skutek powtarzalny: wektory nie rozjeżdżają się
                                nauczony = znak_skutku(nauka["v"])  # skutek ma własne brzmienie, jak słowo
                                bilans_n = nauka["b"] / nauka["n"]
                        if meta.get("temat") == "klamca" and meta.get("cel") is not None and int(meta["cel"]) != self.nr:
                            # plotka o kłamcy: głos + głos kłamcy. Kto ją rozumie i ufa mówiącemu, przestaje wierzyć kłamcy
                            if random.random() < self.ufnosc:
                                self.klamcy.add(int(meta["cel"]))
                                self.czyn, self.czyn_verb, self.czyn_do, self.czyn_cel = nazwa_czynu("nie_wierz"), "nie_wierz", syg[0], int(meta["cel"])
                                self.czyn_slowo = klucz_slowa(meta.get("temat"), meta.get("cel"), meta.get("slowo_id"))
                        elif meta.get("temat") == "spichlerz" and (meta.get("spichlerz") or 0) > self.spichlerz * 1.2 and (meta.get("swoj") or random.random() < self.ufnosc):
                            # spichlerz przekazuje się tylko słowem, jak uprawa
                            self.spichlerz = max(self.spichlerz, min(float(meta["spichlerz"]), PRZEKAZ * (0.7 + 0.6 * self.pojetnosc) * float(meta["spichlerz"])))
                            self.czyn, self.czyn_verb, self.czyn_do = nazwa_czynu("gromadz"), "gromadz", syg[0]
                            self.czyn_slowo = klucz_slowa("spichlerz")
                        elif meta.get("temat") == "uprawa" and meta.get("uprawa", 0) > self.uprawa * 1.2 and (meta.get("swoj") or random.random() < self.ufnosc):
                            # przekaz umiejętności tylko słowem: kto zrozumiał mówiącą o uprawie, uczy się. Swoim wierzy bez wahania,
                            # obcym wg ufności. Pojętny bierze prawie wszystko, tępy część.
                            self.uprawa = max(self.uprawa, min(float(meta["uprawa"]), PRZEKAZ * (0.7 + 0.6 * self.pojetnosc) * float(meta["uprawa"])))
                            self.czyn, self.czyn_verb, self.czyn_do = nazwa_czynu("uprawiaj"), "uprawiaj", syg[0]
                            self.czyn_slowo = klucz_slowa("uprawa")
                        elif nauczony is not None:
                            # znaczenie z doświadczenia, nie z listy: słowo znaczy to, co po nim zwykle następowało.
                            # Każda istota uczy się osobno, więc to samo słowo może dla dwóch znaczyć co innego.
                            if meta.get("temat") in ("zapach", "bol", "choroba") and meta.get("cel") is not None:
                                obiekt_n, cel_n = "laka", str(meta["cel"])
                            elif meta.get("temat") == "inny" and meta.get("cel") is not None and int(meta["cel"]) != self.nr:
                                obiekt_n, cel_n = "istota", int(meta["cel"])
                            else:
                                obiekt_n, cel_n = "nadawca", syg[0]
                            # wartość skutku to bilans energii, jaki po nim zostawał: dobre przyciąga, złe odpycha,
                            # obojętne tylko się zapamiętuje. Nikt nie wpisał, co jest dobre — mówi o tym energia.
                            if bilans_n > 0.3 * KOSZT_TRWANIA:
                                verb_n = "idz" if glod >= GLOD_RUCHU else "zapamietaj"
                            elif bilans_n < -0.3 * KOSZT_TRWANIA:
                                verb_n = "unikaj"
                            else:
                                verb_n = "zapamietaj"
                            self.czyn, self.czyn_verb, self.czyn_skutek = nazwa_bo(verb_n, nauczony), verb_n, nauczony
                            self.czyn_do, self.czyn_cel, self.czyn_obiekt = syg[0], cel_n, obiekt_n
                            self.czyn_slowo = kl
                        elif zr:
                            # znaczenie składane, bez listy: CZASOWNIK z historii genu, który dźwięk otworzył (co go dotąd otwierało),
                            # PRZEDMIOT ze wskazania w słowie (łąka z zapachu albo bólu, istota z powtórzonego słowa, inaczej nadawca).
                            # Nowe znaczenie = nowa para, której nikt nie przewidział. Czyn wykonuje świat.
                            glowne = max(zr, key=zr.get)
                            czasownik = {"pokarm": "idz", "slowo": "idz", "rana": "unikaj", "echo": "zapamietaj", "inny": "odpowiedz"}.get(glowne)
                            if czasownik is not None:
                                if meta.get("temat") in ("zapach", "bol", "choroba") and meta.get("cel") is not None:
                                    obiekt, cel = "laka", str(meta["cel"])
                                elif meta.get("temat") == "inny" and meta.get("cel") is not None and int(meta["cel"]) != self.nr:
                                    obiekt, cel = "istota", int(meta["cel"])
                                else:
                                    obiekt, cel = "nadawca", syg[0]
                                if czasownik == "idz" and glod < GLOD_RUCHU:
                                    czasownik = "zapamietaj"                          # syta nie idzie za pokarmem, ale zapamiętuje
                                if czasownik == "odpowiedz":
                                    obiekt, cel = "nadawca", syg[0]                   # odpowiada się temu, kto mówił
                                nazwa = nazwa_czynu(czasownik, obiekt)
                                if nazwa:
                                    self.czyn, self.czyn_verb = nazwa, czasownik
                                    self.czyn_do, self.czyn_cel, self.czyn_obiekt = syg[0], cel, obiekt
                                    self.czyn_slowo = klucz_slowa(meta.get("temat"), meta.get("cel"), meta.get("slowo_id"))
            else:
                typ = syg[2] if len(syg) > 2 else "wyjscie"
                if typ in ("glos", "odpowiedz") and o_p:
                    # nagroda: głos słyszany przy jedzeniu wchodzi mocniej i tylko do genów pokarmu
                    for nr in set(o_p):
                        self.wchlon(nr, syg[1]); self.wchlon(nr, syg[1])
                else:
                    for nr in set(o_r + o_p + o_e):
                        self.wchlon(nr, syg[1])
        inny = sygnaly[0] if sygnaly else None
        self.do_echa(w_r + w_p + w_e + w_s + w_i)
        self.energia -= k_r + k_p + k_e + k_s + k_i
        nawyk = 1.0 - NAWYK ** self.otwarcia_genu[o_p[0]] if o_p else 0.0
        self.lownosc = self.jakosc(KIERUNEK_POKARMU)              # gen pokarmu: jak sprawnie zdobywa
        self.zjadl = wziete(ilosc, len(o_p), nawyk) * (0.5 + 0.5 * self.lownosc) * (0.55 if self.chora else 1.0)   # chora je gorzej: przy ciężkim szczepie energia wypala się szybciej, niż da się nadrobić
        self.energia = min(POJEMNOSC, self.energia + self.zjadl)
        self.zapamietaj_posilek()
        # uprawa łąki: nabyta umiejętność. Syta, która została na miejscu, pracuje (koszt) i podnosi odrost łąki (liczy świat).
        # Odkrycie: rzadki przypadek u sytej, która siedzi tu długo; częściej u pojętnej. Praktyka podnosi umiejętność.
        self.uprawiala = False
        if not self.ruszyl and self.energia > SYTOSC and not noc:
            if self.uprawa <= 0.0 and self.staz >= 3 and random.random() < ODKRYCIE_UPRAWY * self.ciekawosc * (0.5 + self.pojetnosc):
                self.uprawa = 0.2
                self.odkryla_uprawe = True
            if self.uprawa > 0.0:
                self.energia -= KOSZT_UPRAWY * self.uprawa
                self.uprawa = min(1.0, self.uprawa + PRAKTYKA)
                self.uprawiala = True
        # spichlerz: nabyta umiejętność. Syta odkłada część nadwyżki na łące (ze stratą), głodna bierze z zapasu łąki.
        # Odkrycie tylko jesienią (potrzeba matką wynalazku), u ciekawej i pojętnej, która siedzi na łące.
        self.odklada, self.pobiera, self.gromadzila = 0.0, 0.0, False
        if not self.ruszyl:
            if self.spichlerz <= 0.0 and self.pora == "jesien" and self.staz >= 3 and self.energia > SYTOSC and not noc \
                    and random.random() < ODKRYCIE_UPRAWY * self.ciekawosc * (0.5 + self.pojetnosc):
                self.spichlerz = 0.2
                self.odkryla_spichlerz = True
            if self.spichlerz > 0.0:
                if self.energia > SYTOSC + 2.0 and not noc and self.pora in ("lato", "jesien"):
                    self.odklada = min(3.0, ODKLADANIE * self.spichlerz * (self.energia - SYTOSC))
                    self.energia -= self.odklada
                    self.spichlerz = min(1.0, self.spichlerz + PRAKTYKA)
                    self.gromadzila = True
                elif self.energia < SYTOSC and klimat.get("zapas", 0.0) > 0.0:
                    self.pobiera = min(POBOR * self.spichlerz, SYTOSC - self.energia)
                    self.gromadzila = True
        self.otwarcia += len(o_r) + len(o_p) + len(o_e) + len(o_s) + len(o_i)
        self.najdluzsza = max(self.najdluzsza, len(o_r), len(o_p), len(o_e), len(o_s), len(o_i))
        self.wyszlo = w_r + w_p + w_e + w_s + w_i
        # o czym mówi: to, co w tym cyklu otworzyło najwięcej bramek albo najmocniej ją dotknęło.
        # Bez listy tematów: pokarm, rana, cudzy głos, zapach łąki (gdy się najadła), pora (gdy marznie), noc, przyłapany kłamca.
        kand = []
        if o_p:
            kand.append((len(o_p), "pokarm", list(KIERUNEK_POKARMU), None))
        if o_r and glod > 0.3:
            kand.append((len(o_r), "rana", list(s_rany), None))
        if klimat.get("zapach") is not None and self.zjadl >= KOSZT_TRWANIA * 2:
            kand.append((len(o_p) + 1, "zapach", list(klimat["zapach"]), str(self.miejsce)))
        if klimat.get("pora_syg") is not None and mnoznik > 1.2:
            kand.append((1, "pora", list(klimat["pora_syg"]), klimat.get("pora")))
        if klimat.get("spichlerz_syg") is not None and self.gromadzila:
            kand.append((50, "spichlerz", list(klimat["spichlerz_syg"]), None))   # o zapasach mówi się jak o pracy: tak się je przekazuje
        if klimat.get("uprawa_syg") is not None and self.uprawiala:
            kand.append((50, "uprawa", list(klimat["uprawa_syg"]), None))   # rzemieślnik gada o robocie: w każdym cyklu pracy (kłamca 10 i ból 9 i tak niżej)
        if klimat.get("noc_syg") is not None and noc:
            kand.append((1, "noc", list(klimat["noc_syg"]), None))
        if self.bolalo is not None:
            # ból ze świata: po starciu mówi o bólu i o zapachu tej łąki (rana + zapach), głośno, do 2 cykli
            m_, zap, ile = self.bolalo
            r_ = np.asarray(rana(), dtype=float); r_ = r_ / (float(np.linalg.norm(r_)) or 1.0)
            z_ = np.asarray(zap, dtype=float); z_ = z_ / (float(np.linalg.norm(z_)) or 1.0)
            kand.append((9, "bol", (r_ + z_).tolist(), str(m_)))
            self.bolalo = (m_, zap, ile - 1) if ile > 1 else None
        if getattr(self, "snil", None) is not None and sum(x * x for x in self.snil) > 0.5:
            kand.append((2.0, "sen", list(self.snil), znak_slowa(self.snil)))   # opowiada sen: dźwięk bez źródła w świecie
            self.snil = None
        if self.chora and klimat.get("choroba_syg") is not None:
            # o chorobie się mówi: chora na skażonej łące ostrzega przed tym miejscem (gorączka + zapach łąki),
            # poza ogniskiem mówi o samej gorączce. Nikt tego nie tłumaczy: to po prostu głośny temat.
            ch = np.asarray(klimat["choroba_syg"], dtype=float)
            ch = ch / (float(np.linalg.norm(ch)) or 1.0)
            if klimat.get("ognisko") and klimat.get("zapach") is not None:
                z2 = np.asarray(klimat["zapach"], dtype=float)
                z2 = z2 / (float(np.linalg.norm(z2)) or 1.0)
                kand.append((8, "choroba", (ch + z2).tolist(), str(self.miejsce)))
            else:
                kand.append((6, "choroba", ch.tolist(), None))
        if self.przylapala is not None:
            # przyłapany kłamca brzmi najgłośniej; temat czeka do 3 cykli, aż będzie okazja się odezwać
            kand.append((10, "klamca", list(self.przylapala[1]), self.przylapala[0]))
            self.przylapala = (self.przylapala[0], self.przylapala[1], self.przylapala[2] - 1) if len(self.przylapala) > 2 else (self.przylapala[0], self.przylapala[1], 2)
            if self.przylapala[2] <= 0:
                self.przylapala = None
        if otwarte_przez:
            od = max(otwarte_przez, key=lambda k: len(otwarte_przez[k]))
            kand.append((len(otwarte_przez[od]), "inny", list(wektory_od[od]), od))   # powtarza cudze słowo: tak się szerzy
        # rytualizacja: to, co z niej wyszło (skutek uboczny bramek), może stać się tematem, czyli nowym dźwiękiem.
        # Nikt go nie zaprojektował. Jeśli inni go podchwycą i coś za nim pójdzie, będzie słowem.
        wyjscia = [v for v in (w_r + w_p + w_e + w_i) if sum(x * x for x in v) > 0.5]
        if wyjscia:
            # nie sama siła: dźwięk z genu świeżego (mało otwieranego) przebija dźwięk z odruchu.
            # Inaczej nowy gen nigdy by się nie odezwał — zawsze zagłuszałyby go bramki wyćwiczone.
            def waga_echa(v):
                g = self.skad_wyjscia.get(tuple(v))
                nowosc = 1.0 if g is None or g >= len(self.otwarcia_genu) else 1.0 + 2.0 / (1.0 + self.otwarcia_genu[g])
                return sum(x * x for x in v) * nowosc
            e = max(wyjscia, key=waga_echa)
            self.gen_slowa = self.skad_wyjscia.get(tuple(e))
            kand.append((1.5, "echo", list(e), znak_slowa(e)))
        if self.gawedzi and kand:
            # gawęda: mówi się o niczym. Zwykle o własnym echu (nowy dźwięk), czasem powtarza cudze słowo; liczby bramek
            # (zawyżone przez kaskady) nie mają tu głosu. Kłamca (waga 10) i tak przebija.
            wolny = "echo" if random.random() < 0.6 else "inny"
            if self.uprawiala and random.random() < 0.5:
                wolny = "uprawa"                                                     # kto uprawia, w wolnym czasie opowiada o pracy
            kand = [((50 if k[1] == wolny else k[0]), *k[1:]) for k in kand]
        random.shuffle(kand)
        self.temat = max(kand, key=lambda k: k[0])[1:] if kand else None
        # identyfikator nowego dźwięku: własne echo dostaje nazwę; powtórzone cudze słowo niesie nazwę dalej
        self.slowo_id = None
        if self.temat is None or self.temat[0] != "echo":
            self.gen_slowa = None                   # mówi cudzym słowem albo o bólu: to nie są narodziny dźwięku
        if self.temat is not None:
            if self.temat[0] == "echo":
                self.slowo_id = self.temat[2]
            elif self.temat[0] == "inny":
                self.slowo_id = slowa_od.get(self.temat[2])
        self.mowa = self.co_mowi(glod)
        # co zaszło: wektor tego, co naprawdę weszło w istotę w tym cyklu — pokarm wg tego, ile zjadła,
        # ból wg tego, czy bolało, cudze głosy. Tego uczy się słowo usłyszane cykl wcześniej.
        zaszlo = np.zeros(ROZMIAR)
        dodatki = []                                  # rzeczy, które świat już nazywa: bez nich zima smakowałaby jak chudy posiłek
        if klimat.get("pora_syg") is not None and mnoznik > 1.05:
            dodatki.append((klimat["pora_syg"], min(1.0, mnoznik - 1.0)))          # pora roku, o ile daje się we znaki
        if klimat.get("spichlerz_syg") is not None and self.pobiera > 0:
            dodatki.append((klimat["spichlerz_syg"], min(1.0, self.pobiera / (KOSZT_TRWANIA * 2.0))))   # jadła z zapasu
        if klimat.get("uprawa_syg") is not None and self.uprawiala:
            dodatki.append((klimat["uprawa_syg"], 0.5))                            # pracowała na łące
        if klimat.get("noc_syg") is not None and noc:
            dodatki.append((klimat["noc_syg"], 0.4))                               # było ciemno
        if self.chora and klimat.get("choroba_syg") is not None:
            dodatki.append((klimat["choroba_syg"], 0.8))                           # gorączka: przeżycie ma własny smak
        if klimat.get("drapieznik") and klimat.get("drapieznik_syg") is not None:
            dodatki.append((klimat["drapieznik_syg"], 1.0))                        # ktoś poluje: to zostaje w pamięci
        for wek, waga in ([(oferta, min(1.0, self.zjadl / (KOSZT_TRWANIA * 2.0))), (s_rany, 1.0 if self.bolalo is not None else 0.25)]
                          + [(syg[1], 0.5) for syg in sygnaly[:4]] + dodatki):
            a = np.asarray(wek, dtype=float)
            dl_a = float(np.linalg.norm(a))
            if dl_a > 0 and waga > 0:
                zaszlo = zaszlo + a / dl_a * waga
        self.co_zaszlo = zaszlo.tolist()
        self.bilans = self.energia - getattr(self, "energia_start", self.energia)
        self.cos = self.zapis("jawa", ilosc, o_r, o_p, o_e, self.wyszlo, self.zjadl, glod=glod,
                              o_s=o_s, slowo=slowo,
                              inny=(lambda od: (od, otwarte_przez.get(od, []),
                                    next((x[2] for x in sygnaly if x[0] == od), "wyjscie")))(
                                        self.czyn_do if self.czyn_do is not None else (next(iter(otwarte_przez), inny[0]))) if inny else None,
                              czyn=self.czyn, inni=len(sygnaly))
        return None

    def co_mowi(self, glod):
        """Głodny krzyczy własną raną (wszyscy to rozumieją bez nauki).
        Poza tym mówi tylko słowami, które do niego dotarły: gdy to, co z niego
        wyszło, jest blisko któregoś z nich. Bez słów od ludzi: milczenie."""
        krzyk = glod > 0.6
        glos = self.zjadl >= KOSZT_TRWANIA or self.gawedzi or (self.temat is not None and self.temat[0] == "bol")   # najadła się, ma czas wolny albo boli: wydaje głos
        odpowiedz = getattr(self, "odpowiada", None)
        glos = glos or odpowiedz is not None       # albo odpowiada na czyjś głos
        slowo, najlepiej = None, ZGODNOSC
        for w in self.wyszlo:
            for tekst, wek in self.slownik.items():
                p = podobienstwo(w, wek)
                if p >= najlepiej:
                    slowo, najlepiej = tekst, p
        # wypowiedź: własny głos + sygnatura tematu, o tej samej sile co głos. Słuchacz słyszy jedno brzmienie.
        g = np.asarray(self.glos, dtype=float)
        ng = float(np.linalg.norm(g)) or 1.0
        if glos and self.temat is not None:
            tv = np.asarray(self.temat[1], dtype=float)
            nt = float(np.linalg.norm(tv)) or 1.0
            wyp = g + TEMAT_W_GLOSIE * tv / nt * ng
            wyp = wyp / (float(np.linalg.norm(wyp)) or 1.0) * ng
            self.wypowiedz = wyp.tolist()
            if self.temat[0] == "klamca":
                self.przylapala = None                 # powiedziała, co miała
        else:
            self.wypowiedz = g.tolist()
        return {"krzyk": krzyk, "slowo": slowo, "glos": glos, "znaki": glos_na_znaki(self.glos) if glos else None,
                "wolanie": self.mowa.get("wolanie", False), "odpowiedz": odpowiedz, "alarm": self.mowa.get("alarm", False),
                "temat": self.temat[0] if (glos and self.temat is not None) else None,
                "slowo_id": getattr(self, "slowo_id", None) if (glos and self.temat is not None) else None,
                "uprawa": round(self.uprawa, 2) if (glos and self.temat is not None and self.temat[0] == "uprawa") else None,
                "spichlerz": round(self.spichlerz, 2) if (glos and self.temat is not None and self.temat[0] == "spichlerz") else None,
                "cel": self.temat[2] if (glos and self.temat is not None) else None}

    def zapis(self, tryb, oferta, o_r, o_p, o_e, wyjscie, zjedzone, glod=0.0, dziecko=None,
              o_s=(), slowo=None, inny=None, czyn=None, inni=0):
        """Surowy zapis cyklu dla Keja. Bez znaczeń."""
        znane = lambda geny: [round(1 - NAWYK ** self.otwarcia_genu[g], 2) for g in geny]
        return {
            "byt": self.nr, "pokolenie": self.pokolenie, "wiek": self.wiek, "tryb": tryb,
            "energia": round(self.energia, 2), "glod": round(glod, 2),
            "pelnosc": round(max(0.0, (self.energia - SYTOSC) / (POJEMNOSC - SYTOSC)), 2),
            "oferta": round(oferta, 2), "zjedzone": round(zjedzone, 2),
            "rana": {"geny": o_r, "znane": znane(o_r)},
            "pokarm": {"geny": o_p, "znane": znane(o_p)},
            "echo": {"geny": o_e, "znane": znane(o_e), "w_kolejce": len(self.echo)},
            "slowo": {"tekst": slowo, "geny": list(o_s), "znane": znane(o_s)},
            "inny": {"od": inny[0], "geny": list(inny[1]), "typ": inny[2] if len(inny) > 2 else "wyjscie",
                     "glos": (inny[2] == "glos") if len(inny) > 2 else False, "czyn": czyn} if inny else None,
            "mowa": dict(self.mowa), "inni": inni,
            "miejsce": self.miejsce, "ruszyl": self.ruszyl, "karmione": round(getattr(self, "karmione", 0.0), 2),
            "lownosc": round(getattr(self, "lownosc", 0.0), 3), "sila": round(self.sila, 2), "ciekawosc": round(self.ciekawosc, 2),
            "klimat_koszt": getattr(self, "klimat_koszt", 1.0), "nauczone": getattr(self, "nauczone", 0), "plec": self.plec, "stadnosc": round(self.stadnosc, 2), "dlugowiecznosc": round(self.dlugowiecznosc, 2), "ufnosc": round(self.ufnosc, 2), "szczerosc": round(self.szczerosc, 2), "pojetnosc": round(self.pojetnosc, 2), "towarzyskosc": round(self.towarzyskosc, 2), "przechodzi": self.przechodzi, "deklaruje": self.deklaruje, "uprawa": round(self.uprawa, 2), "uprawiala": self.uprawiala, "gawedzi": self.gawedzi, "spichlerz": round(self.spichlerz, 2), "odklada": round(self.odklada, 2), "pobiera": round(self.pobiera, 2),
            "wyszlo": [],                                   # wektory wyjść nie idą do dziennika: nikt ich nie czyta, a ważyły trzecią część wpisu
            "dziecko": dziecko, "zyje": self.energia > 0,
        }

    def zyje(self):
        return self.energia > 0


def receptor(kierunek):
    """Gen zbudowany, nie wylosowany: przepuszcza swój kierunek prawie bez zmian."""
    return [[2.0 * kierunek[i] * kierunek[j] + random.gauss(0, 0.05) for j in range(ROZMIAR)]
            for i in range(ROZMIAR)]


def pierwszy_cud(ile_genow=ILE_GENOW, max_prob=300):
    """Losuj rdzeń, aż są receptory rany i pokarmu. W wielu wymiarach losowanie
    nie skończyłoby się nigdy: wtedy cud buduje oba receptory sam. Zwraca (byt, ile losowań).
    Budżet losowań maleje z liczbą genów i wymiarów, żeby cud nie trwał godzin."""
    proby = 0
    max_prob = max(1, min(max_prob, int(2_000_000 / (ile_genow * ROZMIAR * ROZMIAR))))
    licznik = Byt.licznik
    while proby < max_prob:
        proby += 1
        b = Byt([losowa_macierz() for _ in range(ile_genow)], SYTOSC * START, 1)
        if b.zgodne_geny(KIERUNEK_RANY) and b.zgodne_geny(KIERUNEK_POKARMU) and b.zgodne_geny(KIERUNEK_WOLANIA) and b.zgodne_geny(KIERUNEK_GLOSU, prog=SLUCH):
            Byt.licznik = licznik + 1
            b.nr = Byt.licznik
            return b, proby
    Byt.licznik = licznik
    geny = [losowa_macierz() for _ in range(ile_genow)]
    miejsca = random.sample(range(ile_genow), min(4, ile_genow))
    for i, kierunek in zip(miejsca, (KIERUNEK_RANY, KIERUNEK_POKARMU, KIERUNEK_WOLANIA, KIERUNEK_GLOSU)):
        geny[i] = receptor(kierunek)                # receptor głosu gatunku: rodzi się ze słuchem na swoich
    b = Byt(geny, SYTOSC * START, 1)
    return b, proby


if __name__ == "__main__":
    # --- cud pierwszy: losuj rdzeń, aż są receptory rany i pokarmu ---
    pierwszy, proby = pierwszy_cud(ILE_GENOW)
    Byt.licznik = 1
    pierwszy.nr = 1
    print(f"cud pierwszy: {proby} losowań\n")

    zywi = [pierwszy]
    zmarli = []
    najwiecej = 1
    for t in range(1, CYKLE_SWIATA + 1):
        dryf_swiata()
        nowi = []
        for b in zywi:
            dziecko = b.cykl()
            if dziecko:
                nowi.append(dziecko)
        for b in zywi:
            if not b.zyje():
                zmarli.append(b)
        zywi = [b for b in zywi if b.zyje()] + nowi
        najwiecej = max(najwiecej, len(zywi))
        if t % 25 == 0 or not zywi:
            pok = max((b.pokolenie for b in zywi), default=0)
            print(f"świat {t:4d}  żywych {len(zywi):3d}  zmarłych {len(zmarli):3d}  pokolenie {pok}")
        if not zywi:
            break

    wszyscy = zmarli + zywi
    print(f"\nkoniec świata po {t} cyklach. bytów w sumie: {len(wszyscy)}, "
          f"najwięcej naraz: {najwiecej}, pokoleń: {max(b.pokolenie for b in wszyscy)}, "
          f"linia {'żyje' if zywi else 'wygasła'}.")
    print(f"średnie życie: {(sum(b.wiek for b in zmarli) / len(zmarli)) if zmarli else 0:.1f} cykli, "
          f"średnio otwarć: {sum(b.otwarcia for b in wszyscy) / len(wszyscy):.0f}, "
          f"rodziców: {sum(1 for b in wszyscy if b.dzieci)}")
