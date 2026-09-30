"""Checks for module 06: first pandas, cleaning the Online Retail II table.

Task 06.1 reads ``fixtures/online_retail_sample.xlsx``: 40 rows in the two
sheets of the original workbook, with its cell types. Tasks 06.2 to 06.6 run
on small hand-made frames and, where a realistic table helps, on
``fixtures/online_retail_sample.parquet``: 1263 rows in the format of the
cache, whole invoices for each kind of anomaly plus every line of six
products. Tasks 06.1 to 06.6 build their own inputs, so none of them fails
because of an earlier one; 06.7 runs the whole chain on the parquet sample.
Expected numbers are constants measured on these files, so the checks do not
contain a second implementation of the tasks.
"""

import tempfile
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any

import pandas as pd

from coursekit import paths
from coursekit.checking import CheckFailed, expect, task

XLSX = paths.FIXTURES_DIR / "online_retail_sample.xlsx"
SAMPLE = paths.FIXTURES_DIR / "online_retail_sample.parquet"
SHEET_A = "Year 2009-2010"
SHEET_B = "Year 2010-2011"
RAW_COLUMNS = [
    "invoice",
    "stock_code",
    "description",
    "quantity",
    "invoice_date",
    "price",
    "customer_id",
    "country",
    "sheet",
]
FLAGS = ["is_cancellation", "is_non_product", "is_missing_customer", "is_bad_price"]
DAILY_COLUMNS = ["stock_code", "date", "units_sold", "units_returned", "revenue"]
BASE_LINE: dict[str, Any] = {
    "invoice": "500001",
    "stock_code": "85123A",
    "description": "THING",
    "quantity": 1,
    "invoice_date": "2010-01-04 10:00",
    "price": 2.0,
    "customer_id": 12345,
    "country": "United Kingdom",
    "sheet": SHEET_A,
}

# Measured on the workbook sample.
XLSX_ROWS = {SHEET_A: 21, SHEET_B: 19}
XLSX_MISSING_CUSTOMERS = 8
XLSX_MISSING_DESCRIPTIONS = 2
# Measured on the parquet sample.
SAMPLE_ROWS = 1263
SAMPLE_FLAGS = {
    "is_cancellation": 76,
    "is_non_product": 27,
    "is_missing_customer": 422,
    "is_bad_price": 27,
}
SAMPLE_SHARED_INVOICES = 18
SAMPLE_ROWS_AFTER_OVERLAP = {SHEET_A: 897, SHEET_B: 321}
SAMPLE_REPEATS = 52  # lines equal to an earlier line, sheet copies included
SAMPLE_DAILY_ROWS = 970
SAMPLE_PRODUCTS = 201
SAMPLE_DAYS = 425
SAMPLE_UNITS_SOLD = 7075
SAMPLE_UNITS_RETURNED = 257
SAMPLE_REVENUE = 24629.95
SAMPLE_RETURN_ONLY_ROWS = 51


def _raises(
    call: Callable[[], object],
    error: type[Exception],
    when: str,
    count: int | None = None,
) -> None:
    """Fail unless ``call`` raises ``error``. ``when`` describes the input.

    With ``count`` the message of the error must contain that number: the
    rules say how many rows break them.
    """
    try:
        call()
    except error as raised:
        if count is not None and str(count) not in str(raised):
            raise CheckFailed(
                f"Gdy {when}, komunikat błędu ma podawać liczbę {count} (tyle "
                f"jest naruszeń), a brzmi: {raised}"
            ) from raised
        return
    except NotImplementedError:
        raise
    except Exception as other:  # noqa: BLE001 - the wrong exception type is the finding
        raise CheckFailed(
            f"Gdy {when}, oczekiwano {error.__name__}, a poleciał "
            f"{type(other).__name__}: {other}"
        ) from other
    raise CheckFailed(
        f"Gdy {when}, funkcja powinna zgłosić {error.__name__}, a zakończyła się "
        "bez błędu."
    )


def _unchanged(frame: pd.DataFrame, before: pd.DataFrame, function: str) -> None:
    expect(
        frame.equals(before) and list(frame.columns) == list(before.columns),
        f"{function} zmieniło ramkę wejściową (kolumny: {list(frame.columns)}).",
    )


def _raw(*rows: dict[str, Any]) -> pd.DataFrame:
    """Typed raw table from hand-written lines. Keys left out take BASE_LINE."""
    frame = pd.DataFrame([{**BASE_LINE, **row} for row in rows])
    return frame.astype(
        {
            "invoice": "str",
            "stock_code": "str",
            "description": "str",
            "quantity": "int64",
            "invoice_date": "datetime64[us]",
            "price": "float64",
            "customer_id": "Int64",
            "country": "str",
            "sheet": "str",
        }
    )


def _line(invoice: str, code: str, quantity: int, sheet: str) -> dict[str, Any]:
    return {
        "invoice": invoice,
        "stock_code": code,
        "quantity": quantity,
        "sheet": sheet,
    }


