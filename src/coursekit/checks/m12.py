"""Checks for module 12: the stockout label, classification metrics, thresholds."""

from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

from coursekit.checking import CheckFailed, expect, task

NAN = float("nan")


def _raises(call: Callable[[], object], error: type[Exception], when: str) -> None:
    try:
        call()
    except error:
        return
    except NotImplementedError:
        raise
    except Exception as other:  # noqa: BLE001 - the wrong exception type is the finding
        raise CheckFailed(
            f"Gdy {when}, oczekiwano {error.__name__}, a poleciał "
            f"{type(other).__name__}: {other}"
        ) from other
    raise CheckFailed(f"Gdy {when}, kod powinien zgłosić {error.__name__}.")


def _floats(values: Any) -> np.ndarray:
    """Any column or array as floats, with missing values as NaN."""
    return pd.Series(values).to_numpy(dtype="float64", na_value=np.nan)


def _same(got: Any, wanted: list[float]) -> bool:
    numbers = _floats(got)
    return numbers.shape == (len(wanted),) and bool(
        np.allclose(numbers, wanted, equal_nan=True)
    )


def _shown(values: Any) -> list[float]:
    return [round(float(v), 4) for v in _floats(values)]


def _days(oos_by_store: dict[int, list[int]]) -> pd.DataFrame:
    """One product in several shops: one row per shop and day, sorted."""
    frames = [
        pd.DataFrame(
            {
                "store_id": store,
                "product_id": 7,
                "dt": pd.date_range("2024-04-01", periods=len(hours)),
                "oos_hours": hours,
            }
        )
        for store, hours in oos_by_store.items()
    ]
    return pd.concat(frames, ignore_index=True)


@task("12.1", "add_stockout_label, drop_unlabelled: etykieta na jutro w obrębie serii")
def check_label(_target: object) -> None:
    from freshcast.classify import stockout

    label = stockout.LABEL
    # Shop 2 starts with a full stockout, so a look-ahead that crosses from
    # shop 1 into shop 2 would read 16 after the last day of shop 1.
    panel = _days({1: [0, 16, 3, 16], 2: [16, 16, 15, 5]})
    before = panel.copy()

    tomorrow = stockout.next_day_value(panel, "oos_hours")
    expect(
        isinstance(tomorrow, pd.Series) and tomorrow.index.equals(panel.index),
        "next_day_value ma zwrócić Series z indeksem ramki wejściowej.",
    )
    expect(
        bool(pd.isna(tomorrow.iloc[3])) and bool(pd.isna(tomorrow.iloc[7])),
        "Ostatni dzień serii nie ma jutra, więc wartość ma być brakiem (NaN). "
        f"Ostatnie dni obu serii dostały {_floats(tomorrow)[[3, 7]].tolist()}. "
        "Sklep 2 zaczyna się od 16 godzin.",
    )
    expect(
        _same(tomorrow, [16, 3, 16, NAN, 16, 15, 5, NAN]),
        "Dla oos_hours [0, 16, 3, 16] i [16, 16, 15, 5] wartości z jutra to "
        f"[16, 3, 16, NaN] i [16, 15, 5, NaN]. Dostałem {_shown(tomorrow)}.",
    )

    labelled = stockout.add_stockout_label(panel)
    expect(
        isinstance(labelled, pd.DataFrame) and labelled.index.equals(panel.index),
        "add_stockout_label ma zwrócić ramkę z indeksem ramki wejściowej.",
    )
    expect(
        label in labelled.columns
        and list(labelled.columns) == [*before.columns, label],
        f"Wynik ma mieć kolumny wejściowe i jedną nową, {label}. "
        f"Ma kolumny {list(labelled.columns)}.",
    )
    last_days = _floats(labelled[label])[[3, 7]]
    expect(
        bool(np.isnan(last_days).all()),
        "Ostatni dzień każdej serii nie ma jutra, więc jego etykieta ma być "
        f"NaN, a nie 0. Etykiety ostatnich dni to {last_days.tolist()}.",
    )
    expect(
        _same(labelled[label], [1, 0, 1, NAN, 1, 0, 0, NAN]),
        "Etykieta to 1, gdy jutro oos_hours wynosi dokładnie 16. Dla serii "
        "[0, 16, 3, 16] to [1, 0, 1, NaN], dla [16, 16, 15, 5] to "
        f"[1, 0, 0, NaN]. Dostałem {_shown(labelled[label])}. "
        "15 godzin bez towaru to jeszcze nie cały dzień.",
    )
    expect(
        panel.equals(before) and list(panel.columns) == list(before.columns),
        "Funkcja zmieniła ramkę wejściową (add_stockout_label albo next_day_value).",
    )

    shifted = panel.set_axis(range(10, 18))
    expect(
        stockout.add_stockout_label(shifted)[label].index.equals(shifted.index),
        "Wynik ma zachować indeks ramki wejściowej także wtedy, gdy nie "
        "zaczyna się od 0.",
    )
    _raises(
        lambda: stockout.add_stockout_label(panel.iloc[[1, 0, 2, 3, 4, 5, 6, 7]]),
        ValueError,
        "wiersze nie są posortowane po serii i dacie",
    )
    _raises(
        lambda: stockout.add_stockout_label(panel.drop(index=5)),
        ValueError,
        "w serii brakuje jednego dnia",
    )
    _raises(
        lambda: stockout.add_stockout_label(panel.iloc[[0, 1, 1, 2, 3]]),
        ValueError,
        "dzień w serii się powtarza",
    )

    given = [1, 0, 1, NAN, 1, 0, 0, NAN]
    frame = panel.assign(**{label: given})
    kept = stockout.drop_unlabelled(frame)
    expect(
        kept.index.tolist() == [0, 1, 2, 4, 5, 6],
        "drop_unlabelled ma odrzucić wiersze bez etykiety (ostatni dzień "
        "każdej serii) i zachować indeks. Zostały wiersze o indeksach "
        f"{kept.index.tolist()}.",
    )
    expect(
        str(kept[label].dtype) == "int8" and kept[label].tolist() == [1, 0, 1, 1, 0, 0],
        "Etykieta po odrzuceniu ma być liczbą całkowitą int8: [1, 0, 1, 1, 0, 0]. "
        f"Jest {kept[label].dtype}, {kept[label].tolist()}.",
    )
    expect(
        frame[label].isna().sum() == 2 and str(frame[label].dtype) == "float64",
        "Funkcja drop_unlabelled zmieniła ramkę wejściową.",
    )
    _raises(
        lambda: stockout.drop_unlabelled(
            panel.assign(**{label: [1, NAN, 1, NAN, 1, 0, 0, NAN]})
        ),
        ValueError,
        "brak etykiety jest w środku serii, a nie na jej ostatnim dniu",
    )
    _raises(
        lambda: stockout.drop_unlabelled(
            panel.assign(**{label: [1, 0, 1, 0, 1, 0, 0, NAN]})
        ),
        ValueError,
        "ostatni dzień jednej serii ma etykietę 0 zamiast braku",
    )


