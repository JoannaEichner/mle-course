# Lab 06: czyszczenie sprzedaży sklepu internetowego

Wykład: [`lectures/06-pandas-cleaning/index.html`](../../lectures/06-pandas-cleaning/index.html)

Notebook: `06-pandas-cleaning.ipynb`. Kod piszesz w pakiecie, w `src/freshcast/warmup/`.

## Co oddajesz

| Zadanie | Co | Sprawdzenie |
|---|---|---|
| 06.1 | `read_sheets`, `build_cache`, `load_raw` w `online_retail.py` | `uv run course check 06.1` |
| 06.2 | `check_raw` | `uv run course check 06.2` |
| 06.3 | `add_flags` w `lines.py` | `uv run course check 06.3` |
| 06.4 | `drop_sheet_overlap`, `flag_repeat_lines` | `uv run course check 06.4` |
| 06.5 | `product_lines` | `uv run course check 06.5` |
| 06.6 | `daily_totals`, `check_daily` w `daily.py` | `uv run course check 06.6` |
| 06.7 | `build_daily`, `save_daily`, `load_daily` | `uv run course check 06.7` |

Wynik: `data/processed/online_retail_daily.parquet`. Wróci w module 17.

## Zanim zaczniesz

- Skoroszyt jest pobrany (`uv run course data`). Pierwsze wczytanie trwa około pół minuty. Potem pracujesz na cache w Parquet.
- Moduł 05 za Tobą, albo `uv run course catchup 06`.
- Przeczytałeś wykład 06.

## Gdy utkniesz

1. Policz: ile wierszy dotyczy reguła, flaga albo filtr, który piszesz? Porównaj z liczbą w docstringu.
2. Przeczytaj komunikat sprawdzenia: sprawdzenia pracują na małej próbce prawdziwego pliku.
3. Otwórz kolejną podpowiedź pod zadaniem.
4. Zapytaj tutora: `/hint 06.4`.
