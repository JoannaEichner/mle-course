# Lab 16: Docker, CI i review

Wykład: [`lectures/16-docker-ci/index.html`](../../lectures/16-docker-ci/index.html)

Pipeline działa na Twoim komputerze. Po tym labie zadziała też w kontenerze na dowolnej maszynie, każdy pull request przejdzie automatyczne sprawdzenia, a błędy formatowania nie dotrą nawet do commita. Na koniec zrobisz review cudzego kodu i sam przejdziesz **punkt kontrolny 3**.

Ten lab nie ma notebooka: cała praca to pliki konfiguracyjne i terminal.

**Czas:** około 5 godzin.

---

## 16.1 Obraz Dockera

**Kontekst.** "U mnie działa" przestaje być argumentem, gdy aplikacja jedzie w kontenerze: ten sam system, te same biblioteki, te same wersje pakietów z `uv.lock`. Obraz ma być mały, bez narzędzi budowania i bez danych, a proces w kontenerze nie potrzebuje uprawnień roota.

**Kryteria akceptacji:**

- `Dockerfile` w katalogu głównym repozytorium: obraz `python:3.12-slim`, zależności z `uv.lock` przez `uv sync --locked`, biblioteka `libgomp1` dla LightGBM, zwykły użytkownik zamiast roota, `freshcast` jako polecenie obrazu,
- `.dockerignore`, który nie wpuszcza do kontekstu budowania danych, artefaktów, środowiska `.venv`, katalogu `.git` i lokalnego stanu kursu,
- obraz buduje się i uruchamia trening na zamontowanym katalogu.

**Sprawdzenie:** `uv run course check 16.1`, potem:

```bash
docker build -t freshcast .
docker run --rm freshcast --help
docker run --rm -v "$PWD":/work freshcast train --config configs/standard.yaml
```

<details>
<summary>Podpowiedź 1: kierunek</summary>

Dwa etapy (multi-stage build): w pierwszym instalujesz wszystko uv, do drugiego kopiujesz tylko gotowe środowisko `.venv`. uv bierzesz z jego oficjalnego obrazu: `COPY --from=ghcr.io/astral-sh/uv:<wersja> /uv /bin/uv`.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

Najpierw sam `uv sync --locked --no-install-project` z plikami `pyproject.toml` i `uv.lock`: ta warstwa przebuduje się tylko po zmianie zależności. Potem kod i `uv sync --locked --no-editable`, żeby pakiet był zainstalowany, a nie podlinkowany do `src/`, którego w drugim etapie nie będzie. W drugim etapie `useradd` i `USER`.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```dockerfile
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_DEV=1
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --locked --no-editable

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home app
USER app
WORKDIR /work
COPY --from=build --chown=app:app /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["freshcast"]
```

</details>

---

## 16.2 CI w GitHub Actions

**Kontekst.** Sprawdzenia, które uruchamiasz lokalnie (reguła G3), mają się uruchamiać same przy każdym pull requeście, na czystej maszynie. Zielony znaczek przy PR to warunek review.

**Kryteria akceptacji:** `.github/workflows/ci.yml` uruchamiany dla pull requestów i pushy do `main`, z krokami: checkout, instalacja uv, `uv sync --locked`, `ruff check`, `ruff format --check`, `mypy`, `pytest`.

**Sprawdzenie:** `uv run course check 16.2`, potem push gałęzi do Twojego forka i otwarty pull request: zakładka "Checks" pokazuje przebieg.

<details>
<summary>Podpowiedź 1: kierunek</summary>

Workflow to plik YAML: `on` (kiedy), `jobs` (co), a w zadaniu `runs-on` i lista `steps`. uv instaluje akcja `astral-sh/setup-uv`.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

`--locked` sprawia, że CI odmówi pracy, gdy `uv.lock` nie zgadza się z `pyproject.toml`. To lepsze niż cicha aktualizacja zależności na maszynie CI.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```yaml
on:
  pull_request:
  push:
    branches: [main]
jobs:
  checks:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@v9
        with:
          enable-cache: true
      - run: uv sync --locked
      - run: uv run ruff check .
      # ...
```