def _long_panel() -> pd.DataFrame:
    """Two series of 30 days with hand-set patterns (see the constants below).

    Shop 1: a full stockout on days 0-9, none on days 10-27, 4 hours on day
    28, a full stockout on day 29. Shop 2: a full stockout every day. Sales
    are the day number in shop 1 and 100 plus the day number in shop 2.
    """
    days = 30
    frames = []
    for store, hours, sales, discount, last_discount, last_holiday in (
        (1, [16] * 10 + [0] * 18 + [4, 16], np.arange(days, dtype=float), 0.9, 0.7, 1),
        (2, [16] * days, 100.0 + np.arange(days), 0.8, 0.6, 0),
    ):
        frame = pd.DataFrame(
            {
                "store_id": store,
                "product_id": 7,
                "dt": pd.date_range("2024-04-01", periods=days),
                "sale_amount": sales,
                "discount": discount,
                "holiday_flag": 0,
                "oos_hours": hours,
                "oos_hours_total": 3,
                "sales_in_stock": 1.0,
                "sales_while_oos": 0.0,
                "activity_flag": 0,
                "avg_temperature": 20.0,
            }
        )
        frame.loc[days - 1, ["discount", "holiday_flag"]] = [
            last_discount,
            last_holiday,
        ]
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


@task("12.2", "cechy znane na koniec dnia t: okno kończące się dziś, jutrzejszy rabat")
def check_features(_target: object) -> None:
    from freshcast.classify import stockout

    small = _days({1: [0, 0, 0, 0], 2: [0, 0, 0, 0]}).assign(
        sale_amount=[1.0, 2.0, 3.0, 4.0, 10.0, 20.0, 30.0, 40.0]
    )
    mean = stockout.rolling_mean_through_today(small, "sale_amount", 2)
    expect(
        isinstance(mean, pd.Series) and mean.name == "sale_amount_mean_2",
        "rolling_mean_through_today(df, 'sale_amount', 2) ma zwrócić Series o "
        f"nazwie sale_amount_mean_2. Dostałem {getattr(mean, 'name', None)!r}.",
    )
    expect(
        _same(mean, [NAN, 1.5, 2.5, 3.5, NAN, 15.0, 25.0, 35.0]),
        "Okno 2 dni kończy się dziś i obejmuje dziś. Dla sprzedaży "
        "[1, 2, 3, 4] i [10, 20, 30, 40] średnie to [NaN, 1.5, 2.5, 3.5] i "
        f"[NaN, 15, 25, 35]. Dostałem {_shown(mean)}.",
    )
    _raises(
        lambda: stockout.rolling_mean_through_today(small, "sale_amount", 0),
        ValueError,
        "okno ma 0 dni",
    )
    _raises(
        lambda: stockout.rolling_mean_through_today(
            small.iloc[[1, 0, 2, 3, 4, 5, 6, 7]], "sale_amount", 2
        ),
        ValueError,
        "wiersze nie są posortowane po serii i dacie",
    )

    panel = _long_panel()
    before = panel.copy()
    out = stockout.add_stockout_features(panel)
    expect(
        panel.equals(before),
        "Funkcja add_stockout_features zmieniła ramkę wejściową.",
    )
    absent = sorted((set(stockout.FEATURES) | set(panel.columns)) - set(out.columns))
    expect(
        isinstance(out, pd.DataFrame) and out.index.equals(panel.index) and not absent,
        "Wynik ma mieć indeks ramki wejściowej, jej kolumny i wszystkie "
        f"kolumny z FEATURES. Brakuje kolumn: {absent}.",
    )
    expect(
        str(out["oos_full_today"].dtype) == "int8",
        f"oos_full_today ma być typu int8, jest {out['oos_full_today'].dtype}.",
    )

    # Hand-computed rows: (position, series, day) -> expected features.
    wanted: dict[int, dict[str, float]] = {
        29: {  # last day of shop 1
            "oos_hours": 16,
            "oos_full_today": 1,
            "oos_hours_lag_1": 4,
            "oos_hours_lag_7": 0,
            "oos_hours_mean_7": 20 / 7,
            "oos_full_share_7": 1 / 7,
            "oos_full_share_28": 9 / 28,
            "sale_amount": 29,
            "sale_amount_mean_7": 26.0,
            "discount_tomorrow": NAN,
            "tomorrow_is_day_off": NAN,
        },
        28: {  # the day before: tomorrow is the discounted holiday
            "oos_full_today": 0,
            "oos_hours_lag_1": 0,
            "oos_hours_mean_7": 4 / 7,
            "oos_full_share_7": 0.0,
            "oos_full_share_28": 9 / 28,
            "sale_amount_mean_7": 25.0,
            "discount_tomorrow": 0.7,
            "tomorrow_is_day_off": 1.0,
        },
        27: {"oos_full_share_28": 10 / 28, "discount_tomorrow": 0.9},
        7: {
            "oos_hours_lag_1": 16,
            "oos_hours_lag_7": 16,
            "oos_hours_mean_7": 16.0,
            "oos_full_share_7": 1.0,
            "oos_full_share_28": NAN,
        },
        5: {"oos_hours_lag_7": NAN, "oos_hours_mean_7": NAN},
        59: {  # last day of shop 2
            "oos_hours_lag_1": 16,
            "oos_hours_lag_7": 16,
            "oos_hours_mean_7": 16.0,
            "oos_full_share_7": 1.0,
            "oos_full_share_28": 1.0,
            "sale_amount_mean_7": 126.0,
            "discount_tomorrow": NAN,
        },
        58: {"discount_tomorrow": 0.6, "tomorrow_is_day_off": 0.0},
    }
    for position, columns in wanted.items():
        row = out.iloc[position]
        for column, value in columns.items():
            got = float(row[column])
            expect(
                bool(np.isclose(got, value, equal_nan=True)),
                f"Wiersz {position} (sklep {int(row['store_id'])}, dzień "
                f"{row['dt'].date()}): kolumna {column} powinna mieć wartość "
                f"{value:.4f}, a ma {got:.4f}.",
            )

    gaps = {
        "oos_hours_lag_1": 2,
        "oos_hours_lag_7": 14,
        "oos_hours_mean_7": 12,
        "oos_full_share_7": 12,
        "oos_full_share_28": 54,
        "sale_amount_mean_7": 12,
        "discount_tomorrow": 2,
        "tomorrow_is_day_off": 2,
    }
    for column, count in gaps.items():
        got_count = int(out[column].isna().sum())
        expect(
            got_count == count,
            f"{column} ma mieć {count} braków (początek serii albo jej ostatni "
            f"dzień, w obu seriach), a ma {got_count}. Dwie serie mają łącznie "
            "60 wierszy, a okno nie może sięgać do poprzedniej serii.",
        )

    # The leak test. Everything from day d on is replaced by junk outcomes.
    # Rows before day d know nothing of it, unless they read "tomorrow": the
    # row of day d - 1 has the junk day as its tomorrow. Only the calendar and
    # the discount may be read from there, and they are left alone.
    outcomes = [
        "sale_amount",
        "oos_hours",
        "oos_hours_total",
        "sales_in_stock",
        "sales_while_oos",
        "avg_temperature",
        "activity_flag",
    ]
    junk = [9999.0, 7, 24, 9999.0, 9999.0, -5.0, 1]
    first_day = panel["dt"].min()
    for day in (5, 12, 20, 29):
        start = first_day + pd.Timedelta(days=day)
        corrupted = panel.copy()
        corrupted.loc[corrupted["dt"] >= start, outcomes] = junk
        again = stockout.add_stockout_features(corrupted)
        earlier = (panel["dt"] < start).to_numpy()
        moved = [
            column
            for column in stockout.FEATURES
            if not np.allclose(
                _floats(out[column])[earlier],
                _floats(again[column])[earlier],
                equal_nan=True,
            )
        ]
        expect(
            not moved,
            f"Cechy wierszy sprzed dnia {start.date()} zmieniły się po zmianie "
            "sprzedaży, godzin bez towaru, pogody i flagi akcji od tego dnia. "
            "Cecha wiersza t nie może zależeć od wyniku dnia t + 1: z jutra "
            f"wolno brać tylko kalendarz i planowany rabat. Zmieniły się: {moved}.",
        )
    _raises(
        lambda: stockout.add_stockout_features(panel.iloc[::-1]),
        ValueError,
        "wiersze są w odwrotnej kolejności",
    )


