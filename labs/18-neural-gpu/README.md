# Lab 18: neuronowa prognoza na GPU

Wykład: [`lectures/18-neural-gpu/index.html`](../../lectures/18-neural-gpu/index.html)

Jeden model dla wszystkich serii naraz: sieć GRU czyta 28 ostatnich dni serii i pisze prognozę na 7 następnych, z tym, co wiadomo o przyszłych dniach (rabat, promocje, kalendarz), i z wyuczoną "wizytówką" sklepu i produktu. Uczy się na karcie graficznej. Na końcu stanie w tym samym backteście co LightGBM, a potem to samo zbudujesz w Lightning.

To jedyny moduł kursu, który wymaga karty NVIDIA. Bez niej wszystko działa na CPU, tylko kilkanaście razy wolniej.

Tickety są niżej, notebook `18-neural-gpu.ipynb` uruchamia całość i porównuje wyniki.

**Czas:** około 10 godzin.

---

## 18.1 Urządzenie i ziarno

**Kryteria akceptacji** (`src/freshcast/neural/device.py`): `pick_device(prefer_gpu)` zwraca `cuda`, gdy jest dostępna i jej chcesz, w przeciwnym razie `cpu`. `seed_everything(seed)` ustawia ziarna Pythona, NumPy i PyTorch (także CUDA).

**Sprawdzenie:** `uv run course check 18.1`, potem `nvidia-smi` i `uv run python -c "import torch; print(torch.cuda.is_available())"`.

<details>
<summary>Podpowiedź 1: kierunek</summary>

`torch.cuda.is_available()`, `torch.device("cuda")`. Ziarna: `random.seed`, `np.random.seed`, `torch.manual_seed`, `torch.cuda.manual_seed_all`.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

Na Windowsie z WSL2 sterownik NVIDIA instalujesz w Windowsie, nie w Ubuntu. W WSL działa wtedy `nvidia-smi`, a PyTorch z kursu ma już biblioteki CUDA.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```python
if prefer_gpu and torch.cuda.is_available():
    return torch.device("cuda")
return torch.device("cpu")
```

</details>

---

## 18.2 Panel jako tablica

**Kontekst.** Sieć nie czyta ramek pandas. Panel ma stać się tablicą `(serie, dni, kanały)`: jeden wiersz na serię, jedna kolumna na dzień, a w głąb sprzedaż, godziny braku, rabat i pozostałe kanały.

**Kryteria akceptacji:** `panel_cube(panel, channels)` w `src/freshcast/neural/windows.py` według docstringu, z odrzuceniem panelu z lukami.

**Sprawdzenie:** `uv run course check 18.2`

<details>
<summary>Podpowiedź 1: kierunek</summary>

To `to_matrix` z modułu 05, tylko z trzecim wymiarem. Posortowany, kompletny panel ma `serie × dni` wierszy w kolejności, którą `reshape` zamienia w tablicę.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

Nie sortuj po cichu: panel ma przyjść posortowany, a jeśli nie jest, to błąd (sortowanie zmieniłoby kolejność względem ramki wywołującego). Sprawdź, że każda seria ma te same daty w tej samej kolejności. Potem `reshape`.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```python
dates = pd.DatetimeIndex(sorted(panel[DATE].unique()))
series = len(panel) // len(dates)
if not (panel[DATE].to_numpy().reshape(series, len(dates)) == dates.to_numpy()).all():
    raise ValueError("Every series must cover the same days, in order.")
data = panel[list(channels)].to_numpy(np.float32).reshape(series, len(dates), -1)
```

</details>

---

## 18.3 Okna jako tensory

**Kontekst.** Przykład treningowy to okno: 28 dni historii jednej serii i 7 dni do prognozy. `WindowDataset` wycina okna z tablicy i oddaje je jako tensory PyTorch, całymi batchami naraz.

**Kryteria akceptacji:** `WindowDataset` w `windows.py` według docstringu: przeskalowana historia (sprzedaż podzielona przez średnią serii w oknie), kanały przyszłości, cel w oryginalnych jednostkach, maska dni bez braków.

**Sprawdzenie:** `uv run course check 18.3`

<details>
<summary>Podpowiedź 1: kierunek</summary>

Indeksowanie tablicy tablicami indeksów: `data[series[:, None], starts[:, None] + np.arange(past)]` daje od razu `(batch, past, kanały)`.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

Skala to średnia sprzedaży serii w oknie historii, z dolnym progiem 0.1: seria prawie bez sprzedaży nie dostaje ogromnych wartości po podzieleniu. Braki w oknie pomija `np.nanmean`.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```python
past_days = starts[:, None] + np.arange(self.spec.past)
past = self.data[series[:, None], past_days][:, :, self.past_idx]
scale = np.maximum(np.nanmean(past[:, :, 0], axis=1), 0.1)
past[:, :, 0] = past[:, :, 0] / scale[:, None]
```

</details>

---

## 18.4 Sieć GRU

**Kontekst.** GRU czyta dni historii po kolei i kończy na wektorze-podsumowaniu. Głowa łączy to podsumowanie z kanałami przyszłych dni i z embeddingami sklepu i produktu i pisze 7 liczb.