def _good_daily() -> pd.DataFrame:
    """A valid daily table: four rows, one of them return-only."""
    return pd.DataFrame(
        {
            "stock_code": pd.Series(["10002", "10002", "10002", "20001"], dtype="str"),
            "date": pd.to_datetime(
                ["2010-01-03", "2010-01-04", "2010-01-05", "2010-01-05"]
            ),
            "units_sold": [4, 5, 0, 1],
            "units_returned": [0, 1, 2, 0],
            "revenue": [8.0, 10.0, 0.0, 1.5],
        }
    )


def _flagged(*rows: dict[str, Any]) -> pd.DataFrame:
    """Like ``_raw``, with the four flags taken from the keys of each row."""
    plain = [{k: v for k, v in row.items() if k not in FLAGS} for row in rows]
    flags = {flag: [bool(row.get(flag, False)) for row in rows] for flag in FLAGS}
    return _raw(*plain).assign(**flags)


def _times(frame: pd.DataFrame, count: int, **values: Any) -> pd.DataFrame:
    """Return ``frame`` with ``count`` copies of its first row, values overridden."""
    first = frame.iloc[[0]].assign(**values)
    return pd.concat([first] * count + [frame], ignore_index=True)


@task("06.1", "read_sheets, build_cache, load_raw: skoroszyt raz, potem parquet")
def check_read(_target: object) -> None:
    from freshcast.warmup import online_retail as retail

    raw = retail.read_sheets(XLSX)
    expect(
        isinstance(raw, pd.DataFrame) and list(raw.columns) == RAW_COLUMNS,
        f"read_sheets ma zwrócić kolumny {RAW_COLUMNS} w tej kolejności. "
        f"Dostałem: {list(getattr(raw, 'columns', raw))}",
    )
    expect(
        list(raw["sheet"])
        == [SHEET_A] * XLSX_ROWS[SHEET_A] + [SHEET_B] * XLSX_ROWS[SHEET_B]
        and raw.index.equals(pd.RangeIndex(len(raw))),
        f"Próbka ma {XLSX_ROWS[SHEET_A]} wierszy w arkuszu {SHEET_A} i "
        f"{XLSX_ROWS[SHEET_B]} w arkuszu {SHEET_B}, w kolejności pliku, z indeksem "
        f"0..n-1. Dostałem {len(raw)} wierszy, arkusze: "
        f"{raw['sheet'].value_counts().to_dict()}.",
    )

    for column in ("invoice", "stock_code", "description", "country"):
        kinds = set(raw[column].dropna().map(lambda cell: type(cell).__name__))
        expect(
            kinds <= {"str"},
            f"Kolumna {column} ma zawierać tylko tekst. W skoroszycie numery faktur "
            "i kody towarów są raz liczbami, raz tekstem, a po wczytaniu w kolumnie "
            f"są komórki typów: {sorted(kinds)}.",
        )
    expect(
        raw["invoice"].iloc[0] == "489434" and "C489449" in set(raw["invoice"]),
        "Pierwsza faktura w pliku to 489434 (liczba w skoroszycie), a faktura "
        "anulująca C489449 jest tekstem. W kolumnie invoice pierwsza wartość to "
        f"{raw['invoice'].iloc[0]!r}.",
    )

    missing = int(raw["description"].isna().sum())
    as_text = int((raw["description"] == "nan").sum())
    expect(
        missing == XLSX_MISSING_DESCRIPTIONS and as_text == 0,
        f"W próbce {XLSX_MISSING_DESCRIPTIONS} opisy są puste. Po wczytaniu "
        f'brakujących opisów jest {missing}, a napisów "nan" jest {as_text}.',
    )
    expect(
        {"21494", "20713"} <= set(raw["description"].dropna()),
        "W dwóch wierszach próbki opis jest liczbą (21494 i 20713). Po wczytaniu "
        "ma być tekstem, tak jak reszta opisów.",
    )

    customers = raw["customer_id"]
    expect(
        pd.api.types.is_integer_dtype(customers)
        and int(customers.isna().sum()) == XLSX_MISSING_CUSTOMERS
        and customers.iloc[0] == 13085,
        "customer_id ma być liczbą całkowitą z brakami (13085 w pierwszym wierszu, "
        f"{XLSX_MISSING_CUSTOMERS} braków w próbce). Dostałem typ {customers.dtype}, "
        f"{int(customers.isna().sum())} braków i {customers.iloc[0]!r} w pierwszym "
        "wierszu.",
    )
    expect(
        pd.api.types.is_datetime64_any_dtype(raw["invoice_date"])
        and pd.api.types.is_integer_dtype(raw["quantity"])
        and pd.api.types.is_float_dtype(raw["price"]),
        "invoice_date ma być datą, quantity liczbą całkowitą, price liczbą "
        f"zmiennoprzecinkową. Dostałem: {raw['invoice_date'].dtype}, "
        f"{raw['quantity'].dtype}, {raw['price'].dtype}.",
    )

    codes = set(raw["stock_code"])
    spellings = {"72349b", "72349B", "15056bl", "15056BL", "47503J ", "47503J"}
    expect(
        {"72349B", "15056BL", "47503J"} <= codes
        and codes.isdisjoint({"72349b", "15056bl", "47503J "}),
        "W skoroszycie ten sam towar bywa zapisany małymi literami (72349b, "
        '15056bl) albo z odstępem na końcu ("47503J "). Po wczytaniu mają to być '
        "kody 72349B, 15056BL i 47503J. Z tych zapisów w kolumnie są: "
        f"{sorted(codes & spellings)}.",
    )

    with tempfile.TemporaryDirectory() as scratch:
        broken = Path(scratch) / "broken.xlsx"
        pd.DataFrame({"Invoice": [489434], "StockCode": ["85048"]}).to_excel(
            broken, index=False
        )
        _raises(
            lambda: retail.read_sheets(broken),
            ValueError,
            "arkusz nie ma nagłówków Price, Country i kilku innych",
        )

        cache = Path(scratch) / "nested" / "online_retail.parquet"
        written = retail.build_cache(XLSX, cache)
        expect(
            written == cache and cache.is_file(),
            "build_cache ma utworzyć brakujące katalogi, zapisać plik parquet i "
            f"zwrócić jego ścieżkę. Zwróciło {written!r}, plik "
            f"{'istnieje' if cache.is_file() else 'nie istnieje'}.",
        )
        retail.build_cache(XLSX, cache)  # a second run overwrites without error
        restored = retail.load_raw(cache)
        try:
            pd.testing.assert_frame_equal(restored, raw)
        except AssertionError as error:
            raise CheckFailed(
                "Tabela po zapisie do parquet i odczycie różni się od tabeli z "
                f"read_sheets: {str(error).splitlines()[0]}"
            ) from error

        _raises(
            lambda: retail.load_raw(Path(scratch) / "missing.parquet"),
            FileNotFoundError,
            "pliku cache jeszcze nie ma",
        )
        raw.drop(columns="price").to_parquet(cache, index=False)
        _raises(
            lambda: retail.load_raw(cache),
            ValueError,
            "plik cache nie ma kolumny price",
        )


