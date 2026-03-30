from typing import Optional

from fastmcp import FastMCP

from tools import (
    ACCESS_PERMISSION,
    DATE_TYPE,
    LOGIC_OPERATOR,
    SEARCH_FILTER,
    get_dataset_details,
    scroll_search,
    search_datasets,
    search_datasets_advanced,
)

mcp = FastMCP(name="datenatlas-zivilgesellschaft", stateless_http=True)


@mcp.tool()
async def piveau_search_datasets(
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
    Search the piveau portal for datasets and related resources.

    Args:
        q: Free-text query, for example "climate berlin"
        filters: Restrict result types, for example ["dataset"] or ["dataset", "catalogue"]
        facets: Structured facet filters, for example {"catalog": ["city-berlin"]}
        page: Zero-based page number
        limit: Maximum number of results to return
        sort: Sort fields such as ["modified+desc"]
        show_score: Include relevance scores when available
        aggregation: Include facet aggregations in the response
        scroll: Enable scroll mode for very large result sets

    Returns:
        Search response object from the piveau search API
    """

    return await search_datasets(
        q=q,
        filters=filters,
        facets=facets,
        page=page,
        limit=limit,
        sort=sort,
        show_score=show_score,
        aggregation=aggregation,
        scroll=scroll,
    )


@mcp.tool()
async def piveau_search_datasets_advanced(
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
    Run an advanced piveau search with structured filters and cursor-style pagination.

    Use this when the simple search tool is not enough and the query needs date
    ranges, bounding boxes, field selection, vocabulary filters, or explicit
    `searchAfter` pagination.
    """

    return await search_datasets_advanced(
        q=q,
        filters=filters,
        facets=facets,
        page=page,
        limit=limit,
        fields=fields,
        includes=includes,
        sort=sort,
        min_date=min_date,
        max_date=max_date,
        date_type=date_type,
        bbox_min_lon=bbox_min_lon,
        bbox_max_lon=bbox_max_lon,
        bbox_min_lat=bbox_min_lat,
        bbox_max_lat=bbox_max_lat,
        min_scoring=min_scoring,
        max_scoring=max_scoring,
        boost=boost,
        global_aggregation=global_aggregation,
        facet_operator=facet_operator,
        facet_group_operator=facet_group_operator,
        filter_distributions=filter_distributions,
        aggregation=aggregation,
        aggregation_all_fields=aggregation_all_fields,
        aggregation_fields=aggregation_fields,
        country_data=country_data,
        data_services=data_services,
        autocomplete=autocomplete,
        show_score=show_score,
        vocabulary=vocabulary,
        resource=resource,
        access_control_permissions=access_control_permissions,
        scroll=scroll,
        search_after=search_after,
        search_after_sort=search_after_sort,
        pit_id=pit_id,
    )


@mcp.tool()
async def piveau_search_scroll(scroll_id: str) -> dict:
    """
    Continue a search that was started with `scroll=true`.

    Args:
        scroll_id: Scroll identifier returned by a previous search response

    Returns:
        The next chunk of search results
    """

    return await scroll_search(scroll_id)


@mcp.tool()
async def piveau_get_dataset_details(dataset_id: str) -> dict:
    """
    Fetch one dataset by ID using the public CKAN-compatible package endpoint.

    Args:
        dataset_id: The dataset identifier returned by search results

    Returns:
        CKAN-compatible dataset response object
    """

    return await get_dataset_details(dataset_id)


def main():
    print("[Datenatlas Zivilgesellschaft MCP] Starting server...")
    try:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=8011)
        print("[Datenatlas Zivilgesellschaft MCP] Finished")
    except Exception as exc:
        print(f"[Datenatlas Zivilgesellschaft MCP] Error: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
