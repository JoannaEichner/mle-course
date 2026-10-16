# Lab 03: serie jako obiekty, typy popytu i pierwsze prognozy

Wykład: [`lectures/03-classes/index.html`](../../lectures/03-classes/index.html)

Notebook: `03-classes.ipynb`. Kod piszesz w `demand.py` obok notebooka. Komentarze w `demand.py` (po angielsku) to umowa każdego bloku. Notebook opisuje to samo po polsku, krok po kroku.

## Co oddajesz

Plik `demand.py`, który przechodzi `ruff format --check`, `ruff check` i `mypy --strict`, oraz uzupełnione komórki notebooka.

| Zadanie | Krok | Co | Gdzie | Sprawdzenie w notebooku |
|---|---|---|---|---|
| 03.1 | 03.1a | pola `name`, `start`, `values` i walidacja w `__post_init__` | `demand.py`, `DemandSeries` | komórka z `assert` po 03.1b |
| | 03.1b | metoda klasy `from_record` | `demand.py`, `DemandSeries.from_record` | komórka z `assert` po 03.1b |
| | 03.1c | właściwości `known`, `is_complete`, `adi`, `cv2` | `demand.py`, `DemandSeries` | `check("03.1", demand)` |
| | 03.1d | wszystkie serie jako obiekty | notebook, `series`, `complete` | `assert` w komórce |
| 03.2 | 03.2a | `DemandType` (StrEnum) | `demand.py` | `check("03.2", demand)` |
| | 03.2b | `classify` z `match` | `demand.py` | `check("03.2", demand)` |
| | 03.2c | liczba serii każdego typu | notebook, `counts` | `assert` w komórce |
| 03.3 | 03.3a | `LocalForecaster` (ABC): `fit`, `predict`, `_forecast` | `demand.py` | `check("03.3", demand)` |
| | 03.3b | `NaiveForecaster` | `demand.py` | `check("03.3", demand)` |
| 03.4 | 03.4a | `SeasonalNaiveForecaster` | `demand.py` | `check("03.4", demand)` |
| | 03.4b | `MovingAverageForecaster` | `demand.py` | `check("03.4", demand)` |
| 03.5 | 03.5a | `Forecaster` (Protocol) | `demand.py` | `check("03.5", demand)` |
| | 03.5b | `mae` | `demand.py` | `assert` w komórce, potem `check("03.5", demand)` |
| | 03.5c | `evaluate` | `demand.py` | `check("03.5", demand)` |
| | 03.5d | porównanie czterech modeli | notebook, `models`, `scores` | `assert` w komórce |
| 03.6 | | eksploracja, trzy pytania | notebook | bez sprawdzenia |

`check("03.5", demand)` uruchamia też ruff i `mypy --strict` na całym `demand.py`.

## Co wykorzystasz z poprzednich labów

- Wzór na ADI z labu 01 (`demand_stats`). ADI to liczba znanych miesięcy podzielona przez liczbę miesięcy ze sprzedażą większą od zera.
- Wzór na CV² z labu 02 (`cv2` w `carparts.py`). CV² to wariancja populacyjna niezerowych wartości podzielona przez kwadrat ich średniej. W tym labie liczysz CV² bez wymogu 12 znanych miesięcy.
- Format rekordu `(nazwa, "YYYY-MM-DD", wartości)` z `read_series` z labów 01 i 02. W `demand.py` robi to gotowa funkcja `read_tsf`, więc `carparts.py` nie jest potrzebny do uruchomienia labu.
- `lambda` i typ `Callable` z wykładu 02, przydatne w 03.5.
- Narzędzia z labu 02: `uv run ruff format`, `uv run ruff check`, `uv run mypy --strict`.

## Zanim zaczniesz

- Przeczytałeś wykład 03.

## Gdy utkniesz

1. Uruchom `uv run mypy --strict labs/03-classes/demand.py` i przeczytaj pierwszy komunikat.
2. Przeczytaj komunikat sprawdzenia.
3. Otwórz kolejną podpowiedź pod zadaniem.
4. Zapytaj tutora: `/hint 03.3`.