@task("06.2", "check_raw: reguły surowej tabeli, każda z liczbą w komunikacie")
def check_check_raw(_target: object) -> None:
    from freshcast.warmup import online_retail as retail

    sample = pd.read_parquet(SAMPLE)
    before = sample.copy()
    try:
        retail.check_raw(sample)
    except ValueError as error:
        raise CheckFailed(
            f"check_raw odrzuciło próbkę prawdziwych danych, w której każda reguła "
            f"jest spełniona. Komunikat: {error}"
        ) from error
    _unchanged(sample, before, "check_raw")

    unusual = _raw(
        {"invoice": "C500002", "quantity": -3},
        {
            "invoice": "500003",
            "quantity": -50,
            "price": 0.0,
            "customer_id": None,
            "description": None,
        },
        {"invoice": "A500004", "stock_code": "B", "price": -500.0, "customer_id": None},
        {"invoice": "500005", "stock_code": "POST", "customer_id": None},
    )
    try:
        retail.check_raw(unusual)
    except ValueError as error:
        raise CheckFailed(
            "check_raw odrzuciło dane, które reguły dopuszczają: anulowanie z ujemną "
            "ilością, ujemną ilość przy cenie 0, ujemną cenę na fakturze A, brak "
            f"opisu i brak klienta. Komunikat: {error}"
        ) from error

    ok = _raw({}, {"invoice": "500002"})
    _raises(
        lambda: retail.check_raw(sample.drop(columns="price")),
        ValueError,
        "tabeli brakuje kolumny price",
    )
    _raises(
        lambda: retail.check_raw(_times(ok, 3, price=None)),
        ValueError,
        "w trzech wierszach brakuje ceny",
        3,
    )
    _raises(
        lambda: retail.check_raw(_times(ok, 3, country=None)),
        ValueError,
        "w trzech wierszach brakuje kraju",
        3,
    )
    for bad_invoice in ("X500001", "50000", "5000012"):
        _raises(
            partial(retail.check_raw, _times(ok, 3, invoice=bad_invoice)),
            ValueError,
            f"w trzech wierszach numer faktury to {bad_invoice!r}",
            3,
        )
    for bad_code in ("85123a", " 85123A", "85123A "):
        _raises(
            partial(retail.check_raw, _times(ok, 3, stock_code=bad_code)),
            ValueError,
            f"w trzech wierszach kod towaru to {bad_code!r}",
            3,
        )
    _raises(
        lambda: retail.check_raw(_times(ok, 3, quantity=0)),
        ValueError,
        "w trzech wierszach ilość wynosi 0",
        3,
    )
    _raises(
        lambda: retail.check_raw(_times(ok, 3, quantity=-1)),
        ValueError,
        "w trzech wierszach ilość jest ujemna poza fakturą anulującą, przy cenie 2",
        3,
    )
    _raises(
        lambda: retail.check_raw(_times(ok, 3, price=-1.0)),
        ValueError,
        "w trzech wierszach cena jest ujemna poza fakturą korygującą (A)",
        3,
    )
    two_customers = _raw(
        {"invoice": "500011", "customer_id": 1},
        {"invoice": "500011", "customer_id": 2},
        {"invoice": "500012", "customer_id": 3},
        {"invoice": "500012", "customer_id": 4},
        {"invoice": "500013", "customer_id": 5},
        {"invoice": "500013", "customer_id": 6},
        {"invoice": "500014", "customer_id": 7},
    )
    _raises(
        lambda: retail.check_raw(two_customers),
        ValueError,
        "trzy faktury mają po dwóch klientów",
        3,
    )
    two_countries = _raw(
        {"invoice": "500011", "country": "France"},
        {"invoice": "500011", "country": "Spain"},
        {"invoice": "500012", "country": "France"},
        {"invoice": "500012", "country": "Spain"},
        {"invoice": "500013", "country": "France"},
        {"invoice": "500013", "country": "Spain"},
    )
    _raises(
        lambda: retail.check_raw(two_countries),
        ValueError,
        "trzy faktury mają po dwa kraje",
        3,
    )


