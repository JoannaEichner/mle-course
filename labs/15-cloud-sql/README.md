# Lab 15: dane w chmurze i SQL

Wykład: [`lectures/15-cloud-sql/index.html`](../../lectures/15-cloud-sql/index.html)

Model z modułu 14 leży na Twoim dysku. W zespole leżałby w **buckecie S3**, skąd pobiera go serwer prognoz, a dane czytałoby się SQL-em prosto z plików. W tym labie budujesz oba kawałki na lokalnym serwerze, który mówi tym samym protokołem co Amazon S3.

Tickety są niżej. Notebook `15-cloud-sql.ipynb` uruchamia całość i pokazuje wyniki.

**Czas:** około 9 godzin.

---

## Przygotowanie: lokalny serwer S3 i Docker

W tym module instalujesz Dockera. Na Windowsie: Docker Desktop z integracją WSL2 (Settings → Resources → WSL integration → włącz dla Ubuntu). Na Linuksie: Docker Engine według instrukcji dystrybucji. Sprawdzenie:

```bash
docker run --rm hello-world
```

Serwer S3 uruchamiasz z katalogu repozytorium:

```bash
docker compose up -d          # serwer na http://localhost:9000
docker compose ps
```

Bez Dockera ten sam serwer działa z Pythona: `uv run moto_server -p 9000` w osobnym terminalu. To serwer `moto`: trzyma dane w pamięci, więc restart czyści buckety. Przyjmuje dowolne klucze, ale boto3 i DuckDB i tak potrzebują jakiejś pary:

```bash
set -a; . configs/s3.env.example; set +a
```

Notebook sam ustawia te klucze i, jeśli serwer nie odpowiada, uruchamia go w swoim procesie. W prawdziwej pracy klucze trafiają tylko do zmiennych środowiskowych, nigdy do kodu ani do repozytorium.

---

## 15.1 Ustawienia bucketu

**Kontekst.** Sekcja `storage` w konfiguracji mówi, gdzie publikować modele: bucket, prefiks kluczy, adres serwera. Bez tej sekcji nic nie jest publikowane.

**Kryteria akceptacji** (`src/freshcast/config.py`, `StorageSettings`): nazwa bucketu według reguł S3 (3-63 znaki, małe litery, cyfry, myślniki), prefiks bez ukośników na końcach i bez pustych części, adres serwera z protokołem, hostem i portem albo brak.

**Sprawdzenie:** `uv run course check 15.1`

<details>
<summary>Podpowiedź 1: kierunek</summary>

Każde pole ma swój `field_validator`. Wzorzec nazwy bucketu jest już w pliku (`BUCKET_NAME`).

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

Prefiks: `strip("/")`, potem `split("/")` i odrzucenie części pustych, `.` i `..`. Adres: `urllib.parse.urlparse` i sprawdzenie `scheme` oraz `netloc`.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```python
@field_validator("bucket")
@classmethod
def _valid_bucket(cls, bucket: str) -> str:
    if BUCKET_NAME.fullmatch(bucket) is None:
        raise ValueError(f"bucket {bucket!r} is not a valid name ...")
    return bucket
```

</details>

---

## 15.2 Ponawianie

**Kontekst.** Sieć zawodzi: timeout, przeciążony serwer (503, `SlowDown`). Takie błędy mijają same, więc warto spróbować jeszcze raz, po chwili, a przy kolejnej porażce po dłuższej chwili. Błąd uprawnień albo brak obiektu nie minie: ponawianie tylko opóźnia porażkę.

**Kryteria akceptacji:** dekorator `retry` w `src/freshcast/storage/retry.py` (liczba prób, rosnące odstępy, ponawia tylko to, co przepuści `retry_if`, na końcu rzuca ostatni błąd, `functools.wraps`, wstrzykiwane `sleep`) i `is_transient` w `s3.py`.

**Sprawdzenie:** `uv run course check 15.2`

<details>
<summary>Podpowiedź 1: kierunek</summary>

To fabryka dekoratorów z modułu 02: `retry(attempts=..., retry_if=..., sleep=...)` zwraca dekorator.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

Pętla po próbach. Błąd, którego `retry_if` nie przepuszcza, albo błąd ostatniej próby: `raise`. W przeciwnym razie czekasz `min(base_delay * factor ** (próba - 1), max_delay)` i próbujesz znowu. Nie czekaj po ostatniej próbie.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```python
attempt = 1
while True:
    try:
        return func(*args, **kwargs)
    except Exception as error:
        if attempt == attempts or not retry_if(error):
            raise
        sleep(min(base_delay * factor ** (attempt - 1), max_delay))
        attempt += 1
```