**Kryteria akceptacji:** `GRUForecastNet` w `src/freshcast/neural/gru.py` według docstringu, wynik kształtu `(batch, horizon)`.

**Sprawdzenie:** `uv run course check 18.4`

<details>
<summary>Podpowiedź 1: kierunek</summary>

`nn.GRU(kanały, hidden, batch_first=True)` zwraca `(wyjścia, ostatni_stan)`. Podsumowanie to ostatni stan: `h[-1]`, kształt `(batch, hidden)`.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

`nn.Embedding(liczba_sklepów, rozmiar)` zamienia kod sklepu w wektor, którego sieć się uczy. Kanały przyszłości spłaszcz do `(batch, horizon * kanały)` i złącz wszystko przez `torch.cat(..., dim=1)`.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```python
_, h = self.gru(past)
joined = torch.cat([h[-1], future.flatten(1), self.stores(store), self.products(product)], dim=1)
return self.head(joined)
```

</details>

---

## 18.5 Pętla treningowa na GPU

**Kontekst.** Pętla z modułu 13, z trzema nowościami: dane i model na GPU, mixed precision (obliczenia w 16 bitach tam, gdzie to bezpieczne) i strata liczona tylko na dniach bez braków, bo sprzedaż w dzień braku nie jest popytem.

**Kryteria akceptacji:** `masked_mae`, `fit_windows`, `predict_windows` w `src/freshcast/neural/training.py` według docstringów.

**Sprawdzenie:** `uv run course check 18.5`

<details>
<summary>Podpowiedź 1: kierunek</summary>

`masked_mae`: średnia `|prognoza − cel|` po dniach, gdzie maska jest 1 i cel jest znany. Batch przenosisz na urządzenie: `tensor.to(device, non_blocking=True)`.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

`torch.autocast(device_type=device.type, enabled=use_amp)` wokół przebiegu w przód, a `torch.amp.GradScaler` wokół kroku wstecz: w 16 bitach małe gradienty znikają, więc skaler mnoży stratę przed `backward` i dzieli gradienty z powrotem. Harmonogram `OneCycleLR` zmienia krok uczenia w trakcie epoki. Najlepsze wagi zapamiętuj jako kopię, jak w module 13.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```python
weights = in_stock * torch.isfinite(target)
if weights.sum() == 0:
    raise ValueError("No in-stock day in the batch to compute the loss on.")
errors = (forecast - torch.nan_to_num(target)).abs() * weights
return errors.sum() / weights.sum()
```

</details>

---

## 18.6 `GRUForecaster` w backteście

**Kontekst.** Sieć ma interfejs `PanelForecaster`, więc wchodzi do tego samego `backtest` co LightGBM. `fit` uczy dwa razy: pierwszy raz z odłożonym ostatnim tygodniem, żeby znaleźć liczbę epok, drugi raz na wszystkim, przez tyle epok.

**Kryteria akceptacji:** `GRUForecaster.fit` i `predict` w `src/freshcast/models/neural.py`.

**Sprawdzenie:** `uv run course check 18.6`

---

## 18.7 To samo w Lightning

**Kontekst.** Lightning zabiera pętlę treningową, urządzenie, mixed precision, early stopping i zapis najlepszego modelu. Ty piszesz, co robi jeden krok.

**Kryteria akceptacji:** `WindowModule` i `fit_with_lightning` w `src/freshcast/neural/lightning.py`.

**Sprawdzenie:** `uv run course check 18.7`

<details>
<summary>Podpowiedź 1: kierunek</summary>

`LightningModule` z `training_step`, `validation_step` i `configure_optimizers`. `Trainer(callbacks=[EarlyStopping(...), ModelCheckpoint(...)])`.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

Kody sklepów i produktów zarejestruj jako bufory (`register_buffer`): Lightning przeniesie je na GPU razem z siecią. Po treningu wczytaj checkpoint najlepszej epoki: `ModelCheckpoint.best_model_path`.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```python
trainer = L.Trainer(
    max_epochs=max_epochs,
    precision="16-mixed" if torch.cuda.is_available() else "32-true",
    callbacks=[EarlyStopping("valid_loss", patience=patience), checkpoint],
)
trainer.fit(module, train_loader, valid_loader)
```

</details>

---

## Profil `full` (nieobowiązkowy)

Z kartą z co najmniej 8 GB pamięci i 16 GB RAM możesz postawić GRU i LightGBM obok siebie na wszystkich 50 000 seriach: w notebooku ustaw `RUN_FULL = True`. Na maszynie autora GRU miało WAPE 0.308, LightGBM 0.306.

## Gdy utkniesz

1. Wypisz kształty tensorów na każdym kroku i urządzenie każdego z nich (`tensor.device`).
2. Najpierw uruchom na CPU z małym batchem: błędy są czytelniejsze niż na GPU.
3. Przeczytaj komunikat sprawdzenia i otwórz kolejną podpowiedź.
4. Zapytaj tutora: `/hint 18.5`.
