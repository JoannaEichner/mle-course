# Lab 13: segmenty serii i pierwsza sieć neuronowa

Wykład: [`lectures/13-unsupervised-nn/index.html`](../../lectures/13-unsupervised-nn/index.html)

Notebook: `13-unsupervised-nn.ipynb`. Kod piszesz w `src/freshcast/segments.py` i `src/freshcast/models/mlp.py`.

## Co oddajesz

| Zadanie | Co | Sprawdzenie |
|---|---|---|
| 13.1 | `series_profile` | `uv run course check 13.1` |
| 13.2 | `standardise`, `fit_segments` | `uv run course check 13.2` |
| 13.3 | `inertia_by_k`, `silhouette_by_k` | `uv run course check 13.3` |
| 13.4 | `hour_profiles`, `project_2d` | `uv run course check 13.4` |
| 13.5 | `TabularMLP` | `uv run course check 13.5` |
| 13.6 | `train_mlp` | `uv run course check 13.6` |
| 13.7 | `MLPForecaster` | `uv run course check 13.7` |

Eksperyment z segmentem (13.8) i porównanie MLP z LightGBM (13.9) są w notebooku, bez sprawdzeń. Oba backtesty trwają łącznie kilka minut.

## Zanim zaczniesz

- Moduł 12 za Tobą, albo `uv run course catchup 13`.
- PyTorch jest w środowisku kursu. Ten lab liczy na CPU. GPU przyda się w module 18.
- Przeczytałeś wykład 13.

## Gdy utkniesz

1. Wypisz kształty tensorów na każdym kroku pętli, zanim zaczniesz szukać błędu w logice.
2. Przeczytaj komunikat sprawdzenia.
3. Otwórz kolejną podpowiedź pod zadaniem.
4. Zapytaj tutora: `/hint 13.6`.