</details>

---

## 15.3 `S3Storage`

**Kontekst.** Reszta projektu nie powinna wiedzieć, jak wygląda API boto3. Klasa-serwis daje kilka operacji na jednym buckecie: utworzenie, wysłanie i pobranie pliku, sprawdzenie istnienia, lista kluczy. Każde wywołanie serwera idzie przez `retry`.

**Kryteria akceptacji:** `make_client` i metody `S3Storage` w `src/freshcast/storage/s3.py` według docstringów.

**Sprawdzenie:** `uv run course check 15.3`

<details>
<summary>Podpowiedź 1: kierunek</summary>

`boto3.client("s3", endpoint_url=..., region_name=..., config=Config(...))`. Metody klienta: `create_bucket`, `put_object`, `get_object` albo `download_file`, `head_object`, `list_objects_v2`.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

`exists` to `head_object` na dokładnym kluczu: błąd 404 znaczy "nie ma", każdy inny błąd leci dalej. `list_keys` przechodzi po stronach (`get_paginator("list_objects_v2")`), bo jedna odpowiedź ma najwyżej 1000 kluczy.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```python
def exists(self, key: str) -> bool:
    try:
        self._retrying(self._client.head_object)(Bucket=self.bucket, Key=key)
    except ClientError as error:
        if is_missing(error):
            return False
        raise
    return True
```

</details>

---

## 15.4 Pobieranie z cache

**Kontekst.** Ten sam plik pobierany przy każdym uruchomieniu marnuje czas i transfer. `fetch(key)` trzyma kopię lokalnie i pobiera obiekt tylko wtedy, gdy się zmienił. O zmianie mówi ETag obiektu.

**Kryteria akceptacji:** `S3Storage.fetch` według docstringu. Kopia podmienionego obiektu nigdy nie jest zwracana, a klucz z `..` nie może wyjść poza katalog cache.

**Sprawdzenie:** `uv run course check 15.4`

<details>
<summary>Podpowiedź 1: kierunek</summary>

`head_object` zwraca `ETag` bez przesyłania treści. Zapisz ETag obok kopii i porównuj.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

ETag może wyznaczać katalog kopii: `cache_dir / bucket / etag / key`. Podmieniony obiekt ma nowy ETag, więc trafia do nowego katalogu, a stara kopia nigdy nie zostanie zwrócona zamiast nowej. Klucz sprawdź, zanim złożysz z niego ścieżkę.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```python
if not key or key.startswith("/") or ".." in key.split("/"):
    raise ValueError(...)
head = self._retrying(self._client.head_object)(Bucket=self.bucket, Key=key)
local = self.cache_dir / self.bucket / head["ETag"].strip('"') / key
if not local.is_file():
    self.download_file(key, local)
return local
```

</details>

---

## 15.5 Publikacja modelu

**Kontekst.** Model zapisany przez `train` ma trafić do bucketu pod swoją sygnaturą, a serwer prognoz ma go stamtąd pobrać. Model opublikowany częściowo nie może wyglądać na kompletny.

**Kryteria akceptacji:** `publish_model` i `fetch_model` w `s3.py` oraz krok publikacji na końcu `pipeline.train`, gdy ustawienia mają sekcję `storage`.

**Sprawdzenie:** `uv run course check 15.5`

<details>
<summary>Podpowiedź 1: kierunek</summary>

`metadata.json` wysyłasz na końcu: jego obecność w buckecie znaczy, że reszta już jest.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

`fetch_model` pobiera do katalogu tymczasowego obok celu i zmienia jego nazwę dopiero, gdy wszystkie pliki są na miejscu (`Path.rename` jest atomowe w obrębie jednego systemu plików).

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```python
files = sorted(p for p in model_dir.rglob("*") if p.is_file())
ordered = [p for p in files if p.name != METADATA_FILE] + [model_dir / METADATA_FILE]
for path in ordered:
    storage.upload_file(path, _join_key(prefix, signature, path.relative_to(model_dir).as_posix()))
```

</details>

---

## 15.6 Testy serwisu

