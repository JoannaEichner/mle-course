# Lab 03: serie jako obiekty, typy popytu i pierwsze prognozy

Wykład: [`lectures/03-classes/index.html`](../../lectures/03-classes/index.html)

Notebook: `03-classes.ipynb`. Kod piszesz w `demand.py` obok notebooka.

## Co oddajesz

Plik `demand.py`, który przechodzi `ruff format --check`, `ruff check` i `mypy --strict`, z:

| Zadanie | Co | Sprawdzenie w notebooku |
|---|---|---|
| 03.1 | `DemandSeries`: zamrożony dataclass z walidacją i właściwościami | `check("03.1", demand)` |
| 03.2 | `DemandType` (StrEnum), `classify` z `match` | `check("03.2", demand)` |
| 03.3 | `LocalForecaster` (ABC), `NaiveForecaster` | `check("03.3", demand)` |
| 03.4 | `SeasonalNaiveForecaster`, `MovingAverageForecaster` | `check("03.4", demand)` |
| 03.5 | `Forecaster` (Protocol), `mae`, `evaluate` | `check("03.5", demand)` |

## Zanim zaczniesz

- Przeczytałeś wykład 03.
- Lab 02 nie jest potrzebny do uruchomienia tego labu: `demand.py` ma własny `read_tsf`.

## Gdy utkniesz

1. Uruchom `uv run mypy --strict demand.py` i przeczytaj pierwszy komunikat.
2. Przeczytaj komunikat sprawdzenia.
3. Otwórz kolejną podpowiedź pod zadaniem.
4. Zapytaj tutora: `/hint 03.3`.
