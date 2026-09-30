# Capstone: prognoza dziennej sprzedaży świeżych produktów

Autor: … · Data: … · Commit: … · Profil danych: …

## Dane

Skąd pochodzą dane, ile serii, dni i miast. Co zrobiłeś z rabatem równym zero, z dniami braków towaru i dlaczego. Jaki jest tydzień testowy i czym różni się od danych treningowych (pogoda, promocje, święta): podaj liczby.

## Walidacja

Jak podzieliłeś dane i dlaczego po czasie. Ile foldów, jakiej długości, na jakich wierszach model się uczy, a na jakich jest oceniany. Którą metrykę optymalizujesz i dlaczego ją. Kiedy i ile razy zajrzałeś do testu.

## Wyniki

Tabela: każdy model z backtestu (WAPE i bias na dniach bez braków, średnio i per fold) obok prognozy naiwnej sezonowej. Potem wynik na tygodniu testowym, model obok baseline'u, z `freshcast evaluate`.

| Model | WAPE backtest | Bias backtest | WAPE test | Bias test |
|---|---|---|---|---|
| naiwna sezonowa | | | | |
| … | | | | |

## Wybór modelu

Który model wybierasz do produkcji i dlaczego: wynik, rozrzut między foldami, bias, koszt uczenia i uruchamiania, prostota. Porównaj LightGBM z modelem neuronowym z modułu 18.

## Ograniczenia

Czego ten wynik nie mówi. Co może pójść źle w produkcji i jak byś to zauważył. Co zrobiłbyś w następnym tygodniu pracy i dlaczego akurat to.