@task("12.3", "confusion_counts, precision, recall, f1 w NumPy")
def check_metrics(_target: object) -> None:
    from freshcast.classify import metrics

    truth = [1, 1, 1, 1, 0, 0, 0, 0]
    pred = [1, 1, 1, 0, 1, 1, 0, 0]
    counts = metrics.confusion_counts(truth, pred)
    got = (counts.tp, counts.fp, counts.fn, counts.tn)
    expect(
        got == (3, 2, 1, 2),
        "Dla y_true [1, 1, 1, 1, 0, 0, 0, 0] i y_pred [1, 1, 1, 0, 1, 1, 0, 0] "
        "trafne alarmy (tp) to 3, fałszywe alarmy (fp) 2, przegapione zdarzenia "
        f"(fn) 1 i trafne braki alarmu (tn) 2. Dostałem tp, fp, fn, tn = {got}.",
    )
    same = metrics.confusion_counts(np.array(truth, dtype=bool), np.array(pred))
    expect(
        (same.tp, same.fp, same.fn, same.tn) == (3, 2, 1, 2),
        "Etykiety typu bool dają te same liczby co 0 i 1.",
    )

    p = metrics.precision(truth, pred)
    r = metrics.recall(truth, pred)
    f = metrics.f1(truth, pred)
    expect(
        bool(np.isclose(p, 0.6)) and bool(np.isclose(r, 0.75)),
        "Dla tych danych z 5 alarmów 3 były trafne (precision 0.6), a z 4 "
        f"zdarzeń wychwycono 3 (recall 0.75). Dostałem {p:.4f} i {r:.4f}.",
    )
    expect(
        bool(np.isclose(f, 2 / 3)),
        f"F1 dla precision 0.6 i recall 0.75 to 0.6667. Dostałem {f:.4f}.",
    )
    half = metrics.f1([1, 1, 0], [1, 0, 0])
    expect(
        bool(np.isclose(half, 2 / 3)),
        "Dla precision 1.0 i recall 0.5 F1 to średnia harmoniczna, 0.6667, a "
        f"nie arytmetyczna 0.75. Dostałem {half:.4f}.",
    )

    rare = [1] + [0] * 9
    silent = [0] * 10
    zeros = (
        metrics.precision(rare, silent),
        metrics.recall(rare, silent),
        metrics.f1(rare, silent),
    )
    expect(
        zeros == (0.0, 0.0, 0.0),
        "Model, który nigdy nie alarmuje, przy jednym zdarzeniu na 10 dni: "
        "precision to 0 / 0, czyli 0.0 z definicji, recall 0 z 1, czyli 0.0, "
        f"f1 0.0. Dostałem {zeros}.",
    )
    quiet = (
        metrics.precision(silent, [1, 1] + [0] * 8),
        metrics.recall(silent, [1, 1] + [0] * 8),
        metrics.f1(silent, silent),
    )
    expect(
        quiet == (0.0, 0.0, 0.0),
        "Gdy zdarzeń nie było, recall to 0 / 0, czyli 0.0. Gdy nie było "
        "zdarzeń ani alarmów, f1 też wynosi 0.0. Precision przy 2 fałszywych "
        f"alarmach to 0.0. Dostałem {quiet}.",
    )

    _raises(
        lambda: metrics.confusion_counts([1, NAN, 0], [1, 0, 0]),
        ValueError,
        "w y_true jest NaN",
    )
    _raises(
        lambda: metrics.precision([1, 0, 2], [1, 0, 1]),
        ValueError,
        "w y_true jest wartość 2",
    )
    _raises(
        lambda: metrics.recall([1, 0, 1], [1, 0]),
        ValueError,
        "y_true i y_pred mają różne długości",
    )
    kept = np.array(truth)
    metrics.f1(kept, pred)
    expect(kept.tolist() == truth, "Metryka zmieniła tablicę wejściową.")