@task("06.3", "add_flags: cztery flagi opisujące każdy wiersz, bez usuwania")
def check_flags(_target: object) -> None:
    from freshcast.warmup import lines

    frame = _raw(
        {"invoice": "500001", "stock_code": "85123A", "quantity": 6},
        {"invoice": "C500002", "stock_code": "85123A", "quantity": -2},
        {"invoice": "500003", "stock_code": "POST", "price": 18.0, "customer_id": None},
        {"invoice": "500004", "stock_code": "22139", "price": 0.0, "customer_id": None},
        {"invoice": "A500005", "stock_code": "B", "price": -100.0, "customer_id": None},
        {"invoice": "500006", "stock_code": "DCGS0058", "price": 0.83},
        {"invoice": "500007", "stock_code": "79323LP"},
        {"invoice": "500008", "stock_code": "85123ABC"},
        {"invoice": "500009", "stock_code": "8512"},
        {"invoice": "C500010", "stock_code": "M", "price": 373.57, "customer_id": None},
        {
            "invoice": "500011",
            "stock_code": "10002",
            "quantity": -5,
            "price": 0.0,
            "customer_id": None,
        },
    ).set_axis(range(10, 21))  # a non-default index the result must keep
    before = frame.copy()

    flagged = lines.add_flags(frame)
    expect(
        isinstance(flagged, pd.DataFrame)
        and list(flagged.columns) == [*RAW_COLUMNS, *FLAGS],
        f"add_flags ma zwrócić kolumny wejścia i za nimi flagi {FLAGS}, w tej "
        f"kolejności. Dostałem: {list(getattr(flagged, 'columns', flagged))}",
    )
    expect(
        flagged.index.equals(before.index),
        "add_flags ma zwrócić te same wiersze w tej samej kolejności, z tym samym "
        f"indeksem. Indeks wejścia: {list(before.index)[:3]}..., wyniku: "
        f"{list(flagged.index)[:3]}...",
    )
    expect(
        all(flagged[flag].dtype == bool for flag in FLAGS),
        f"Flagi mają być kolumnami typu bool. Dostałem: "
        f"{ {flag: str(flagged[flag].dtype) for flag in FLAGS} }",
    )
    wanted = {
        "is_cancellation": [0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0],
        "is_non_product": [0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0],
        "is_missing_customer": [0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1],
        "is_bad_price": [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1],
    }
    hints = {
        "is_cancellation": "numer faktury zaczyna się od C (wiersze 1 i 9)",
        "is_non_product": "kod towaru to nie pięć cyfr i najwyżej dwie litery "
        "(POST, B, DCGS0058, 85123ABC, 8512, M są nietowarami, 79323LP jest towarem)",
        "is_missing_customer": "brak numeru klienta",
        "is_bad_price": "cena wynosi 0 albo mniej",
    }
    for flag, expected in wanted.items():
        seen = [int(value) for value in flagged[flag]]
        expect(
            seen == expected,
            f"Flaga {flag} oznacza: {hints[flag]}. Dla tych 11 wierszy ma dać "
            f"{expected}, a daje {seen}.",
        )
    _unchanged(frame, before, "add_flags")

    counts = {
        flag: int(lines.add_flags(pd.read_parquet(SAMPLE))[flag].sum())
        for flag in FLAGS
    }
    expect(
        counts == SAMPLE_FLAGS,
        f"Na próbce {SAMPLE_ROWS} wierszy flagi mają dać {SAMPLE_FLAGS}, a dają "
        f"{counts}.",
    )


