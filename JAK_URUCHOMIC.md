# Jak uruchomić i zatrzymać świat

Wszystko dzieje się w katalogu `~/projekty/human`. Internet niepotrzebny.

## Najkrócej

    cd ~/projekty/human
    python3 serwer.py

Otwórz <http://localhost:8080> i przyciskiem powołaj świat — serwer sam uruchomi proces życia.
Reszta tego pliku jest dla tych, którzy chcą prowadzić świat z terminala.

## Uruchomienie z terminala

1. Otwórz Terminal i wejdź do katalogu:

       cd ~/projekty/human

2. Sprawdź, czy świat już nie chodzi (nie uruchamiaj drugiego!):

       ps -Ao pid,command | grep "[z]ycie.py"

   Jeśli coś wypisze — świat już żyje, pomiń resztę.

3. Uruchom proces życia (jeden cykl co 5 sekund):

       CYKL=5.0 GENY=64 DWOJE=1 WYMIARY=8 ISTOT=32 ROZMIAR=rozlegly nohup python3 zycie.py >> zycie.log 2>&1 &
       ps -Ao pid,command | grep "[z]ycie.py" | grep Python | awk '{print $1}' > zycie.pid

   Można dodać `POJEMNOSC_SWIATA=2000` — ilu żywych świat uniesie (powyżej nie ma urodzeń).

   Ustawienia `GENY`, `WYMIARY`, `ISTOT`, `ROZMIAR`, `POJEMNOSC_SWIATA` liczą się **tylko przy tworzeniu nowego świata**.
   Gdy `swiat.json` już istnieje, świat wraca do swojego ciała i bierze je stamtąd; zostaje tylko `CYKL`.

4. Uruchom serwer strony:

       nohup python3 serwer.py >> serwer.log 2>&1 &
       ps -Ao pid,command | grep "[s]erwer.py" | grep Python | awk '{print $1}' > serwer.pid

5. Otwórz w przeglądarce: http://localhost:8080

   Podstrony: `/wnetrze`, `/rod`, `/jezyk`.

6. Sprawdź, że świat idzie (cykl ma rosnąć):

       tail -f zycie.log

   Wyjście z podglądu: Ctrl+C (to zatrzymuje tylko podgląd, nie świat).

## Zatrzymanie i zapisanie cywilizacji

Świat zapisuje się **sam, na końcu każdego cyklu** — do `swiat.json` i katalogu `cialo/`.
Zatrzymanie w połowie cyklu kosztuje najwyżej ten jeden cykl.

1. Zatrzymaj procesy (po numerze, nigdy po nazwie):

       kill $(cat zycie.pid)
       kill $(cat serwer.pid)

2. Sprawdź, że nic nie zostało:

       ps -Ao pid,command | grep -E "[z]ycie.py|[s]erwer.py"

3. Zobacz, na czym stanął świat:

       python3 -c "import json; d=json.load(open('swiat.json')); print('cykl', d['cykl_swiata'], '| żywych', len(d['zywi']))"

### Kopia zapasowa cywilizacji

Cywilizacja to `swiat.json` (ciało świata) plus katalog `cialo/` (rdzenie i powłoki istot).
Reszta to kronika: `zdarzenia.jsonl`, `dziennik.jsonl`.

    mkdir -p ~/kopie/human-$(date +%Y%m%d-%H%M)
    cp -R swiat.json cialo zdarzenia.jsonl dziennik.jsonl WORD.md ~/kopie/human-$(date +%Y%m%d-%H%M)/

Przywrócenie: skopiuj te pliki z powrotem do `~/projekty/human` (przy zatrzymanym świecie) i uruchom jak wyżej.

### Odłożenie świata do archiwum

Zakończone światy leżą w `swiaty/<numer>/` — razem z `dzieje.json` i `SWIAT.txt`.
Robi to strona (powołanie nowego świata przenosi stary do archiwum); ręcznie nie trzeba.

## Oglądanie dawnego świata

Zakończone światy leżą w `swiaty/<numer>/`. Można podejrzeć każdy z nich, nie ruszając żywego:

    SWIAT=49 PORT=8081 python3 serwer.py

Albo krócej: `python3 serwer.py 49` (wtedy port domyślny 8080 — nie uruchamiaj tak, gdy żywy świat już zajmuje ten port).

Otwórz http://localhost:8081 — strona wygląda tak samo, ale nagłówek mówi „dawny świat nr 49",
a wszystko, co zmienia świat (słowa, karmienie, powołanie nowego), jest zablokowane.
Proces życia dla archiwum się **nie** uruchamia: to zapis, nie życie.

Lista światów: `ls swiaty` — a `cat swiaty/49/SWIAT.txt` mówi, ile cykli i istot miał.

## Gdy świat padnie sam

W `zycie.log` będzie ślad. Wystarczy uruchomić proces życia jeszcze raz (krok 3) —
wróci do ciała z ostatniego zapisanego cyklu.
