# Lab 02: z notebooka do typowanego modułu

Wykład: [`lectures/02-functions/index.html`](../../lectures/02-functions/index.html)

Notebook: `02-functions.ipynb`. Kod piszesz w `carparts.py` obok notebooka.

## Co oddajesz

Plik `carparts.py`, który przechodzi `ruff format --check`, `ruff check` i `mypy --strict`, oraz kilka zmiennych z odpowiedziami w notebooku.

| Zadanie | Krok | Co piszesz | Gdzie | Sprawdzenie w notebooku |
|---|---|---|---|---|
| 02.1 | 02.1a | sześć funkcji z labu 01, przeniesionych z docstringami, plus importy | `carparts.py`, w miejscu komentarza `# 02.1` | komórka z `assert` |
| | 02.1b | typy parametrów i wyników tych sześciu funkcji | `carparts.py` | `check("02.1", carparts)` |
| 02.2 | | dekorator `timed` | `carparts.py`, funkcja `timed` | `check("02.2", carparts.timed)` |
| 02.3 | | fabryka dekoratorów `requires_history` | `carparts.py`, funkcja `requires_history` | `check("02.3", carparts.requires_history)` |
| 02.4 | 02.4a | dekorator `register` | `carparts.py`, funkcja `register` | `check("02.4", carparts)` |
| | 02.4b | statystyki `months`, `missing`, `total`, `zero_share`, `adi`, `cv2` | `carparts.py`, w miejscu komentarza `# 02.4` | komórka z `assert`, potem `check("02.4", carparts)` |
| | 02.4c | `summarise` | `carparts.py`, funkcja `summarise` | `check("02.4", carparts)` |
| | 02.4d | zmienne `stats`, `with_cv2` | notebook | bez sprawdzenia |
| 02.5 | 02.5a | `at_least` | `carparts.py`, funkcja `at_least` | `check("02.5", carparts)` |
| | 02.5b | `select` | `carparts.py`, funkcja `select` | `check("02.5", carparts)` |
| | 02.5c | zmienna `steady` | notebook | bez sprawdzenia |
| 02.6 | | statystyka `peak`, zmienne `peaks`, `spiky`, dwie odpowiedzi tekstem | notebook | bez sprawdzenia |

## Co wykorzystasz z poprzednich labów

Z labu 01 (`labs/01-python-data/01-python-data.ipynb`) bierzesz sześć funkcji. Każdą kopiujesz w całości, z docstringiem:

| Funkcja | Zadanie w labie 01 | Co zmieniasz w labie 02 |
|---|---|---|
| `parse_value` | 01.1 | typy. Stałej `MISSING` nie kopiujesz, już jest w `carparts.py` |
| `parse_series_line` | 01.2 | typy |
| `read_series` | 01.3a | typy, import `Path` |
| `demand_stats` | 01.4a | typy (alias `Values`, `Stats`). W docstringu "a sequence" zamiast "a list" |
| `top_series` | 01.5 | typy. Być może drobna zmiana ciała, żeby mypy widział, że wartość nie jest `None` |
| `save_summary` | 01.6 | typy, import `json` i `Path` |

Zmiennych z notebooka labu 01 (`series`, `stats`) nie przenosisz. Notebook labu 02 buduje własne: `series` w 02.2, `stats` w 02.4d.

Jeśli pominąłeś lab 01, napisz te funkcje według opisu labu 01. `course catchup` nie uzupełnia notebooków.

## Zanim zaczniesz

- Masz zrobiony lab 01: w 02.1 przenosisz swoje funkcje.
- Przeczytałeś wykład 02.

## Gdy utkniesz

1. Uruchom `ruff check` i `mypy --strict` i przeczytaj pierwszy komunikat.
2. Przeczytaj komunikat sprawdzenia.
3. Otwórz kolejną podpowiedź pod zadaniem.
4. Zapytaj tutora: `/hint 02.3`.
