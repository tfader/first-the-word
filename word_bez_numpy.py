"""Word: prawa świata i byt. Symulacja wielu światów: python3 word.py. Życie: zycie.py."""
import os
import random

ILE_GENOW = int(os.environ.get("GENY", 8))
ROZMIAR = int(os.environ.get("WYMIARY", 4))


def ustaw_wymiary(n):
    """Wymiary świata ustala się raz, przy cudzie. Wczytywane z ciała świata."""
    global ROZMIAR
    ROZMIAR = int(n)
CYKLE_SWIATA = int(os.environ.get("CYKLE", 300))

# --- prawa świata ---
SYTOSC = 10.0                # tyle energii ma byt na starcie; poniżej zaczyna się głód
KOSZT_TRWANIA = 1.0          # każdy cykl kosztuje
KOSZT_SNU = 0.5              # spoczynek to złudzenie: też kosztuje, tylko mniej
STARZENIE = 0.01             # o tyle maleje zdolność absorpcji co cykl
KOSZT_BRAMKI = 0.5           # otwarcie bramki kosztuje
NAWYK = 0.8                  # każde kolejne otwarcie tego samego genu kosztuje tyle razy mniej
KOSZT_ODRUCHU = 0.1          # ale nigdy mniej niż tyle
ZGODNOSC = 0.9               # jak bardzo sygnał musi "pasować" do genu
SKAPSTWO = 0.3               # najwyżej taką część energii byt wyda w cyklu na bramki
WCHLANIANIE = 0.2            # ile sygnału powłoka wchłania przy otwarciu
SKUPIENIE = 1                # ile genów naraz może odpowiedzieć na jeden sygnał
SZUM_RANY = 0.1              # rana zawsze boli tak samo, z lekkim szumem
SZUM_POKARMU = 0.3           # pokarm smakuje podobnie, ale bardziej zmiennie
HOJNOSC = 3.0                # średnia oferta świata; byt bierze z niej tylko część
POWROT_ECHA = 0.3            # szansa, że dane echo wróci w tym cyklu
ECHA_NA_CYKL = 2             # najwyżej tyle ech wraca w jednym cyklu
ZNIEKSZTALCENIE = 0.15       # szum echa rośnie o tyle na każdy cykl czekania
SLABNIECIE = 0.8             # siła echa maleje tyle razy na cykl czekania
SILA_MIN = 0.1               # ale nigdy do zera
SUFIT_ECHA = 100             # praktyczny sufit kolejki
PROG_CUDU = 2.0 * SYTOSC     # przy takiej nadwyżce byt powołuje potomka
POJEMNOSC = 3.0 * SYTOSC     # więcej byt nie zmieści, nadmiar przepada
BUDZENIE = 0.5               # syty budzi się na ofertę > HOJNOSC * (BUDZENIE + 2 * pełność)
DRYFT = float(os.environ.get("DRYFT", 0.03))                 # o tyle na cykl świata przesuwa się smak pokarmu
MUTACJA = 0.1                # jak mocno potomek odchyla się od rodzica
MIEJSC = 16                  # świat to koło z tylu miejsc
KOSZT_RUCHU = 0.3            # przejście do sąsiedniego miejsca
GLOD_RUCHU = 0.25            # poniżej takiego głodu byt nie rusza się z miejsca
ODRASTANIE = 0.10            # gęstość pokarmu wraca do żyzności o tyle na cykl
WYJADANIE = 0.005            # zjedzenie 1 energii wyjada tyle gęstości
NOWY_GEN = 0.02              # szansa, że gen potomka jest całkiem nowy, losowy


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
SZUM_WOLANIA = 0.15


def wolanie():
    return [k + random.gauss(0, SZUM_WOLANIA) for k in KIERUNEK_WOLANIA]


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
    """Głos istoty: suma pierwszych wierszy kilku pierwszych genów, znormalizowana."""
    k = [0.0] * ROZMIAR
    for gen in kregoslup[:8]:
        for i in range(ROZMIAR):
            k[i] += gen[0][i]
    d = sum(x * x for x in k) ** 0.5 or 1.0
    return [x / d for x in k]


