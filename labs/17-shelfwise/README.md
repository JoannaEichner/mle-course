# Lab 17: cudzy kod

Wykład: [`lectures/17-shelfwise/index.html`](../../lectures/17-shelfwise/index.html)

Przejmujesz `shelfwise`: mały pakiet do tygodniowych prognoz i sugestii zamówień dla sklepu internetowego, na danych UCI Online Retail II z modułu 06. Dane znasz. Kodu nie znasz, pisało go kilka osób przez kilka lat, a zespół zgłosił sześć ticketów.

Kod leży w `shelfwise/` w katalogu głównym repozytorium, tickety w `shelfwise/tickets/`. Zacznij od `shelfwise/README.md`: tak jak zaczynałbyś w nowej pracy.

**Czas:** około 7 godzin. **Zaliczenie:** cztery z sześciu ticketów, każdy jako osobny pull request.

## Tickety

| Ticket | Rodzaj | Sprawdzenie |
|---|---|---|
| T1 | błąd: sumy nie zgadzają się z fakturami | `uv run course check 17.1` |
| T2 | nowa funkcja: błąd prognozy per kategoria | `uv run course check 17.2` |
| T3 | nowa cecha z ustawieniem, testami i dokumentacją | `uv run course check 17.3` |
| T4 | śledztwo: walidacja lepsza niż rzeczywistość | `uv run course check 17.4` |
| T5 | niestabilny test | `uv run course check 17.5` |
| T6 | wydajność raportu | `uv run course check 17.6` |

Sprawdzenia 17.7-17.9 dotyczą problemów, o których nikt nie zgłosił ticketu. Jeśli znajdziesz któryś po drodze, popraw go w osobnym pull requeście. Na starcie wszystkie sprawdzenia modułu padają: to nie błąd kursu, tylko stan kodu, który przejmujesz.

## Jak pracujesz

To moduł o metodzie, a nie o bibliotekach. Dla każdego ticketu:

1. **Mapa.** Uruchom program i znajdź punkt wejścia (`python -m shelfwise` → `cli.py`). Prześledź jedną liczbę z ticketu od pliku wejściowego do raportu: która funkcja ją tworzy, która zmienia.
2. **Objaw na danych.** Odtwórz liczbę z ticketu sam, zanim zmienisz choćby linię. Notebook `17-shelfwise.ipynb` jest dziennikiem śledztwa: tam liczysz i zapisujesz, co znalazłeś.
3. **Przyczyna jednym zdaniem.** Trafi do opisu pull requesta.
4. **Test, który pada.** Najpierw test w `shelfwise/tests/`, który pada na obecnym kodzie z powodu tej przyczyny. Potem poprawka. Test przechodzi, pozostałe też.
5. **Jeden ticket, jedna gałąź, jeden pull request.** Poprawiasz to, czego dotyczy ticket. Ticket nie jest licencją na przepisanie połowy pakietu.

Polecenia, z katalogu `shelfwise/`:

```bash
uv run python -m shelfwise run --config settings.yaml
uv run pytest
uv run ruff check .
```

`shelfwise` ma własne, starsze ustawienia ruff i nie ma typów. Nie dopisuj ich wszędzie: dopisz je w funkcjach, które zmieniasz.

## Pull request dla ticketu

```bash
git switch main && git pull
git switch -c shelfwise/t1-returns
# test, poprawka, uv run pytest
git add shelfwise
git commit -m "Count customer returns once in net sales"
git push -u origin shelfwise/t1-returns
gh pr create --fill
```

W opisie pull requesta: objaw z ticketu, przyczyna jednym zdaniem, jak ją odtworzyłeś, co mówi nowy test.

## Gdy utkniesz

Tutor nie zdradzi, gdzie są błędy, i nie powinien. Zapyta za to o to, o co zapytałby doświadczony kolega:

1. Skąd bierze się liczba z ticketu? Która funkcja zapisuje tę kolumnę?
2. Czy umiesz policzyć tę samą liczbę ręcznie dla jednego produktu, z linii faktur?
3. Na którym kroku Twoja liczba i liczba programu rozchodzą się po raz pierwszy?
4. Jak wyglądałby test, który pada dokładnie z tego powodu?

`/hint 17.1` daje takie pytania dla konkretnego ticketu.
