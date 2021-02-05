from __future__ import annotations

from datetime import datetime
from typing import Union, Dict, Any, Literal, cast, TYPE_CHECKING

from .enums import Language
from .champion import Champion
from .utils import _convert_timestamp
from .mixins import APIClient, CacheObject

if TYPE_CHECKING:
    from .api import PaladinsAPI


__all__ = ["BountyItem"]


class BountyItem(APIClient):
    """
    Represents a bounty store item deal.

    Attributes
    ----------
    active : bool
        `True` if this deal hasn't expired yet, `False` otherwise.
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
        The initial deal price.\n
        ``0`` is returned for active deals.
    final_price : int
        The final deal price.\n
        ``0`` is returned for active deals.

    .. note::

        All active deals have their prices hidden, and remaining quantity is missing altogether.
        This is a limitation of the Hi-Rez API, not the library.
    """
    def __init__(self, api: PaladinsAPI, language: Language, data: Dict[str, Any]):
        super().__init__(api)
        self.active: bool = data["active"] == 'y'
        self.item = CacheObject(id=data["bounty_item_id2"], name=data["bounty_item_name"])
        self.expires: datetime = cast(
            datetime, _convert_timestamp(data["sale_end_datetime"])
        )
        self.sale_type: Literal["Increasing", "Decreasing"] = data["sale_type"]
        # handle prices
        initial: str = data["initial_price"]
        final: str = data["final_price"]
        self.initial_price: int = int(initial) if initial.isdecimal() else 0
        self.final_price: int = int(final) if final.isdecimal() else 0
        # handle champion
        champion = api.get_champion(data["champion_id"], language)
        if champion:
            self.champion: Union[Champion, CacheObject] = champion
        else:
            self.champion = CacheObject(
                id=data["champion_id"], name=data["champion_name"]
            )
