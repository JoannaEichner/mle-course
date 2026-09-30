# shelfwise

Tygodniowe prognozy popytu i sugestie zamówień dla sklepu internetowego z upominkami. Kod napisał zespół analityczny w 2011 roku i od tamtej pory był rozwijany przez kilka osób. Teraz przejmujesz go Ty.

## Co robi

1. Czyta linie faktur (`io.py`) i odrzuca pozycje, które nie są produktami (`cleaning.py`).
2. Liczy sprzedaż netto: sprzedane sztuki minus zwroty klientów.
3. Sumuje ją do tygodni kalendarza firmy, od poniedziałku do niedzieli (`calendar.py`, `weekly.py`).
4. Buduje cechy: sprzedaż z poprzednich tygodni, średnie kroczące, tydzień roku (`features.py`).
5. Trenuje model Ridge i sprawdza go na ostatnich tygodniach historii (`model.py`).
6. Prognozuje następny tydzień, liczy sugerowane zamówienie i spodziewany przychód (`report.py`).

## Dane

shelfwise czyta plik `data/raw/online_retail/online_retail_II.parquet`, który powstaje w module 06 kursu (funkcja `build_cache`). Jeśli go nie masz, zbuduj go z katalogu głównego repozytorium:

```bash
uv run python -c "from coursekit import paths; from freshcast.warmup.online_retail import build_cache; build_cache(paths.ONLINE_RETAIL, paths.ONLINE_RETAIL.with_suffix('.parquet'))"
```

## Uruchomienie

Wszystko z katalogu `shelfwise/`:

```bash
uv run python -m shelfwise run --config settings.yaml
uv run pytest
```

Wyniki trafiają do `output/`: `report.csv` z jednym wierszem na produkt i `title.txt` z tytułem raportu.

## Ustawienia

| Klucz | Znaczenie |
|---|---|
| `lines_file` | plik z liniami faktur |
| `output_dir` | katalog wyników |
| `week_start_day` | pierwszy dzień tygodnia, 0 to poniedziałek |
| `min_weeks` | minimalna liczba tygodni ze sprzedażą, żeby produkt był prognozowany |
| `validation_weeks` | tygodnie odłożone do walidacji |
| `price_lookback_weeks` | z ilu ostatnich tygodni brana jest cena produktu |
| `cover_weeks` | na ile tygodni sprzedaży ma starczyć zamówienie |
| `model.alpha` | siła regularyzacji modelu Ridge |

## Jak pracujesz z ticketami

Tickety są w `tickets/`. Dla każdego:

1. Przeczytaj ticket i odtwórz objaw na danych, zanim zmienisz choćby linię.
2. Znajdź przyczynę. Zapisz ją jednym zdaniem w opisie pull requesta.
3. Napisz test, który pada na obecnym kodzie z powodu tej przyczyny.
4. Popraw kod. Test ma przejść, pozostałe testy też.
5. Jeden ticket to jedna gałąź i jeden pull request.

`uv run course check 17` z katalogu głównego pokazuje, które tickety są już zamknięte.
