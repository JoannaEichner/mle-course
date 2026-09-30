# Standard inżynierski

Reguły, według których piszesz kod w tym kursie i według których tutor robi review. Każda ma identyfikator. Review powołuje się na identyfikatory, więc warto je kojarzyć.

Reguła zaczyna obowiązywać od modułu, który ją wprowadza. Kolumna "Od" mówi, od którego. Reguły oznaczone **blokuje** zatrzymują scalenie pull requesta na punkcie kontrolnym.

## Zasada nadrzędna

**Cicha zła prognoza jest gorsza niż błąd.** Kod ma się wywrócić głośno i wcześnie, zamiast policzyć coś na danych, których nie rozumie.

## D. Dane

| Id | Reguła | Od | |
|---|---|---|---|
| D1 | Kolumny i wiersze wybierasz przy czytaniu pliku, nie po nim. | 07 | |
| D2 | Założenie o danych to kod, który rzuca wyjątek. Komunikat mówi, która reguła jest złamana i ile wierszy ją łamie. | 06 | **blokuje** |
| D3 | `fillna`, `errors="coerce"`, `drop_duplicates` i `dropna` tylko po sprawdzeniu, ilu wierszy dotyczą, i z uzasadnieniem w komentarzu albo docstringu. | 06 | **blokuje** |
| D4 | Funkcja nie zmienia ramki, którą dostała. Zwraca nową. Bez `inplace=True`. | 06 | **blokuje** |
| D5 | Każdy `merge` ma jawne `on`, `how` i `validate`. Po złączeniu z wymiarem sprawdzasz klucze bez pary. | 07 | **blokuje** |
| D6 | Operacja zależna od kolejności wierszy (`shift`, `rolling`, `cumsum`, `head`) stoi za jawnym sortowaniem albo sprawdzeniem posortowania. | 07 | |
| D7 | Nazwy kolumn bierzesz ze stałych w `schema.py`, nie wpisujesz napisów z ręki. | 07 | |
| D8 | Zbiór zapisywany dla innych modułów ma kontrakt kolumn sprawdzany przy zapisie i przy odczycie. | 07 | |
| D9 | Wiersze wybierasz przez `.loc` z maską albo etykietą. Bez łańcuchowego indeksowania (`df[a][b] = ...`). | 06 | |

## C. Czas i leakage

| Id | Reguła | Od | |
|---|---|---|---|
| C1 | Lagi i okna liczysz wewnątrz serii, na panelu posortowanym i kompletnym. | 07 | **blokuje** |
| C2 | Cecha używa tylko informacji dostępnej w chwili prognozy. Okno kończy się najpóźniej wczoraj, a lag jest nie krótszy niż horyzont. | 07 | **blokuje** |
| C3 | Dane dzielisz po czasie. Zbiór walidacyjny leży w całości po treningowym. | 08 | **blokuje** |
| C4 | Wszystko, co się dopasowuje do danych (skalery, kodowania, imputacja, selekcja cech), dopasowujesz tylko na zbiorze treningowym. | 08 | **blokuje** |
| C5 | Zbiór testowy oglądasz raz, na końcu. Decyzje podejmujesz na walidacji. | 08 | **blokuje** |
| C6 | Każdy wynik modelu stoi obok wyniku baseline'u liczonego na tych samych wierszach. | 08 | |

## K. Kod

| Id | Reguła | Od | |
|---|---|---|---|
| K1 | Każda funkcja ma adnotacje typów argumentów i wyniku. `mypy` przechodzi bez błędów. | 02 | **blokuje** |
| K2 | Funkcja publiczna ma docstring w stylu Google: co robi, co przyjmuje, co zwraca, co rzuca. Opisuje zachowanie, nie implementację. | 02 | |
| K3 | Funkcja robi jedną rzecz. Jeśli opis wymaga słowa "oraz", to są dwie funkcje. | 02 | |
| K4 | Rzucasz wbudowane wyjątki z konkretnym komunikatem. `except` łapie konkretny typ. Bez gołego `except` i bez `except Exception`, poza jawną granicą błędów. | 01 | **blokuje** |
| K5 | Wartości o znaczeniu mają nazwę: stała albo `StrEnum`. Bez magicznych liczb i napisów w środku funkcji. | 03 | |
| K6 | Importy absolutne, na górze pliku. | 02 | |
| K7 | Na tablicach i ramkach liczysz operacjami wektorowymi. Pętla po wierszach wymaga uzasadnienia. | 05 | |
| K8 | W pakiecie nie ma `print`. Komunikaty idą przez `logging`. | 14 | |
| K9 | `ruff check` i `ruff format --check` przechodzą. | 02 | **blokuje** |
| K10 | Komentarz mówi, dlaczego. Co robi kod, mówi sam kod. | 02 | |

## T. Testy

| Id | Reguła | Od | |
|---|---|---|---|
| T1 | Każda funkcja publiczna pakietu ma test. | 04 | **blokuje** |
| T2 | Test buduje małe, jawne dane w miejscu i sprawdza konkretną wartość. | 04 | |
| T3 | Testujesz też przypadki brzegowe i błędy: `pytest.raises` z `match`. | 04 | |
| T4 | Test nie zależy od sieci, bieżącej daty, losowości bez ziarna ani od kolejności testów. | 04 | **blokuje** |
| T5 | Ramki porównujesz przez `pd.testing.assert_frame_equal`, liczby zmiennoprzecinkowe przez `pytest.approx`. | 06 | |

## G. Git i pull requesty

| Id | Reguła | Od | |
|---|---|---|---|
| G1 | Jeden pull request to jedna sprawa. | 00 | |
| G2 | Komunikat commita mówi, co się zmienia i po co, w trybie rozkazującym: "Add panel validation". | 00 | |
| G3 | Przed prośbą o review sprawdzenia przechodzą lokalnie: `ruff`, `mypy`, `pytest`, `course check`. | 04 | **blokuje** |
| G4 | W repozytorium nie ma danych, modeli, sekretów ani wyjść notebooków z danymi. | 00 | **blokuje** |
