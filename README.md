# Word

A small world that runs on its own: beings made of gene-matrices eat, age, speak, fall ill and die —
and the words they invent get their meaning from what happened next. Nobody writes the dictionary; selection does.

Świat, który toczy się sam: istoty zbudowane z macierzy-genów jedzą, starzeją się, mówią, chorują i umierają —
a słowa, które wymyślają, biorą znaczenie z tego, co po nich nastąpiło. Nikt nie pisze słownika; robi to dobór.

**[What this is and how it works →](IDEA.md)** · **[Czym to jest i jak działa →](IDEA.md)**

---

## English

### Requirements

Python 3.9 or newer and `numpy`. Nothing else — no internet, no database, no build step.

    pip3 install numpy

### Run it

    python3 serwer.py

Open <http://localhost:8080> and press the button to call a world into being. That is all: the server starts
the life process itself. In the form you choose how many genes, how many dimensions a signal has, how many
beings to begin with, how large the world is, how many it can hold at once, and **which language** it names
its meanings in (`pl` / `en`).

To keep it running after you close the terminal:

    nohup python3 serwer.py >> serwer.log 2>&1 &

The command line is only needed if you want to start the world without the page:

    CYKL=5.0 GENY=64 WYMIARY=8 ISTOT=32 ROZMIAR=rozlegly POJEMNOSC_SWIATA=500 JEZYK=en python3 zycie.py

All of those settings matter only when a **new** world is born. Once `swiat.json` exists, the world returns
to its own body and reads them from there; only `CYKL` (seconds per cycle) still applies.

### Stop it

The world saves itself at the end of every cycle, so stopping costs one cycle at most:

    kill $(cat zycie.pid)
    kill $(cat serwer.pid)

There is also a **stop the world** button on the page, with a confirmation.

### Look at a past world

Finished worlds are kept in `swiaty/<number>/`:

    SWIAT=49 PORT=8081 python3 serwer.py

Read-only: anything that would change the world is refused.

### What lives where

- `word.py` — the being: genes, gates, cascade, shell, speech, meanings
- `zycie.py` — the world: meadows, seasons, plagues, predators, birth and death
- `serwer.py` — the viewer: a local HTTP server and its JSON API
- `strona/` — the page (Polish and English, switchable)
- [`IDEA.md`](IDEA.md) — what this is and how the mechanics work, in both languages
- `WORD.md` — the project's diary: every decision, why it was made, what it measured
- `JAK_URUCHOMIC.md` — the long version of this file (in Polish)
- `*_przed_przegladem.py`, `word_bez_numpy.py`, `strona/_stara_glowna.html` — earlier drafts, kept as history
- `zbuduj.py`, `strona/bytek.html` — an abandoned build for a hosted page; no longer maintained

The world writes its data next to the code (`swiat.json`, `cialo/`, `swiaty/`, journals). None of it belongs
in the repository — `.gitignore` keeps it out. A fresh clone has no world; it makes one on first run.

### Contributing

The world is far from finished and every layer of it can be taken further — this is an open invitation.

What is worth doing next is written down in `WORD.md` under **Odłożone** (things set aside): more verbs
and objects in meanings, sentences carrying two topics at once, division of labour, stories passed between
generations, crossing-over inside a gene. Beyond that: whatever you think this world is missing.

Two things worth knowing before you start:

- **Read `WORD.md` first.** Every piece carries its reasoning, usually with the measurement that settled it. The project
  is closer to biology than to engineering: a change is judged by what the world does with it, not by how
  clean the code looks. Run the world, measure the result, and include the numbers in the pull request.
- **Nothing in this world is designed.** Genes come from multiplying random matrices, meanings come from
  experience, and what is good is decided by energy. If your change writes down an answer that selection was
  supposed to find, it is probably the wrong change.

Issues, pull requests, forks and worlds run on entirely different settings are all welcome here.

### License

MIT — see [`LICENSE`](LICENSE).

---

## Polski

### Czego potrzeba

Python 3.9 lub nowszy i `numpy`. Nic więcej — bez internetu, bez bazy danych, bez budowania.

    pip3 install numpy

### Uruchomienie

    python3 serwer.py

