# Lab 14: od notebooka do pipeline'u

Wykład: [`lectures/14-pipeline/index.html`](../../lectures/14-pipeline/index.html)

Od tego modułu praca wygląda jak w zespole. Zadania to **tickety**: opis problemu, kryteria akceptacji i sprawdzenie. Kod piszesz w pakiecie, a notebook `14-pipeline.ipynb` służy tylko do uruchomienia całości i obejrzenia wyników.

Cel sprintu: dwa polecenia, które zrobią wszystko, co do tej pory robiłeś w notebookach.

```bash
uv run freshcast train --config configs/standard.yaml
uv run freshcast forecast --config configs/standard.yaml --model artifacts/lightgbm_20240101-120000 --future data/raw/freshretailnet/eval.parquet
```

Pierwsze przygotowuje dane, robi backtest, uczy model na całej historii i zapisuje go z metadanymi. Drugie wczytuje zapisany model i prognozuje dni z pliku.

**Czas:** około 7 godzin.

---

## 14.1 Ustawienia z pliku i ze środowiska

**Kontekst.** Ścieżki, miasta, liczba drzew i foldów są dziś rozrzucone po notebookach. Mają trafić do jednego pliku YAML (`configs/*.yaml`), a każda wartość ma dać się nadpisać zmienną środowiskową, bez edycji pliku: `FRESHCAST_MODEL__ROUNDS=200`.

**Kryteria akceptacji** (`src/freshcast/config.py`):

- `load_settings(path)` czyta YAML, a zmienne `FRESHCAST_...` wygrywają z plikiem,
- nieznany klucz, zły typ albo pusta lista miast to błąd walidacji z nazwą pola, a brak pliku to `FileNotFoundError`,
- walidatory sekcji `data` odrzucają pustą listę miast.

**Sprawdzenie:** `uv run course check 14.1`

<details>
<summary>Podpowiedź 1: kierunek</summary>

Klasa `Settings` dziedziczy po `BaseSettings` z `pydantic-settings`, który czyta zmienne środowiskowe. Pozostaje dołożyć plik YAML jako drugie źródło, słabsze od środowiska.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

`settings_customise_sources` zwraca krotkę źródeł, od najważniejszego. `YamlConfigSettingsSource(settings_cls, yaml_file=path)` czyta plik. Ścieżka pliku jest znana dopiero w `load_settings`, więc klasę z tą metodą tworzysz wewnątrz funkcji.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```python
class FromFile(Settings):
    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
        return env_settings, YamlConfigSettingsSource(settings_cls, yaml_file=path)

return FromFile()
```

</details>

---

## 14.2 Zapis modelu z metadanymi

**Kontekst.** Model zapisany jako goły plik `model.joblib` za miesiąc nic nikomu nie powie. Obok ma leżeć `metadata.json`: cechy, parametry, okres treningu, wyniki backtestu. Katalog modelu ma nazwę z sygnaturą czasu (`lightgbm_20240618-213000`) i nigdy nie jest nadpisywany.

**Kryteria akceptacji** (`src/freshcast/artifacts.py`): `save_model` i `load_model` według docstringów.

**Sprawdzenie:** `uv run course check 14.2`

<details>
<summary>Podpowiedź 1: kierunek</summary>

`joblib.dump(model, plik)` zapisuje obiekt Pythona. `json.dumps(..., default=str)` zapisze też daty.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

`mkdir(parents=True, exist_ok=False)`: istniejący katalog to `FileExistsError`, a nie cicha podmiana modelu.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```python
target = directory / model_signature(name, moment or datetime.now())
target.mkdir(parents=True, exist_ok=False)
joblib.dump(model, target / MODEL_FILE)
```

</details>

---

## 14.3 Dane dla każdej wielkości zbioru

**Kontekst.** Profil `full` to 4,5 mln wierszy i kolumny godzinowe, które w całości nie mieszczą się w pamięci laptopa. Dane mają się przygotowywać miasto po mieście, tak żeby szczyt pamięci wyznaczało największe miasto, a nie cały plik. Do tego jedna funkcja decyduje, na których wierszach wolno uczyć.

**Kryteria akceptacji** (`src/freshcast/pipeline.py`):

- `cities_in(raw_path)` czyta tylko kolumnę miast,
- `prepare_in_chunks(raw_path, cities)` daje to samo co `prepare_daily` dla wszystkich miast naraz,
- `training_mask(table, in_stock_only=...)` odrzuca pierwsze tygodnie serii (niepełne lagi), a z `in_stock_only` także dni z brakami.

**Sprawdzenie:** `uv run course check 14.3`

<details>
<summary>Podpowiedź 1: kierunek</summary>

