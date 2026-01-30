"""
Wegweiser Kommune MCP Tools

Core tools for accessing statistical data about German municipalities
from the Bertelsmann Stiftung Wegweiser Kommune API.
"""

import base64
from typing import Optional

import httpx

BASE_URL = "https://www.wegweiser-kommune.de/data-api"


async def _make_request(
    method: str,
    endpoint: str,
    params: Optional[dict] = None,
    json_body: Optional[dict] = None,
) -> dict | list | str:
    """Make an HTTP request to the Wegweiser Kommune API."""
    url = f"{BASE_URL}{endpoint}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "GET":
            response = await client.get(url, params=params)
        elif method == "POST":
            response = await client.post(url, params=params, json=json_body)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text


async def search_regions(
    search: Optional[str] = None,
    max_results: int = 10,
    types: Optional[list[str]] = None,
    exclude_ids: Optional[list[int]] = None,
) -> list[dict]:
    """
    Search for municipalities (Kommunen) by name or filter criteria.

    Args:
        search: Optional search text to find matching municipalities
        max_results: Maximum number of results to return (default: 10)
        types: Filter by region types. Options: BUND, BUNDESLAND, GEMEINDE,
               KLEINE_GEMEINDE, KREISFREIE_STADT, LANDKREIS
        exclude_ids: List of region IDs to exclude from results

    Returns:
        List of matching regions with their metadata (name, friendlyUrl, ags, ars, type, etc.)
    """
    params = {"max": max_results}
    if search:
        params["search"] = search
    if types:
        params["types"] = types
    if exclude_ids:
        params["exclude"] = exclude_ids

    return await _make_request("GET", "/rest/region/list", params=params)


async def get_region(friendly_url: str) -> dict:
    """
    Get detailed information about a specific municipality.

    Args:
        friendly_url: The URL-friendly identifier of the region
                      (e.g., "berlin", "guetersloh-gt", "nordrhein-westfalen")

    Returns:
        Region details including name, title, ags, ars, demographicType, type, parent
    """
    return await _make_request("GET", f"/rest/region/get/{friendly_url}")


async def filter_regions(
    ags: Optional[list[str]] = None,
    demographic_types: Optional[list[int]] = None,
    parent_ids: Optional[list[int]] = None,
    populations: Optional[list[str]] = None,
    region_types: Optional[list[str]] = None,
) -> dict:
    """
    Advanced filtering of municipalities by various criteria.

    Args:
        ags: AGS/ARS codes to filter by (supports wildcards like "05*" for NRW)
        demographic_types: Filter by demographic type numbers (1-9)
        parent_ids: Filter by parent region IDs
        populations: Population ranges (e.g., "50000-100000")
        region_types: Administrative types (BUND, BUNDESLAND, GEMEINDE, etc.)

    Returns:
        Filter result with friendlyUrl, name, title, and list of matching regions
    """
    body = {}
    if ags:
        body["ags"] = ags
    if demographic_types:
        body["demographicTypes"] = demographic_types
    if parent_ids:
        body["parentIds"] = parent_ids
    if populations:
        body["populations"] = populations
    if region_types:
        body["regionTypes"] = region_types

    return await _make_request("POST", "/rest/region/filter", json_body=body)


async def search_indicators(
    search: Optional[str] = None,
    max_results: int = 10,
    exclude_ids: Optional[list[int]] = None,
) -> list[dict]:
    """
    Search for statistical indicators by keyword.

    Args:
        search: Search text to find matching indicators (e.g., "Geburten", "Frauen")
        max_results: Maximum number of results to return (default: 10)
        exclude_ids: List of indicator IDs to exclude from results

    Returns:
        List of matching indicators with basic metadata
    """
    params = {"max": max_results}
    if search:
        params["search"] = search
    if exclude_ids:
        params["exclude"] = exclude_ids

    return await _make_request("GET", "/rest/indicator/list", params=params)


async def get_indicator(friendly_url: str) -> dict:
    """
    Get detailed metadata about a specific indicator.

    Args:
        friendly_url: The URL-friendly identifier of the indicator (e.g., "geburten")

    Returns:
        Full indicator details including calculation, explanation, source,
        available years, unit, colorSchema, and more
    """
    return await _make_request("GET", f"/rest/indicator/get/{friendly_url}")


async def search_topics(
    search: Optional[str] = None,
    max_results: int = 10,
    exclude_ids: Optional[list[int]] = None,
) -> list[dict]:
    """
    Search for topics (thematic groupings of indicators).

    Args:
        search: Search text to find matching topics (e.g., "Alter", "Wirtschaft")
        max_results: Maximum number of results to return (default: 10)
        exclude_ids: List of topic IDs to exclude from results

    Returns:
        List of matching topics with basic metadata
    """
    params = {"max": max_results}
    if search:
        params["search"] = search
    if exclude_ids:
        params["exclude"] = exclude_ids

    return await _make_request("GET", "/rest/topic/list", params=params)


async def get_topic(friendly_url: str) -> dict:
    """
    Get a topic with its sub-topics and contained indicators.

    Args:
        friendly_url: The URL-friendly identifier of the topic
                      (e.g., "demografische-entwicklung")

    Returns:
        Topic details including name, title, explanation, indicators, and sub-topics
    """
    return await _make_request("GET", f"/rest/topic/get/{friendly_url}")