Otwórz <http://localhost:8080> i przyciskiem powołaj świat. To wszystko: serwer sam uruchamia proces życia.
W formularzu wybierasz, ile genów, ile wymiarów ma sygnał, ile istot na początek, jak duży jest świat,
ilu najwyżej uniesie i **w jakim języku** nazywa swoje znaczenia (`pl` / `en`).

Żeby działał po zamknięciu terminala:

    nohup python3 serwer.py >> serwer.log 2>&1 &

Linia komend jest potrzebna tylko wtedy, gdy chcesz powołać świat bez strony:

    CYKL=5.0 GENY=64 WYMIARY=8 ISTOT=32 ROZMIAR=rozlegly POJEMNOSC_SWIATA=500 JEZYK=pl python3 zycie.py

Te ustawienia liczą się **tylko przy powoływaniu nowego świata**. Gdy `swiat.json` już istnieje, świat wraca
do swojego ciała i bierze je stamtąd; zostaje tylko `CYKL` (sekundy na cykl).

### Zatrzymanie

Świat zapisuje się sam na końcu każdego cyklu, więc zatrzymanie kosztuje najwyżej jeden:

    kill $(cat zycie.pid)
    kill $(cat serwer.pid)

Na stronie jest też przycisk **zatrzymaj świat**, z potwierdzeniem.

### Podgląd dawnego świata

Zakończone światy leżą w `swiaty/<numer>/`:

    SWIAT=49 PORT=8081 python3 serwer.py

Tylko do oglądania: wszystko, co zmienia świat, jest odmawiane.

### Co gdzie mieszka

- `word.py` — istota: geny, bramki, kaskada, powłoka, mowa, znaczenia
- `zycie.py` — świat: łąki, pory roku, zarazy, drapieżniki, narodziny i śmierć
- `serwer.py` — podgląd: lokalny serwer HTTP i jego API
- `strona/` — strona (polski i angielski, przełączane)
- [`IDEA.md`](IDEA.md) — czym to jest i jak działa mechanika, w obu językach
- `WORD.md` — dziennik projektu: każda decyzja, dlaczego zapadła, co zmierzyła
- `JAK_URUCHOMIC.md` — dłuższa wersja tego pliku
- `*_przed_przegladem.py`, `word_bez_numpy.py`, `strona/_stara_glowna.html` — wcześniejsze wersje, zostawione jako historia
- `zbuduj.py`, `strona/bytek.html` — porzucona wersja strony dla claude.ai; nieutrzymywana

Świat zapisuje dane obok kodu (`swiat.json`, `cialo/`, `swiaty/`, dzienniki). Nic z tego nie należy do
repozytorium — pilnuje tego `.gitignore`. Świeża kopia nie ma świata; tworzy go przy pierwszym uruchomieniu.

### Współtworzenie

Ten świat jest daleki od skończenia i każdą jego warstwę można rozwinąć — zapraszamy.

Co warto zrobić dalej, spisane jest w `WORD.md` w sekcji **Odłożone**: więcej czasowników i przedmiotów
w znaczeniach, wypowiedzi z dwoma tematami naraz, podział pracy, opowieści między pokoleniami,
crossing-over wewnątrz genu. Poza tym: cokolwiek, czego według Ciebie temu światu brakuje.

Dwie rzeczy warto wiedzieć, zanim zaczniesz:

- **Najpierw przeczytaj `WORD.md`.** Przy każdym kawałku zapisane jest uzasadnienie, zwykle z pomiarem,
  który rozstrzygnął sprawę.
  Projekt jest bliższy biologii niż inżynierii: zmianę ocenia się po tym, co świat z nią robi, a nie po tym,
  jak czysty jest kod. Uruchom świat, zmierz wynik i dołącz liczby do pull requesta.
- **Nic w tym świecie nie jest zaprojektowane.** Geny biorą się z mnożenia losowych macierzy, znaczenia
  z doświadczenia, a o tym, co dobre, rozstrzyga energia. Jeśli Twoja zmiana wpisuje odpowiedź, którą miał
  znaleźć dobór, to prawdopodobnie zła zmiana.

Zgłoszenia, pull requesty, kopie projektu i światy uruchomione na zupełnie innych ustawieniach — wszystko jest mile widziane.

### Licencja

MIT — zobacz [`LICENSE`](LICENSE).
