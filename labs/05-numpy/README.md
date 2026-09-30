# Lab 05: NumPy na prawdziwym panelu sprzedaży

Wykład: [`lectures/05-numpy/index.html`](../../lectures/05-numpy/index.html)

Notebook: `05-numpy.ipynb`. Część kodu piszesz w notebooku, część w pakiecie.

## Co oddajesz

| Zadanie | Co | Sprawdzenie |
|---|---|---|
| 05.1 | `prepare` w `src/freshcast/metrics.py` | `uv run course check 05.1` |
| 05.2 | `mae`, `rmse` | `uv run course check 05.2` |
| 05.3 | `wape`, `bias` | `uv run course check 05.3` |
| 05.4 | `row_shares` w `src/freshcast/numeric.py` | `uv run course check 05.4` |
| 05.5 | Co najmniej 6 testów w `tests/test_metrics.py`, które wykrywają 7 zepsutych metryk | `uv run course check 05.5` |
| 05.6 | `to_matrix` w notebooku | `check("05.6", to_matrix)` |
| 05.7 | `seasonal_naive` w notebooku | `check("05.7", seasonal_naive)` |

## Zanim zaczniesz

- Dane są pobrane (`uv run course data`), a `uv run course doctor` nie pokazuje błędów.
- Masz zrobiony moduł 04. Jeśli nie, `uv run course catchup 05`.
- Przeczytałeś wykład 05.

## Gdy utkniesz

1. Wypisz `shape` i `dtype` każdej tablicy, której używasz. Większość błędów w NumPy to zły kształt.
2. Przeczytaj komunikat sprawdzenia.
3. Otwórz kolejną podpowiedź pod zadaniem.
4. Zapytaj tutora: `/hint 05.6`.
