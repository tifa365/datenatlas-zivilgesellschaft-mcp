# Datenatlas Zivilgesellschaft MCP

FastMCP server for the Bertelsmann Datenatlas Zivilgesellschaft search stack.

This repository exposes a narrow, AI-facing MCP surface on top of the Datenatlas
piveau search API. It is intentionally optimized for LLM clients such as ChatGPT
or Claude: simple dataset discovery first, advanced search as an escape hatch,
scroll continuation for large result sets, and public dataset detail lookup.

## Scope

This server is specific to the Bertelsmann Datenatlas Zivilgesellschaft
deployment. By default it talks to:

`https://piveau-search.datenkatalog.datenatlas-zivilgesellschaft.de`

The implementation still supports an override for development or compatible
deployments, but the Bertelsmann endpoint is the default behavior.

The server listens locally on port `8011` and serves FastMCP over:

`http://127.0.0.1:8011/mcp`

## MCP Tool Surface

Primary tools:

- `piveau_search_datasets`
  Default entry point for keyword-based dataset discovery.
- `piveau_search_datasets_advanced`
  Structured search with field selection, date filters, scoring filters, bounding
  boxes, aggregations, and cursor-style pagination controls.
- `piveau_search_scroll`
  Continue a search started with `scroll=true`.
- `piveau_get_dataset_details`
  Fetch dataset details from the public CKAN-compatible endpoint.

Not exposed as a primary MCP tool:

- `autocomplete_location`
  Still exists in the Python helper layer, but is not part of the primary MCP
  surface because it is less useful for AI clients than for human typing UIs.

## Which Tool To Use

Use `piveau_search_datasets` first for almost everything.

Use `piveau_search_datasets_advanced` only when the query needs one or more of:

- explicit field selection via `includes` or `fields`
- date filtering
- bounding box filtering
- scoring filters
- fine-grained aggregation control
- `searchAfter` pagination controls

Use `piveau_search_scroll` only after a prior search returned a `scrollId`.

Use `piveau_get_dataset_details` after search has already identified a concrete
dataset id.

## Example MCP Calls

Simple search:

```json
{
  "name": "piveau_search_datasets",
  "arguments": {
    "q": "zivilgesellschaft",
    "filters": ["dataset"],
    "limit": 3
  }
}
```

Advanced search:

```json
{
  "name": "piveau_search_datasets_advanced",
  "arguments": {
    "q": "zivilgesellschaft",
    "filters": ["dataset"],
    "includes": ["id", "title", "description"],
    "show_score": true,
    "aggregation": true,
    "limit": 3
  }
}
```

Dataset details:

```json
{
  "name": "piveau_get_dataset_details",
  "arguments": {
    "dataset_id": "transformationsindex-bti"
  }
}
```

## Runtime Configuration

Default outbound API target:

- `https://piveau-search.datenkatalog.datenatlas-zivilgesellschaft.de`

Optional overrides:

- `PIVEAU_SEARCH_BASE_URL`
  Override the default search endpoint.
- `PIVEAU_API_KEY`
  Add an `X-API-Key` header when needed.
- `PIVEAU_BEARER_TOKEN`
  Add an `Authorization: Bearer ...` header when needed.

Behavior:

- if `PIVEAU_SEARCH_BASE_URL` is not set, the server uses the Bertelsmann
  Datenatlas endpoint automatically
- auth is optional for the current read-only MCP surface

## Prerequisites

For local development:

- `uv` installed locally

For containerized runs:

- Docker with Compose support

## Run Locally

Install dependencies and start the server:

```bash
uv sync
uv run python3 server.py
```

The MCP endpoint is available at `http://127.0.0.1:8011/mcp`.

## Run With Docker

Build the image and start the server:

```bash
docker compose up --build
```

The MCP endpoint is available at `http://127.0.0.1:8011/mcp`.

## Testing

Run the full test suite:

```bash
uv run python3 -m unittest discover -s tests
uv run python3 -m py_compile server.py tools.py tests/test_tools.py tests/test_live_integration.py
```

Test coverage currently includes:

- unit tests for request construction, validation, auth headers, and error paths
- live integration tests against the Bertelsmann deployment
- end-to-end MCP transport checks against the Dockerized server

Known upstream caveat:

- the Bertelsmann `/gazetteer/autocomplete` endpoint currently returns `500`
  upstream, which is why autocomplete is not part of the primary MCP surface and
  related live tests may skip when that endpoint is unavailable
