"""One matplotlib style for every chart in the labs."""

import matplotlib.pyplot as plt
from cycler import cycler

# Categorical colours in a fixed order chosen to stay distinguishable for
# colour-blind readers. Use them in this order; do not pick by taste.
SERIES_COLORS = [
    "#2a78d6",
    "#eb6834",
    "#1baf7a",
    "#eda100",
    "#e87ba4",
    "#008300",
    "#4a3aa7",
    "#e34948",
]
_SURFACE = "#fcfcfb"
_INK = "#0b0b0b"
_INK_SECONDARY = "#52514e"
_MUTED = "#898781"
_GRID = "#e1e0d9"
_AXIS = "#c3c2b7"


def use_course_style() -> None:
    """Apply the course chart style to all figures created afterwards."""
    plt.rcParams.update(
        {
            "figure.figsize": (8, 3.6),
            "figure.dpi": 110,
            "figure.facecolor": _SURFACE,
            "axes.facecolor": _SURFACE,
            "axes.edgecolor": _AXIS,
            "axes.labelcolor": _INK_SECONDARY,
            "axes.titlecolor": _INK,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "axes.axisbelow": True,
            "axes.prop_cycle": cycler(color=SERIES_COLORS),
            "grid.color": _GRID,
            "grid.linewidth": 1.0,
            "lines.linewidth": 2.0,
            "lines.solid_capstyle": "round",
            "xtick.color": _MUTED,
            "ytick.color": _MUTED,
            "xtick.labelcolor": _INK_SECONDARY,
            "ytick.labelcolor": _INK_SECONDARY,
            "legend.frameon": False,
            "font.size": 10,
        }
    )
