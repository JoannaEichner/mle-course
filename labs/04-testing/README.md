# Lab 04: prognozy w pakiecie, testy, które łapią błędy

Wykład: [`lectures/04-testing/index.html`](../../lectures/04-testing/index.html)

Notebook: `04-testing.ipynb`. Kod piszesz w pakiecie, w dwóch plikach: `src/freshcast/models/local.py` (klasy prognoz) i `tests/models/test_local.py` (testy do nich). Notebook uruchamia sprawdzenia i pokazuje modele w działaniu.

## Co oddajesz

| Zadanie | Krok | Co | Gdzie | Sprawdzenie |
|---|---|---|---|---|
| 04.1 | 04.1a | `fit` i `predict` klasy bazowej | `src/freshcast/models/local.py`, `LocalForecaster` | `assert` w notebooku po 04.1b |
| | 04.1b | prognoza naiwna | `local.py`, `NaiveForecaster._forecast` | `assert` w notebooku po 04.1b |
| | 04.1c | prognoza sezonowa | `local.py`, `SeasonalNaiveForecaster`: `__init__`, `fit`, `_forecast` | `uv run course check 04.1` |
| | 04.1d | średnia krocząca | `local.py`, `MovingAverageForecaster`: `__init__`, `_forecast` | `uv run course check 04.1` |
| 04.2 | 04.2a | testy wartości prognoz trzech klas | `tests/models/test_local.py` | `uv run pytest tests/models -q` |
| | 04.2b | test liczby wartości prognozy | `tests/models/test_local.py` | `uv run pytest tests/models -q` |
| | 04.2c | testy błędów z docstringów | `tests/models/test_local.py` | `uv run pytest tests/models -q` |
| | 04.2d | testy wykrywają 8 celowo wprowadzonych błędów | | `uv run course check 04.2` |
| 04.3 | | ten sam pakiet w Poetry i w uv, odpowiedzi w notebooku | `~/sandbox`, poza repozytorium | bez sprawdzenia |
| PK1 | | pull request z modułami 01-04 i review | gałąź `checkpoint/01` | `/review` albo samodzielnie |

Sprawdzenie 04.2 działa w dwóch krokach:

- Wymaga co najmniej 6 testów w pliku, które przechodzą na Twoim kodzie. Gotowy test się liczy, a każdy przypadek parametryzacji liczy się osobno.
- Uruchamia te testy na ośmiu wersjach `local.py`, z których każda ma jeden celowy błąd. Wypisuje te błędy, których Twoje testy nie zauważyły.

## Co wykorzystasz z poprzednich labów

- `labs/03-classes/demand.py`, zadania 03.3 i 03.4: `LocalForecaster`, `NaiveForecaster`, `SeasonalNaiveForecaster`, `MovingAverageForecaster`. Ciała metod przenosisz do `local.py` bez zmian. Sprawdzenie 04.1 bada wprost dwie rzeczy z tej samej umowy: domyślne `season` i `window` równe 7 oraz wynik zawsze typu `float`, także dla historii z liczb całkowitych.
- Wzór testu z wykładu 04 i gotowy `test_naive_repeats_the_last_value` w `tests/models/test_local.py`.
- Z labu 02: `uv run ruff format`, `uv run ruff check`, `uv run mypy` przed punktem kontrolnym.

## Zanim zaczniesz

- Masz zrobiony lab 03. Jeśli nie, `uv run course catchup 04` wpisze kod referencyjny modułów 01-03 do plików `.py` (nie do notebooków).
- Przeczytałeś wykład 04.

## Gdy utkniesz

1. Uruchom `uv run pytest tests/models -q` i przeczytaj pierwszy błąd.
2. Przeczytaj listę błędów, których Twoje testy nie wykryły: każdy mówi, jakiego testu brakuje.
3. Otwórz kolejną podpowiedź pod zadaniem.
4. Zapytaj tutora: `/hint 04.2`.
