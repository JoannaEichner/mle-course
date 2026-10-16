# Lab 01: popyt na części samochodowe w czystym Pythonie

Wykład: [`lectures/01-python-data/index.html`](../../lectures/01-python-data/index.html)

Notebook: `01-python-data.ipynb`. Otwórz go w VS Code albo przez `uv run jupyter lab`.

## Co oddajesz

Sześć funkcji w komórkach notebooka, kilka zmiennych z odpowiedziami i plik `data/processed/car_parts_summary.json`. Każda funkcja ma gotową nazwę, argumenty i docstring. Ty piszesz jej ciało.

| Zadanie | Gdzie w notebooku | Co dostaje, co zwraca | Sprawdzenie w notebooku |
|---|---|---|---|
| 01.1 | funkcja `parse_value` | napis z jedną wartością → `float` albo `None` | `check("01.1", parse_value)` |
| 01.2 | funkcja `parse_series_line` | jedna linia danych → krotka (nazwa, data, lista wartości) | `check("01.2", parse_series_line)` |
| 01.3a | funkcja `read_series` | ścieżka pliku → generator krotek z 01.2 | `check("01.3", read_series)` |
| 01.3b | zmienne `series`, `lengths` | słownik nazwa → wartości, zbiór długości | komórka z `assert` |
| 01.4a | funkcja `demand_stats` | lista wartości jednej serii → słownik pięciu statystyk | `check("01.4", demand_stats)` |
| 01.4b | zmienne `stats`, `missing_share`, `zero_share` | słownik nazwa → statystyki, dwa udziały od 0 do 1 | komórka z `assert` |
| 01.5 | funkcja `top_series` | statystyki, nazwa statystyki, `n` → lista par (nazwa, wartość) | `check("01.5", top_series)` |
| 01.6 | funkcja `save_summary` | statystyki, ścieżka → zapisany plik JSON, jego ścieżka | `check("01.6", save_summary)` |
| 01.7 | zmienne `regular`, `intermittent`, dwie odpowiedzi tekstem | listy nazw serii | bez sprawdzenia |

`uv run course check` pokaże zadania 01 jako nierozpoczęte z dopiskiem "sprawdzasz w notebooku". Tak ma być. Te funkcje żyją w komórkach, więc sprawdza je tylko notebook.

## Co wykorzystasz z poprzednich labów

To pierwszy lab z kodem. Z modułu 00 potrzebujesz tylko działającego środowiska i pobranych danych. Wewnątrz labu funkcje budują jedna na drugiej:

- 01.2 wywołuje `parse_value` z 01.1,
- 01.3 wywołuje `parse_series_line` z 01.2,
- 01.4b liczy `demand_stats` dla każdej serii ze słownika `series` z 01.3b,
- 01.5, 01.6 i 01.7 dostają słownik `stats` z 01.4b.

W labie 02 przeniesiesz wszystkie sześć funkcji, razem z docstringami, do pliku `labs/02-functions/carparts.py`.

## Zanim zaczniesz

- `uv run course doctor` nie pokazuje błędów, dane są pobrane (`uv run course data`).
- Przeczytałeś wykład 01.

## Gdy utkniesz

1. Przeczytaj jeszcze raz opis zadania i docstring funkcji.
2. Przeczytaj komunikat sprawdzenia: mówi, dla jakich danych wynik się nie zgadza.
3. Otwórz kolejną podpowiedź pod zadaniem.
4. Zapytaj tutora: `/hint 01.3`.