@task("12.4", "counts_by_threshold, precision_recall_curve, average_precision")
def check_curve(_target: object) -> None:
    from freshcast.classify import metrics

    # Two rows share the score 0.9: one positive, one negative. No threshold
    # can separate them, so they enter together. Input is not sorted.
    truth = [1, 1, 0, 0]
    scores = [0.5, 0.9, 0.1, 0.9]
    thresholds, tp, fp = metrics.counts_by_threshold(truth, scores)
    expect(
        len(thresholds) == 3,
        "Progi to różne wartości wyniku: 0.9, 0.5 i 0.1, od najwyższego. "
        f"Dostałem wpisów: {len(thresholds)}, progi {_shown(thresholds)}. "
        "Wiersze o równym wyniku wchodzą razem.",
    )
    expect(
        _same(thresholds, [0.9, 0.5, 0.1])
        and [int(v) for v in tp] == [1, 2, 2]
        and [int(v) for v in fp] == [1, 1, 2],
        "Dla y [1, 1, 0, 0] i wyników [0.5, 0.9, 0.1, 0.9] progi to "
        "[0.9, 0.5, 0.1], trafne alarmy [1, 2, 2], fałszywe [1, 1, 2]. "
        f"Dostałem {_shown(thresholds)}, {tp.tolist()}, {fp.tolist()}.",
    )

    precisions, recalls, curve_thresholds = metrics.precision_recall_curve(
        truth, scores
    )
    expect(
        _same(precisions, [0.5, 2 / 3, 0.5]) and _same(recalls, [0.5, 1.0, 1.0]),
        "Dla tych danych precision na progach 0.9, 0.5, 0.1 to [0.5, 0.6667, "
        "0.5], a recall [0.5, 1, 1]. Dostałem "
        f"{_shown(precisions)} i {_shown(recalls)}.",
    )
    expect(
        _same(curve_thresholds, [0.9, 0.5, 0.1]),
        "precision_recall_curve zwraca progi od najwyższego: [0.9, 0.5, 0.1]. "
        f"Dostałem {_shown(curve_thresholds)}.",
    )

    average = metrics.average_precision(truth, scores)
    expect(
        isinstance(average, float) and bool(np.isclose(average, 7 / 12)),
        "Average precision to suma (przyrost recall) * precision po progach: "
        f"0.5 * 0.5 + 0.5 * 0.6667 + 0 * 0.5 = 0.5833. Dostałem {average!r}.",
    )
    perfect = metrics.average_precision([1, 1, 0, 0], [0.9, 0.8, 0.2, 0.1])
    worst = metrics.average_precision([0, 0, 1, 1], [0.9, 0.8, 0.2, 0.1])
    expect(
        bool(np.isclose(perfect, 1.0)) and bool(np.isclose(worst, 5 / 12)),
        "Idealny ranking ma AP 1.0. Ranking odwrócony (zdarzenia na końcu) ma "
        f"AP 5/12 = 0.4167. Dostałem {perfect:.4f} i {worst:.4f}.",
    )
    flat = metrics.average_precision([1, 0, 0, 0], [0.3, 0.3, 0.3, 0.3])
    expect(
        bool(np.isclose(flat, 0.25)),
        "Gdy wszystkie wyniki są równe, jest jeden próg, na którym precision to "
        f"udział zdarzeń (0.25), a recall 1. AP wynosi 0.25. Dostałem {flat:.4f}.",
    )
    binary = metrics.average_precision([1, 1, 0, 0, 1, 0], [1, 0, 1, 0, 1, 0])
    expect(
        bool(np.isclose(binary, 11 / 18)),
        "Wyniki 0 i 1 (prognoza 'jak dziś') dają dwa progi. AP to "
        f"2/3 * 2/3 + 1/3 * 1/2 = 0.6111. Dostałem {binary:.4f}.",
    )

    _raises(
        lambda: metrics.average_precision([0, 0, 0], [0.1, 0.2, 0.3]),
        ValueError,
        "w y_true nie ma żadnego zdarzenia",
    )
    _raises(
        lambda: metrics.counts_by_threshold([1, 0, 1], [0.1, NAN, 0.3]),
        ValueError,
        "w wynikach jest NaN",
    )
    _raises(
        lambda: metrics.counts_by_threshold([1, 0, 1], [0.1, 0.2]),
        ValueError,
        "y_true i wyniki mają różne długości",
    )
    _raises(
        lambda: metrics.counts_by_threshold([1, NAN], [0.1, 0.2]),
        ValueError,
        "w y_true jest NaN",
    )
    _raises(
        lambda: metrics.counts_by_threshold([], []),
        ValueError,
        "nie ma żadnych wierszy",
    )
    kept = np.array(scores)
    metrics.average_precision(truth, kept)
    expect(kept.tolist() == scores, "Funkcja zmieniła tablicę wyników.")


