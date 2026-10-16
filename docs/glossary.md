# Słowniczek

Kurs używa angielskich terminów, bo takich używa się w pracy i w dokumentacji. Tu jest ich polskie znaczenie. Lista rośnie z kolejnymi modułami.

| Termin | Po polsku | Znaczenie |
|---|---|---|
| adapter |  | Obiekt, który dopasowuje jeden interfejs do drugiego, np. modele jednej serii do interfejsu `fit(X, y)` / `predict(X)` |
| average precision (AP) |  | Pole pod krzywą precision-recall liczone schodkowo. Mierzy ranking modelu bez wyboru progu |
| axis | oś | Kierunek w tablicy NumPy: `axis=0` to wiersze (w dół), `axis=1` to kolumny (w poprzek) |
| backoff | odczekiwanie | Rosnące odstępy między kolejnymi próbami przy ponawianiu |
| backtest | test wsteczny | Ocena modelu na kilku kolejnych okresach z przeszłości, każdy z treningiem tylko na danych sprzed niego |
| baseline | punkt odniesienia | Najprostsza sensowna prognoza, z którą porównujesz każdy model |
| batch | partia | Porcja przykładów, na której model robi jeden krok uczenia |
| bias | obciążenie | Metryka: (suma prognoz − suma rzeczywista) / suma rzeczywista. Plus to prognoza za wysoka, minus za niska |
| broadcasting |  | Reguła NumPy dopasowująca kształty dwóch tablic w jednym działaniu |
| bucket |  | Kontener na obiekty w magazynie S3 |
| cache | pamięć podręczna | Zapisana kopia wyniku albo pliku, żeby nie liczyć ani nie pobierać go drugi raz |
| calibration | kalibracja | Zgodność przewidywanych prawdopodobieństw z obserwowanymi częstościami |
| check | sprawdzenie | Automatyczny test zadania z kursu: `uv run course check` |
| CI | ciągła integracja | Automatyczne sprawdzenia uruchamiane na czystej maszynie przy każdej zmianie |
| closure | domknięcie | Funkcja razem ze zmiennymi z otaczającej funkcji, które zapamiętała |
| commit | zatwierdzenie | Zapisany stan zmian w gicie |
| comprehension |  | Wyrażenie budujące listę, słownik albo zbiór z innej kolekcji: `[f(x) for x in xs]` |
| container | kontener | Uruchomiony obraz Dockera: proces odizolowany od reszty maszyny |
| correlation | korelacja | Liczba od −1 do 1 mówiąca, na ile dwie kolumny rosną i maleją razem |
| cutoff | data podziału | Pierwszy dzień, od którego dane trafiają do części walidacyjnej albo testowej |
| data contract | kontrakt danych | Umowa o kolumnach i typach pliku, sprawdzana przy zapisie i przy odczycie |
| dataclass |  | Klasa, której `__init__`, `__repr__` i `__eq__` Python tworzy z listy pól |
| decorator | dekorator | Funkcja, która dostaje funkcję i zwraca nową, zwykle ją opakowującą |
| dimension table | tabela wymiaru | Tabela z jednym wierszem na obiekt (sklep, produkt), opisująca jego stałe cechy |
| docstring |  | Opis funkcji w potrójnym cudzysłowie zaraz pod `def`. W tym kursie to specyfikacja zadania |
| downcast | zmniejszenie typu | Zamiana typu liczbowego na mniejszy (np. `int64` na `int8`) bez zmiany wartości |
| drift | dryf | Zmiana danych albo zależności w czasie, przez którą model działa gorzej |
| dtype | typ danych | Typ wartości w kolumnie albo tablicy, np. `int8`, `float64` |
| early stopping | wczesne zatrzymanie | Przerwanie uczenia, gdy błąd na walidacji przestaje spadać, i powrót do najlepszego stanu |
| editable install | instalacja edytowalna | Instalacja pakietu, w której zmiany w kodzie źródłowym działają od razu, bez ponownej instalacji |
| embedding |  | Wyuczony wektor liczb zastępujący wartość kategorii, np. sklep albo produkt |
| epoch | epoka | Jedno przejście uczenia przez wszystkie przykłady treningowe |
| exit code | kod wyjścia | Liczba, którą proces kończy działanie. 0 znaczy sukces |
| F1 |  | Średnia harmoniczna precision i recall |
| fact table | tabela faktów | Tabela z jednym wierszem na zdarzenie, np. sprzedaż serii w danym dniu |
| fail fast | | Podejście, w którym program przerywa działanie przy pierwszym złamanym założeniu |
| feature | cecha | Kolumna wejściowa modelu |
| fork | | Własna kopia cudzego repozytorium na GitHubie |
| generator |  | Funkcja z `yield`, która oddaje wartości po jednej, na żądanie |
| gradient descent | spadek gradientu | Uczenie przez przesuwanie parametrów małymi krokami przeciwnie do gradientu straty |
| holdout | okres testowy | Ostatnie okresy danych schowane przed modelem, na których mierzysz jego błąd |
| horizon | horyzont prognozy | Liczba okresów naprzód, na które liczysz prognozę |
| hyperparameter | hiperparametr | Ustawienie modelu wybierane przez człowieka, nie przez uczenie, np. `alpha` albo liczba drzew |
| image | obraz | Zapis systemu plików z aplikacją i jej środowiskiem, z którego Docker uruchamia kontenery |
| intercept | wyraz wolny | Stała dodawana do sumy ważonej cech w modelu liniowym |
| JSON |  | Tekstowy format zapisu danych: słowniki, listy, liczby i napisy |
| k-means |  | Klastrowanie, które przypisuje punkty do najbliższego z k środków i przesuwa środki do średnich |
| lag | opóźnienie | Wartość sprzed określonej liczby dni w tej samej serii |
| lambda |  | Krótka funkcja bez nazwy zapisana w jednej linii: `lambda x: x[1]` |
| leakage | przeciek | Informacja w cechach, której w chwili prognozy nie będzie |
| learning rate | krok uczenia | O ile parametry przesuwają się w jednym kroku gradient descent albo boostingu |
| loss function | funkcja straty | Liczba mierząca, jak bardzo model myli się na danych treningowych. Uczenie ją minimalizuje |
| MAE | średni błąd bezwzględny | Średnia z wartości bezwzględnych różnic między prognozą a rzeczywistością |
| mask | maska | Tablica wartości logicznych wybierająca elementy albo wiersze |
| merge | złączenie | Połączenie dwóch tabel po kluczu |
| mixed precision | mieszana precyzja | Liczenie części operacji w 16 bitach zamiast 32, szybciej i przy mniejszej pamięci |
| mock | atrapa | Obiekt udający zależność w teście i zapamiętujący, jak go wołano |
| MSE | średni błąd kwadratowy | Średnia z kwadratów różnic między prognozą a rzeczywistością |
| mutation testing | testowanie mutacyjne | Sprawdzanie testów przez celowe psucie kodu: dobry test wykrywa zepsutą wersję |
| NaN | brak wartości | Specjalna wartość zmiennoprzecinkowa oznaczająca brak liczby |
| nullable integer | liczba całkowita z brakami | Typ pandas `Int64` (wielka litera), który obok liczb całkowitych mieści brak wartości |
| oos (out of stock) | brak towaru | Skrót używany w nazwach kolumn: godziny, w których produktu nie było na półce |
| overfitting | przeuczenie | Dopasowanie modelu do szumu danych treningowych: dobry wynik na treningu, słaby na nowych danych |
| panel | dane panelowe | Wiele szeregów czasowych w jednej tabeli |
| Parquet |  | Kolumnowy, skompresowany format pliku, który zapisuje też typy kolumn |
| PCA | analiza głównych składowych | Rzutowanie danych na kierunki, wzdłuż których różnią się najbardziej |
| pipeline | potok | Ciąg kroków od surowych danych do wyniku, uruchamiany jednym poleceniem |
| precision | precyzja | Jaka część alarmów była trafiona: TP / (TP + FP) |
| pull request | | Prośba o włączenie zmian z jednej gałęzi do drugiej, razem z miejscem na review |
| recall | czułość | Jaka część zdarzeń została złapana: TP / (TP + FN) |
| registry | rejestr | Słownik nazw i funkcji wypełniany w chwili definiowania funkcji, np. przez dekorator |
| regularization | regularyzacja | Kara za złożoność modelu, która zmniejsza przeuczenie |
| reshape | zmiana kształtu | Ułożenie tych samych wartości tablicy w innej liczbie wierszy i kolumn |
| review | przegląd kodu | Czytanie cudzych zmian przed ich scaleniem |
| Ridge |  | Regresja liniowa z karą za duże wagi (kara L2) |
| rolling origin |  | Schemat backtestu: kolejne okna walidacji, każde po całym treningu |
| rolling window | okno kroczące | Stałej długości wycinek kolejnych dni, przesuwany wzdłuż serii |
| seasonal naive | naiwna sezonowa | Prognoza "tak jak jeden sezon temu", np. jak w tym samym dniu tygodnia tydzień wcześniej |
| series | seria | Jeden szereg czasowy. W tym kursie: jeden produkt w jednym sklepie |
| SHAP |  | Rozkład pojedynczej prognozy na wkłady cech |
| silhouette |  | Miara od −1 do 1, jak dobrze punkty pasują do swojego klastra w porównaniu z najbliższym obcym |
| src layout | układ src | Układ projektu, w którym kod pakietu leży w katalogu `src/` |
| stable sort | sortowanie stabilne | Sortowanie, które zostawia równe elementy w ich pierwotnej kolejności |
| standardization | standaryzacja | Przeskalowanie cechy tak, żeby miała średnią 0 i odchylenie standardowe 1 |
| stockout | brak towaru | Okres, w którym produktu nie było na stanie |
| target | zmienna celu | Wartość, którą model ma przewidzieć. W tym kursie `sale_amount` |
| target encoding | kodowanie średnią celu | Zamiana kategorii na średni cel w tej kategorii. Dopasowane na danych spoza treningu przecieka |
| test set | zbiór testowy | Dane odłożone do jednorazowej, końcowej oceny modelu |
| threshold | próg | Wartość wyniku modelu, od której podnosisz alarm |
| training set | zbiór treningowy | Dane, na których model uczy się parametrów |
| underfitting | niedouczenie | Model zbyt prosty, żeby uchwycić zależność: myli się i na treningu, i na walidacji |
| upstream | | Oryginalne repozytorium, z którego zrobiono fork |
| validation set | zbiór walidacyjny | Dane do porównywania modeli i wyboru ustawień, oddzielne od treningowych |
| vectorization | wektoryzacja | Zastąpienie pętli w Pythonie jednym działaniem na całej tablicy |
| view | widok | Tablica NumPy, która dzieli pamięć z inną tablicą: zmianę w jednej widać w drugiej |
| walrus operator | operator morsa | `:=`, przypisanie wewnątrz wyrażenia: `if (n := len(xs)) > 3:` |
| WAPE |  | Suma błędów bezwzględnych podzielona przez sumę wartości rzeczywistych |
| weights | wagi | Liczby, przez które model liniowy mnoży cechy |
| window function | funkcja okna | Funkcja SQL liczona dla każdego wiersza z jego otoczenia: `OVER (PARTITION BY ... ORDER BY ...)` |
