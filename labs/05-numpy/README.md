# Lab 05: NumPy na prawdziwym panelu sprzedaży

Wykład: [`lectures/05-numpy/index.html`](../../lectures/05-numpy/index.html)

Notebook: `05-numpy.ipynb`. Część kodu piszesz w notebooku, część w pakiecie.

## Co oddajesz

Zadania w kolejności notebooka. Kroki z literą (05.6a, 05.6b) to części jednego zadania: pierwszy krok to funkcja, drugi jej użycie na prawdziwych danych. Kroki "b" nie mają osobnego `check`. Sprawdza je komórka z asercjami pod nimi.

| Zadanie | Gdzie | Co | Sprawdzenie |
|---|---|---|---|
| 05.6a | notebook | funkcja `to_matrix`: długa tabela jako macierz (serie, dni) | `check("05.6", to_matrix)` |
| 05.6b | notebook | zmienne `series`, `sales`, `stockouts` | komórka z asercjami |
| 05.1 | `src/freshcast/metrics.py` | `prepare`: walidacja wejść metryk i maska | `uv run course check 05.1` |
| 05.2 | `src/freshcast/metrics.py` | `mae`, `rmse` | `uv run course check 05.2` |
| 05.3a | `src/freshcast/metrics.py` | `wape`, `bias` | `uv run course check 05.3` |
| 05.7 | notebook | funkcja `seasonal_naive`: prognoza sezonowa dla wszystkich serii | `check("05.7", seasonal_naive)` |
| 05.3b | notebook | zmienne `forecasts`, `in_stock`: trzy prognozy i maska dni bez braków | komórka z asercjami |
| 05.4a | `src/freshcast/numeric.py` | `row_shares` | `uv run course check 05.4` |
| 05.4b | notebook | zmienne `profiles`, `no_profile`, `mean_profile` | komórka z asercjami |
| 05.5 | `tests/test_metrics.py` | razem co najmniej 6 testów (z gotowym), które wykrywają 7 zepsutych metryk | `uv run course check 05.5` |
| 05.8 | notebook | trzy pytania, odpowiedź słowami | bez sprawdzenia |

Tabela to tylko spis. Pełny opis każdego zadania (cel, wejście, wynik, kroki, sprawdzenie) jest w notebooku pod nagłówkiem zadania, a dokładna umowa funkcji z pakietu w jej docstringu. Lista siedmiu zepsutych metryk z 05.5 i trzy pytania 05.8 też są w notebooku.

W zadaniach z notebooka do `check` przekazujesz samą funkcję, bez nawiasów. `uv run course check` w terminalu pokazuje je jako nierozpoczęte z dopiskiem "sprawdzasz w notebooku". Tak ma być.

## Co wykorzystasz z poprzednich labów

- **Lab 04:** klasę `SeasonalNaiveForecaster` z `src/freshcast/models/local.py` (`from freshcast.models.local import SeasonalNaiveForecaster`). Notebook porównuje z nią Twoją `seasonal_naive` w 05.7, więc ta klasa musi działać. Z labu 04 bierzesz też sposób pisania testów, czyli `pytest.approx`, `pytest.raises(ValueError, match=...)` i `@pytest.mark.parametrize`. Bierzesz też mechanizm sprawdzenia testów zepsutym kodem (04.2).
- **Lab 02:** adnotacje typów i docstringi. Funkcje w `metrics.py` i `numeric.py` mają gotowe adnotacje i docstringi. Czytasz je jak umowę.
- **Moduł 00:** `uv run course data` (dane FreshRetailNet) i `uv run course check`.

Z notebooka tego labu: tablice `ids`, `day`, `dates`, `sale`, `stockout_hours`, `hours` z sekcji "Dane jako tablice" są gotowe. Opis każdej jest w tabeli pod komórką, która je tworzy.

## Zanim zaczniesz

- Dane są pobrane (`uv run course data`), a `uv run course doctor` nie pokazuje błędów.
- Masz zrobiony moduł 04. Jeśli nie, `uv run course catchup 05`.
- Przeczytałeś wykład 05.

## Gdy utkniesz

1. Wypisz `shape` i `dtype` każdej tablicy, której używasz. Większość błędów w NumPy to zły kształt.
2. Przeczytaj komunikat sprawdzenia.
3. Otwórz kolejną podpowiedź pod zadaniem.
4. Zapytaj tutora: `/hint 05.6`.