@task(
    "06.4",
    "drop_sheet_overlap, flag_repeat_lines: kopie arkuszy i powtórzone wiersze",
)
def check_duplicates(_target: object) -> None:
    from freshcast.warmup import lines

    a_rows = [
        _line("500001", "20001", 1, SHEET_A),
        _line("500001", "20001", 1, SHEET_A),
        _line("500001", "20002", 5, SHEET_A),
        _line("500002", "20003", 2, SHEET_A),
    ]
    b_rows = [
        _line("500001", "20001", 1, SHEET_B),
        _line("500001", "20001", 1, SHEET_B),
        _line("500001", "20002", 5, SHEET_B),
        _line("500003", "20004", 3, SHEET_B),
        _line("500004", "20005", 1, SHEET_B),
        _line("500004", "20005", 1, SHEET_B),
    ]
    frame = _raw(*a_rows, *b_rows)
    before = frame.copy()

    kept = lines.drop_sheet_overlap(frame)
    expect(
        isinstance(kept, pd.DataFrame) and list(kept.columns) == RAW_COLUMNS,
        "drop_sheet_overlap ma zwrócić tabelę o tych samych kolumnach co wejście.",
    )
    expected_invoices = ["500001"] * 3 + ["500002", "500003", "500004", "500004"]
    expected_sheets = [SHEET_A] * 4 + [SHEET_B] * 3
    expect(
        list(kept["invoice"]) == expected_invoices
        and list(kept["sheet"]) == expected_sheets,
        "Faktura 500001 jest w obu arkuszach (po 3 wiersze, w tym dwa razy ta sama "
        "linia). Z 10 wierszy zostaje 7: kopia z drugiego arkusza odpada, a "
        "powtórzone wiersze w obrębie jednego arkusza (500001 w pierwszym, 500004 "
        f"w drugim) zostają. Dostałem {len(kept)} wierszy, faktury "
        f"{list(kept['invoice'])}, arkusze {[s[-9:] for s in kept['sheet']]}.",
    )
    expect(
        kept.index.equals(pd.RangeIndex(len(kept))),
        f"Po usunięciu wierszy indeks ma biec od 0 do n-1. Jest: {list(kept.index)}",
    )
    _unchanged(frame, before, "drop_sheet_overlap")

    b_first = pd.concat([frame.iloc[4:], frame.iloc[:4]], ignore_index=True)
    kept_b_first = lines.drop_sheet_overlap(b_first)
    expect(
        len(kept_b_first) == 7
        and set(kept_b_first.loc[kept_b_first["invoice"] == "500001", "sheet"])
        == {SHEET_A},
        "Gdy wiersze drugiego arkusza stoją w tabeli przed wierszami pierwszego, "
        "z faktury 500001 nadal ma zostać kopia z pierwszego arkusza (według "
        f"nazwy). Dostałem arkusze: {set(kept_b_first['sheet'])} i "
        f"{len(kept_b_first)} wierszy.",
    )
    alone = _raw(*a_rows)
    expect(
        len(lines.drop_sheet_overlap(alone)) == len(a_rows),
        "Bez faktur występujących w dwóch arkuszach wszystkie wiersze zostają.",
    )

    changed = _raw(*a_rows, *b_rows[:2], _line("500001", "20002", 6, SHEET_B))
    _raises(
        lambda: lines.drop_sheet_overlap(changed),
        ValueError,
        "kopia faktury 500001 ma inną ilość w jednym wierszu",
        1,
    )
    _raises(
        lambda: lines.drop_sheet_overlap(frame.drop(index=6)),
        ValueError,
        "kopia faktury 500001 w drugim arkuszu ma 2 wiersze zamiast 3",
        1,
    )

    real = lines.drop_sheet_overlap(pd.read_parquet(SAMPLE))
    per_sheet = real["sheet"].value_counts().to_dict()
    expect(
        per_sheet == SAMPLE_ROWS_AFTER_OVERLAP,
        f"W próbce {SAMPLE_SHARED_INVOICES} faktur jest w obu arkuszach. Po "
        f"usunięciu kopii ma zostać {SAMPLE_ROWS_AFTER_OVERLAP} wierszy w "
        f"arkuszach, a zostało {per_sheet}.",
    )

    repeats = _raw(
        {"invoice": "500001", "stock_code": "20001"},
        {"invoice": "500001", "stock_code": "20001"},
        {"invoice": "500001", "stock_code": "20001"},
        {"invoice": "500001", "stock_code": "20001", "quantity": 2},
        {"invoice": "500002", "stock_code": "20001"},
        {
            "invoice": "500003",
            "stock_code": "20002",
            "customer_id": None,
            "description": None,
        },
        {
            "invoice": "500003",
            "stock_code": "20002",
            "customer_id": None,
            "description": None,
        },
        {"invoice": "500001", "stock_code": "20001", "sheet": SHEET_B},
    ).set_axis(range(10, 18))
    repeats_before = repeats.copy()
    flagged = lines.flag_repeat_lines(repeats)
    expect(
        isinstance(flagged, pd.DataFrame)
        and list(flagged.columns) == [*RAW_COLUMNS, "is_repeat_line"]
        and flagged.index.equals(repeats.index),
        "flag_repeat_lines ma zwrócić kolumny wejścia i za nimi is_repeat_line, "
        "te same wiersze w tej samej kolejności, z tym samym indeksem. "
        f"Dostałem: {list(getattr(flagged, 'columns', flagged))}",
    )
    seen = [int(value) for value in flagged["is_repeat_line"]]
    expect(
        flagged["is_repeat_line"].dtype == bool and seen == [0, 1, 1, 0, 0, 0, 1, 1],
        "is_repeat_line (bool) ma być True dla każdego wiersza równego "
        "wcześniejszemu we wszystkich ośmiu kolumnach linii, bez kolumny sheet: "
        "drugi i trzeci wiersz to powtórzenia pierwszego, wiersz z inną ilością "
        "albo z inną fakturą nie, dwa wiersze z brakującym klientem i opisem są "
        "sobie równe, ostatni wiersz powtarza pierwszy z drugiego arkusza. Ma "
        f"wyjść [0, 1, 1, 0, 0, 0, 1, 1], a wyszło {seen}.",
    )
    _unchanged(repeats, repeats_before, "flag_repeat_lines")

    marked = int(
        lines.flag_repeat_lines(pd.read_parquet(SAMPLE))["is_repeat_line"].sum()
    )
    expect(
        marked == SAMPLE_REPEATS,
        f"W próbce {SAMPLE_REPEATS} wierszy powtarza wcześniejszy wiersz (razem z "
        f"kopiami arkuszy). Flaga wskazuje {marked}.",
    )