@task("12.5", "best_threshold: próg o najniższym koszcie")
def check_threshold(_target: object) -> None:
    from freshcast.classify import metrics

    truth = [1, 0, 1, 0, 0, 1, 0, 0]
    scores = [0.9, 0.8, 0.7, 0.6, 0.4, 0.3, 0.2, 0.1]
    choice = metrics.best_threshold(truth, scores, 1.0, 5.0)
    expect(
        bool(np.isclose(choice.threshold, 0.3)) and bool(np.isclose(choice.cost, 3.0)),
        "Przy koszcie fałszywego alarmu 1 i przegapionego zdarzenia 5 koszty "
        "na kolejnych progach 0.9, 0.8, 0.7, 0.6, 0.4, 0.3, 0.2, 0.1 to "
        "10, 11, 6, 7, 8, 3, 4, 5, a brak alarmów kosztuje 15. Najlepszy jest "
        f"próg 0.3 z kosztem 3. Dostałem {choice.threshold} i {choice.cost}.",
    )
    choice = metrics.best_threshold(truth, scores, 5.0, 1.0)
    expect(
        bool(np.isclose(choice.threshold, 0.9)) and bool(np.isclose(choice.cost, 2.0)),
        "Gdy fałszywy alarm kosztuje 5, a przegapione zdarzenie 1, najlepszy "
        f"jest próg 0.9 z kosztem 2. Dostałem {choice.threshold} i {choice.cost}.",
    )

    choice = metrics.best_threshold([0, 1, 0, 0], [0.9, 0.8, 0.7, 0.6], 3.0, 2.0)
    expect(
        choice.threshold == float("inf") and bool(np.isclose(choice.cost, 2.0)),
        "Gdy żaden próg nie jest tańszy niż brak alarmów (koszt 2 za jedno "
        "przegapione zdarzenie), wynikiem jest próg inf z kosztem 2. "
        f"Dostałem {choice.threshold} i {choice.cost}.",
    )
    choice = metrics.best_threshold([1, 0, 1], [0.9, 0.5, 0.2], 1.0, 1.0)
    expect(
        bool(np.isclose(choice.threshold, 0.9)) and bool(np.isclose(choice.cost, 1.0)),
        "Progi 0.9 i 0.2 kosztują tyle samo (1). Przy remisie wygrywa wyższy "
        f"próg, czyli mniej alarmów. Dostałem {choice.threshold}.",
    )
    choice = metrics.best_threshold([0, 1], [0.9, 0.1], 1.0, 1.0)
    expect(
        choice.threshold == float("inf") and bool(np.isclose(choice.cost, 1.0)),
        "Brak alarmów i próg 0.1 kosztują tyle samo (1). Przy remisie wygrywa "
        f"brak alarmów. Dostałem {choice.threshold}.",
    )
    choice = metrics.best_threshold([1, 0, 1, 0], [0.8, 0.8, 0.3, 0.3], 1.0, 3.0)
    expect(
        bool(np.isclose(choice.threshold, 0.3)) and bool(np.isclose(choice.cost, 2.0)),
        "Wiersze o równym wyniku wchodzą razem. Dla y [1, 0, 1, 0] i wyników "
        "[0.8, 0.8, 0.3, 0.3] próg 0.8 kosztuje 1 + 3 = 4, a próg 0.3 kosztuje "
        f"2. Dostałem {choice.threshold} i {choice.cost}.",
    )

    _raises(
        lambda: metrics.best_threshold(truth, scores, -1.0, 5.0),
        ValueError,
        "koszt fałszywego alarmu jest ujemny",
    )
    _raises(
        lambda: metrics.best_threshold(truth, scores, 1.0, -5.0),
        ValueError,
        "koszt przegapionego zdarzenia jest ujemny",
    )
    _raises(
        lambda: metrics.best_threshold([1, NAN], [0.1, 0.2], 1.0, 1.0),
        ValueError,
        "w y_true jest NaN",
    )


