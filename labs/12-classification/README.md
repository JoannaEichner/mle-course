# Lab 12: czy jutro zabraknie towaru na cały dzień

Wykład: [`lectures/12-classification/index.html`](../../lectures/12-classification/index.html)

Notebook: `12-classification.ipynb`. Kod piszesz w `src/freshcast/classify/`.

## Co oddajesz

| Zadanie | Co | Sprawdzenie |
|---|---|---|
| 12.1 | `next_day_value`, `add_stockout_label`, `drop_unlabelled` | `uv run course check 12.1` |
| 12.2 | `rolling_mean_through_today`, `add_stockout_features` | `uv run course check 12.2` |
| 12.3 | `confusion_counts`, `precision`, `recall`, `f1` | `uv run course check 12.3` |
| 12.4 | `counts_by_threshold`, `precision_recall_curve`, `average_precision` | `uv run course check 12.4` |
| 12.5 | `best_threshold` | `uv run course check 12.5` |
| 12.6 | `calibration_table` | `uv run course check 12.6` |
| 12.7 | `StockoutClassifier` | `uv run course check 12.7` |

Notebook kończy się tabelą decyzji na teście (baseline, regresja logistyczna, LightGBM, "nigdy nie alarmuj"), tabelami kalibracji i eksperymentem z kolumnami z jutra.

## Zanim zaczniesz

- Moduł 11 za Tobą, albo `uv run course catchup 12`.
- Przeczytałeś wykład 12.

## Gdy utkniesz

1. Wypisz cztery wiersze jednej serii z etykietą i kolumną, z której powstała. Sprawdź ręcznie, który dzień trafił do którego wiersza.
2. Przeczytaj komunikat sprawdzenia.
3. Otwórz kolejną podpowiedź pod zadaniem.
4. Zapytaj tutora: `/hint 12.4`.