@task("06.5", "product_lines: sprzedaż i zwroty towarów, bez nietowarów i cen 0")
def check_product_lines(_target: object) -> None:
    from freshcast.warmup import lines

    flagged = _flagged(
        {
            "invoice": "500001",
            "stock_code": "85123A",
            "quantity": 6,
            "price": 2.5,
            "invoice_date": "2010-01-04 10:30",
        },
        {
            "invoice": "C500002",
            "stock_code": "85123A",
            "quantity": -2,
            "price": 2.5,
            "invoice_date": "2010-01-05 17:45",
            "is_cancellation": True,
        },
        {
            "invoice": "500003",
            "stock_code": "POST",
            "price": 18.0,
            "is_non_product": True,
        },
        {
            "invoice": "C500004",
            "stock_code": "M",
            "quantity": -1,
            "price": 10.0,
            "is_cancellation": True,
            "is_non_product": True,
        },
        {
            "invoice": "500005",
            "stock_code": "22139",
            "quantity": 12,
            "price": 0.0,
            "customer_id": None,
            "is_missing_customer": True,
            "is_bad_price": True,
        },
        {
            "invoice": "500006",
            "stock_code": "10002",
            "quantity": -50,
            "price": 0.0,
            "customer_id": None,
            "is_missing_customer": True,
            "is_bad_price": True,
        },
        {
            "invoice": "500007",
            "stock_code": "22139",
            "quantity": 3,
            "price": 1.5,
            "invoice_date": "2010-01-06 08:05",
            "customer_id": None,
            "is_missing_customer": True,
        },
    ).set_axis(range(20, 27))
    before = flagged.copy()

    result = lines.product_lines(flagged)
    wanted = pd.DataFrame(
        {
            "stock_code": ["85123A", "85123A", "22139"],
            "date": pd.to_datetime(["2010-01-04", "2010-01-05", "2010-01-06"]),
            "units_sold": [6, 0, 3],
            "units_returned": [0, 2, 0],
            "revenue": [15.0, 0.0, 4.5],
        }
    )
    expect(
        isinstance(result, pd.DataFrame) and list(result.columns) == DAILY_COLUMNS,
        f"product_lines ma zwrócić kolumny {DAILY_COLUMNS} w tej kolejności. "
        f"Dostałem: {list(getattr(result, 'columns', result))}",
    )
    try:
        pd.testing.assert_frame_equal(result, wanted, check_dtype=False)
    except AssertionError as error:
        raise CheckFailed(
            "Z 7 wierszy zostają trzy: sprzedaż towaru, zwrot towaru i sprzedaż "
            "bez klienta. Odpadają: postage, anulowanie kodu M, wydanie towaru po "
            "cenie 0 i spisanie towaru (ilość ujemna, cena 0). Zwrot ma "
            "units_returned dodatnie i units_sold 0, sprzedaż ma units_returned "
            "0, date to północ dnia faktury, revenue to ilość razy cena. Wiersze "
            "zostają w pierwotnej kolejności, indeks biegnie od 0.\n"
            f"Oczekiwano:\n{wanted.to_string()}\nDostałem:\n{result.to_string()}\n"
            f"({str(error).splitlines()[0]})"
        ) from error
    expect(
        pd.api.types.is_integer_dtype(result["units_sold"])
        and pd.api.types.is_integer_dtype(result["units_returned"])
        and pd.api.types.is_float_dtype(result["revenue"])
        and pd.api.types.is_datetime64_any_dtype(result["date"]),
        "units_sold i units_returned mają być liczbami całkowitymi, revenue liczbą "
        f"zmiennoprzecinkową, date datą. Dostałem: {result.dtypes.to_dict()}",
    )
    _unchanged(flagged, before, "product_lines")

    _raises(
        lambda: lines.product_lines(_flagged({"invoice": "500008", "quantity": -1})),
        ValueError,
        "wiersz sprzedaży towaru ma ujemną ilość i cenę powyżej 0",
        1,
    )
    _raises(
        lambda: lines.product_lines(
            _flagged({"invoice": "C500009", "quantity": 1, "is_cancellation": True})
        ),
        ValueError,
        "anulowanie towaru ma dodatnią ilość",
        1,
    )
    only_manual = _flagged(
        {
            "invoice": "C500010",
            "stock_code": "M",
            "quantity": 1,
            "price": 373.57,
            "is_cancellation": True,
            "is_non_product": True,
        }
    )
    try:
        nothing = lines.product_lines(only_manual)
    except ValueError as error:
        raise CheckFailed(
            "product_lines zgłosiło błąd dla anulowania z dodatnią ilością na "
            "kodzie M (nietowar). Takie wiersze są w danych i mają po prostu "
            f"odpaść. Komunikat: {error}"
        ) from error
    expect(
        len(nothing) == 0 and list(nothing.columns) == DAILY_COLUMNS,
        "Gdy wszystkie wiersze odpadają, wynik ma mieć kolumny "
        f"{DAILY_COLUMNS} i zero wierszy. Dostałem {len(nothing)} wierszy.",
    )