</details>

---

## 16.3 pre-commit

**Kontekst.** CI mówi o błędzie po kilku minutach, pre-commit przed commitem. Te same narzędzia, te same wersje (z `uv.lock`), uruchamiane na zmienionych plikach.

**Kryteria akceptacji:** `.pre-commit-config.yaml` z ruff (linter i formatter) i mypy, uruchamianymi przez `uv run`, plus podstawowe haki: końcowe spacje, koniec pliku, poprawny YAML, blokada dużych plików.

**Sprawdzenie:** `uv run course check 16.3`, potem:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

Spróbuj zacommitować plik z niesformatowanym kodem i zobacz, co się stanie.

<details>
<summary>Podpowiedź 1: kierunek</summary>

Haki z repozytorium `pre-commit/pre-commit-hooks` i haki `local`, które wołają narzędzia projektu przez `uv run`.

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

mypy sprawdza cały projekt, a nie pojedyncze pliki: `pass_filenames: false`.

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```yaml
  - repo: local
    hooks:
      - id: ruff-check
        name: ruff check
        entry: uv run ruff check --fix
        language: system
        types: [python]
```

</details>

---

## 16.4 Review cudzego kodu

**Kontekst.** Kolega z zespołu otworzył pull request: `review/pull-request-42.diff`. Twoje zadanie to review według `docs/standard.md`, tak jak robi to tutor w punktach kontrolnych.

**Kryteria akceptacji:** plik `review/review.md` z:

- werdyktem: "do scalenia" albo "do poprawy",
- uwagami blokującymi, każda z miejscem w diffie, numerem reguły i konkretnym przykładem, co pójdzie źle,
- najwyżej pięcioma uwagami nieblokującymi,
- jedną rzeczą zrobioną dobrze albo pytaniem, które zadałbyś autorowi.

Bez sprawdzenia automatycznego. Gdy skończysz, pokaż swoje review tutorowi i poproś o porównanie z jego własnym review tego diffu. Dobre review znajduje co najmniej sześć problemów blokujących.

<details>
<summary>Podpowiedź 1: kierunek</summary>

Przejdź po regułach standardu, jedna po drugiej, i dla każdej przeczytaj cały diff. Szybciej znajdziesz błędy, szukając łamania konkretnej reguły, niż czytając "czy coś jest nie tak".

</details>

<details>
<summary>Podpowiedź 2: podejście</summary>

Zacznij od reguł blokujących: C1-C5, D2-D5, K1, K4, K9, T1, T4, G3, G4. Przy każdej uwadze napisz, na jakich danych kod da zły wynik: "na panelu dwóch serii średnia pierwszego dnia serii B obejmuje ostatnie dni serii A".

</details>

<details>
<summary>Podpowiedź 3: prawie kod</summary>

```markdown
**Werdykt:** do poprawy

**Blokujące**
1. `promo.py:6-11`, G4: klucze dostępu i adres wewnętrznego serwera w kodzie. ...
2. `promo.py:16`, C2: `sales_in_stock` z tego samego dnia ...
```

</details>

---

## Punkt kontrolny 3

Moduły 12-16. Pull request z Twoim Dockerfile, workflow i konfiguracją pre-commit, z zielonym CI:

```bash
git switch -c checkpoint/03
git add Dockerfile .dockerignore .github .pre-commit-config.yaml labs src tests
git commit -m "Add container image, CI and pre-commit"
git push -u origin checkpoint/03
gh pr create --fill
```

Poczekaj na zielony wynik CI, potem `/review` albo samodzielne review według standardu. Pull request z czerwonym CI nie idzie do review (G3).

## Gdy utkniesz

1. `docker build` z `--progress=plain` pokazuje pełny log każdego kroku.
2. W GitHub Actions kliknij czerwony krok: log kończy się komunikatem narzędzia.
3. Otwórz kolejną podpowiedź w tickecie.
4. Zapytaj tutora: `/hint 16.1`.