@task(
    "12.6", "calibration_table: przewidywane prawdopodobieństwo a obserwowana częstość"
)
def check_calibration(_target: object) -> None:
    from freshcast.classify import metrics

    columns = ["bin_low", "bin_high", "rows", "mean_predicted", "observed_rate"]
    truth = [0, 0, 1, 0, 1, 1]
    probabilities = [0.1, 0.2, 0.4, 0.5, 0.9, 1.0]
    table = metrics.calibration_table(truth, probabilities, bins=2)
    expect(
        isinstance(table, pd.DataFrame) and list(table.columns) == columns,
        f"calibration_table ma zwrócić ramkę z kolumnami {columns}.",
    )
    expect(
        table["rows"].tolist() == [3, 3],
        "Dla bins=2 przedziały to [0, 0.5) i [0.5, 1]. Prawdopodobieństwa 0.1, "
        "0.2, 0.4 trafiają do pierwszego, a 0.5, 0.9 i 1.0 do drugiego "
        f"(0.5 leży na dolnej krawędzi, 1.0 w ostatnim przedziale). Liczby "
        f"wierszy: {table['rows'].tolist()}.",
    )
    expect(
        _same(table["mean_predicted"], [0.7 / 3, 0.8])
        and _same(table["observed_rate"], [1 / 3, 2 / 3]),
        "Średnie przewidywane prawdopodobieństwo w przedziałach to 0.2333 i 0.8, "
        f"a obserwowane częstości to 0.3333 i 0.6667. Dostałem "
        f"{_shown(table['mean_predicted'])} i {_shown(table['observed_rate'])}.",
    )
    expect(
        _same(table["bin_low"], [0.0, 0.5]) and _same(table["bin_high"], [0.5, 1.0]),
        "bin_low i bin_high to krawędzie przedziałów: [0, 0.5] i [0.5, 1]. "
        f"Dostałem {_shown(table['bin_low'])} i {_shown(table['bin_high'])}.",
    )

    sparse = metrics.calibration_table([0, 1, 1], [0.05, 0.1, 0.9], bins=4)
    expect(
        _same(sparse["bin_low"], [0.0, 0.75])
        and sparse["rows"].tolist() == [2, 1]
        and _same(sparse["observed_rate"], [0.5, 1.0]),
        "Przy bins=4 prawdopodobieństwa 0.05 i 0.1 wpadają do przedziału "
        "[0, 0.25), a 0.9 do [0.75, 1]. Przedziały bez wierszy nie mają wpisu, "
        f"więc wynik ma 2 wiersze. Dostałem bin_low {_shown(sparse['bin_low'])}, "
        f"rows {sparse['rows'].tolist()}.",
    )
    edge = metrics.calibration_table([1, 0], [0.0, 1.0], bins=10)
    expect(
        edge["rows"].tolist() == [1, 1] and _same(edge["bin_low"], [0.0, 0.9]),
        "Prawdopodobieństwo 0.0 należy do pierwszego przedziału, a 1.0 do "
        f"ostatniego (bin_low 0.9). Dostałem bin_low {_shown(edge['bin_low'])}, "
        f"rows {edge['rows'].tolist()}.",
    )

    _raises(
        lambda: metrics.calibration_table(truth, probabilities, bins=0),
        ValueError,
        "bins wynosi 0",
    )
    _raises(
        lambda: metrics.calibration_table([0, 1], [0.2, 1.2]),
        ValueError,
        "prawdopodobieństwo wynosi 1.2",
    )
    _raises(
        lambda: metrics.calibration_table([0, 1], [-0.1, 0.5]),
        ValueError,
        "prawdopodobieństwo jest ujemne",
    )
    _raises(
        lambda: metrics.calibration_table([0, 1], [NAN, 0.5]),
        ValueError,
        "w prawdopodobieństwach jest NaN",
    )
    _raises(
        lambda: metrics.calibration_table([0, NAN], [0.2, 0.5]),
        ValueError,
        "w y_true jest NaN",
    )
    _raises(
        lambda: metrics.calibration_table([0, 1, 1], [0.2, 0.5]),
        ValueError,
        "y_true i prawdopodobieństwa mają różne długości",
    )