def glos_na_znaki(glos):
    """Cztery znaki z ośmiu: znak i wielkość każdej składowej. Bez tłumaczenia."""
    out = []
    for x in glos:
        i = (0 if x >= 0 else 4) + min(3, int(abs(x) * 4))
        out.append(ZNAKI[i])
    return "".join(out)


def rana():
    return [(k + random.gauss(0, SZUM_RANY)) * KOSZT_TRWANIA for k in KIERUNEK_RANY]


def oferta_swiata(wiek):
    surowa = random.expovariate(1.0 / HOJNOSC)
    absorpcja = max(0.0, 1.0 - STARZENIE * wiek)
    ilosc = surowa * absorpcja
    return [(k + random.gauss(0, SZUM_POKARMU)) * ilosc for k in KIERUNEK_POKARMU], ilosc


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
        self.kregoslup = kregoslup                                   # rdzeń: stały
        self.powloka = [[[0.0] * ROZMIAR for _ in range(ROZMIAR)] for _ in kregoslup]
        self.otwarcia_genu = [0] * len(kregoslup)
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
        self.zle = 0
        self.idzie = False
        self.krokow = 0
        self.srednio = KOSZT_TRWANIA * 2            # na start ufa miejscu, w którym się urodził
        self.poprzednio_zjadl = 0.0
        self.ruszyl = False
        self.mowa = {"krzyk": False, "slowo": None, "glos": False, "wolanie": False}   # co mówi światu po tym cyklu
        self.czyn = None                    # co sygnał innej istoty kazał jej zrobić
        self.glos = glos_z_rdzenia(kregoslup)   # własny głos: z rdzenia, więc dziedziczny

    # --- geny ---
    def przez_gen(self, nr, s):
        return [sum((self.kregoslup[nr][i][j] + self.powloka[nr][i][j]) * s[j]
                    for j in range(ROZMIAR)) for i in range(ROZMIAR)]

    def wchlon(self, nr, s):
        d = sum(x * x for x in s) ** 0.5 or 1.0
        k = [x / d for x in s]
        for i in range(ROZMIAR):
            for j in range(ROZMIAR):
                self.powloka[nr][i][j] += WCHLANIANIE * k[i] * k[j]

    def koszt_bramki(self, nr):
        return max(KOSZT_ODRUCHU, KOSZT_BRAMKI * NAWYK ** self.otwarcia_genu[nr])

    def zgodne_geny(self, s, pomin=(), prog=ZGODNOSC):
        kandydaci = []
        for nr in range(len(self.kregoslup)):
            if nr in pomin:
                continue
            p = podobienstwo(self.przez_gen(nr, s), s)
            if p >= prog:
                kandydaci.append((self.otwarcia_genu[nr], p, nr))
        kandydaci.sort(reverse=True)
        return [nr for _, _, nr in kandydaci[:SKUPIENIE]]

    def kaskada(self, sygnal, budzet, prog=ZGODNOSC, zrodlo=None):
        otwarte, wyjscie, koszt = [], [], 0.0
        fala = [sygnal]
        while fala:
            nastepna = []
            for s in fala:
                trafione = self.zgodne_geny(s, pomin=otwarte, prog=prog)
                if not trafione:
                    wyjscie.append(s)
                for nr in trafione:
                    c = self.koszt_bramki(nr)
                    if budzet < c:
                        wyjscie.append(s)
                        return otwarte, wyjscie, koszt
                    budzet -= c
                    koszt += c
                    otwarte.append(nr)
                    self.otwarcia_genu[nr] += 1
                    if zrodlo:
                        z = self.zrodla.setdefault(str(nr), {})
                        z[zrodlo] = z.get(zrodlo, 0) + 1
                    nastepna.append(self.przez_gen(nr, s))
                    self.wchlon(nr, s)
            fala = nastepna
        return otwarte, wyjscie, koszt

    # --- echo ---
    def do_echa(self, wektory):
        for w in wektory:
            d = sum(x * x for x in w) ** 0.5
            if d > 0:
                self.echo.append(([x / d for x in w], d, self.wiek))
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
        self.poprzednio_zjadl = self.zjadl
        return self.idzie and self.energia > KOSZT_RUCHU

    def krok(self, dokad):
        self.poprzednie = self.miejsce
        self.miejsce = dokad
        self.energia -= KOSZT_RUCHU
        self.ruszyl = True
        self.krokow += 1

    # --- cud ---
    def potomek(self, partner=None):
        """Rdzeń dziedziczony z przypadkiem. Powłoka, nawyki, echo: puste.
        Z partnerem: każdy gen losowo od jednego z dwojga rodziców."""
        nowy = []
        for i, gen in enumerate(self.kregoslup):
            if partner is not None and i < len(partner.kregoslup) and random.random() < 0.5:
                gen = partner.kregoslup[i]
            if random.random() < NOWY_GEN:
                nowy.append(losowa_macierz())
            else:
                nowy.append([[x + random.gauss(0, MUTACJA) for x in wiersz] for wiersz in gen])
        oddane = self.energia / 2
        self.energia -= oddane
        self.dzieci += 1
        d = Byt(nowy, oddane, self.pokolenie + 1)
        d.rodzic = self.nr
        d.rodzic2 = partner.nr if partner is not None else None
        d.miejsce = self.miejsce
        d.poprzednie = None
        zrodlo = partner if (partner is not None and random.random() < 0.5) else self
        d.wytrwalosc = max(1, zrodlo.wytrwalosc + random.choice((-1, 0, 0, 1)))   # gen ruchu, z mutacją
        if partner is not None:
            partner.dzieci += 1
        return d

    # --- cykl ---
    def cykl(self, slowo=None, surowa=None, inny=None, partner=None, dwoje=False):
        """Zwraca potomka, jeśli w tym cyklu nastąpił cud.
        slowo: sygnał ze świata. surowa: wspólna oferta świata (ilość), gdy bytów jest wielu.
        inny: (nr, wektor, czy_glos) — to, co wyszło z innego bytu, albo jego głos."""
        self.wiek += 1
        self.slyszy = False
        self.zjadl = 0.0
        if surowa is None:
            oferta, ilosc = oferta_swiata(self.wiek)
        else:
            absorpcja = max(0.0, 1.0 - STARZENIE * self.wiek)
            ilosc = surowa * absorpcja
            oferta = [(k + random.gauss(0, SZUM_POKARMU)) * ilosc for k in KIERUNEK_POKARMU]
        if self.energia > SYTOSC:
            if self.energia > PROG_CUDU and (not dwoje or partner is not None):
                dziecko = self.potomek(partner)
                self.cos = self.zapis("cud", ilosc, [], [], [], [], 0, dziecko=dziecko.nr)
                return dziecko
            pelnosc = (self.energia - SYTOSC) / (POJEMNOSC - SYTOSC)
            if ilosc <= HOJNOSC * (BUDZENIE + 2 * pelnosc):
                self.energia -= KOSZT_SNU          # śpi: oferta za mała, żeby wstać
                self.sen += 1
                self.mowa = {"krzyk": False, "slowo": None, "glos": False}
                self.cos = self.zapis("sen", ilosc, [], [], [], [], 0, slowo=slowo)
                return None
            # duża oferta budzi sytego: wstaje i je, gromadzi
        self.energia -= KOSZT_TRWANIA
        budzet = max(KOSZT_BRAMKI, SKAPSTWO * self.energia)
        glod = min(1.0, max(0.0, 1.0 - self.energia / SYTOSC))
        smak = ZGODNOSC - glod * (ZGODNOSC - 0.5)
        s_rany = rana()
        if random.random() < glod:
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
        # inny byt: to, co z niego wyszło, jest dla mnie sygnałem. Widzimy się.
        o_i, w_i, k_i = [], [], 0.0
        if inny is not None:
            o_i, w_i, k_i = self.kaskada(inny[1], budzet, zrodlo="inny")
            budzet -= k_i
            if not o_i:
                for nr in set(o_r + o_p + o_e):
                    self.wchlon(nr, inny[1])
        self.do_echa(w_r + w_p + w_e + w_s + w_i)
        self.energia -= k_r + k_p + k_e + k_s + k_i
        nawyk = 1.0 - NAWYK ** self.otwarcia_genu[o_p[0]] if o_p else 0.0
        self.zjadl = wziete(ilosc, len(o_p), nawyk)
        self.energia = min(POJEMNOSC, self.energia + self.zjadl)
        self.otwarcia += len(o_r) + len(o_p) + len(o_e) + len(o_s) + len(o_i)
        self.najdluzsza = max(self.najdluzsza, len(o_r), len(o_p), len(o_e), len(o_s), len(o_i))
        self.wyszlo = w_r + w_p + w_e + w_s + w_i
        self.mowa = self.co_mowi(glod)
        self.czyn = None
        if inny is not None and o_i:
            typ = inny[2] if len(inny) > 2 else "wyjscie"
            if typ == "wolanie" and self.energia > SYTOSC / 2:
                self.czyn = "chodź do mnie"              # wrodzone: syta idzie do wołającej
            elif typ == "glos" and glod >= GLOD_RUCHU:
                zr = self.zrodla.get(str(o_i[0]), {})
                if zr and max(zr, key=zr.get) == "pokarm":
                    self.czyn = "chodź, tu pokarm"        # wyuczone: głos otworzył gen pokarmu
        self.cos = self.zapis("jawa", ilosc, o_r, o_p, o_e, self.wyszlo, self.zjadl, glod=glod,
                              o_s=o_s, slowo=slowo, inny=(inny[0], o_i, inny[2] if len(inny) > 2 else "wyjscie") if inny else None,
                              czyn=self.czyn)
        return None

    def co_mowi(self, glod):
        """Głodny krzyczy własną raną (wszyscy to rozumieją bez nauki).
        Poza tym mówi tylko słowami, które do niego dotarły: gdy to, co z niego
        wyszło, jest blisko któregoś z nich. Bez słów od ludzi: milczenie."""
        krzyk = glod > 0.6
        glos = self.zjadl >= KOSZT_TRWANIA          # najadła się: wydaje głos
        slowo, najlepiej = None, ZGODNOSC
        for w in self.wyszlo:
            for tekst, wek in self.slownik.items():
                p = podobienstwo(w, wek)
                if p >= najlepiej:
                    slowo, najlepiej = tekst, p
        return {"krzyk": krzyk, "slowo": slowo, "glos": glos, "znaki": glos_na_znaki(self.glos) if glos else None,
                "wolanie": self.mowa.get("wolanie", False)}

    def zapis(self, tryb, oferta, o_r, o_p, o_e, wyjscie, zjedzone, glod=0.0, dziecko=None,
              o_s=(), slowo=None, inny=None, czyn=None):
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
            "mowa": dict(self.mowa),
            "miejsce": self.miejsce, "ruszyl": self.ruszyl,
            "wyszlo": [[round(x, 2) for x in w] for w in wyjscie],
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
    while proby < max_prob:
        proby += 1
        b = Byt([losowa_macierz() for _ in range(ile_genow)], SYTOSC, 1)
        if b.zgodne_geny(KIERUNEK_RANY) and b.zgodne_geny(KIERUNEK_POKARMU) and b.zgodne_geny(KIERUNEK_WOLANIA):
            return b, proby
    geny = [losowa_macierz() for _ in range(ile_genow)]
    miejsca = random.sample(range(ile_genow), min(3, ile_genow))
    for i, kierunek in zip(miejsca, (KIERUNEK_RANY, KIERUNEK_POKARMU, KIERUNEK_WOLANIA)):
        geny[i] = receptor(kierunek)
    b = Byt(geny, SYTOSC, 1)
    return b, proby


if __name__ == "__main__":
    # --- cud pierwszy: losuj rdzeń, aż są receptory rany i pokarmu ---
    proby = 0
    while True:
        proby += 1
        pierwszy = Byt([losowa_macierz() for _ in range(ILE_GENOW)], SYTOSC, 1)
        if pierwszy.zgodne_geny(KIERUNEK_RANY) and pierwszy.zgodne_geny(KIERUNEK_POKARMU):
            break
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
    print(f"średnie życie: {sum(b.wiek for b in zmarli) / len(zmarli):.1f} cykli, "
          f"średnio otwarć: {sum(b.otwarcia for b in wszyscy) / len(wszyscy):.0f}, "
          f"rodziców: {sum(1 for b in wszyscy if b.dzieci)}")
