"""Base class of the v1 resource interfaces."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import ItemsView, Iterator, ValuesView
from typing import TYPE_CHECKING, Any, Generic, final

from ...interfaces.api_handlers import ItemEvent, SubscriptionHandler
from ...models.api import ApiItemT
from .models.api import MAX_PAGE_LIMIT

if TYPE_CHECKING:
    from .api_client import ApiClient
    from .models.api import ApiRequest


class APIHandler(SubscriptionHandler, Generic[ApiItemT]):
    """A cache of one resource, kept fresh by polling.

    The v1 API has no websocket, so `update` is the only source of change.
    It walks every page of the list endpoint and then drops any item the
    console no longer lists, signalling `DELETED` for each, so subscribers
    see a client leave the way they would over the legacy websocket.
    """

    item_cls: type[ApiItemT]
    obj_id_key: str

    def __init__(self, api_client: ApiClient) -> None:
        """Initialize."""
        super().__init__()
        self.api_client = api_client
        self._items: dict[str, ApiItemT] = {}

    @abstractmethod
    def list_request(self, offset: int, limit: int) -> ApiRequest:
        """Return the list request for one page."""

    def normalize_obj_id(self, obj_id: str) -> str:
        """Canonical form of an object ID, for storage and lookup."""
        return obj_id

    @final
    async def update(self) -> None:
        """Fetch every page and reconcile the cache with it."""
        offset = 0
        seen: set[str] = set()
        while True:
            response = await self.api_client.request(
                self.list_request(offset, MAX_PAGE_LIMIT)
            )
            page = response["data"]
            for raw in page:
                if (obj_id := self.process_item(raw)) is not None:
                    seen.add(obj_id)
            offset += len(page)
            if not page or offset >= response.get("totalCount", 0):
                break

        for obj_id in [obj_id for obj_id in self._items if obj_id not in seen]:
            self._items.pop(obj_id)
            self.signal_subscribers(ItemEvent.DELETED, obj_id)

    @final
    def process_item(self, raw: dict[str, Any]) -> str | None:
        """Store one item and tell subscribers. Returns its ID."""
        if self.obj_id_key not in raw:
            return None
        obj_id = self.normalize_obj_id(raw[self.obj_id_key])
        obj_is_known = obj_id in self._items
        self._items[obj_id] = self.item_cls(raw)
        self.signal_subscribers(
            ItemEvent.CHANGED if obj_is_known else ItemEvent.ADDED, obj_id
        )
        return obj_id

    @final
    def items(self) -> ItemsView[str, ApiItemT]:
        """Return items dictionary."""
        return self._items.items()

    @final
    def values(self) -> ValuesView[ApiItemT]:
        """Return items."""
        return self._items.values()

    @final
    def get(self, obj_id: str, default: Any | None = None) -> ApiItemT | None:
        """Get item value based on key, return default if no match."""
        return self._items.get(self.normalize_obj_id(obj_id), default)

    @final
    def __contains__(self, obj_id: str) -> bool:
        """Validate membership of item ID."""
        return self.normalize_obj_id(obj_id) in self._items

    @final
    def __getitem__(self, obj_id: str) -> ApiItemT:
        """Get item value based on key."""
        return self._items[self.normalize_obj_id(obj_id)]

    @final
    def __iter__(self) -> Iterator[str]:
        """Allow iterate over items."""
        return iter(self._items)