@task(
    "06.6",
    "daily_totals, check_daily: jeden wiersz na towar i dzień, kontrakt tabeli",
)
def check_daily_table(_target: object) -> None:
    from freshcast.warmup import daily

    lines = pd.DataFrame(
        {
            "stock_code": pd.Series(
                ["20001", "10002", "10002", "10002", "10002", "10002"], dtype="str"
            ),
            "date": pd.to_datetime(
                [
                    "2010-01-05",
                    "2010-01-04",
                    "2010-01-04",
                    "2010-01-04",
                    "2010-01-05",
                    "2010-01-03",
                ]
            ),
            "units_sold": [1, 2, 3, 0, 0, 4],
            "units_returned": [0, 0, 0, 1, 2, 0],
            "revenue": [1.5, 4.0, 6.0, 0.0, 0.0, 8.0],
        }
    ).set_axis([50, 51, 52, 53, 54, 55])
    before = lines.copy()

    totals = daily.daily_totals(lines)
    good = _good_daily()
    expect(
        isinstance(totals, pd.DataFrame) and list(totals.columns) == DAILY_COLUMNS,
        f"daily_totals ma zwrócić kolumny {DAILY_COLUMNS} w tej kolejności. "
        f"Dostałem: {list(getattr(totals, 'columns', totals))}",
    )
    try:
        pd.testing.assert_frame_equal(totals, good, check_dtype=False)
    except AssertionError as error:
        raise CheckFailed(
            "Z 6 linii ma powstać 4 wiersze: po jednym na towar i dzień, "
            "posortowane po stock_code, potem po date, z sumami po każdej z trzech "
            "miar (dzień z samym zwrotem ma units_sold 0), indeks od 0.\n"
            f"Oczekiwano:\n{good.to_string()}\nDostałem:\n{totals.to_string()}\n"
            f"({str(error).splitlines()[0]})"
        ) from error
    expect(
        pd.api.types.is_integer_dtype(totals["units_sold"])
        and pd.api.types.is_integer_dtype(totals["units_returned"])
        and pd.api.types.is_float_dtype(totals["revenue"]),
        "Sumy jednostek mają zostać liczbami całkowitymi, a revenue liczbą "
        f"zmiennoprzecinkową. Dostałem: {totals.dtypes.to_dict()}",
    )
    _unchanged(lines, before, "daily_totals")

    keyless = lines.assign(stock_code=lines["stock_code"].mask(lines.index == 50))
    with_gap = daily.daily_totals(keyless)
    expect(
        len(with_gap) == 4 and int(with_gap["stock_code"].isna().sum()) == 1,
        "Linia z brakującym stock_code nie może zniknąć po cichu z sumowania: "
        "zostaje jako wiersz z brakującym kluczem, żeby check_daily mogło go "
        "odrzucić. Dla 6 linii, z których jedna ma brak klucza, ma wyjść 4 "
        f"wiersze z jednym brakiem stock_code. Wyszło {len(with_gap)} wierszy "
        f"i {int(with_gap['stock_code'].isna().sum())} braków.",
    )

    try:
        daily.check_daily(good)
    except ValueError as error:
        raise CheckFailed(
            f"check_daily odrzuciło tabelę zgodną z kontraktem. Komunikat: {error}"
        ) from error
    good_before = good.copy()

    def broken(**columns: Any) -> pd.DataFrame:
        """The valid table with some columns replaced."""
        return good.assign(**columns)

    _raises(
        lambda: daily.check_daily(good.drop(columns="revenue")),
        ValueError,
        "tabeli brakuje kolumny revenue",
    )
    _raises(
        lambda: daily.check_daily(good[list(reversed(DAILY_COLUMNS))]),
        ValueError,
        "kolumny są w odwrotnej kolejności",
    )
    _raises(
        lambda: daily.check_daily(broken(units_sold=good["units_sold"].astype(float))),
        ValueError,
        "units_sold jest typu float",
    )
    _raises(
        lambda: daily.check_daily(broken(revenue=good["revenue"].astype(int))),
        ValueError,
        "revenue jest typu int",
    )
    _raises(
        lambda: daily.check_daily(broken(date=good["date"].dt.strftime("%Y-%m-%d"))),
        ValueError,
        "date jest tekstem",
    )
    _raises(
        lambda: daily.check_daily(broken(revenue=[float("nan")] * 3 + [1.5])),
        ValueError,
        "w trzech wierszach brakuje revenue",
        3,
    )
    _raises(
        lambda: daily.check_daily(broken(units_returned=[-1, -1, -1, 0])),
        ValueError,
        "w trzech wierszach units_returned jest ujemne",
        3,
    )
    _raises(
        lambda: daily.check_daily(
            broken(date=good["date"] + pd.to_timedelta([3, 3, 3, 0], unit="h"))
        ),
        ValueError,
        "w trzech wierszach date ma godzinę",
        3,
    )
    _raises(
        lambda: daily.check_daily(pd.concat([good, good.iloc[:3]], ignore_index=True)),
        ValueError,
        "trzy pary (stock_code, date) się powtarzają",
        3,
    )
    _raises(
        lambda: daily.check_daily(good.iloc[[1, 0, 2, 3]]),
        ValueError,
        "dwa pierwsze wiersze mają zamienioną kolejność",
    )
    _raises(
        lambda: daily.check_daily(
            broken(units_sold=[0, 0, 0, 1], units_returned=[0, 0, 0, 0])
        ),
        ValueError,
        "w trzech wierszach nie ma ani sprzedaży, ani zwrotu",
        3,
    )
    _unchanged(good, good_before, "check_daily")


