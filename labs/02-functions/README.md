# Lab 02: z notebooka do typowanego modułu

Wykład: [`lectures/02-functions/index.html`](../../lectures/02-functions/index.html)

Notebook: `02-functions.ipynb`. Kod piszesz w `carparts.py` obok notebooka.

## Co oddajesz

Plik `carparts.py`, który przechodzi `ruff format --check`, `ruff check` i `mypy --strict`, z:

| Zadanie | Co | Sprawdzenie w notebooku |
|---|---|---|
| 02.1 | sześć funkcji z labu 01, z typami i docstringami | `check("02.1", carparts)` |
| 02.2 | dekorator `timed` | `check("02.2", carparts.timed)` |
| 02.3 | fabryka dekoratorów `requires_history` | `check("02.3", carparts.requires_history)` |
| 02.4 | `register`, sześć statystyk, `summarise` | `check("02.4", carparts)` |
| 02.5 | `at_least`, `select` | `check("02.5", carparts)` |

## Zanim zaczniesz

- Masz zrobiony lab 01: w 02.1 przenosisz swoje funkcje. Jeśli go pominąłeś, napisz je według opisu labu 01: `course catchup` nie uzupełnia notebooków.
- Przeczytałeś wykład 02.

## Gdy utkniesz

1. Uruchom `ruff check` i `mypy --strict` i przeczytaj pierwszy komunikat.
2. Przeczytaj komunikat sprawdzenia.
3. Otwórz kolejną podpowiedź pod zadaniem.
4. Zapytaj tutora: `/hint 02.3`.
