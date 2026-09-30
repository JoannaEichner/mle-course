# Lab 04: prognozy w pakiecie, testy, które łapią błędy

Wykład: [`lectures/04-testing/index.html`](../../lectures/04-testing/index.html)

Notebook: `04-testing.ipynb`. Kod piszesz w pakiecie: `src/freshcast/models/local.py` i `tests/models/test_local.py`.

## Co oddajesz

| Zadanie | Co | Sprawdzenie |
|---|---|---|
| 04.1 | Klasy prognoz z labu 03 w `src/freshcast/models/local.py` | `uv run course check 04.1` |
| 04.2 | Co najmniej 6 testów, które wykrywają 8 celowo wprowadzonych błędów | `uv run course check 04.2` |
| 04.3 | Piaskownica Poetry i uv, odpowiedzi w notebooku | bez sprawdzenia |
| PK1 | Pull request z modułami 01-04 i review | `/review` albo samodzielnie |

## Zanim zaczniesz

- Masz zrobiony lab 03. Jeśli nie, `uv run course catchup 04` wpisze kod referencyjny modułów 01-03 do plików `.py` (nie do notebooków).
- Przeczytałeś wykład 04.

## Gdy utkniesz

1. Uruchom `uv run pytest tests/models -q` i przeczytaj pierwszy błąd.
2. Przeczytaj listę błędów, których Twoje testy nie wykryły: każdy mówi, jakiego testu brakuje.
3. Otwórz kolejną podpowiedź pod zadaniem.
4. Zapytaj tutora: `/hint 04.2`.