@task(
    "06.7",
    "build_daily, save_daily, load_daily: złożenie całości i zapis z kontraktem",
)
def check_build(_target: object) -> None:
    from freshcast.warmup import daily

    built = daily.build_daily(SAMPLE)
    expect(
        isinstance(built, pd.DataFrame) and list(built.columns) == DAILY_COLUMNS,
        f"build_daily ma zwrócić kolumny {DAILY_COLUMNS} w tej kolejności. "
        f"Dostałem: {list(getattr(built, 'columns', built))}",
    )
    seen = {
        "wiersze": len(built),
        "towary": int(built["stock_code"].nunique()),
        "dni": int(built["date"].nunique()),
        "sprzedane jednostki": int(built["units_sold"].sum()),
        "zwrócone jednostki": int(built["units_returned"].sum()),
        "wiersze tylko ze zwrotem": int(
            ((built["units_sold"] == 0) & (built["units_returned"] > 0)).sum()
        ),
    }
    wanted = {
        "wiersze": SAMPLE_DAILY_ROWS,
        "towary": SAMPLE_PRODUCTS,
        "dni": SAMPLE_DAYS,
        "sprzedane jednostki": SAMPLE_UNITS_SOLD,
        "zwrócone jednostki": SAMPLE_UNITS_RETURNED,
        "wiersze tylko ze zwrotem": SAMPLE_RETURN_ONLY_ROWS,
    }
    expect(
        seen == wanted,
        f"Na próbce ({SAMPLE_ROWS} wierszy surowych) tabela dzienna ma mieć "
        f"{wanted}. Dostałem {seen}.",
    )
    revenue = float(built["revenue"].sum())
    expect(
        abs(revenue - SAMPLE_REVENUE) < 0.01,
        f"Suma revenue na próbce ma wynosić {SAMPLE_REVENUE}, a wynosi {revenue:.2f}.",
    )
    expect(
        built["date"].min() == pd.Timestamp("2009-12-01")
        and built["date"].max() == pd.Timestamp("2011-12-09"),
        "Daty w próbce mają obejmować 2009-12-01 do 2011-12-09. Dostałem "
        f"{built['date'].min()} do {built['date'].max()}.",
    )
    expect(
        list(built["stock_code"]) == sorted(built["stock_code"]),
        "Wiersze mają być posortowane po stock_code, potem po date.",
    )

    with tempfile.TemporaryDirectory() as scratch:
        directory = Path(scratch)
        _raises(
            lambda: daily.build_daily(directory / "missing.parquet"),
            FileNotFoundError,
            "pliku cache jeszcze nie ma",
        )
        zero_quantity = pd.read_parquet(SAMPLE)
        zero_quantity.loc[0, "quantity"] = 0
        broken_cache = directory / "broken_cache.parquet"
        zero_quantity.to_parquet(broken_cache, index=False)
        _raises(
            lambda: daily.build_daily(broken_cache),
            ValueError,
            "w surowych danych jest wiersz z ilością 0",
        )

        path = directory / "processed" / "online_retail_daily.parquet"
        written = daily.save_daily(built, path)
        expect(
            written == path and path.is_file(),
            "save_daily ma utworzyć katalogi, zapisać plik i zwrócić jego "
            f"ścieżkę. Zwróciło {written!r}, plik "
            f"{'istnieje' if path.is_file() else 'nie istnieje'}.",
        )
        restored = daily.load_daily(path)
        try:
            pd.testing.assert_frame_equal(restored, built)
        except AssertionError as error:
            raise CheckFailed(
                "Tabela po zapisie i odczycie różni się od oryginału: "
                f"{str(error).splitlines()[0]}"
            ) from error

        _raises(
            lambda: daily.load_daily(directory / "nothing.parquet"),
            FileNotFoundError,
            "pliku z tabelą jeszcze nie ma",
        )
        refused = directory / "refused.parquet"
        _raises(
            lambda: daily.save_daily(built.drop(columns="revenue"), refused),
            ValueError,
            "tabeli brakuje kolumny z kontraktu",
        )
        _raises(
            lambda: daily.save_daily(
                pd.concat([built, built.iloc[:3]], ignore_index=True), refused
            ),
            ValueError,
            "trzy pary (stock_code, date) się powtarzają",
        )
        expect(
            not refused.exists(),
            "save_daily zapisało plik mimo tabeli, która łamie kontrakt.",
        )
        built.drop(columns="revenue").to_parquet(refused, index=False)
        _raises(
            lambda: daily.load_daily(refused),
            ValueError,
            "plik na dysku nie ma kolumny z kontraktu",
        )
        built.iloc[::-1].to_parquet(refused, index=False)
        _raises(
            lambda: daily.load_daily(refused),
            ValueError,
            "wiersze w pliku nie są posortowane",
        )
