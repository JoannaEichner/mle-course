"""A small sequence model: a GRU reads the past, a head writes the next week."""

import torch
from torch import nn


class GRUForecastNet(nn.Module):
    """Forecast ``horizon`` days from a window of past days.

    The GRU reads the past days one by one and ends in a summary vector.
    The head combines that summary with what is known about the forecast
    days (price, promotions, calendar) and with learned embeddings of the
    store and the product, and outputs one number per forecast day, in the
    scaled units of the past target.

    Args:
        past_channels: Channels per past day.
        future_channels: Channels per forecast day.
        horizon: Forecast days.
        n_stores: Number of distinct stores (embedding rows).
        n_products: Number of distinct products.
        hidden: Size of the GRU summary.
        embedding: Size of each embedding.
    """

    def __init__(
        self,
        past_channels: int,
        future_channels: int,
        horizon: int,
        n_stores: int,
        n_products: int,
        hidden: int = 128,
        embedding: int = 16,
    ) -> None:
        raise NotImplementedError("Zadanie 18.4")

    def forward(
        self,
        past: torch.Tensor,
        future: torch.Tensor,
        store: torch.Tensor,
        product: torch.Tensor,
    ) -> torch.Tensor:
        """Return forecasts of shape ``(batch, horizon)``.

        Args:
            past: ``(batch, past_days, past_channels)``.
            future: ``(batch, horizon, future_channels)``.
            store: ``(batch,)`` store codes.
            product: ``(batch,)`` product codes.
        """
        raise NotImplementedError("Zadanie 18.4")
