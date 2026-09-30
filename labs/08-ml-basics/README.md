# Lab 08: pierwszy model i uczciwy test

Wykład: [`lectures/08-ml-basics/index.html`](../../lectures/08-ml-basics/index.html)

Notebook: `08-ml-basics.ipynb`. Kod piszesz w pakiecie `src/freshcast/`.

## Co oddajesz

| Zadanie | Co | Sprawdzenie |
|---|---|---|
| 08.1 | `last_days_start`, `split_by_date` w `split.py` | `uv run course check 08.1` |
| 08.2 | `PerSeriesForecaster` w `models/panel.py` | `uv run course check 08.2` |
| 08.3 | `predict_linear`, `mse`, `mse_gradient`, `fit_linear_gd` w `models/gradient.py` | `uv run course check 08.3` |
| 08.4 | `LinearForecaster` w `models/panel.py` | `uv run course check 08.4` |
| 08.5 | `score_forecast` w `evaluation/scores.py` | `uv run course check 08.5` |

Notebook kończy się tabelą: baseline kontra Ridge na teście, na wszystkich dniach i na dniach bez braków towaru.

## Zanim zaczniesz

- Masz `data/processed/daily.parquet` z labu 07. Jeśli nie, `uv run course catchup 08` i pierwsza komórka notebooka zbuduje plik.
- Przeczytałeś wykład 08.

## Gdy utkniesz

1. Wypisz kształty i pierwsze wiersze tego, co wchodzi do modelu i co z niego wychodzi.
2. Przeczytaj komunikat sprawdzenia.
3. Otwórz kolejną podpowiedź pod zadaniem.
4. Zapytaj tutora: `/hint 08.3`.
