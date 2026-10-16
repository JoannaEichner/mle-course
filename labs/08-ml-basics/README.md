# Lab 08: pierwszy model i uczciwy test

Wykład: [`lectures/08-ml-basics/index.html`](../../lectures/08-ml-basics/index.html)

Notebook: `08-ml-basics.ipynb`. Zadania 08.1-08.5 piszesz w pakiecie `src/freshcast/`, zadania 08.6-08.7 w komórkach notebooka. Każde zadanie w notebooku ma ten sam układ: **Cel**, **Gdzie**, **Wejście**, **Wynik**, **Skorzystaj z**, **Kroki**, **Sprawdzenie**, potem podpowiedzi.

## Co oddajesz

| Zadanie | Krok | Plik i funkcja albo zmienna w notebooku | Sprawdzenie |
|---|---|---|---|
| 08.1 Podział po czasie | 08.1a | `src/freshcast/split.py`: `last_days_start` | `uv run course check 08.1` |
| | 08.1b | `src/freshcast/split.py`: `split_by_date` | jak wyżej |
| | 08.1c | notebook: `rest`, `test`, `train`, `valid` | `assert` pod komórką |
| 08.2 Baseline na panelu | 08.2a | `src/freshcast/models/panel.py`: `PerSeriesForecaster.fit` | `uv run course check 08.2` |
| | 08.2b | `src/freshcast/models/panel.py`: `PerSeriesForecaster.predict` | jak wyżej |
| 08.3 Regresja od zera | 08.3a | `src/freshcast/models/gradient.py`: `predict_linear` | `uv run course check 08.3` |
| | 08.3b | `src/freshcast/models/gradient.py`: `mse` | jak wyżej |
| | 08.3c | `src/freshcast/models/gradient.py`: `mse_gradient` | jak wyżej |
| | 08.3d | `src/freshcast/models/gradient.py`: `fit_linear_gd` | jak wyżej |
| 08.4 `LinearForecaster` | 08.4a | `src/freshcast/models/panel.py`: `LinearForecaster._checked` | `uv run course check 08.4` |
| | 08.4b | `src/freshcast/models/panel.py`: `LinearForecaster.fit` | jak wyżej |
| | 08.4c | `src/freshcast/models/panel.py`: `LinearForecaster.predict` | jak wyżej |
| 08.5 Jedna funkcja oceny | | `src/freshcast/evaluation/scores.py`: `score_forecast` | `uv run course check 08.5` |
| 08.6 Pułapka: wszystkie kolumny | 08.6a | notebook: `everything`, `greedy`, `greedy_scores` | `assert` pod komórką, Twoja reguła |
| | 08.6b | notebook: `with_oos_scores` | tabela pod komórką |
| 08.7 Walidacja, potem test | 08.7a | notebook: `by_alpha`, `best_alpha` | `assert` pod komórką |
| | 08.7b | notebook: `results` | `assert` pod komórką |

Na górze trzech plików dopisujesz importy. W Twojej wersji plików ich nie ma:

- `split.py`: `from freshcast.data.schema import DATE`,
- `models/panel.py`: `from freshcast.data.schema import DATE, SERIES_KEY`, `from sklearn.linear_model import Ridge`, `from sklearn.preprocessing import StandardScaler` i `make_pipeline` dopisane do linii `from sklearn.pipeline import Pipeline`,
- `evaluation/scores.py`: `from freshcast import metrics`.

`gradient.py` ma już `numpy`.

Całość z pakietu: `uv run course check 08`. Zadania 08.6 i 08.7 nie mają `check`. Sprawdzają je komórki z `assert` w notebooku.

Notebook kończy się tabelą: baseline kontra Ridge na teście, na wszystkich dniach i na dniach bez braków towaru.

## Co wykorzystasz z poprzednich labów

| Co | Skąd | Jak to dostajesz | Gdzie w labie 08 |
|---|---|---|---|
| `data/processed/daily.parquet`: jeden wiersz to sprzedaż jednego produktu w jednym sklepie jednego dnia | zadanie 07.6 (budowa: 07.6a, zapis: 07.6b, odczyt: 07.6c) | `from freshcast.data.prepare import load_processed`, potem `load_processed(paths.PROCESSED_DIR)`. Pierwsza komórka z danymi robi to za Ciebie i buduje plik, jeśli go nie ma | zmienna `daily`, z niej `panel` |
| `add_lag`, `add_rolling_mean` | kroki 07.5b i 07.5c | `from freshcast.data.panel import add_lag, add_rolling_mean` (pierwsza komórka) | komórka z `FEATURES` buduje nimi cztery cechy w `panel` |
| nazwy kolumn `DATE`, `TARGET`, `SERIES_KEY`, `OOS_HOURS`, `OUTCOME_COLUMNS` | plik dany `src/freshcast/data/schema.py`, kontrakt z modułu 07 | `from freshcast.data.schema import ...` | wszędzie. `SERIES_KEY` i `DATE` w 08.2, `OUTCOME_COLUMNS` w 08.6 |
| kolumny `discount`, `discount_is_zero`, `oos_hours` | kroki 07.2d (`clean_discount`) i 07.4c (`summarise_hours`), zapisane w `daily.parquet` | są w `daily` | cechy rabatu, maska "dzień bez braków towaru", 08.6b |
| `SeasonalNaiveForecaster` i interfejs `fit(history)`, `predict(horizon)` | zadanie 04.1 | `from freshcast.models.local import SeasonalNaiveForecaster` | 08.2 (baseline), 08.7b |
| `metrics.wape`, `metrics.mae`, `metrics.bias` z argumentem `mask` | zadania 05.2 i 05.3 | `from freshcast import metrics` | 08.2 (komórka z baseline'em), 08.5 |

Jeśli któregoś z tych zadań nie masz albo nie przechodzi sprawdzenia, `uv run course catchup 08` wpisze kod referencyjny modułów przed 08 do Twojego pakietu. Pierwsza komórka z danymi zbuduje wtedy `daily.parquet`.

## Zanim zaczniesz

- Masz `data/processed/daily.parquet` z labu 07 albo kod z `uv run course catchup 08`.
- `uv run course check 07` pokazuje zaliczone zadania 07.5 i 07.6, albo zrobiłeś catchup.
- Przeczytałeś wykład 08.

## Gdy utkniesz

1. Wypisz kształty i pierwsze wiersze tego, co wchodzi do modelu i co z niego wychodzi.
2. Przeczytaj komunikat sprawdzenia.
3. Otwórz kolejną podpowiedź pod zadaniem.
4. Zapytaj tutora: `/hint 08.3`.
