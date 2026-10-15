# Lab 07: panel sprzedaży w pandas

Wykład: [`lectures/07-pandas-panel/index.html`](../../lectures/07-pandas-panel/index.html)

Notebook: `07-pandas-panel.ipynb`. Otwórz go w VS Code albo przez `uv run jupyter lab`.

## Co oddajesz

Sześć plików w `src/freshcast/data/` i zbiór `data/processed/daily.parquet`.

Każde zadanie jest podzielone na kroki. Krok to jedna funkcja w pakiecie albo jedna zmienna w notebooku. Notebook opisuje każdy krok: cel, wejście, wynik, z czego skorzystać i jak sprawdzić. Dokładna specyfikacja funkcji jest w jej docstringu.

| Krok | Gdzie | Sprawdzenie |
|---|---|---|
| 07.0 Rozpoznanie pliku | notebook: `scalar_bytes`, `nested_bytes`, `total_gb` | `assert` w notebooku |
| 07.1a Najmniejsze typy całkowite | `load.py`: `shrink_integers` | `uv run course check 07.1` |
| 07.1b Wczytanie wybranych kolumn i miast | `load.py`: `load_sales` | `uv run course check 07.1` |
| 07.1c Ile pamięci zaoszczędziłeś | notebook: `saving` | `assert` w notebooku |
| 07.2a Śledztwo: pięć pytań do danych | notebook: `n_duplicated`, `days_distribution`, `n_zero`, `n_above_one`, `zero_days`, `comparison` | `assert` w notebooku (pytania 1 i 2) |
| 07.2b Twój wniosek o zerowym rabacie | notebook: komórka tekstowa | rozmowa z tutorem |
| 07.2c Reguły panelu | `validate.py`: `check_panel` | `uv run course check 07.2` |
| 07.2d Zero rabatu poza skalą | `validate.py`: `clean_discount` | `uv run course check 07.2` |
| 07.3a Wymiar sklepu | `dims.py`: `build_store_dim` | `uv run course check 07.3` |
| 07.3b Wymiar produktu | `dims.py`: `build_product_dim` | `uv run course check 07.3` |
| 07.3c Bezpieczne złączenie | `dims.py`: `attach_dim` | `uv run course check 07.3` |
| 07.3d Najlepiej sprzedająca się kategoria | notebook: `top_category` | `assert` w notebooku |
| 07.4a Wczytanie tablic godzinowych | `hourly.py`: `load_hourly` | `uv run course check 07.4` |
| 07.4b Kolumna tablic jako jedna tablica | `hourly.py`: `to_matrix` | `uv run course check 07.4` |
| 07.4c Cztery liczby na dzień | `hourly.py`: `summarise_hours` | `uv run course check 07.4` |
| 07.4d Zgodność z surową kolumną | notebook: `n_disagree` | `assert` w notebooku |
| 07.4e Sprzedaż mimo braku towaru | notebook: `share_rows`, `share_sales` | `assert` w notebooku |
| 07.5a Czy panel jest posortowany | `panel.py`: `is_sorted_panel` | `uv run course check 07.5` |
| 07.5b Lag w obrębie serii | `panel.py`: `add_lag` | `uv run course check 07.5` |
| 07.5c Średnia krocząca z przeszłości | `panel.py`: `add_rolling_mean` | `uv run course check 07.5` |
| 07.5d Profil tygodnia | `panel.py`: `dow_profile` | `uv run course check 07.5` |
| 07.5e Czy lagi coś mówią | notebook: `corr_lag`, `corr_mean` | `assert` w notebooku |
| 07.6a Zbiór przetworzony | `prepare.py`: `prepare_daily` | `uv run course check 07.6` |
| 07.6b Zapis | `prepare.py`: `save_processed` | `uv run course check 07.6` |
| 07.6c Odczyt z kontrolą kontraktu | `prepare.py`: `load_processed` | `uv run course check 07.6` |
| 07.7 Eksploracja | notebook: cztery odpowiedzi pisemne | rozmowa z tutorem |

Całość: `uv run course check 07`. Jedno sprawdzenie obejmuje wszystkie funkcje zadania i testuje je w kolejności kroków. ⬜ „jeszcze nie zrobione” znaczy, że doszło do funkcji, która wciąż ma `raise NotImplementedError`. Sprawdzenie 07.6 korzysta z Twoich funkcji z 07.1, 07.2 i 07.4.

## Co wykorzystasz z poprzednich labów

- **Moduł 02:** funkcja z sygnaturą i docstringiem jako umowa, import z modułu (`from freshcast.data.load import load_sales`).
- **Moduł 05 (NumPy):** osie (`sum(axis=1)` to jedna liczba na wiersz), wycinki `[:, 6:22]`, maski i `np.where`, `.nbytes`. W 07.4 robisz z kolumny tablic jedną tablicę, podobnie jak `to_matrix` z 05.6a robiła macierz z długiej tabeli. To jednak inna funkcja, z innymi argumentami: w 07.4b piszesz nową.
- **Moduł 06 (pandas):** typy kolumn, `isna`, `duplicated`, `drop_duplicates`, `assign` i łańcuchy metod, `sort_values` z `reset_index(drop=True)`. Reguła „policz, sprawdź, rzuć `ValueError` z liczbą” z `check_raw` (06.2) i `check_daily` (06.6b). Zapis i odczyt z kontrolą (`save_daily`, `load_daily` z 06.7b) to wzorzec dla 07.6b i 07.6c.
- **Stałe z `src/freshcast/data/schema.py`:** `SERIES_KEY`, `DATE`, `TARGET`, `CITY`, `HIERARCHY`, `DAILY_COLUMNS`, `HOURLY_COLUMNS`, `OOS_WINDOW`, `PROCESSED_COLUMNS` i nazwy nowych kolumn. Importujesz je, zamiast pisać nazwy kolumn w cudzysłowie.
- **W obrębie labu:** każdy krok korzysta z poprzednich. `daily` z 07.1 jest wejściem 07.2-07.5, `load_sales` wczytuje też `hierarchy` dla 07.3b, `to_matrix` służy `summarise_hours`, `is_sorted_panel` chroni `add_lag` i `add_rolling_mean`, a `prepare_daily` składa `load_sales`, `check_panel`, `clean_discount`, `load_hourly` i `summarise_hours`.

## Zanim zaczniesz

- `uv run course doctor` nie pokazuje błędów, dane są pobrane.
- Znasz materiał modułów 05 (NumPy) i 06 (pandas: typy, `.loc`, łańcuchy metod).

## Gdy utkniesz

1. Przeczytaj jeszcze raz docstring funkcji. To specyfikacja.
2. Przeczytaj komunikat sprawdzenia. Mówi, który warunek nie jest spełniony.
3. Otwórz kolejną podpowiedź pod zadaniem w notebooku.
4. Zapytaj tutora: `/hint 07.3`.
5. Rozwiązanie referencyjne jest na gałęzi `solutions`. `uv run course catchup 08` wpisze je za Ciebie, jeśli chcesz iść dalej.
