# Lab 06: czyszczenie sprzedaży sklepu internetowego

Wykład: [`lectures/06-pandas-cleaning/index.html`](../../lectures/06-pandas-cleaning/index.html)

Notebook: `06-pandas-cleaning.ipynb`. Kod piszesz w pakiecie, w `src/freshcast/warmup/`. W notebooku piszesz tylko 06.4c i komórki eksploracji 06.8.

## Co oddajesz

Kroki z literą (06.1a, 06.1b, ...) to części jednego zadania. Sprawdza je jedno `check` z numerem zadania: `uv run course check 06.1` sprawdza 06.1a, 06.1b i 06.1c naraz.

| Zadanie | Plik | Funkcja albo zmienna | Sprawdzenie |
|---|---|---|---|
| 06.1a | `src/freshcast/warmup/online_retail.py` | `read_sheets`: skoroszyt z typami | `uv run course check 06.1` |
| 06.1b | `online_retail.py` | `build_cache`: zapis do Parquet | `uv run course check 06.1` |
| 06.1c | `online_retail.py` | `load_raw`: odczyt cache | `uv run course check 06.1` |
| 06.2a | `online_retail.py` | `check_raw`, reguły 1-4 | `uv run course check 06.2` |
| 06.2b | `online_retail.py` | `check_raw`, reguły 5-8 | `uv run course check 06.2` |
| 06.3 | `src/freshcast/warmup/lines.py` | `add_flags` | `uv run course check 06.3` |
| 06.4a | `lines.py` | `drop_sheet_overlap` | `uv run course check 06.4` |
| 06.4b | `lines.py` | `flag_repeat_lines` | `uv run course check 06.4` |
| 06.4c | notebook | `all_duplicates`, `deduplicated`, `copies`, `repeats` | komórka z asercjami |
| 06.5 | `lines.py` | `product_lines` | `uv run course check 06.5` |
| 06.6a | `src/freshcast/warmup/daily.py` | `daily_totals` | `uv run course check 06.6` |
| 06.6b | `daily.py` | `check_daily` | `uv run course check 06.6` |
| 06.7a | `daily.py` | `build_daily` | `uv run course check 06.7` |
| 06.7b | `daily.py` | `save_daily`, `load_daily` | `uv run course check 06.7` |
| 06.8 | notebook | pięć pytań, odpowiedź z liczbami | bez sprawdzenia |

Wynik: `data/processed/online_retail_daily.parquet`. Wróci w module 17.

## Co wykorzystasz z poprzednich labów

- **Lab 05:** maski, `~`, `&`, `|`, `NaN` i liczenie przez `.sum()` i `.mean()` na masce. pandas działa na tych samych zasadach, kolumna po kolumnie.
- **Lab 04:** testy i `pytest.raises`. Sprawdzenia tego labu oczekują `ValueError` z liczbą w komunikacie, tak jak Twoje testy w 04.2 i 05.5 oczekiwały błędów.
- **Lab 02:** adnotacje typów i docstringi jako umowa. Każda funkcja w `src/freshcast/warmup/` ma gotowy docstring z wejściem, wynikiem i błędami.
- **Lab 01:** `pathlib.Path`, `mkdir(parents=True, exist_ok=True)`, wyjątki `ValueError` i `FileNotFoundError`.
- **Moduł 00:** `uv run course data` (skoroszyt Online Retail II) i `uv run course check`.

Z kodu tego labu: stałe na górze `online_retail.py` (`SHEET_HEADERS`, `RAW_COLUMNS`, `REQUIRED_COLUMNS`, `INVOICE_PATTERN`, `PRODUCT_CODE_PATTERN`, `FLAG_COLUMNS`, `REPEAT_FLAG`, `PRODUCT_KEY`, `MEASURE_COLUMNS`, `DAILY_COLUMNS`), `LINE_COLUMNS` w `lines.py` i funkcja pomocnicza `_wrong_dtypes` w `daily.py` są gotowe. Każda funkcja korzysta z wyniku poprzedniej: `build_daily` w 06.7a składa je wszystkie.

## Zanim zaczniesz

- Skoroszyt jest pobrany (`uv run course data`). Pierwsze wczytanie trwa od pół minuty do półtorej minuty, zależnie od komputera. Potem pracujesz na cache w Parquet.
- Moduł 05 za Tobą, albo `uv run course catchup 06`.
- Przeczytałeś wykład 06.

## Gdy utkniesz

1. Policz: ile wierszy dotyczy reguła, flaga albo filtr, który piszesz? Porównaj z liczbą w docstringu.
2. Przeczytaj komunikat sprawdzenia: sprawdzenia pracują na małej próbce prawdziwego pliku.
3. Otwórz kolejną podpowiedź pod zadaniem.
4. Zapytaj tutora: `/hint 06.4`.
