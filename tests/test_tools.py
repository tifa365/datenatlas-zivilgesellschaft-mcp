import json
import os
import unittest
from unittest.mock import patch

import httpx

import tools


class RecordingAsyncClient:
    instances = []
    response_factory = None

    def __init__(self, *, timeout, headers):
        self.timeout = timeout
        self.headers = headers
        self.calls = []
        RecordingAsyncClient.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def request(self, method, url, params=None, json=None):
        call = {
            "method": method,
            "url": url,
            "params": params,
            "json": json,
        }
        self.calls.append(call)

        if RecordingAsyncClient.response_factory is None:
            request = httpx.Request(method, url, params=params)
            return httpx.Response(200, request=request, json={"success": True})

        return RecordingAsyncClient.response_factory(method, url, params, json)


class ToolsTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        RecordingAsyncClient.instances = []
        RecordingAsyncClient.response_factory = None

    async def test_search_datasets_uses_get_search_endpoint(self):
        def response_factory(method, url, params, json_body):
            request = httpx.Request(method, url, params=params)
            return httpx.Response(200, request=request, json={"result": []})

        RecordingAsyncClient.response_factory = response_factory

        with patch.dict(
            os.environ,
            {tools.BASE_URL_ENV: "https://search.example"},
            clear=False,
        ), patch("tools.httpx.AsyncClient", RecordingAsyncClient):
            result = await tools.search_datasets(
                q="climate berlin",
                filters=["dataset", "catalogue"],
                facets={"catalog": ["berlin"]},
                sort=["modified+desc"],
                show_score=True,
                aggregation=False,
                scroll=True,
            )

        self.assertEqual(result, {"result": []})
        client = RecordingAsyncClient.instances[0]
        self.assertEqual(client.calls[0]["method"], "GET")
        self.assertEqual(client.calls[0]["url"], "https://search.example/search")
        self.assertEqual(
            client.calls[0]["params"],
            {
                "q": "climate berlin",
                "filters": "dataset,catalogue",
                "facets": json.dumps({"catalog": ["berlin"]}),
                "page": 0,
                "limit": 10,
                "sort": "modified+desc",
                "showScore": "true",
                "aggregation": "false",
                "scroll": "true",
            },
        )

    async def test_search_datasets_advanced_uses_post_search_endpoint(self):
        def response_factory(method, url, params, json_body):
            request = httpx.Request(method, url)
            return httpx.Response(200, request=request, json={"hits": {"total": 1}})

        RecordingAsyncClient.response_factory = response_factory

        with patch.dict(
            os.environ,
            {tools.BASE_URL_ENV: "https://search.example"},
            clear=False,
        ), patch("tools.httpx.AsyncClient", RecordingAsyncClient):
            result = await tools.search_datasets_advanced(
                q="mobility",
                filters=["dataset"],
                fields=["title"],
                includes=["title", "description"],
                min_date="2024-01-01T00:00:00Z",
                max_date="2024-12-31T23:59:59Z",
                bbox_min_lon=13.0,
                bbox_max_lon=14.0,
                bbox_min_lat=52.0,
                bbox_max_lat=53.0,
                min_scoring=60,
                max_scoring=100,
                vocabulary=["licenses"],
                access_control_permissions=["view"],
                search_after=True,
                search_after_sort=["123", "abc"],
                pit_id="pit-1",
            )

        self.assertEqual(result, {"hits": {"total": 1}})
        client = RecordingAsyncClient.instances[0]
        self.assertEqual(client.calls[0]["method"], "POST")
        self.assertEqual(client.calls[0]["url"], "https://search.example/search")
        self.assertIsNone(client.calls[0]["params"])
        self.assertEqual(
            client.calls[0]["json"],
            {
                "q": "mobility",
                "filters": ["dataset"],
                "page": 0,
                "limit": 10,
                "fields": ["title"],
                "includes": ["title", "description"],
                "searchParams": {
                    "minDate": "2024-01-01T00:00:00Z",
                    "maxDate": "2024-12-31T23:59:59Z",
                    "boundingBox": {
                        "minLon": 13.0,
                        "maxLon": 14.0,
                        "minLat": 52.0,
                        "maxLat": 53.0,
                    },
                    "scoring": {"min": 60, "max": 100},
                },
                "globalAggregation": True,
                "facetOperator": "OR",
                "facetGroupOperator": "AND",
                "filterDistributions": False,
                "aggregation": True,
                "aggregationAllFields": True,
                "scroll": False,
                "autocomplete": False,
                "showScore": False,
                "vocabulary": ["licenses"],
                "accessControlPermissions": ["view"],
                "searchAfter": True,
                "searchAfterSort": ["123", "abc"],
                "pitId": "pit-1",
                "minScoring": 60,
                "maxScoring": 100,
                "dataServices": False,
            },
        )

    async def test_search_datasets_advanced_requires_pit_and_sort_together(self):
        with patch.dict(
            os.environ,
            {tools.BASE_URL_ENV: "https://search.example"},
            clear=False,
        ):
            with self.assertRaises(ValueError):
                await tools.search_datasets_advanced(
                    search_after=True,
                    search_after_sort=["abc"],
                )

            with self.assertRaises(ValueError):
                await tools.search_datasets_advanced(
                    search_after=True,
                    pit_id="pit-only",
                )

    async def test_scroll_search_uses_scroll_endpoint(self):
        def response_factory(method, url, params, json_body):
            request = httpx.Request(method, url, params=params)
            return httpx.Response(200, request=request, json={"scroll": "next"})

        RecordingAsyncClient.response_factory = response_factory

        with patch.dict(
            os.environ,
            {tools.BASE_URL_ENV: "https://search.example"},
            clear=False,
        ), patch("tools.httpx.AsyncClient", RecordingAsyncClient):
            result = await tools.scroll_search("scroll-123")

        self.assertEqual(result, {"scroll": "next"})
        client = RecordingAsyncClient.instances[0]
        self.assertEqual(client.calls[0]["url"], "https://search.example/scroll")
        self.assertEqual(client.calls[0]["params"], {"scrollId": "scroll-123"})

    async def test_autocomplete_location_uses_gazetteer_endpoint(self):
        def response_factory(method, url, params, json_body):
            request = httpx.Request(method, url, params=params)
            return httpx.Response(200, request=request, json={"items": ["Berlin"]})

        RecordingAsyncClient.response_factory = response_factory

        with patch.dict(
            os.environ,
            {tools.BASE_URL_ENV: "https://search.example"},
            clear=False,
        ), patch("tools.httpx.AsyncClient", RecordingAsyncClient):
            result = await tools.autocomplete_location("Berl")

        self.assertEqual(result, {"items": ["Berlin"]})
        client = RecordingAsyncClient.instances[0]
        self.assertEqual(
            client.calls[0]["url"],
            "https://search.example/gazetteer/autocomplete",
        )
        self.assertEqual(client.calls[0]["params"], {"q": "Berl"})

    async def test_get_dataset_details_uses_public_ckan_endpoint(self):
        def response_factory(method, url, params, json_body):
            request = httpx.Request(method, url, params=params)
            return httpx.Response(200, request=request, json={"result": {"id": "ds-1"}})

        RecordingAsyncClient.response_factory = response_factory

        with patch.dict(
            os.environ,
            {tools.BASE_URL_ENV: "https://search.example"},
            clear=False,
        ), patch("tools.httpx.AsyncClient", RecordingAsyncClient):
            result = await tools.get_dataset_details("ds-1")

        self.assertEqual(result, {"result": {"id": "ds-1"}})
        client = RecordingAsyncClient.instances[0]
        self.assertEqual(
            client.calls[0]["url"],
            "https://search.example/ckan/package_show",
        )
        self.assertEqual(client.calls[0]["params"], {"id": "ds-1"})

    async def test_request_adds_optional_auth_headers(self):
        def response_factory(method, url, params, json_body):
            request = httpx.Request(method, url)
            return httpx.Response(200, request=request, json={"ok": True})

        RecordingAsyncClient.response_factory = response_factory

        with patch.dict(
            os.environ,
            {
                tools.BASE_URL_ENV: "https://search.example",
                tools.API_KEY_ENV: "api-key-1",
                tools.BEARER_TOKEN_ENV: "token-1",
            },
            clear=False,
        ), patch("tools.httpx.AsyncClient", RecordingAsyncClient):
            await tools.search_datasets(q="energy")

        client = RecordingAsyncClient.instances[0]
        self.assertEqual(client.headers["X-API-Key"], "api-key-1")
        self.assertEqual(client.headers["Authorization"], "Bearer token-1")
        self.assertEqual(client.headers["Accept"], "application/json")

    async def test_uses_default_base_url_when_env_is_not_set(self):
        def response_factory(method, url, params, json_body):
            request = httpx.Request(method, url, params=params)
            return httpx.Response(200, request=request, json={"ok": True})

        RecordingAsyncClient.response_factory = response_factory

        with patch.dict(os.environ, {}, clear=True):
            with patch("tools.httpx.AsyncClient", RecordingAsyncClient):
                await tools.search_datasets(q="water")

        client = RecordingAsyncClient.instances[0]
        self.assertEqual(
            client.calls[0]["url"],
            f"{tools.DEFAULT_BASE_URL}/search",
        )

    async def test_http_error_is_raised_with_context(self):
        def response_factory(method, url, params, json_body):
            request = httpx.Request(method, url, params=params)
            return httpx.Response(
                403,
                request=request,
                json={"message": "forbidden"},
            )

        RecordingAsyncClient.response_factory = response_factory

        with patch.dict(
            os.environ,
            {tools.BASE_URL_ENV: "https://search.example"},
            clear=False,
        ), patch("tools.httpx.AsyncClient", RecordingAsyncClient):
            with self.assertRaises(RuntimeError) as ctx:
                await tools.search_datasets(q="restricted")

        self.assertIn("403", str(ctx.exception))
        self.assertIn("/search", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
