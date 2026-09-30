# Lab 07: panel sprzedaży w pandas

Wykład: [`lectures/07-pandas-panel/index.html`](../../lectures/07-pandas-panel/index.html)

Notebook: `07-pandas-panel.ipynb`. Otwórz go w VS Code albo przez `uv run jupyter lab`.

## Co oddajesz

Sześć plików w `src/freshcast/data/` i zbiór `data/processed/daily.parquet`.

| Zadanie | Plik | Sprawdzenie |
|---|---|---|
| 07.1 Wczytanie | `load.py` | `uv run course check 07.1` |
| 07.2 Reguły i anomalie | `validate.py` | `uv run course check 07.2` |
| 07.3 Wymiary i złączenia | `dims.py` | `uv run course check 07.3` |
| 07.4 Tablice godzinowe | `hourly.py` | `uv run course check 07.4` |
| 07.5 Obliczenia w serii | `panel.py` | `uv run course check 07.5` |
| 07.6 Zbiór przetworzony | `prepare.py` | `uv run course check 07.6` |

Całość: `uv run course check 07`.

## Zanim zaczniesz

- `uv run course doctor` nie pokazuje błędów, dane są pobrane.
- Znasz materiał modułów 05 (NumPy) i 06 (pandas: typy, `.loc`, łańcuchy metod).

## Gdy utkniesz

1. Przeczytaj jeszcze raz docstring funkcji. To specyfikacja.
2. Przeczytaj komunikat sprawdzenia. Mówi, który warunek nie jest spełniony.
3. Otwórz kolejną podpowiedź pod zadaniem w notebooku.
4. Zapytaj tutora: `/hint 07.3`.
5. Rozwiązanie referencyjne jest na gałęzi `solutions`. `uv run course catchup 08` wpisze je za Ciebie, jeśli chcesz iść dalej.
