# Word: eksperyment z powstawaniem języka i pisma w sztucznej ewolucji

Opis dla osób z zewnątrz. Stan na 2026-09-13. Szczegóły i historia decyzji: `WORD.md`.

## Jedno zdanie
Word to symulacja populacji prostych agentów, którym nie daliśmy ani języka, ani celu,
tylko energię, geny i śmierć, i sprawdzamy, czy sam dobór naturalny wytworzy
u nich znaczenia, mowę o rzeczach nieobecnych i pismo, które przeżyje autora.

## Pytanie badawcze
Czy język i kultura mogą powstać wyłącznie z presji przetrwania, bez żadnej
nagrody za „sensowność”, i czy pismo (pamięć poza ciałem) zwiększa szansę
przetrwania kultury po załamaniu populacji (wąskim gardle)?

## Co jest w świecie (metoda)
- **Istota** to zestaw genów-macierzy. Sygnał (wektor o 16 wymiarach) przechodzi
  przez gen jak przez bramkę; otwarcie bramki kosztuje energię i trwale zmienia
  istotę. Geny regulują inne geny przez stan, nie bezpośrednio.
- **Czas to energia.** Każdy cykl życia kosztuje. Energia przychodzi z łąk,
  losowo. Zdolność jej wchłaniania maleje z wiekiem. Jedyny koniec to brak
  energii. Nie ma innej funkcji celu.
- **Dobór.** Gen przeżywa, gdy przeżywa istota. Potomek dostaje geny rodziców
  z mutacją. Nie oceniamy niczego poza przetrwaniem.
- **Świat**: koło miejsc, z których część to łąki o różnej żyzności; pory roku,
  noc, deszcz, susza, pożary, powodzie, drapieżnik, zarazy z ogniskami.
- **Sygnały**: pokarm, ból, zapach miejsca, głos innej istoty, echo własnego
  głosu (to, co wyszło, wraca osłabione i zniekształcone), sen (echa zmieszane
  z szumem), śmierć obok. Wszystko jest tym samym rodzajem wektora.
- **Znaczenie** nie jest wpisane. Istota zapamiętuje, co następowało po
  usłyszanym wektorze (bilans energii). Gdy skutek powtórzy się co najmniej
  3 razy i jest spójny, wektor wywołuje czyn: idź, unikaj, odpowiedz, broń.
  Znaczenie to powtarzalny skutek.
- **Kultura nabyta, nie genetyczna**: uprawa łąki, spichlerz (zapas na zimę),
  mapa łąk, znaczenia słów. Przechodzą tylko przez naukę od sytego rodzica.
  Głodny nie uczy. Po wąskim gardle kultura zwykle ginie.
- **Ryt** (pismo): istota może wyryć w miejscu znaczenie, które rozumie.
  Ryt zostaje po jej śmierci, blednie, kto go znajdzie, uczy się słabiej niż
  od rodzica. Umiejętność rytu odkrywa się dopiero po spichlerzu, przeżytej
  zimie i trzech rozumianych znaczeniach. Osobno: **spuścizna**, instynkt
  z genu troski: istota u kresu oddaje resztę czasu na wyrycie tego, co
  najwięcej ważyło w energii (jeden wpis na cykl), a kto nic nie ma, ryje
  swój głos: imię bez znaczenia.
- **Geny zachowań** (dziedziczne, z mutacją): siła, ciekawość, pojętność,
  stadność, towarzyskość, ufność, szczerość, troska, płochliwość, długowieczność,
  odporność, ozdoba i gust (dobór płciowy), optimum i tolerancja klimatu.

## Co mierzymy
- **Korpus** (`korpus.jsonl`): każde słowo z kontekstem (kto, komu, gdzie,
  pora, kto słyszał) i każda widoczna reakcja słuchacza. Bez zaglądania do
  wnętrza istot.
- **Zdarzenia** (`zdarzenia.jsonl`): narodziny, śmierci, odkrycia, zarazy,
  klęski, ryty, odczytania, spuścizny.
- **Słownik z obserwacji**: dla każdego ciągu znaków, co słuchacze po nim
  zrobili, z liczbą przypadków i pewnością. Budowany tak, jak odczytuje się
  pismo obcej cywilizacji: tylko z zewnątrz. Rozkład wektora skutku na osie,
  które sami nazwaliśmy, jest dostępny osobno jako „podgląd wnętrza” i służy
  wyłącznie do sprawdzania, nie do czytania.
- **Dzieje cywilizacji**: liczba istot na osi cykli i zdarzenia rzadkie,
  dotykające wielu naraz.

## Zasady metodologiczne
1. Nic nie jest projektowane pod wynik: nie ma nagrody za słowo, sens ani
   współpracę. Jedyny sędzia to śmierć.
2. Nie czytamy istotom w głowach. Przekład ich języka powstaje z obserwacji,
   z dziurami tam, gdzie nie widać skutku.
3. Każda zmiana reguł jest spisana z datą i powodem (`WORD.md`, 90+ kawałków),
   a każdy świat jest archiwizowany w całości (`swiaty/`), więc przebiegi są
   odtwarzalne i porównywalne.

## Dotychczasowe obserwacje (wstępne, pojedyncze przebiegi)
- Populacje dochodzą do 200 istot i ponad 20 pokoleń; w obiegu bywa ponad
  2000 różnych słów, z których kilkaset ma stałą, widoczną reakcję.
- Wąskie gardło (3 istoty z 200) wymazało kulturę: ocalałe nie rozumiały
  żadnego znaczenia, choć geny przetrwały. To była bezpośrednia motywacja
  dla pisma.
- Mowa jest o tym, co oboje widzą, dopóki się nie opłaca inaczej: po dodaniu
  odpowiedzi z pamięci na krzyk głodu udział słów o łące, której słuchacz nie
  widzi, wzrósł z 1 na 580 do około 1 na 3.
- Pierwsze spuścizny to prawie zawsze łąki, nie znaczenia: młoda cywilizacja
  ma mapę, zanim ma słowa.
- Pierwsze odczytania rytów (kilkaset w jednym świecie) pojawiły się przed
  pierwszym odkryciem rytu za życia: pismo zaczyna się od nagrobków.

## Uczciwe zastrzeżenie
Mówimy, że niczego nie projektujemy pod wynik, a jednocześnie w trakcie
przebiegów zmieniamy reguły świata: częstość drapieżnika, gęstość na start,
odruch ucieczki, warunki odkrycia rytu. To także jest dobór, tylko naszą
ręką. Świat ewoluuje pod okiem obserwatora, nie sam. Każda taka zmiana jest
spisana z datą i powodem; od pewnego momentu reguły trzeba zamrozić i dopiero
wtedy liczyć przebiegi.

## Czego jeszcze nie ma
- Wielu przebiegów z tym samym ziarnem, z pismem i bez, do porównania
  statystycznego. Dziś to esej z narzędziami; z tym byłby eksperyment.
- Automatycznego odczytu korpusu (np. modelem językowym) jako niezależnego
  testu, czy ich język ma strukturę.

## Na tle innych prac
Poszczególne składniki mają poprzedników: ewolucja cyfrowa (Tierra, Avida),
gry językowe z wyłanianiem znaczeń (Steels), ekologie agentów (Polyworld).
Nowe jest złożenie: znaczenie wyłącznie ze skutku energetycznego, brak
jakiejkolwiek funkcji celu poza przetrwaniem, kultura nabyta oddzielona od
genów i ginąca z głodnym rodzicem, pismo rodzące się z instynktu u kresu,
oraz zakaz interpretacji „od środka”: język istot czytamy jak pismo obcej
cywilizacji.
