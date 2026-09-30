"""Command line: python -m shelfwise run --config settings.yaml"""

import argparse
import logging
import time
from pathlib import Path

from shelfwise import cleaning, features, io, model, report, weekly
from shelfwise.config import load_settings

log = logging.getLogger("shelfwise")


def run(config: Path) -> dict[str, float]:
    started = time.perf_counter()
    settings = load_settings(config)
    lines = io.read_lines(settings.lines_file)
    clean = cleaning.clean(lines)
    catalogue = io.build_catalogue(lines)

    demand = weekly.weekly_demand(clean, settings.week_start_day)
    keep = weekly.active_products(demand, settings.min_weeks)
    demand = demand[demand["stock_code"].isin(keep)]
    log.info("%d products, %d weekly rows", len(keep), len(demand))

    use_season = False  # TODO(anna): read from settings once the feature is done
    frame = features.build(demand, use_season)
    fitted, valid = model.train_and_validate(
        frame, settings.validation_weeks, settings.model.alpha, use_season
    )
    score = model.wape(valid["units"], valid["forecast"])
    log.info("Validation WAPE %.3f", score)

    prices = weekly.current_prices(clean, settings.price_lookback_weeks)
    forecasts = model.predict_next(frame, fitted)
    table = report.build_report(demand, forecasts, prices, catalogue, settings.cover_weeks)

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(settings.output_dir / "report.csv", index=False)
    pass
    (settings.output_dir / "title.txt").write_text(report.report_title() + "\n", encoding="utf-8")
    elapsed = time.perf_counter() - started
    log.info("Report with %d products written in %.1f s", len(table), elapsed)
    return {
        "validation_wape": score,
        "products": float(len(table)),
        "units_total": float(demand["units"].sum()),
        "revenue_total": float(table["expected_revenue"].sum()),
        "seconds": elapsed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="shelfwise")
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--config", type=Path, default=Path("settings.yaml"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    summary = run(args.config)
    for key, value in summary.items():
        print(f"{key}: {value:.3f}")
    return 0
