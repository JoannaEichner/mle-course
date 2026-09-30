# Lab 09: cechy, które model może znać

Wykład: [`lectures/09-features/index.html`](../../lectures/09-features/index.html)

Notebook: `09-features.ipynb`. Kod piszesz w `src/freshcast/features/`. Plik `catalog.py` jest gotowy: łączy Twoje funkcje w zestaw cech, na którym uczą się modele od modułu 10.

## Co oddajesz

| Zadanie | Co | Sprawdzenie |
|---|---|---|
| 09.1 | `calendar.py` | `uv run course check 09.1` |
| 09.2 | `lags.py` | `uv run course check 09.2` |
| 09.3 | `demand.py` | `uv run course check 09.3` |
| 09.4 | `encoding.py`: `TargetEncoder` | `uv run course check 09.4` |
| 09.5 | `build.py`: `resolve_order`, `build_features` | `uv run course check 09.5` |

Wynik: `data/processed/features.parquet` i trzy tabele eksperymentów w notebooku.

## Zanim zaczniesz

- Moduł 08 za Tobą, albo `uv run course catchup 09`.
- Przeczytałeś wykład 09.

## Gdy utkniesz

1. Policz cechę na dwóch seriach po pięć dni i sprawdź ją ręcznie.
2. Przeczytaj komunikat sprawdzenia.
3. Otwórz kolejną podpowiedź pod zadaniem.
4. Zapytaj tutora: `/hint 09.5`.
