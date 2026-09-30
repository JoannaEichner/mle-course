# Lab 19: capstone

Wykład: [`lectures/19-capstone/index.html`](../../lectures/19-capstone/index.html)

Ostatni moduł zbiera cały kurs w jeden produkt i jeden raport. Nie ma tu nowych technik. Jest pytanie, które zada Ci każdy zespół: **czy ten model jest lepszy od tego, co mamy, i skąd to wiesz?**

**Czas:** około 10 godzin. Kończy się **punktem kontrolnym 4**.

## Co oddajesz

1. **Pakiet** z poleceniami `freshcast train`, `freshcast forecast` i nowym `freshcast evaluate`, z testami, zielonym CI i obrazem Dockera z modułu 16.
2. **Backtest** kilku modeli na tych samych foldach, zapisany w MLflow: co najmniej prognoza naiwna sezonowa, LightGBM i GRU z modułu 18.
3. **Jedną ocenę na zamkniętym teście**: `eval.parquet`, tydzień po danych treningowych, oglądany raz, na końcu.
4. **Raport** `reports/capstone.md` według szablonu `report-template.md`.

## Kryteria zaliczenia

- Model bije prognozę naiwną sezonową w backteście i na tygodniu testowym, w WAPE na dniach bez braków towaru, a raport podaje też bias.
- Raport porównuje LightGBM z modelem neuronowym w tym samym backteście i uzasadnia wybór.
- Raport opisuje schemat walidacji i to, że tydzień testowy jest cieplejszy niż prawie cały zbiór treningowy.
- `/review` bez uwag blokujących.

---

## 19.1 Porównanie modeli

**Kryteria akceptacji:** `compare_models(candidates, table, folds, fit_masks)` w `src/freshcast/evaluation/final.py`: każdy kandydat w tym samym backteście, wynik w jednej tabeli z kolumną `model`. Maska dla nieznanego modelu to błąd (najpewniej literówka).

**Sprawdzenie:** `uv run course check 19.1`

<details>
<summary>Podpowiedź</summary>

Pętla po kandydatach, `backtest` z maską z `fit_masks.get(name)`, `assign(model=name)`, na końcu `pd.concat`. Sprawdź `set(fit_masks) - set(candidates)` przed pętlą.

</details>

## 19.2 Baseline na teście

**Kryteria akceptacji:** `seasonal_naive_forecast(history, days)` i `test_scores(forecasts, actuals, history)` w `final.py`: model i baseline oceniane na tych samych wierszach testu.

**Sprawdzenie:** `uv run course check 19.2`

<details>
<summary>Podpowiedź</summary>

Prognoza naiwna sezonowa dnia to sprzedaż tej samej serii 7 dni wcześniej: `merge` dni testu z historią po kluczu serii i dacie przesuniętej o 7 dni, z `validate="one_to_one"`. Brak wartości tydzień wcześniej to błąd, a nie zero.

</details>

## 19.3 `freshcast evaluate`

**Kryteria akceptacji:** `pipeline.evaluate` i polecenie `evaluate` w CLI: ocena prognozy zapisanej przez `forecast` (`forecast.parquet` w katalogu modelu) na pliku z wynikami tych dni, obok baseline'u, z zapisem `test_scores.csv` w katalogu modelu.

**Sprawdzenie:** `uv run course check 19.3`, potem jeden raz:

```bash
uv run freshcast train --config configs/standard.yaml
uv run freshcast forecast --config configs/standard.yaml --model artifacts/<sygnatura> --future data/raw/freshretailnet/eval.parquet
uv run freshcast evaluate --config configs/standard.yaml --model artifacts/<sygnatura> --test data/raw/freshretailnet/eval.parquet
```

## 19.4 Raport

Skopiuj `labs/19-capstone/report-template.md` do `reports/capstone.md` i wypełnij. Notebook `19-capstone.ipynb` liczy wszystkie liczby, których potrzebujesz.

**Sprawdzenie:** `uv run course check 19.4` pilnuje tylko formy: sekcji i liczb. Treść ocenia review.

---

## Punkt kontrolny 4

```bash
git switch -c checkpoint/04
git add src tests reports labs
git commit -m "Add model comparison, final evaluation and capstone report"
git push -u origin checkpoint/04
gh pr create --fill
```

Zielone CI, potem `/review` całego pull requesta według standardu. Review sprawdza też raport: czy liczby w nim zgadzają się z MLflow i `test_scores.csv`, czy test był oglądany raz i czy wnioski wynikają z liczb.

## Gdy utkniesz

1. Wróć do modułu, z którego pochodzi problem: walidacja (11), cechy (09), pipeline (14), sieć (18).
2. `/explain` na konkretnym pytaniu o wynik: tutor pomoże go przeczytać, ale nie napisze raportu.
