# Datenatlas Zivilgesellschaft MCP

Small FastMCP server for the Bertelsmann Datenatlas Zivilgesellschaft search API.

## Tool Surface

This server intentionally exposes a narrow AI-facing tool set:

- `piveau_search_datasets`
- `piveau_search_datasets_advanced`
- `piveau_search_scroll`
- `piveau_get_dataset_details`

The gazetteer autocomplete helper remains available in the Python client code, but
it is not exposed as a primary MCP tool.

## Runtime Configuration

- Default outbound API base URL:
  `https://piveau-search.datenkatalog.datenatlas-zivilgesellschaft.de`
- Optional override:
  `PIVEAU_SEARCH_BASE_URL`
- Optional auth:
  `PIVEAU_API_KEY`
  `PIVEAU_BEARER_TOKEN`

## Development

Run locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 server.py
```

Run with Docker:

```bash
docker compose up --build
```

The compose setup builds the image from the local [Dockerfile](/home/tim/Projekte/wegweiser-kommune-mcp/Dockerfile), so dependencies are installed at image build time rather than on every container start.

Run tests:

```bash
python3 -m unittest discover -s tests
python3 -m py_compile server.py tools.py tests/test_tools.py tests/test_live_integration.py
```
