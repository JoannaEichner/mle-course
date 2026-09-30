"""Car Parts demand series as objects: demand types and local forecasts."""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

MISSING = "?"
# Syntetos-Boylan cut-offs: above ADI_CUTOFF demand is intermittent, above
# CV2_CUTOFF the sizes of the orders vary a lot.
ADI_CUTOFF = 1.32
CV2_CUTOFF = 0.49


def read_tsf(path: str | Path) -> Iterator[tuple[str, str, list[float | None]]]:
    """Yield (name, start, values) for every series of a .tsf file.

    The same job as ``read_series`` from labs 01 and 02, kept short here.
    """
    in_data = False
    with Path(path).open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower() == "@data":
                in_data = True
            elif in_data:
                name, start, values = line.split(":", 2)
                parsed = [None if v == MISSING else float(v) for v in values.split(",")]
                yield name, start.split(" ")[0], parsed


@dataclass(frozen=True)
class DemandSeries:
    """One monthly demand series, oldest value first; None marks a missing month.

    03.1: fields name, start, values; from_record, known, is_complete, adi
    and cv2. The notebook describes each of them.
    """


# 03.2: DemandType and classify.


# 03.3: LocalForecaster and NaiveForecaster.


# 03.4: SeasonalNaiveForecaster and MovingAverageForecaster.


# 03.5: Forecaster, mae and evaluate.
