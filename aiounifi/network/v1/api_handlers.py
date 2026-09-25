"""Base class of the v1 resource interfaces."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import ItemsView, Iterator, ValuesView
from typing import TYPE_CHECKING, Any, Generic, final

from ...interfaces.api_handlers import ItemEvent, SubscriptionHandler
from ...models.api import ApiItemT
from .models.api import MAX_PAGE_LIMIT, SiteResourceRequest

if TYPE_CHECKING:
    from .api_client import ApiClient
    from .models.api import ApiRequest


class APIHandler(SubscriptionHandler, Generic[ApiItemT]):
    """A cache of one resource, kept fresh by polling.

    The v1 API has no websocket, so `update` is the only source of change.
    It walks every page of the list endpoint and then hands every item the
    console no longer lists to `item_missing`, which by default drops it and
    signals `DELETED`.
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
        listed: list[dict[str, Any]] = []
        while True:
            response = await self.api_client.request(
                self.list_request(offset, MAX_PAGE_LIMIT)
            )
            page = response["data"]
            listed.extend(page)
            offset += len(page)
            if not page or offset >= response.get("totalCount", 0):
                break

        seen = {obj_id for raw in listed if (obj_id := self._obj_id(raw)) is not None}
        self.items_listed(seen)
        for raw in listed:
            self.process_item(raw)
        for obj_id in [obj_id for obj_id in self._items if obj_id not in seen]:
            self.item_missing(obj_id)

    def items_listed(self, obj_ids: set[str]) -> None:
        """Handle the IDs a completed `update` listed.

        Called before any item is stored or signalled, so what a subclass
        records here is in place when subscribers hear of the changes.
        """

    def item_missing(self, obj_id: str) -> None:
        """Handle an item the console no longer lists: forget it."""
        self._items.pop(obj_id)
        self.signal_subscribers(ItemEvent.DELETED, obj_id)

    @final
    def _obj_id(self, raw: dict[str, Any]) -> str | None:
        """Return the ID of one raw item, or `None` if it has none."""
        if self.obj_id_key not in raw:
            return None
        return self.normalize_obj_id(raw[self.obj_id_key])

    @final
    def process_item(self, raw: dict[str, Any]) -> str | None:
        """Store one item and tell subscribers. Returns its ID."""
        if (obj_id := self._obj_id(raw)) is None:
            return None
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


class SiteResourceHandler(APIHandler[ApiItemT]):
    """A collection under `/v1/sites/{site_id}/`, keyed by ID."""

    collection: str
    obj_id_key = "id"

    def list_request(self, offset: int, limit: int) -> SiteResourceRequest:
        """Return the list request for one page."""
        return SiteResourceRequest.create_list(
            self.api_client.site_id, self.collection, offset, limit
        )

    async def list_page(
        self,
        offset: int = 0,
        limit: int = 25,
        filter_value: str | None = None,
    ) -> list[ApiItemT]:
        """Return one page without touching the cache."""
        response = await self.api_client.request(
            SiteResourceRequest.create_list(
                self.api_client.site_id, self.collection, offset, limit, filter_value
            )
        )
        return [self.item_cls(raw) for raw in response["data"]]

    async def get_details(self, obj_id: str) -> ApiItemT:
        """Fetch one item with every field and refresh the cache with it."""
        response = await self.api_client.request(
            SiteResourceRequest.create_get(
                self.api_client.site_id, self.collection, obj_id
            )
        )
        raw = response["data"][0]
        self.process_item(raw)
        return self.item_cls(raw)


class ConfigurationHandler(SiteResourceHandler[ApiItemT]):
    """A site collection whose items can be changed and switched on and off.

    The API updates these with PUT, which replaces the whole object, so a
    change of one field is a read-modify-write: fetch the details, drop the
    fields the console sets itself, change the field and send it back.
    """

    read_only_keys: tuple[str, ...] = ("id", "metadata")

    async def update_item(self, obj_id: str, changes: dict[str, Any]) -> ApiItemT:
        """Change top-level fields of one item, keeping the rest as they are."""
        details = await self.get_details(obj_id)
        data = {
            key: value
            for key, value in details.raw.items()
            if key not in self.read_only_keys
        }
        data.update(changes)
        response = await self.api_client.request(
            SiteResourceRequest.create_put(
                self.api_client.site_id, self.collection, obj_id, data
            )
        )
        raw = response["data"][0] if response["data"] else {**details.raw, **changes}
        self.process_item(raw)
        return self.item_cls(raw)

    async def set_enabled(self, obj_id: str, enabled: bool) -> ApiItemT:
        """Enable or disable one item."""
        return await self.update_item(obj_id, {"enabled": enabled})
