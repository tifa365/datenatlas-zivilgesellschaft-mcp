"""
Bertelsmann Datenatlas Zivilgesellschaft MCP helpers.

This module implements a focused, AI-facing subset of the Datenatlas piveau
search API: search, advanced search, scroll pagination, a location helper, and
public CKAN-compatible dataset detail lookup.
"""

from __future__ import annotations

import json
import os
from typing import Any, Literal, Optional

import httpx

SEARCH_FILTER = Literal["catalogue", "dataset", "dataservice", "resource", "vocabulary"]
DATE_TYPE = Literal["issued", "modified", "temporal"]
LOGIC_OPERATOR = Literal["AND", "OR"]
ACCESS_PERMISSION = Literal["view", "edit", "publish", "delete"]

DEFAULT_BASE_URL = "https://piveau-search.datenkatalog.datenatlas-zivilgesellschaft.de"
BASE_URL_ENV = "PIVEAU_SEARCH_BASE_URL"
API_KEY_ENV = "PIVEAU_API_KEY"
BEARER_TOKEN_ENV = "PIVEAU_BEARER_TOKEN"
DEFAULT_TIMEOUT_SECONDS = 30.0


def _base_url() -> str:
    configured_base_url = os.getenv(BASE_URL_ENV, "").strip().rstrip("/")
    if configured_base_url:
        return configured_base_url
    return DEFAULT_BASE_URL


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}

    api_key = os.getenv(API_KEY_ENV, "").strip()
    bearer_token = os.getenv(BEARER_TOKEN_ENV, "").strip()

    if api_key:
        headers["X-API-Key"] = api_key
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    return headers


def _compact(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item is not None}


def _normalize_query_params(params: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}

    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            normalized[key] = str(value).lower()
        elif isinstance(value, list):
            normalized[key] = ",".join(str(item) for item in value)
        elif isinstance(value, dict):
            normalized[key] = json.dumps(value)
        else:
            normalized[key] = value

    return normalized


async def _request(
    method: str,
    path: str,
    *,
    params: Optional[dict[str, Any]] = None,
    json_body: Optional[dict[str, Any]] = None,
) -> Any:
    url = f"{_base_url()}{path}"

    async with httpx.AsyncClient(
        timeout=DEFAULT_TIMEOUT_SECONDS,
        headers=_headers(),
    ) as client:
        response = await client.request(method, url, params=params, json=json_body)

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text.strip()
        raise RuntimeError(
            f"piveau request failed with {exc.response.status_code} for {path}: {detail}"
        ) from exc

    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        return response.json()

    return {
        "content_type": content_type,
        "content": response.text,
    }


async def search_datasets(
    q: Optional[str] = None,
    filters: Optional[list[SEARCH_FILTER]] = None,
    facets: Optional[dict[str, list[str]]] = None,
    page: int = 0,
    limit: int = 10,
    sort: Optional[list[str]] = None,
    show_score: bool = False,
    aggregation: bool = True,
    scroll: bool = False,
) -> dict:
    """
    Run a basic dataset search against the piveau search API.

    This tool is intended for the common case: keyword search with optional
    content-type filters, facets, sorting, and aggregation.
    """

    params = _normalize_query_params(
        {
            "q": q,
            "filters": filters,
            "facets": facets,
            "page": page,
            "limit": limit,
            "sort": sort,
            "showScore": show_score,
            "aggregation": aggregation,
            "scroll": scroll,
        }
    )
    return await _request("GET", "/search", params=params)


async def search_datasets_advanced(
    q: Optional[str] = None,
    filters: Optional[list[SEARCH_FILTER]] = None,
    facets: Optional[dict[str, list[str]]] = None,
    page: int = 0,
    limit: int = 10,
    fields: Optional[list[str]] = None,
    includes: Optional[list[str]] = None,
    sort: Optional[list[str]] = None,
    min_date: Optional[str] = None,
    max_date: Optional[str] = None,
    date_type: Optional[DATE_TYPE] = None,
    bbox_min_lon: Optional[float] = None,
    bbox_max_lon: Optional[float] = None,
    bbox_min_lat: Optional[float] = None,
    bbox_max_lat: Optional[float] = None,
    min_scoring: Optional[int] = None,
    max_scoring: Optional[int] = None,
    boost: Optional[dict[str, float]] = None,
    global_aggregation: bool = True,
    facet_operator: LOGIC_OPERATOR = "OR",
    facet_group_operator: LOGIC_OPERATOR = "AND",
    filter_distributions: bool = False,
    aggregation: bool = True,
    aggregation_all_fields: bool = True,
    aggregation_fields: Optional[list[str]] = None,
    country_data: Optional[bool] = None,
    data_services: bool = False,
    autocomplete: bool = False,
    show_score: bool = False,
    vocabulary: Optional[list[str]] = None,
    resource: Optional[list[str]] = None,
    access_control_permissions: Optional[list[ACCESS_PERMISSION]] = None,
    scroll: bool = False,
    search_after: bool = False,
    search_after_sort: Optional[list[str]] = None,
    pit_id: Optional[str] = None,
) -> dict:
    """
    Run the full search body supported by the OpenAPI spec.

    Use this when keyword search needs date ranges, bounding boxes, field
    selection, advanced facet control, or cursor-style pagination.
    """

    if (search_after_sort and not pit_id) or (pit_id and not search_after_sort):
        raise ValueError("`pit_id` and `search_after_sort` must be provided together.")

    search_params = _compact(
        {
            "minDate": min_date,
            "maxDate": max_date,
            "boundingBox": _compact(
                {
                    "minLon": bbox_min_lon,
                    "maxLon": bbox_max_lon,
                    "minLat": bbox_min_lat,
                    "maxLat": bbox_max_lat,
                }
            )
            or None,
            "scoring": _compact({"min": min_scoring, "max": max_scoring}) or None,
        }
    )

    body = _compact(
        {
            "q": q,
            "filters": filters,
            "facets": facets,
            "page": page,
            "limit": limit,
            "fields": fields,
            "includes": includes,
            "sort": sort,
            "searchParams": search_params or None,
            "dateType": date_type,
            "boost": boost,
            "globalAggregation": global_aggregation,
            "facetOperator": facet_operator,
            "facetGroupOperator": facet_group_operator,
            "filterDistributions": filter_distributions,
            "aggregation": aggregation,
            "aggregationAllFields": aggregation_all_fields,
            "aggregationFields": aggregation_fields,
            "countryData": country_data,
            "dataServices": data_services,
            "autocomplete": autocomplete,
            "showScore": show_score,
            "vocabulary": vocabulary,
            "resource": resource,
            "accessControlPermissions": access_control_permissions,
            "scroll": scroll,
            "searchAfter": search_after,
            "searchAfterSort": search_after_sort,
            "pitId": pit_id,
            "minScoring": min_scoring,
            "maxScoring": max_scoring,
        }
    )
    return await _request("POST", "/search", json_body=body)


async def scroll_search(scroll_id: str) -> dict:
    """Fetch the next page for a search that was started with `scroll=true`."""
    return await _request("GET", "/scroll", params={"scrollId": scroll_id})


async def autocomplete_location(q: str) -> dict:
    """Return gazetteer matches for a place name or partial location query."""
    return await _request("GET", "/gazetteer/autocomplete", params={"q": q})


async def get_dataset_details(dataset_id: str) -> dict:
    """
    Fetch one dataset by ID using the public CKAN-compatible endpoint.

    This keeps the user flow on the anonymous/public side of the search API
    instead of relying on the bearer-protected `/datasets/{id}` endpoint.
    """
    return await _request("GET", "/ckan/package_show", params={"id": dataset_id})