async def search_topics_and_indicators(
    search: Optional[str] = None,
    max_results: int = 10,
    exclude_indicator_ids: Optional[list[int]] = None,
    exclude_topic_ids: Optional[list[int]] = None,
) -> list[dict]:
    """
    Combined search for both topics and indicators.

    Args:
        search: Search text to find matching topics and indicators
        max_results: Maximum number of results to return (default: 10)
        exclude_indicator_ids: Indicator IDs to exclude
        exclude_topic_ids: Topic IDs to exclude

    Returns:
        List of matching topics and indicators
    """
    params = {"max": max_results}
    if search:
        params["search"] = search
    if exclude_indicator_ids:
        params["excludeIndicator"] = exclude_indicator_ids
    if exclude_topic_ids:
        params["excludeTopic"] = exclude_topic_ids

    return await _make_request("GET", "/rest/indicator/orTopic", params=params)


async def get_statistics(friendly_url: str) -> dict:
    """
    Fetch statistical data using a friendly URL.

    Args:
        friendly_url: Describes the desired topics/indicators, regions, years,
                      and display type. Format matches the statistics page URL.
                      Example: "demografische-entwicklung+berlin+muenchen+2006-2019+tabelle"

    Returns:
        Statistical data response with indicators, regions, values, and metadata
    """
    return await _make_request("GET", f"/rest/statistics/data/{friendly_url}")


async def get_statistics_by_ids(
    region_ids: list[int],
    indicator_ids: Optional[list[int]] = None,
    topic_ids: Optional[list[int]] = None,
    years: Optional[list[int]] = None,
    top_regions_count: Optional[int] = None,
    low_regions_count: Optional[int] = None,
) -> dict:
    """
    Fetch statistical data using database IDs.

    Args:
        region_ids: List of region IDs (required)
        indicator_ids: List of indicator IDs to fetch data for
        topic_ids: List of topic IDs to fetch data for
        years: Specific years to fetch data for
        top_regions_count: Include N regions with highest values for comparison
        low_regions_count: Include N regions with lowest values for comparison

    Returns:
        Statistical data response with indicators, regions, values, and metadata
    """
    body = {"regionIds": region_ids}
    if indicator_ids:
        body["indicatorIds"] = indicator_ids
    if topic_ids:
        body["topicIds"] = topic_ids
    if years:
        body["years"] = years
    if top_regions_count:
        body["topRegionsCount"] = top_regions_count
    if low_regions_count:
        body["lowRegionsCount"] = low_regions_count

    return await _make_request("POST", "/rest/statistics/data", json_body=body)


async def analyze_friendly_url(friendly_url: str) -> dict:
    """
    Parse and analyze a friendly URL to understand its components.

    Args:
        friendly_url: The URL to analyze
                      Example: "demografische-entwicklung+berlin+muenchen+2006-2019+tabelle"

    Returns:
        Parsed components: indicatorsAndTopics, regionsAndRegionFilters, years, renderer, etc.
    """
    return await _make_request("GET", f"/rest/statistics/analyze/{friendly_url}")


async def get_statistic_types() -> list[dict]:
    """
    Get descriptions of all available statistic types.

    Returns:
        List of statistic types with their supported renderers, available years,
        and whether indicators are available
    """
    return await _make_request("GET", "/rest/statistics/types")


async def get_data_version() -> str:
    """
    Get the current version/date of the statistical data.

    Returns:
        Date string indicating when the current data was imported
    """
    return await _make_request("GET", "/rest/statistics/version")


async def list_demographic_types() -> list[dict]:
    """
    Get all demographic types (municipality classifications).

    Returns:
        List of demographic types with number, name, title/description,
        and links to related documents
    """
    return await _make_request("GET", "/rest/demographicTypes")


async def get_demographic_type(number: int) -> dict:
    """
    Get details about a specific demographic type.

    Args:
        number: The demographic type number (1-9)

    Returns:
        Demographic type details including name, title, and document links
    """
    return await _make_request("GET", f"/rest/demographicTypes/{number}")


async def export_statistics(
    friendly_url: str,
    format: str = "json",
    charset: str = "UTF-8",
    raw: bool = False,
) -> dict | str:
    """
    Export statistical data in various formats.

    Args:
        friendly_url: Describes the data to export (same format as statistics page)
        format: Export format - csv, json, xls, xlsx, pdf, png, jpg, gif, svg
        charset: Character encoding (default: UTF-8)
        raw: If True, suppress headers and annotations

    Returns:
        Exported data in the requested format
    """
    params = {"charset": charset, "raw": str(raw).lower()}
    return await _make_request("GET", f"/rest/export/{friendly_url}.{format}", params=params)


async def export_chart_image(
    friendly_url: str,
    format: str = "png",
    width: int = 600,
    raw: bool = False,
    highlight: Optional[str] = None,
) -> dict:
    """
    Export a chart as an image (PNG, JPG, GIF, or SVG).

    Args:
        friendly_url: Describes the data to chart. Use "liniendiagramm" or "balkendiagramm"
                      as the renderer type.
                      Example: "geburten+berlin+guetersloh-gt+2012-2019+liniendiagramm"
        format: Image format - png, jpg, gif, svg (default: png)
        width: Image width in pixels, 256-2048 (default: 800)
        raw: If True, suppress headers and annotations (default: False)
        highlight: Comma-separated elements to highlight (from the legend)

    Returns:
        Dict with image_base64, content_type, and size_bytes
    """

    url = f"{BASE_URL}/rest/export/{friendly_url}.{format}"
    params = {"width": width, "raw": str(raw).lower()}
    if highlight:
        params["highlight"] = highlight

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        image_bytes = response.content
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        return {
            "content_base64": image_base64,
            "content_type": content_type,
            "size_bytes": len(image_bytes),
            "width": width,
            "format": format,
        }
