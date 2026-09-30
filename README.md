# ML Engineering from Scratch

Otwarty kurs po polsku: od podstaw Pythona do pracy inżyniera ML. Około 160 godzin, jeden projekt przez cały kurs.

Budujesz prognozę dziennej sprzedaży świeżych produktów w 898 sklepach: od surowego pliku, przez czyszczenie, cechy, modele i walidację, do pipeline'u z testami, CI i obrazem Dockera. Dane to [FreshRetailNet-50K](https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K), prawdziwy zbiór z brakami towaru, rabatami i pogodą.

## Dla kogo

Umiesz napisać pętlę, funkcję, użyć listy i słownika. Nie musisz znać klas, gita, terminala, NumPy ani pandas. Matematyka na poziomie liceum wystarczy.

Po kursie potrafisz wziąć zadanie w cudzym repozytorium i oddać pull request z testami, typami i zielonym CI. Potrafisz też samodzielnie przejść od prostego baseline'u do dostrojonego modelu i obronić jego wynik.

## Jak zacząć

1. Otwórz [lekcję 00](lectures/00-setup/index.html) w przeglądarce i przejdź ją krok po kroku.
2. Na końcu uruchom tutora (`claude`, potem `/setup`) albo dokończ ścieżką bez tutora.
3. `uv run course check 00` pokazuje trzy zaliczone punkty. Zaczynasz moduł 01.

Wymagania: Windows 10/11 z WSL2 albo Linux, 8 GB RAM (16 GB zalecane), karta NVIDIA do modułu 18.

## Jak wygląda moduł

- **Wykład** w `lectures/`: strona HTML z quizami i interaktywnymi przykładami. Zacznij od [mapy kursu](lectures/index.html).
- **Lab** w `labs/`: notebook, który prowadzi przez zadania. Kod piszesz w pakiecie `src/freshcast/`.
- **Sprawdzenie**: `uv run course check 07` mówi, które zadania działają, a przy pozostałych, co jest nie tak.
- **Podpowiedzi**: trzy poziomy pod każdym zadaniem. Do tego tutor.

| Polecenie | Co robi |
|---|---|
| `uv run course doctor` | Sprawdza środowisko i dobiera profil danych |
| `uv run course data` | Pobiera dane |
| `uv run course check 07` | Sprawdza zadania modułu albo jednego zadania (`07.2`) |
| `uv run course profile small` | Zmienia profil danych |
| `uv run course catchup 08` | Wpisuje kod referencyjny modułów przed podanym |

## Tutor

W repozytorium są instrukcje dla agenta AI (`AGENTS.md`). Uruchomiony w katalogu kursu, na przykład przez Claude Code, staje się tutorem: tłumaczy, zadaje pytania naprowadzające, robi review. Rozwiązań zadań nie pisze.

| Komenda | Kiedy |
|---|---|
| `/setup` | Konfiguracja środowiska w lekcji 00 |
| `/hint 07.3` | Utknąłeś w zadaniu |
| `/check 07.3` | Sprawdzenie nie przechodzi i nie wiesz dlaczego |
| `/explain rolling` | Nie rozumiesz pojęcia |
| `/quiz 07` | Chcesz się sprawdzić |
| `/review` | Punkt kontrolny: review pull requesta |

Kurs da się przejść bez tutora.

## Rozwiązania

Kod referencyjny jest na gałęzi `solutions`. Pobierzesz ją przez `git fetch upstream solutions`. Jeśli utkniesz i chcesz iść dalej, `uv run course catchup NN` wpisze rozwiązania modułów przed `NN` do Twojego pakietu, a poprzednie wersje plików zachowa w `.course/backup/`.

## Stan

Kurs jest w budowie. Gotowe: lekcja 00, moduł 07 i fragment wykładu 01. Plan wszystkich 20 modułów jest na [mapie kursu](lectures/index.html).

## Licencja

Kod na licencji MIT (`LICENSE`). Treści na licencji CC BY 4.0 (`LICENSE-CONTENT.md`). Autor: Jakub Eichner.

Dane: FreshRetailNet-50K, Dingdong-Inc, CC BY 4.0. Wang i in., "FreshRetailNet-50K: A Stockout-Annotated Censored Demand Dataset for Latent Demand Recovery and Forecasting in Fresh Retail", arXiv:2505.16319.