**Kontekst.** Kod sieciowy testuje się na podróbce, nigdy na prawdziwym serwerze: `moto` udaje S3 w pamięci procesu. W `tests/storage/test_s3.py` jest wzór jednego testu. Dopisz co najmniej osiem, które wykryją siedem celowo zepsutych wersji serwisu.

**Sprawdzenie:** `uv run course check 15.6`

<details>
<summary>Podpowiedź 1: kierunek</summary>

Każdy błąd z listy, którą pokaże sprawdzenie, potrzebuje danych, na których zepsuta wersja zachowa się inaczej niż poprawna.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

Dwa błędy dotyczą ponawiania. `moto` nie zawodzi przejściowo, więc tu potrzebujesz własnej podróbki klienta: małej klasy z metodą `head_object`, która najpierw rzuca błąd 503, a potem odpowiada. `sleep` podaj jako funkcję, która tylko zapisuje czasy oczekiwania.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```python
class FlakyClient:
    def __init__(self) -> None:
        self.calls = 0

    def head_object(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            raise ClientError({"Error": {"Code": "SlowDown"}, "ResponseMetadata": {"HTTPStatusCode": 503}}, "HeadObject")
        return {"ETag": '"x"'}
```

</details>

---

## 15.7 SQL: filtr, grupowanie, złączenia

**Kontekst.** Te same pytania, które zadawałeś w pandas, zadasz w SQL, prosto do pliku parquet. DuckDB działa w procesie Pythona, bez serwera, a plik jest tabelą.

**Kryteria akceptacji** (`src/freshcast/storage/sql.py`): `connect`, `city_sales`, `store_summary`, `category_sales` według docstringów. Wartości trafiają do zapytań jako parametry `?`, nigdy wklejone do tekstu.

**Sprawdzenie:** `uv run course check 15.7`

<details>
<summary>Podpowiedź 1: kierunek</summary>

`con.execute("SELECT ... FROM read_parquet(?) WHERE city_id = ?", [str(path), city_id]).df()`.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

`category_sales` najpierw liczy wiersze faktów bez pary w wymiarach (`LEFT JOIN ... WHERE wymiar.klucz IS NULL`) i odmawia, jeśli są. Dopiero potem łączy i grupuje.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```sql
SELECT store_id, COUNT(DISTINCT product_id) AS n_products, SUM(sale_amount) AS total_sales
FROM read_parquet(?)
GROUP BY store_id
ORDER BY store_id
```

</details>

---

## 15.8 SQL: funkcje okna

**Kontekst.** `groupby().shift()` i `rolling()` z modułu 07 mają odpowiedniki w SQL: funkcje okna z `PARTITION BY`. Notebook porównuje wyniki obu.

**Kryteria akceptacji:** `top_products_per_store`, `sales_lag`, `rolling_mean_7` w `sql.py` według docstringów.

**Sprawdzenie:** `uv run course check 15.8`

<details>
<summary>Podpowiedź 1: kierunek</summary>

`LAG(sale_amount, ?) OVER (PARTITION BY store_id, product_id ORDER BY dt)`. `PARTITION BY` to `groupby`, `ORDER BY` w oknie to sortowanie w serii.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

Średnia z 7 dni przed wierszem, bez niego: ramka okna `ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING`. Na początku serii ramka ma mniej niż 7 dni, a `AVG` po cichu uśredni te kilka: sprawdź `COUNT` w tym samym oknie i zwróć `NULL`, gdy dni jest mniej niż 7. Ranking w sklepie: `ROW_NUMBER() OVER (PARTITION BY store_id ORDER BY total_sales DESC, product_id)`, a filtr po rankingu w osobnym kroku `WITH`, bo `WHERE` działa przed funkcjami okna.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```sql
WITH totals AS (
    SELECT store_id, product_id, SUM(sale_amount) AS total_sales
    FROM read_parquet(?) GROUP BY store_id, product_id
), ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY store_id ORDER BY total_sales DESC, product_id) AS rank_in_store
    FROM totals
)
SELECT * FROM ranked WHERE rank_in_store <= ? ORDER BY store_id, rank_in_store
```

</details>

---

## Gdy utkniesz

1. Czy serwer działa? `curl -s http://localhost:9000 | head -c 200` powinno coś zwrócić.
2. Przeczytaj komunikat sprawdzenia i log.
3. Otwórz kolejną podpowiedź w tickecie.
4. Zapytaj tutora: `/hint 15.4`.
