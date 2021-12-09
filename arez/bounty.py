from __future__ import annotations

from datetime import datetime
from typing import Optional, Union, Literal, TYPE_CHECKING

from .utils import _convert_timestamp
from .mixins import CacheClient, CacheObject

if TYPE_CHECKING:
    from . import responses
    from .champion import Champion
    from .cache import DataCache, CacheEntry


__all__ = ["BountyItem"]


class BountyItem(CacheClient):
    """
    Represents a bounty store item deal.

    Attributes
    ----------
    active : bool
        `True` if this deal is available and hasn't expired yet, `False` otherwise.
    item : CacheObject
        The item available for sale, with both ID and name set.
    champion : Union[Champion, CacheObject]
        The champion this item belongs to.\n
        With incomplete cache, this will be a `CacheObject` with the name and ID set.
    expires : datetime
        A timestamp indicating when this deal will expire.
    sale_type : Literal["Increasing", "Decreasing"]
        The type of this bounty deal.
    initial_price : int
        The initial deal price.
    final_price : Optional[int]
        The final deal price.\n
        Due to API restrictions, this can be `None` for active deals.
    """
    def __init__(
        self, api: DataCache, cache_entry: Optional[CacheEntry], data: responses.BountyItemObject
    ):
        super().__init__(api)
        self.active: bool = data["active"] == 'y'
        self.item = CacheObject(id=data["bounty_item_id2"], name=data["bounty_item_name"])
        self.expires: datetime = _convert_timestamp(data["sale_end_datetime"])
        self.sale_type: Literal["Increasing", "Decreasing"] = data["sale_type"]
        # handle prices
        self.initial_price: int = int(data["initial_price"])
        final: str = data["final_price"]
        self.final_price: Optional[int] = int(final) if final.isdecimal() else None
        # handle champion
        champion: Optional[Union[Champion, CacheObject]] = None
        if cache_entry is not None:
            champion = cache_entry.champions.get(data["champion_id"])
        if champion is None:
            champion = CacheObject(id=data["champion_id"], name=data["champion_name"])
        self.champion: Union[Champion, CacheObject] = champion