def _signal(rows: int = 1500, seed: int = 12) -> tuple[pd.DataFrame, pd.Series]:
    """About 15% positives; ``a`` drives them, ``b`` is noise."""
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame({"a": rng.normal(size=rows), "b": rng.normal(size=rows)})
    chance = 1 / (1 + np.exp(-(3.0 * frame["a"] - 3.5)))
    return frame, pd.Series((rng.random(rows) < chance).astype("int8"))


def _xor(rows: int = 1500, seed: int = 5) -> tuple[pd.DataFrame, pd.Series]:
    """A label no linear model can learn: positive when a and b differ in sign."""
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame({"a": rng.normal(size=rows), "b": rng.normal(size=rows)})
    return frame, pd.Series(((frame["a"] > 0) != (frame["b"] > 0)).astype("int8"))


def _gap(probabilities: np.ndarray, truth: pd.Series) -> float:
    """Mean probability on positives minus mean probability on negatives."""
    positive = truth.to_numpy() == 1
    return float(probabilities[positive].mean() - probabilities[~positive].mean())


@task("12.7", "StockoutClassifier: regresja logistyczna albo LightGBM, jeden interfejs")
def check_classifier(_target: object) -> None:
    from freshcast.classify import models

    frame, truth = _signal()
    snapshot, truth_snapshot = frame.copy(), truth.copy()
    features = ["a", "b"]
    for kind in ("logistic", "lightgbm"):
        model = models.StockoutClassifier(features, kind)
        _raises(
            lambda model=model: model.predict_proba(frame),  # type: ignore[misc]
            RuntimeError,
            f"predict_proba jest wołany przed fit ({kind})",
        )
        expect(model.fit(frame, truth) is model, f"fit ma zwracać self ({kind}).")
        proba = model.predict_proba(frame)
        expect(
            isinstance(proba, np.ndarray)
            and proba.shape == (len(frame),)
            and bool(((proba >= 0) & (proba <= 1)).all()),
            f"predict_proba ({kind}) ma zwrócić jednowymiarową tablicę "
            f"prawdopodobieństw z przedziału [0, 1], po jednym na wiersz. "
            f"Dostałem kształt {getattr(proba, 'shape', None)}.",
        )
        gap = _gap(proba, truth)
        expect(
            gap > 0.3,
            f"Model {kind} na danych, w których cecha a wyznacza zdarzenia, "
            "powinien dawać zdarzeniom wyraźnie wyższe prawdopodobieństwo niż "
            f"reszcie. Różnica średnich to {gap:.3f}, oczekiwano ponad 0.3.",
        )

    unweighted = models.StockoutClassifier(features, "logistic").fit(frame, truth)
    mean_p = float(unweighted.predict_proba(frame).mean())
    rate = float(truth.mean())
    expect(
        abs(mean_p - rate) < 0.01,
        "Regresja logistyczna bez wag klas ma średnie prawdopodobieństwo równe "
        f"udziałowi zdarzeń w danych treningowych ({rate:.3f}). Dostałem {mean_p:.3f}.",
    )
    for kind in ("logistic", "lightgbm"):
        plain = models.StockoutClassifier(features, kind).fit(frame, truth)
        weighted = models.StockoutClassifier(features, kind, class_weight="balanced")
        raised = float(weighted.fit(frame, truth).predict_proba(frame).mean())
        unraised = float(plain.predict_proba(frame).mean())
        expect(
            raised > 1.3 * unraised,
            "Z class_weight='balanced' zdarzenia rzadkiej klasy ważą w sumie "
            "tyle, co cała reszta, więc średnie prawdopodobieństwo rośnie "
            f"ponad udział zdarzeń. Model {kind} bez wag: {unraised:.3f}, z "
            f"wagami: {raised:.3f}, oczekiwano co najmniej {1.3 * unraised:.3f}.",
        )

    xor_frame, xor_truth = _xor()
    trees = models.StockoutClassifier(features, "lightgbm").fit(xor_frame, xor_truth)
    linear = models.StockoutClassifier(features, "logistic").fit(xor_frame, xor_truth)
    tree_gap = _gap(trees.predict_proba(xor_frame), xor_truth)
    linear_gap = _gap(linear.predict_proba(xor_frame), xor_truth)
    expect(
        tree_gap > 0.6 and linear_gap < 0.15,
        "Zdarzenie zależy od tego, czy znaki a i b są różne. Modelu "
        "liniowego nie da się tego nauczyć (różnica średnich prawdopodobieństw "
        "poniżej 0.15), a drzewa tak (powyżej 0.6). Dostałem "
        f"logistic {linear_gap:.3f}, lightgbm {tree_gap:.3f}.",
    )

    gappy = frame.assign(a=frame["a"].mask(np.arange(len(frame)) % 10 == 0))
    for kind in ("logistic", "lightgbm"):
        model = models.StockoutClassifier(features, kind).fit(gappy, truth)
        proba = model.predict_proba(gappy)
        expect(
            not bool(np.isnan(proba).any()),
            f"Model {kind} ma przyjąć brakujące wartości cech (NaN) i zwrócić "
            f"liczbę dla każdego wiersza. NaN w wyniku: {int(np.isnan(proba).sum())}.",
        )
        lone = pd.DataFrame({"a": [NAN], "b": [0.0]})
        crowd = pd.DataFrame({"a": [NAN, 50.0, 60.0, 70.0], "b": [0.0, 1.0, 1.0, 1.0]})
        alone = float(model.predict_proba(lone)[0])
        together = float(model.predict_proba(crowd)[0])
        expect(
            bool(np.isclose(alone, together)),
            f"Ten sam wiersz ({kind}) dostał prawdopodobieństwo {alone:.4f} "
            f"osobno i {together:.4f} razem z innymi wierszami. To, czego model "
            "nauczył się w fit, nie może zależeć od wierszy podanych do predict.",
        )

    clean = models.StockoutClassifier(features, "logistic").fit(frame, truth)
    median = float(frame["a"].median())
    row_nan = pd.DataFrame({"a": [NAN], "b": [0.3]})
    row_median = pd.DataFrame({"a": [median], "b": [0.3]})
    expect(
        bool(
            np.isclose(
                clean.predict_proba(row_nan)[0], clean.predict_proba(row_median)[0]
            )
        ),
        "W modelu logistycznym brak w cesze zastępuje mediana z wierszy "
        "treningowych. Jeśli trening nie miał braków, wiersz z NaN w cesze a "
        f"ma dostać to samo prawdopodobieństwo co wiersz z a = {median:.3f}.",
    )

    extra = frame.assign(unrelated="text")
    extra_before = extra.copy()
    model = models.StockoutClassifier(features, "lightgbm").fit(extra, truth)
    model.predict_proba(extra)
    expect(
        extra.equals(extra_before)
        and frame.equals(snapshot)
        and truth.equals(truth_snapshot),
        "Metoda fit albo predict_proba zmieniła ramkę X albo etykiety y.",
    )
    expect(
        model.predict_proba(frame).shape == (len(frame),),
        "Model ma używać tylko kolumn z features: predict_proba na ramce bez "
        "kolumny spoza features ma działać.",
    )

    _raises(
        lambda: models.StockoutClassifier(features).fit(frame[["a"]], truth),
        ValueError,
        "w X brakuje kolumny b z features",
    )
    _raises(
        lambda: model.predict_proba(frame[["a"]]),
        ValueError,
        "predict_proba dostaje ramkę bez kolumny b",
    )
    _raises(
        lambda: models.StockoutClassifier(features).fit(
            frame, truth.astype("float64").mask(truth.index == 3)
        ),
        ValueError,
        "w y jest NaN",
    )
    _raises(
        lambda: models.StockoutClassifier(features).fit(frame, truth + 1),
        ValueError,
        "y zawiera wartość 2",
    )
    _raises(
        lambda: models.StockoutClassifier(features).fit(frame, truth * 0),
        ValueError,
        "y zawiera tylko jedną klasę",
    )
    _raises(
        lambda: models.StockoutClassifier(features).fit(frame, truth.iloc[:-1]),
        ValueError,
        "X i y mają różne długości",
    )
