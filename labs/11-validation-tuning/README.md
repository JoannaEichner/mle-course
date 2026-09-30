# Lab 11: backtest, strojenie i dziennik eksperymentów

Wykład: [`lectures/11-validation-tuning/index.html`](../../lectures/11-validation-tuning/index.html)

Notebook: `11-validation-tuning.ipynb`. Kod piszesz w pakiecie `src/freshcast/`.

## Co oddajesz

| Zadanie | Co | Sprawdzenie |
|---|---|---|
| 11.1 | `Fold`, `rolling_origin_folds` w `split.py` | `uv run course check 11.1` |
| 11.2 | `backtest` w `evaluation/backtest.py` | `uv run course check 11.2` |
| 11.3 | `suggest_params`, `tune` w `tuning.py` | `uv run course check 11.3` |
| PK2 | Pull request z modułami 05-11 i review | `/review` albo samodzielnie |

Runy MLflow trafiają do `data/mlflow/` (poza gitem). Przeglądasz je poleceniem `uv run mlflow ui --backend-store-uri sqlite:///data/mlflow/mlflow.db`.

## Zanim zaczniesz

- Moduł 10 za Tobą, albo `uv run course catchup 11`.
- Przeczytałeś wykład 11.

## Gdy utkniesz

1. Wypisz daty początku i końca treningu i walidacji każdego foldu.
2. Przeczytaj komunikat sprawdzenia.
3. Otwórz kolejną podpowiedź pod zadaniem.
4. Zapytaj tutora: `/hint 11.3`.