`prepare_daily` z modułu 07 przyjmuje listę miast. Wołasz ją w pętli, po jednym mieście.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

Po `pd.concat` części posortuj po serii i dacie i nadaj świeży indeks. Wiersz z najdłuższym lagiem (`WARM_UP_FEATURE`) ustawionym na `NaN` to wiersz z początku serii.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```python
mask = table[WARM_UP_FEATURE].notna()
if in_stock_only:
    mask &= table[OOS_HOURS] == 0
return mask
```

</details>

---

## 14.4 `train` i `forecast`

**Kontekst.** Kroki z labów 07-11 składają się w dwie funkcje. `train`: dane, cechy, maska, backtest, model na całej historii, zapis z metadanymi i historią potrzebną do cech przyszłości. `forecast`: wczytanie modelu i historii, prognoza bezpośrednia dni z pliku, zapis `forecast.parquet`.

**Kryteria akceptacji:** docstringi `train` i `forecast` w `src/freshcast/pipeline.py`. Każdy krok zostawia ślad w logu (`logger.info`), a nie `print` (reguła K8).

**Sprawdzenie:** `uv run course check 14.4`

<details>
<summary>Podpowiedź 1: kierunek</summary>

Wszystkie klocki już masz: `catalog.build_feature_table`, `rolling_origin_folds`, `backtest`, `LightGBMForecaster`, `forecast_direct`. Tu je tylko łączysz.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

`forecast` potrzebuje historii, żeby policzyć lagi dni przyszłych. `train` zapisuje ją obok modelu (`history.parquet`). Plik przyszłości ma surowy układ: przepuść go przez `prepare_in_chunks` z miastami z ustawień i usuń kolumny wyników (`OUTCOME_COLUMNS`), zanim cokolwiek policzysz.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```python
model, metadata = load_model(model_dir)
history = pd.read_parquet(model_dir / "history.parquet")
future = prepare_in_chunks(future_file, settings.data.cities)
known = future.drop(columns=OUTCOME_COLUMNS)
predicted = forecast_direct(model, history, known, catalog.build_feature_table)
```

</details>

---

## 14.5 CLI

**Kontekst.** Pipeline ma dać się uruchomić z terminala, z crona albo z CI. Kod wyjścia mówi, czy się udało: 0 sukces, 2 złe ustawienia (nie ma sensu ponawiać), 1 każdy inny błąd, zalogowany z pełnym tracebackiem.

**Kryteria akceptacji** (`src/freshcast/cli.py`): `build_parser` z poleceniami `train` i `forecast` oraz flagą `--verbose`, `main` z kodami wyjścia jak wyżej i jedną, jawną granicą błędów.

**Sprawdzenie:** `uv run course check 14.5`, potem prawdziwy przebieg z terminala, w katalogu repozytorium:

```bash
uv run freshcast train --config configs/standard.yaml
echo "kod wyjścia: $?"
uv run freshcast train --config configs/nie-ma-takiego.yaml
echo "kod wyjścia: $?"
```

<details>
<summary>Podpowiedź 1: kierunek</summary>

`argparse` z `add_subparsers(dest="command", required=True)`. Polecenie `freshcast` jest już zadeklarowane w `pyproject.toml` (`[project.scripts]`).

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

Dwa bloki `try`: pierwszy wokół `load_settings` łapie tylko `FileNotFoundError` i `ValidationError` i zwraca 2. Drugi wokół polecenia łapie `Exception`, loguje przez `logger.exception` i zwraca 1. To jedyne miejsce w pakiecie, gdzie `except Exception` jest na miejscu (reguła K4).

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```python
try:
    settings = load_settings(args.config)
except (FileNotFoundError, ValidationError) as error:
    logger.error("Cannot load settings: %s", error)
    return 2
try:
    ...
except Exception:
    logger.exception("The %s command failed", args.command)
    return 1
return 0
```

</details>

---

## Przebieg na profilu `full` (nieobowiązkowy)

Jeśli masz co najmniej 16 GB RAM, uruchom pipeline na całym zbiorze, 50 tysiącach serii:

```bash
/usr/bin/time -v uv run freshcast train --config configs/full.yaml 2>&1 | tail -25
```

Na maszynie autora trwało to około 15 minut przy obciążonym procesorze, szczyt pamięci około 5 GB. Zanotuj swój czas i szczyt pamięci (`Maximum resident set size`) w notebooku.

## Gdy utkniesz

1. Uruchom polecenie z `--verbose` i przeczytaj log od góry.
2. Przeczytaj komunikat sprawdzenia.
3. Otwórz kolejną podpowiedź w tickecie.
4. Zapytaj tutora: `/hint 14.4`.
