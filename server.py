from typing import Optional

from fastmcp import FastMCP

from tools import (
    export_chart_image,
    get_indicator,
    get_region,
    get_statistics,
    search_indicators,
    search_regions,
)

mcp = FastMCP("wegweiser-kommune")


@mcp.tool()
async def wegweiser_search_regions(
    search: Optional[str] = None,
    max_results: int = 10,
    types: Optional[list[str]] = None,
) -> list[dict]:
    """
    Search for German municipalities (Kommunen) by name.

    Args:
        search: Search text to find municipalities (e.g., "Berlin", "München", "Hamburg")
        max_results: Maximum number of results (default: 10)
        types: Filter by type: BUND, BUNDESLAND, GEMEINDE, KREISFREIE_STADT, LANDKREIS

    Returns:
        List of regions with: name, friendlyUrl, ags (municipal code), type
    """
    return await search_regions(search=search, max_results=max_results, types=types)


@mcp.tool()
async def wegweiser_get_region(friendly_url: str) -> dict:
    """
    Get details about a specific municipality.

    Args:
        friendly_url: The URL identifier (e.g., "berlin", "muenchen", "hamburg")

    Returns:
        Region details: name, title, ags, ars, demographicType, type, parent
    """
    return await get_region(friendly_url)


@mcp.tool()
async def wegweiser_search_indicators(
    search: Optional[str] = None,
    max_results: int = 10,
) -> list[dict]:
    """
    Search for statistical indicators by keyword.

    Args:
        search: Search text (e.g., "Geburten", "Arbeitslosigkeit", "Einkommen", "Bevölkerung")
        max_results: Maximum number of results (default: 10)
    Returns:
        List of indicators with: id, name, friendlyUrl, type
    """
    return await search_indicators(search=search, max_results=max_results)


@mcp.tool()
async def wegweiser_get_indicator(friendly_url: str) -> dict:
    """
    Get detailed metadata about a specific indicator.

    Args:
        friendly_url: The URL identifier (e.g., "geburten", "arbeitslosenquote")


    Returns:
        Indicator details: name, calculation, explanation, source, unit, years, topics
    """
    return await get_indicator(friendly_url)


# Statistics Tools
@mcp.tool()
async def wegweiser_get_statistics(friendly_url: str) -> dict:
    """
    Fetch statistical data for municipalities.

    Build the friendly_url as: "indicator+region1+region2+years+tabelle"

    Args:
        friendly_url: Query string describing what data to fetch.
            Examples:
            - "geburten+berlin+2020+tabelle" (births in Berlin, 2020)
            - "geburten+berlin+muenchen+2018-2020+tabelle" (compare cities over years)
            - "arbeitslosenquote+hamburg+2015-2022+tabelle" (unemployment in Hamburg)

    Returns:
        Statistical data with: indicators (values per region/year), regions, source
    """
    return await get_statistics(friendly_url)


@mcp.tool()
async def wegweiser_get_chart(
    name: str,
    friendly_url: str,
    highlight: Optional[str] = None,
) -> dict:
    """
    Generate a chart image for statistical data.

    Build the friendly_url with a chart type: "liniendiagramm" (line chart) or "balkendiagramm" (bar chart)

    Args:
        name: A descriptive name for the chart
        friendly_url: Query string with chart type at the end.
            Examples:
            - "geburten+berlin+guetersloh-gt+2012-2019+liniendiagramm" (line chart)
            - "arbeitslosenquote+hamburg+muenchen+2015-2020+balkendiagramm" (bar chart)
        highlight: Comma-separated elements to highlight (from the legend), optional

    Returns:
        Dict with: name, image_base64, content_type, size_bytes
    """
    result = await export_chart_image(
        friendly_url=friendly_url,
        format="png",
        width=600,
        raw=False,
        highlight=highlight,
    )
    result["name"] = name
    return result


def main():
    print("[Wegweiser Kommune MCP] Starting server...")
    try:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=8011)
        print("[Wegweiser Kommune MCP] Finished")
    except Exception as e:
        print(f"[Wegweiser Kommune MCP] Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
