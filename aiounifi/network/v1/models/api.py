"""Request and response types shared by all Network API v1 resources."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict, cast

import orjson

from ....errors import ResponseError

DEFAULT_PAGE_OFFSET = 0
DEFAULT_PAGE_LIMIT = 25
MAX_PAGE_LIMIT = 200


class ApiResponse(TypedDict):
    """Normalised response.

    List endpoints return this envelope as is. Endpoints that return one
    object, or nothing, are wrapped into the same shape by `ApiRequest.decode`
    so every interface reads `data` the same way.
    """

    data: list[dict[str, Any]]
    offset: NotRequired[int]
    limit: NotRequired[int]
    count: NotRequired[int]
    totalCount: NotRequired[int]


class EntityMetadata(TypedDict):
    """Who made the object: `USER_DEFINED`, `SYSTEM_DEFINED`, and so on."""

    origin: str


class ApiErrorResponse(TypedDict):
    """Error envelope returned with most 4xx and 5xx responses."""

    statusCode: int
    statusName: str
    code: str
    message: str
    timestamp: str
    requestPath: str
    requestId: str


@dataclass
class ApiRequest:
    """One request to the Network API v1."""

    method: str
    path: str
    params: Mapping[str, str | int] | None = None
    data: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        """Reject paths outside the versioned API."""
        if not self.path.startswith("/v1/"):
            raise ValueError(
                f"ApiRequest.path must start with '/v1/', got {self.path!r}"
            )

    def decode(self, raw: bytes) -> ApiResponse:
        """Decode a response body into the normalised envelope."""
        if not raw.strip():
            return ApiResponse(data=[])

        decoded: Any = orjson.loads(raw)

        if isinstance(decoded, dict) and isinstance(decoded.get("data"), list):
            return cast("ApiResponse", decoded)

        if isinstance(decoded, dict):
            return ApiResponse(data=[decoded])

        raise ResponseError(f"Unexpected Network API response for {self.path}")


@dataclass
class SiteResourceRequest(ApiRequest):
    """A request on a collection under `/v1/sites/{site_id}/`.

    Most configuration resources share the same five operations, so they
    share one request type instead of one per resource.
    """

    @classmethod
    def create_list(
        cls,
        site_id: str,
        collection: str,
        offset: int = DEFAULT_PAGE_OFFSET,
        limit: int = DEFAULT_PAGE_LIMIT,
        filter_value: str | None = None,
    ) -> SiteResourceRequest:
        """List one page of the collection."""
        return cls(
            method="get",
            path=f"/v1/sites/{site_id}/{collection}",
            params=page_params(offset, limit, filter_value),
        )

    @classmethod
    def create_get(
        cls, site_id: str, collection: str, obj_id: str
    ) -> SiteResourceRequest:
        """Get one item."""
        return cls(method="get", path=f"/v1/sites/{site_id}/{collection}/{obj_id}")

    @classmethod
    def create_put(
        cls, site_id: str, collection: str, obj_id: str, data: Mapping[str, Any]
    ) -> SiteResourceRequest:
        """Replace one item."""
        return cls(
            method="put", path=f"/v1/sites/{site_id}/{collection}/{obj_id}", data=data
        )

    @classmethod
    def create_patch(
        cls, site_id: str, collection: str, obj_id: str, data: Mapping[str, Any]
    ) -> SiteResourceRequest:
        """Change some fields of one item."""
        return cls(
            method="patch",
            path=f"/v1/sites/{site_id}/{collection}/{obj_id}",
            data=data,
        )

    @classmethod
    def create_post(
        cls, site_id: str, collection: str, data: Mapping[str, Any]
    ) -> SiteResourceRequest:
        """Create items in the collection."""
        return cls(method="post", path=f"/v1/sites/{site_id}/{collection}", data=data)

    @classmethod
    def create_delete(
        cls,
        site_id: str,
        collection: str,
        obj_id: str | None = None,
        filter_value: str | None = None,
    ) -> SiteResourceRequest:
        """Delete one item, or every item matching a filter."""
        path = f"/v1/sites/{site_id}/{collection}"
        if obj_id is not None:
            path = f"{path}/{obj_id}"
        params = {"filter": filter_value} if filter_value else None
        return cls(method="delete", path=path, params=params)


def page_params(
    offset: int = DEFAULT_PAGE_OFFSET,
    limit: int = DEFAULT_PAGE_LIMIT,
    filter_value: str | None = None,
) -> dict[str, str | int]:
    """Build the query parameters of a list request.

    The console clamps `limit` to 200 itself; clamping here keeps the request
    honest about what it will get back.
    """
    params: dict[str, str | int] = {
        "offset": max(offset, DEFAULT_PAGE_OFFSET),
        "limit": max(min(limit, MAX_PAGE_LIMIT), 1),
    }
    if filter_value:
        params["filter"] = filter_value
    return params
